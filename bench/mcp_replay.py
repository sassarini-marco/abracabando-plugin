#!/usr/bin/env python3
"""Dependency-free MCP stdio record/replay server for the frozen eval tier.

Two modes:

* **replay** (default) — present as the ``industrial-mcp-free`` server to a
  headless ``claude`` run, serving recorded responses so the frozen tier is
  deterministic, offline and CI-able. ``tools/call`` is matched by
  ``fixture_key(tool, params)`` (sha256 of params with pagination keys stripped
  and nested keys sorted). On a normalized-key miss it falls back to SEQUENTIAL
  matching — the next unconsumed recorded call for that tool name — which
  absorbs LLM argument drift and the pro→free / ``ted_pin_italy`` retries the
  skills perform. A true miss raises ``FixtureMissingError`` → JSON-RPC ``-32000``
  (never a silent empty reply, which would make the skill hallucinate a pass).

* **record** (``--record --case <id>``) — proxy the real ``industrial-mcp``,
  persist the full ordered call sequence per case, and capture ``ted_pin_italy``
  file-path responses by storing the referenced file's content and
  reconstituting it on replay.

The wire protocol is newline-delimited JSON-RPC 2.0: ``initialize`` (echo the
client's protocolVersion), silently consume ``notifications/initialized``,
``tools/list`` from the cached fixture, ``tools/call`` via the replayer.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

BENCH = Path(__file__).resolve().parent
FIXTURES_ROOT = Path(os.environ.get("MCP_REPLAY_FIXTURES", str(BENCH / "fixtures")))
PROTOCOL_VERSION = "2024-11-05"
FILE_SENTINEL = "__FIXTURE_FILE_PATH__"

PAGINATION_KEYS = {"limit", "page", "offset", "sort", "cursor"}


class FixtureMissingError(RuntimeError):
    """No recorded response (keyed or sequential) for a tools/call."""


# --------------------------------------------------------------------------- #
# Keying
# --------------------------------------------------------------------------- #

def _normalize(obj: object) -> object:
    if isinstance(obj, dict):
        return {k: _normalize(v) for k, v in sorted(obj.items()) if k not in PAGINATION_KEYS}
    if isinstance(obj, list):
        return [_normalize(v) for v in obj]
    return obj


def fixture_key(tool: str, params: dict | None) -> str:
    payload = {"tool": tool, "params": _normalize(params or {})}
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Replay
# --------------------------------------------------------------------------- #

class Replayer:
    def __init__(self, calls: list[dict]):
        self.calls = calls
        self.consumed = [False] * len(calls)
        self.by_key: dict[str, list[int]] = {}
        for i, c in enumerate(calls):
            key = c.get("key") or fixture_key(c["tool"], c.get("params"))
            self.by_key.setdefault(key, []).append(i)

    def _materialize(self, idx: int) -> object:
        c = self.calls[idx]
        resp = c["response"]
        if c.get("file_content") is not None:
            tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")  # noqa: SIM115
            tmp.write(c["file_content"])
            tmp.close()
            resp = json.loads(json.dumps(resp).replace(FILE_SENTINEL, tmp.name))
        return resp

    def tools_call(self, tool: str, params: dict | None) -> object:
        key = fixture_key(tool, params)
        # 1. keyed match: first unconsumed call with this key and tool
        for i in self.by_key.get(key, []):
            if not self.consumed[i] and self.calls[i]["tool"] == tool:
                self.consumed[i] = True
                return self._materialize(i)
        # 2. sequential fallback: next unconsumed call for the same tool
        for i, c in enumerate(self.calls):
            if not self.consumed[i] and c["tool"] == tool:
                self.consumed[i] = True
                return self._materialize(i)
        raise FixtureMissingError(
            f"no recorded response for tool={tool!r} params={params!r} "
            f"(keyed miss and sequential exhausted)"
        )


# --------------------------------------------------------------------------- #
# Record
# --------------------------------------------------------------------------- #

def _find_file_path(obj: object) -> str | None:
    """Recursively find a string value that is an existing .json file path."""
    if isinstance(obj, str):
        if obj.endswith(".json") and len(obj) > 5 and os.path.exists(obj):
            return obj
        return None
    if isinstance(obj, dict):
        for v in obj.values():
            found = _find_file_path(v)
            if found:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = _find_file_path(v)
            if found:
                return found
    return None


class Recorder:
    def __init__(self, upstream_call):
        self.upstream_call = upstream_call
        self.calls: list[dict] = []

    def tools_call(self, tool: str, params: dict | None) -> object:
        resp = self.upstream_call(tool, params)
        entry: dict = {
            "tool": tool,
            "params": params,
            "key": fixture_key(tool, params),
            "response": resp,
        }
        path = _find_file_path(resp)
        if path:
            try:
                entry["file_content"] = Path(path).read_text(encoding="utf-8")
                entry["response"] = json.loads(json.dumps(resp).replace(path, FILE_SENTINEL))
            except OSError:
                pass
        self.calls.append(entry)
        return resp

    def dump(self) -> list[dict]:
        return self.calls


# --------------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------------- #

def save_fixture(case_dir: Path, calls: list[dict], tools_list: dict | None = None) -> None:
    case_dir = Path(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "calls.json").write_text(
        json.dumps(calls, ensure_ascii=False, indent=2) + "\n"
    )
    if tools_list is not None:
        (case_dir / "tools_list.json").write_text(
            json.dumps(tools_list, ensure_ascii=False, indent=2) + "\n"
        )


def load_fixture(case_dir: Path) -> tuple[list[dict], dict | None]:
    case_dir = Path(case_dir)
    calls = json.loads((case_dir / "calls.json").read_text())
    tl_path = case_dir / "tools_list.json"
    tools_list = json.loads(tl_path.read_text()) if tl_path.exists() else None
    return calls, tools_list


# --------------------------------------------------------------------------- #
# Minimal stdio JSON-RPC client (used by record mode to proxy real MCP)
# --------------------------------------------------------------------------- #

class StdioUpstream:
    """Talks to the real industrial-mcp over stdio for record mode."""

    def __init__(self, command: str = "industrial-mcp", args: list[str] | None = None):
        self.proc = subprocess.Popen(
            [command, *(args or [])],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
        )
        self._id = 0
        self._init()

    def _send(self, obj: dict) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(obj) + "\n")
        self.proc.stdin.flush()

    def _recv(self, want_id: int) -> dict:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if msg.get("id") == want_id:
                return msg
        raise FixtureMissingError(f"upstream closed before responding to id={want_id}")

    def _init(self) -> None:
        self._id += 1
        self._send({"jsonrpc": "2.0", "id": self._id, "method": "initialize",
                    "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {},
                               "clientInfo": {"name": "mcp-replay-recorder", "version": "1"}}})
        self._recv(self._id)
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def tools_list(self) -> dict:
        self._id += 1
        self._send({"jsonrpc": "2.0", "id": self._id, "method": "tools/list", "params": {}})
        return self._recv(self._id).get("result", {})

    def tools_call(self, tool: str, params: dict | None) -> object:
        self._id += 1
        self._send({"jsonrpc": "2.0", "id": self._id, "method": "tools/call",
                    "params": {"name": tool, "arguments": params or {}}})
        return self._recv(self._id).get("result", {})

    def close(self) -> None:
        self.proc.terminate()


# --------------------------------------------------------------------------- #
# stdio server loop
# --------------------------------------------------------------------------- #

def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def _load_tools_list(case_dir: Path, case_tools_list: dict | None) -> dict:
    """Merge shared tools (full schemas) with per-case tools (skill-specific).

    The shared file has the full tool schemas so ToolSearch can work. The
    per-case file declares tools specific to a new skill not yet in the shared
    list. We merge: start with shared, add any per-case tools not already
    present by name.
    """
    shared = FIXTURES_ROOT / "tools_list.json"
    base: dict = json.loads(shared.read_text()) if shared.exists() else {"tools": []}

    per_case: dict = case_tools_list or {}
    if per_case.get("tools"):
        existing_names = {t["name"] for t in base.get("tools", [])}
        for tool in per_case["tools"]:
            if tool["name"] not in existing_names:
                base.setdefault("tools", []).append(tool)

    return base or {"tools": []}


def serve_replay(case_dir: Path) -> None:
    calls, case_tools_list = load_fixture(case_dir)
    tools_list = _load_tools_list(case_dir, case_tools_list)
    replayer = Replayer(calls)
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        msg = json.loads(raw)
        method = msg.get("method")
        mid = msg.get("id")
        if method == "initialize":
            client_proto = (msg.get("params") or {}).get("protocolVersion", PROTOCOL_VERSION)
            _emit({"jsonrpc": "2.0", "id": mid, "result": {
                "protocolVersion": client_proto,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "mcp-replay", "version": "1"}}})
        elif method == "notifications/initialized":
            continue  # notification: no response
        elif method == "tools/list":
            _emit({"jsonrpc": "2.0", "id": mid, "result": tools_list or {"tools": []}})
        elif method == "tools/call":
            params = msg.get("params") or {}
            tool = params.get("name")
            args = params.get("arguments") or {}
            try:
                result = replayer.tools_call(tool, args)
            except FixtureMissingError as exc:
                _emit({"jsonrpc": "2.0", "id": mid,
                       "error": {"code": -32000, "message": str(exc)}})
                continue
            _emit({"jsonrpc": "2.0", "id": mid, "result": result})
        elif mid is not None:
            _emit({"jsonrpc": "2.0", "id": mid,
                   "error": {"code": -32601, "message": f"method not found: {method}"}})


def serve_record(case_dir: Path) -> None:
    upstream = StdioUpstream()
    recorder = Recorder(lambda t, p: upstream.tools_call(t, p))
    tools_list = upstream.tools_list()
    try:
        for raw in sys.stdin:
            raw = raw.strip()
            if not raw:
                continue
            msg = json.loads(raw)
            method = msg.get("method")
            mid = msg.get("id")
            if method == "initialize":
                client_proto = (msg.get("params") or {}).get("protocolVersion", PROTOCOL_VERSION)
                _emit({"jsonrpc": "2.0", "id": mid, "result": {
                    "protocolVersion": client_proto,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "mcp-replay-record", "version": "1"}}})
            elif method == "notifications/initialized":
                continue
            elif method == "tools/list":
                _emit({"jsonrpc": "2.0", "id": mid, "result": tools_list})
            elif method == "tools/call":
                params = msg.get("params") or {}
                result = recorder.tools_call(params.get("name"), params.get("arguments") or {})
                _emit({"jsonrpc": "2.0", "id": mid, "result": result})
    finally:
        save_fixture(case_dir, recorder.dump(), tools_list)
        upstream.close()


def main(argv: list[str] | None = None) -> None:
    # Line-buffer stdout so replies never hang behind a block buffer.
    with contextlib.suppress(AttributeError):
        sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]

    ap = argparse.ArgumentParser(description="MCP stdio record/replay server.")
    ap.add_argument("--record", action="store_true", help="Proxy the real MCP and record.")
    ap.add_argument("--case", default=os.environ.get("MCP_REPLAY_CASE"),
                    help="Case id whose fixture to use (env: MCP_REPLAY_CASE).")
    ap.add_argument("--fixtures", default=str(FIXTURES_ROOT))
    args = ap.parse_args(argv)

    if not args.case:
        ap.error("--case (or MCP_REPLAY_CASE) is required")
    case_dir = Path(args.fixtures) / args.case

    if args.record:
        serve_record(case_dir)
    else:
        serve_replay(case_dir)


if __name__ == "__main__":
    main()
