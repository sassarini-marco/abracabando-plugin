#!/usr/bin/env python3
"""Capture the independent frozen golden for eval cases.

For each case this fetches the RAW upstream API response **directly** — TED /
ANAC / PNRR HTTP JSON — deliberately bypassing the ``industrial-mcp`` server so
that MCP transform/staleness bugs cannot hide inside the oracle. Raw payloads
land under ``cases/<case_id>/raw_<source>.json`` and a ``PROVENANCE.md`` row
records the source URL + capture date.

The captured records still require **hand-verification** before the golden is
trusted (see bench/REFRESH_PROCEDURE.md §2): a human confirms the records are
real and correct, then fills ``golden.json``'s ``records`` / ``empty_reason``.

A case declares what to fetch via an optional ``golden_capture`` block in
``bench/cases/eval_dataset.json``:

    "golden_capture": [
      {"source": "ted", "method": "POST",
       "url": "https://api.ted.europa.eu/v3/notices/search",
       "body": {"query": "...", "fields": ["publication-number"], "limit": 20}}
    ]

This script is network-gated and intentionally has no unit test.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
DATASET = BENCH / "cases" / "eval_dataset.json"
GOLDEN_DIR = BENCH / "cases"


def _today() -> str:
    return date.today().isoformat()


def _fetch(spec: dict) -> object:
    method = spec.get("method", "GET").upper()
    url = spec["url"]
    headers = {"Accept": "application/json", "User-Agent": "industrial-eval-golden/1"}
    headers.update(spec.get("headers", {}))
    data = None
    if spec.get("body") is not None:
        data = json.dumps(spec["body"]).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (trusted gov endpoints)
        return json.loads(resp.read().decode("utf-8"))


def _write_provenance(case_dir: Path, case_id: str, captured: list[dict]) -> None:
    lines = [
        f"# Provenance — golden for case {case_id}",
        "",
        f"Captured: {datetime.now(timezone.utc).isoformat()}",  # noqa: UP017 (py3.10 compat)
        "",
        "| source | url | raw file | captured_on |",
        "|--------|-----|----------|-------------|",
    ]
    for c in captured:
        lines.append(f"| {c['source']} | {c['url']} | {c['raw_file']} | {_today()} |")
    lines += [
        "",
        "## Hand-verification",
        "",
        "- [ ] A human confirmed these records are real and correct.",
        "- Verified by: __________   on: __________",
        "",
        "Until the box above is checked, `golden.json` is a DRAFT and must not be",
        "treated as an oracle. See bench/REFRESH_PROCEDURE.md §2.",
    ]
    (case_dir / "PROVENANCE.md").write_text("\n".join(lines) + "\n")


def capture_case(case: dict, golden_dir: Path = GOLDEN_DIR) -> Path:
    case_id = case["id"]
    case_dir = golden_dir / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    specs = case.get("golden_capture") or []
    captured: list[dict] = []
    for i, spec in enumerate(specs):
        raw_file = f"raw_{spec['source']}_{i}.json"
        try:
            payload = _fetch(spec)
        except (urllib.error.URLError, ValueError) as exc:
            print(f"  ! {case_id} {spec['source']}: fetch failed: {exc}", file=sys.stderr)
            payload = {"_error": str(exc)}
        (case_dir / raw_file).write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        captured.append({"source": spec["source"], "url": spec["url"], "raw_file": raw_file})

    _write_provenance(case_dir, case_id, captured)

    golden_path = case_dir / "golden.json"
    if not golden_path.exists():
        golden_path.write_text(json.dumps({
            "case_id": case_id,
            "records": [],
            "empty_reason": "DRAFT — fill records after hand-verifying raw_*.json",
        }, ensure_ascii=False, indent=2))
        print(f"  scaffolded DRAFT {golden_path}", file=sys.stderr)

    return case_dir


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", help="Capture only this case id (default: all).")
    ap.add_argument("--golden-dir", default=str(GOLDEN_DIR))
    args = ap.parse_args(argv)

    dataset = json.loads(DATASET.read_text())
    cases = dataset["cases"]
    if args.case:
        cases = [c for c in cases if c["id"] == args.case]
        if not cases:
            ap.error(f"no case {args.case!r} in dataset")

    for case in cases:
        print(f"Capturing golden for {case['id']}...", file=sys.stderr)
        capture_case(case, Path(args.golden_dir))


if __name__ == "__main__":
    main()
