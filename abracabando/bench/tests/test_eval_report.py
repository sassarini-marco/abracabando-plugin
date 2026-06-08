import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import eval_report  # noqa: E402
from eval_report import compare_against_baseline  # noqa: E402


def _write_results(dirpath, results):
    dirpath.mkdir(parents=True, exist_ok=True)
    for r in results:
        (dirpath / f"{r['id']}.json").write_text(json.dumps(r))


BASELINE = [{
    "id": "3.1-001", "d2_recall": 1.0, "d4_freshness": True,
    "output_rules": {"first_line": True, "provenance": True, "audit_trail": True},
    "layer": "skill_ok", "overall_pass": True,
    "d1_score": 1, "d3_score": 1, "d5_score": 1, "d6_score": 1, "d7_score": -1,
}]


def test_gate_fails_on_deterministic_regression_not_judge_noise(tmp_path):
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps({"results": BASELINE}))

    # --- deterministic regression: provenance rule flipped + D2 dropped ---
    bad_dir = tmp_path / "bad"
    _write_results(bad_dir, [{
        "id": "3.1-001", "d2_recall": 0.5, "d4_freshness": True,
        "output_rules": {"first_line": True, "provenance": False, "audit_trail": True},
        "layer": "skill_ok", "overall_pass": False,
        "d1_score": 1, "d3_score": 1, "d5_score": 1, "d6_score": 1, "d7_score": -1,
    }])
    with pytest.raises(SystemExit) as exc:
        eval_report.main(["--gate", "--results-dir", str(bad_dir), "--baseline-path", str(baseline)])
    assert exc.value.code != 0

    # --- judge-only dip: deterministic dims still all pass -> gate passes ---
    ok_dir = tmp_path / "ok"
    _write_results(ok_dir, [{
        "id": "3.1-001", "d2_recall": 1.0, "d4_freshness": True,
        "output_rules": {"first_line": True, "provenance": True, "audit_trail": True},
        "layer": "skill_ok", "overall_pass": True,
        "d1_score": 0, "d3_score": 0, "d5_score": 1, "d6_score": 1, "d7_score": -1,
    }])
    with pytest.raises(SystemExit) as exc2:
        eval_report.main(["--gate", "--results-dir", str(ok_dir), "--baseline-path", str(baseline)])
    assert exc2.value.code == 0


def test_gate_fails_on_failing_layer(tmp_path):
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps({"results": BASELINE}))
    bad_dir = tmp_path / "layerbad"
    _write_results(bad_dir, [{
        "id": "3.1-001", "d2_recall": 1.0, "d4_freshness": True,
        "output_rules": {"first_line": True, "provenance": True, "audit_trail": True},
        "layer": "skill_layer_bug", "overall_pass": False,
    }])
    with pytest.raises(SystemExit) as exc:
        eval_report.main(["--gate", "--results-dir", str(bad_dir), "--baseline-path", str(baseline)])
    assert exc.value.code != 0


def test_compare_against_baseline_separates_dims():
    current = [{
        "id": "3.1-001", "d2_recall": 1.0, "d4_freshness": True,
        "output_rules": {"first_line": True, "provenance": True},
        "layer": "skill_ok", "d1_score": 0,
    }]
    report = compare_against_baseline(current, BASELINE)
    assert report.gate_pass is True
    assert report.deterministic_regressions == []
    # the judge dip from 1 -> 0 is recorded but advisory (never gates)
    assert any("d1_score" in c for c in report.judge_changes)
