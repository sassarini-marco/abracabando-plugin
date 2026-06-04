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
from dataclasses import dataclass, field
from pathlib import Path

BENCH = Path(__file__).resolve().parent
DEFAULT_BASELINE = BENCH / "baseline.json"

# Layers that are NOT a failure (mirrors eval_runner.PASSING_LAYERS).
PASSING_LAYERS = {"skill_ok", "skill_ok_no_data"}
JUDGE_DIMS = ("d1_score", "d3_score", "d5_score", "d6_score", "d7_score")


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
        d2_s = f"{d2_v:.2f}" if d2_v is not None else "?"
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


@dataclass
class RegressionReport:
    gate_pass: bool
    deterministic_regressions: list[str] = field(default_factory=list)
    absolute_failures: list[str] = field(default_factory=list)
    judge_changes: list[str] = field(default_factory=list)


def _deterministic_failures(result: dict) -> list[str]:
    """Absolute deterministic failures in a single result (baseline-independent)."""
    fails = []
    for rid, passed in (result.get("output_rules") or {}).items():
        if passed is False:
            fails.append(f"output_rule:{rid}")
    if result.get("d4_freshness") is False:
        fails.append("D4")
    d2 = result.get("d2_recall")
    if d2 is not None and d2 < 1.0:
        fails.append(f"D2={d2}")
    layer = result.get("layer")
    if layer is not None and layer not in PASSING_LAYERS:
        fails.append(f"layer:{layer}")
    return fails


def load_baseline(path: Path) -> list[dict]:
    data = json.loads(Path(path).read_text())
    return data["results"] if isinstance(data, dict) else data


def write_baseline(results: list[dict], path: Path) -> None:
    """Persist the deterministic-relevant fields of a blessed run as the baseline."""
    keep = ("id", "skill", "scenario", "tier", "template", "d2_recall", "d4_freshness",
            "output_rules", "layer", "overall_pass", *JUDGE_DIMS)
    blessed = [{k: r[k] for k in keep if k in r} for r in results]
    Path(path).write_text(json.dumps({"results": blessed}, ensure_ascii=False, indent=2) + "\n")


def compare_against_baseline(results: list[dict], baseline: list[dict]) -> RegressionReport:
    """Compare a current run against a blessed baseline.

    The gate fails ONLY on deterministic signals: an absolute deterministic
    failure in the current run, or a deterministic dimension that regressed
    relative to the baseline. Judge dims (D1/D3/D5/D6/D7) are reported as
    advisory changes and NEVER hard-fail the gate (Decision 7).
    """
    base_by_id = {r["id"]: r for r in baseline}
    det_regressions: list[str] = []
    abs_failures: list[str] = []
    judge_changes: list[str] = []

    for cur in results:
        cid = cur["id"]
        for f in _deterministic_failures(cur):
            abs_failures.append(f"{cid}: {f}")

        base = base_by_id.get(cid)
        if not base:
            continue

        # output-rule regressions
        cur_rules = cur.get("output_rules") or {}
        base_rules = base.get("output_rules") or {}
        for rid, passed in base_rules.items():
            if passed and cur_rules.get(rid) is False:
                det_regressions.append(f"{cid}: output_rule:{rid} passed->failed")

        # D4 regression
        if base.get("d4_freshness") and cur.get("d4_freshness") is False:
            det_regressions.append(f"{cid}: D4 true->false")

        # D2 regression
        b2, c2 = base.get("d2_recall"), cur.get("d2_recall")
        if b2 is not None and c2 is not None and c2 < b2:
            det_regressions.append(f"{cid}: D2 {b2}->{c2}")

        # layer regression
        if base.get("layer") in PASSING_LAYERS and cur.get("layer") not in PASSING_LAYERS:
            det_regressions.append(f"{cid}: layer {base.get('layer')}->{cur.get('layer')}")

        # judge changes (advisory)
        for dim in JUDGE_DIMS:
            if dim in base and dim in cur and cur[dim] != base[dim]:
                judge_changes.append(f"{cid}: {dim} {base[dim]}->{cur[dim]}")

    gate_pass = not det_regressions and not abs_failures
    return RegressionReport(
        gate_pass=gate_pass,
        deterministic_regressions=det_regressions,
        absolute_failures=abs_failures,
        judge_changes=judge_changes,
    )


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default="bench/eval_results")
    ap.add_argument("--expected-cases", type=int, default=0)
    ap.add_argument("--baseline-path", default=str(DEFAULT_BASELINE))
    ap.add_argument("--gate", action="store_true",
                    help="Fail (exit 1) on a deterministic regression / failure vs the baseline.")
    ap.add_argument("--baseline", action="store_true",
                    help="Bless the current results as the committed baseline and exit.")
    args = ap.parse_args(argv)

    results_dir = Path(args.results_dir)
    results = load_results(results_dir)

    if args.baseline:
        write_baseline(results, Path(args.baseline_path))
        print(f"Blessed {len(results)} result(s) -> {args.baseline_path}")
        sys.exit(0)

    report = build_report(results)
    print(report)

    if args.gate:
        baseline = load_baseline(Path(args.baseline_path))
        reg = compare_against_baseline(results, baseline)
        print("\n=== Deterministic gate ===")
        if reg.absolute_failures:
            print("Absolute deterministic failures:")
            for f in reg.absolute_failures:
                print(f"  {f}")
        if reg.deterministic_regressions:
            print("Deterministic regressions vs baseline:")
            for f in reg.deterministic_regressions:
                print(f"  {f}")
        if reg.judge_changes:
            print("Judge-dim changes (advisory, non-gating):")
            for f in reg.judge_changes:
                print(f"  {f}")
        print(f"GATE: {'PASS' if reg.gate_pass else 'FAIL'}")
        sys.exit(0 if reg.gate_pass else 1)

    if args.expected_cases and len(results) < args.expected_cases:
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
