#!/usr/bin/env python3
"""Headless benchmark runner for the industrial-procurement plugin.

Runs each Tier 1-5 prompt through Claude Code with the plugin + the
industrial-mcp server wired in, capturing which MCP tools fired, the final
answer, latency and cost. Results land in ``bench/results/``.

Usage:
    python3 bench/run_benchmark.py            # run all prompts
    python3 bench/run_benchmark.py t1-1 t2-2  # run specific ids
    python3 bench/run_benchmark.py --tier 1   # run a whole tier

Each query is run with:
    claude -p "<prompt>" \
        --plugin-dir . \
        --mcp-config bench/mcp.json --strict-mcp-config \
        --allowedTools 'mcp__industrial-mcp-free__*' \
        --output-format stream-json --verbose

``--strict-mcp-config`` guarantees ONLY our fresh local stdio server is used
(no other session MCPs, and the plugin's unbuilt "pro" server is excluded).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

BENCH = Path(__file__).resolve().parent
PLUGIN = BENCH.parent
RESULTS = BENCH / "results"
TIMEOUT = 900  # seconds per query


def load_prompts() -> dict:
    return json.loads((BENCH / "prompts.json").read_text())


def run_one(qid: str, spec: dict) -> dict:
    cmd = [
        "claude", "-p", spec["prompt"],
        "--plugin-dir", ".",
        "--mcp-config", "bench/mcp.json", "--strict-mcp-config",
        "--allowedTools", "mcp__industrial-mcp-free__*",
        "--output-format", "stream-json", "--verbose",
    ]
    start = time.time()
    timed_out = False
    try:
        proc = subprocess.run(
            cmd, cwd=PLUGIN, capture_output=True, text=True, timeout=TIMEOUT
        )
        raw = proc.stdout
        err = proc.stderr
    except subprocess.TimeoutExpired as e:
        raw = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = "TIMEOUT after %ds" % TIMEOUT
        timed_out = True
    elapsed = round(time.time() - start, 1)

    (RESULTS / f"{qid}.jsonl").write_text(raw)

    tools: list[str] = []
    mcp_tools: list[str] = []
    result_text = None
    cost = None
    for line in raw.splitlines():
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get("type") == "assistant":
            for b in o.get("message", {}).get("content", []):
                if b.get("type") == "tool_use":
                    tools.append(b["name"])
                    if b["name"].startswith("mcp__"):
                        mcp_tools.append(b["name"].split("__")[-1])
        elif o.get("type") == "result":
            result_text = o.get("result")
            cost = o.get("total_cost_usd")

    summary = {
        "id": qid,
        "tier": spec["tier"],
        "title": spec["title"],
        "elapsed_s": elapsed,
        "timed_out": timed_out,
        "cost_usd": cost,
        "mcp_tools_fired": mcp_tools,
        "n_tool_calls": len(tools),
        "required_fields": spec.get("required", []),
        "answer": result_text,
        "stderr_tail": (err or "")[-400:],
    }
    (RESULTS / f"{qid}.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*", help="specific prompt ids (default: all)")
    ap.add_argument("--tier", type=int, help="run only this tier")
    args = ap.parse_args()

    prompts = load_prompts()
    ids = args.ids or [
        k for k, v in prompts.items() if args.tier is None or v["tier"] == args.tier
    ]
    RESULTS.mkdir(exist_ok=True)

    print(f"Running {len(ids)} prompt(s): {', '.join(ids)}\n")
    for qid in ids:
        if qid not in prompts:
            print(f"  ! unknown id {qid}, skipping")
            continue
        print(f"▶ {qid} (Tier {prompts[qid]['tier']}): {prompts[qid]['title']}")
        s = run_one(qid, prompts[qid])
        flag = "⏱ TIMEOUT" if s["timed_out"] else "✓"
        print(f"  {flag} {s['elapsed_s']}s | ${s['cost_usd']} | tools: {s['mcp_tools_fired'] or '—'}")
        print()

    print(f"Done. Per-query JSON + raw JSONL in {RESULTS}")


if __name__ == "__main__":
    main()
