#!/usr/bin/env python3
"""Scoring report for eval_runner.py results.

Usage:
    python bench/eval_report.py
    python bench/eval_report.py --results-dir bench/eval_results --expected-cases 6
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_results(results_dir: Path) -> list[dict]:
    results = []
    for f in sorted(results_dir.glob("*.json")):
        try:
            results.append(json.loads(f.read_text()))
        except Exception as e:
            print(f"Warning: could not parse {f}: {e}", file=sys.stderr)
    return results


def build_report(results: list[dict]) -> str:
    lines: list[str] = []
    template_data: dict[str, dict] = {}
    failing_dims: list[tuple[str, str, str]] = []

    header = "case_id | template | D1 | D2 | D3 | D4 | D5 | D6 | D7 | overall_pass"
    lines.append(header)
    lines.append("-" * len(header))

    for r in results:
        cid = r.get("id", "?")
        tmpl = r.get("template", "?")

        d1_v = r.get("d1_score")
        d2_v = r.get("d2_recall")
        d3_v = r.get("d3_score")
        d4_v = r.get("d4_freshness")
        d5_v = r.get("d5_score")
        d6_v = r.get("d6_score")
        d7_v = r.get("d7_score")

        d1_s = str(d1_v) if d1_v is not None else "?"
        d2_s = ("%.2f" % d2_v) if d2_v is not None else "?"
        d3_s = str(d3_v) if d3_v is not None else "?"
        d4_s = ("OK" if d4_v else "FAIL") if d4_v is not None else "?"
        d5_s = str(d5_v) if d5_v is not None else "?"
        d6_s = str(d6_v) if d6_v is not None else "?"
        d7_s = str(d7_v) if d7_v is not None else "?"

        def dim_passes(dim: str, val: object) -> bool | None:
            if val is None:
                return None
            if dim in ("D3", "D7"):
                return val in (1, -1)
            if dim == "D2":
                return val == 1.0
            if dim == "D4":
                return bool(val)
            return val == 1

        dim_raw = {
            "D1": d1_v, "D2": d2_v, "D3": d3_v, "D4": d4_v,
            "D5": d5_v, "D6": d6_v, "D7": d7_v,
        }
        dim_results = {dim: dim_passes(dim, val) for dim, val in dim_raw.items()}

        has_unknown = any(v is None for v in dim_results.values())
        has_fail = any(v is False for v in dim_results.values())

        if has_unknown:
            overall = "?"
        elif has_fail:
            overall = "FAIL"
        else:
            overall = "PASS"

        for dim, passes in dim_results.items():
            if passes is False:
                reason = r.get(f"{dim.lower()}_reason", "no reason provided")
                failing_dims.append((cid, dim, str(reason)))

        lines.append(
            f"{cid} | {tmpl} | {d1_s} | {d2_s} | {d3_s} | {d4_s} | {d5_s} | {d6_s} | {d7_s} | {overall}"
        )

        if tmpl not in template_data:
            template_data[tmpl] = {"cases": 0, "passes": 0}
        template_data[tmpl]["cases"] += 1
        if overall == "PASS":
            template_data[tmpl]["passes"] += 1

    lines.append("")
    lines.append("template | cases | passes | rate%")
    lines.append("-" * 40)
    for tmpl, data in sorted(template_data.items()):
        n = data["cases"]
        p = data["passes"]
        rate = (100 * p // n) if n else 0
        lines.append(f"{tmpl} | {n} | {p} | {rate}%")

    lines.append("")
    lines.append("Failing dimensions:")
    if failing_dims:
        for cid, dim, reason in failing_dims:
            lines.append(f"  {cid} | {dim} | {reason}")
    else:
        lines.append("  (none)")

    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default="bench/eval_results")
    ap.add_argument("--expected-cases", type=int, default=6)
    args = ap.parse_args()

    results_dir = Path(args.results_dir)
    results = load_results(results_dir)
    report = build_report(results)
    print(report)

    if len(results) < args.expected_cases:
        print(
            f"\nWarning: expected {args.expected_cases} cases, found {len(results)}",
            file=sys.stderr,
        )
        sys.exit(1)

    if "FAIL" in report or "?" in report:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
