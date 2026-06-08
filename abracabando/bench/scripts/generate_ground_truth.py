#!/usr/bin/env python3
"""Derive eval ground truth from the independent frozen golden.

The golden under ``bench/cases/<case_id>/golden.json`` is the
oracle: raw upstream responses are captured by ``capture_golden.py``,
hand-verified once, and frozen. This module reads that committed, human-verified
golden and produces the ``ground_truth_records`` block for a case.

It deliberately does NOT import ``industrial_mcp`` — deriving ground truth from
the same MCP server the skill calls would make MCP data bugs invisible (a
circular oracle). A unit test enforces that this module never touches it.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

GOLDEN_DIR = Path(__file__).resolve().parent.parent / "cases"


def _load_golden(case_id: str, golden_dir: Path) -> dict:
    path = Path(golden_dir) / case_id / "golden.json"
    if not path.exists():
        raise FileNotFoundError(
            f"No golden for case {case_id!r} at {path}. "
            f"Run: python3 bench/scripts/capture_golden.py --case {case_id}"
        )
    return json.loads(path.read_text())


def generate_ground_truth(case: dict, golden_dir: Path = GOLDEN_DIR) -> dict:
    """Return ``{"ground_truth_records": [...], "empty_reason": <str|None>}``.

    Records come straight from the committed golden. An empty golden yields an
    empty record list plus the recorded ``empty_reason`` (a genuine "no data"
    case, not a failure).
    """
    case_id = case["id"]
    golden = _load_golden(case_id, golden_dir)
    records = golden.get("records") or []

    normalized: list[dict] = []
    for rec in records:
        if not rec.get("source") or not rec.get("record_id"):
            raise ValueError(
                f"Golden record for {case_id} missing source/record_id: {rec!r}"
            )
        normalized.append(dict(rec))

    if not normalized:
        return {
            "ground_truth_records": [],
            "empty_reason": golden.get("empty_reason") or "golden captured empty",
        }
    return {"ground_truth_records": normalized, "empty_reason": None}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", required=True, help="Case id, e.g. 3.1-001")
    ap.add_argument("--golden-dir", default=str(GOLDEN_DIR))
    args = ap.parse_args(argv)

    out = generate_ground_truth({"id": args.case}, golden_dir=Path(args.golden_dir))
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
