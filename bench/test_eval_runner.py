import pathlib
import sys
from datetime import date, timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import eval_runner  # noqa: E402
from eval_report import build_report  # noqa: E402
from eval_runner import check_d2_recall, check_d4_freshness  # noqa: E402


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


def test_build_report_partial_results():
    results = [{"id": "3.1-001", "template": "3.1",
                "d2_recall": 1.0, "d4_freshness": True}]
    report = build_report(results)
    assert "?" in report          # missing judge scores shown as ?
    assert "PASS" not in report   # incomplete run can't pass


def test_eval_results_are_transient_and_well_formed():
    """eval_results/ is gitignored and transient. It may be empty (fresh
    checkout) or populated by a run; whatever is present must be valid result
    JSON carrying at least an id and the deterministic dims."""
    import json
    results_dir = pathlib.Path(__file__).resolve().parent / "eval_results"
    for f in results_dir.glob("*.json"):
        r = json.loads(f.read_text())
        assert "id" in r
        assert "d4_freshness" in r or "layer" in r


NO_DATA_ANSWER = (
    "Dati letti il 2026-06-02\n\n"
    "# Radar PIN TED\n\n"
    "## Dati non disponibili\n"
    "Nessun PIN TED attivo individuato per i parametri richiesti.\n\n"
    "## Audit trail\n```\n"
    "tool_preferito: \"free\"\nfallback_attivato: \"no\"\n"
    "query: ted_pin_italy cpv=65111000\ndata_lettura: 2026-06-02\n"
    "timestamp: 2026-06-02T09:00:00Z\n```\n"
)

HAPPY_ANSWER = (
    "Dati letti il 2026-06-02\n\n"
    "# Radar PIN TED\n\n"
    "- PIN **338240-2026** Azienda Zero "
    "(fonte: https://ted.europa.eu/it/notice/-/detail/338240-2026) — Dati letti il 2026-06-02. "
    "Alta confidenza.\n"
    "- PIN **340106-2026** CSI Piemonte "
    "(fonte: https://ted.europa.eu/it/notice/-/detail/340106-2026) — Dati letti il 2026-06-02. "
    "Media confidenza.\n\n"
    "## Audit trail\n```\ndata_lettura: 2026-06-02\n```\n"
)


def test_frozen_tier_scores_deterministically_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    # --- correct no-data case ---
    nodata_case = {
        "id": "3.1-002", "skill": "pin-radar", "scenario": "missing-data",
        "tier": "frozen", "template": "3.1", "ground_truth_records": [],
    }
    res = eval_runner.score_case_deterministic(
        nodata_case, NO_DATA_ANSWER, golden_records=[], mcp_records=[]
    )
    assert res["layer"] == "skill_ok_no_data"
    assert res["overall_pass"] is True
    assert res["d4_freshness"] is True
    assert "output_rules" in res and res["output_rules"]["first_line"] is True
    # frozen tier builds NO judge request: judge dims must be absent
    assert "d1_score" not in res

    # --- happy case ---
    golden = [
        {"source": "ted", "record_id": "338240-2026"},
        {"source": "ted", "record_id": "340106-2026"},
    ]
    happy_case = {
        "id": "3.1-001", "skill": "pin-radar", "scenario": "happy-path",
        "tier": "frozen", "template": "3.1", "ground_truth_records": golden,
    }
    res2 = eval_runner.score_case_deterministic(
        happy_case, HAPPY_ANSWER, golden_records=golden, mcp_records=golden
    )
    assert res2["d2_recall"] == 1.0
    assert res2["layer"] == "skill_ok"
    assert res2["overall_pass"] is True


def test_run_case_passes_mcp_config_path(monkeypatch):
    captured = {}

    class _Result:
        stdout = '{"type":"result","result":"ok"}\n'

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return _Result()

    monkeypatch.setattr(eval_runner.subprocess, "run", fake_run)
    case = {"id": "3.1-001", "prompt": "/pin-radar test"}
    eval_runner.run_case(
        case, pathlib.Path("."), pathlib.Path("bench/mcp_replay.json"), model="claude-sonnet-4-6"
    )
    cmd = captured["cmd"]
    assert "bench/mcp_replay.json" in cmd
    assert "claude-sonnet-4-6" in cmd
    assert "bench/mcp.json" not in cmd  # must honor the passed config, not the hardcoded one


def test_eval_report_no_zero_scores():
    """Integration test: passes only after a fresh eval run with all fixes applied.

    Skipped automatically when eval_results lack judge scores (d1_score absent),
    meaning the eval hasn't been run with ANTHROPIC_API_KEY set.
    """
    import contextlib
    import json

    import pytest
    results_dir = pathlib.Path(__file__).resolve().parent / "eval_results"
    results = []
    for f in sorted(results_dir.glob("*.json")):
        with contextlib.suppress(Exception):
            results.append(json.loads(f.read_text()))
    if not any("d1_score" in r for r in results):
        pytest.skip("No judge scores in eval_results — run eval with ANTHROPIC_API_KEY set")
    report = build_report(results)
    assert "FAIL" not in report, "Some dimensions failed — check eval_report.py output"
