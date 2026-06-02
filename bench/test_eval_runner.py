import sys
import pathlib
from datetime import date, timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from eval_runner import check_d2_recall, check_d4_freshness


def test_d2_recall_partial():
    records = [
        {"source": "ted", "record_id": "123456-2025"},
        {"source": "ted", "record_id": "999999-2025"},
    ]
    result = check_d2_recall("see PIN 123456-2025 for details", records)
    assert result == 0.5


def test_d2_recall_empty_expected():
    # No ground truth records → N/A, not vacuously 1.0
    assert check_d2_recall("any text", []) is None


def test_d2_recall_consip_substring():
    records = [{"source": "consip", "record_id": "rda-52841"}]
    assert check_d2_recall("...bando rda-52841 per servizi cloud...", records) == 1.0
    assert check_d2_recall("...nessun risultato rilevante...", records) == 0.0


def test_d2_recall_anac_cig():
    records = [{"source": "anac", "record_id": "BB22E2E4B0"}]
    assert check_d2_recall("...CIG BB22E2E4B0 importo 549904...", records) == 1.0
    assert check_d2_recall("...nessun CIG...", records) == 0.0


def test_d4_freshness_valid():
    today = date.today().isoformat()
    assert check_d4_freshness(f"Dati letti il {today} per i seguenti PIN", today) is True


def test_d4_freshness_stale():
    stale_date = (date.today() - timedelta(days=60)).isoformat()
    assert check_d4_freshness(f"Dati letti il {stale_date}", date.today().isoformat()) is False


def test_d4_freshness_missing():
    assert check_d4_freshness("nessuna data presente", date.today().isoformat()) is False


import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from eval_report import build_report


def test_build_report_partial_results():
    results = [{"id": "3.1-001", "template": "3.1",
                "d2_recall": 1.0, "d4_freshness": True}]
    report = build_report(results)
    assert "?" in report          # missing judge scores shown as ?
    assert "PASS" not in report   # incomplete run can't pass


def test_eval_results_populated():
    results_dir = pathlib.Path(__file__).resolve().parent / "eval_results"
    json_files = list(results_dir.glob("*.json"))
    assert len(json_files) == 6, f"Expected 6 result files, found {len(json_files)}"


def test_eval_report_no_zero_scores():
    """Integration test: passes only after a fresh eval run with all fixes applied.

    Skipped automatically when eval_results lack judge scores (d1_score absent),
    meaning the eval hasn't been run with ANTHROPIC_API_KEY set.
    """
    import pytest
    results_dir = pathlib.Path(__file__).resolve().parent / "eval_results"
    results = []
    for f in sorted(results_dir.glob("*.json")):
        try:
            results.append(__import__("json").loads(f.read_text()))
        except Exception:
            pass
    if not any("d1_score" in r for r in results):
        pytest.skip("No judge scores in eval_results — run eval with ANTHROPIC_API_KEY set")
    report = build_report(results)
    assert "FAIL" not in report, "Some dimensions failed — check eval_report.py output"
