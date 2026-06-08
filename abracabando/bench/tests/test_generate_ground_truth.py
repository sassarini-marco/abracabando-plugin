"""Tests for generate_ground_truth.py — the golden-backed ground-truth generator.

The whole point of the independent golden is that ground truth is derived from
committed upstream captures, NOT from the same MCP server the skill calls. These
tests prove that derivation never touches ``industrial_mcp``.
"""
from __future__ import annotations

import json
import pathlib
import sys
import types

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import generate_ground_truth as ggt  # noqa: E402


def test_ground_truth_derives_from_golden_not_mcp(tmp_path, monkeypatch):
    # Poison industrial_mcp: any attribute access blows up loudly.
    poison = types.ModuleType("industrial_mcp")

    def _raise(name):  # module-level __getattr__ (PEP 562)
        raise AssertionError(f"generate_ground_truth must not touch industrial_mcp ({name})")

    poison.__getattr__ = _raise  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "industrial_mcp", poison)

    # --- non-empty golden ---
    case_dir = tmp_path / "3.1-001"
    case_dir.mkdir()
    (case_dir / "golden.json").write_text(json.dumps({
        "case_id": "3.1-001",
        "records": [
            {"source": "ted", "record_id": "338240-2026", "buyer": "Azienda Zero"},
            {"source": "ted", "record_id": "340106-2026", "buyer": "CSI Piemonte"},
        ],
        "empty_reason": None,
    }))
    out = ggt.generate_ground_truth({"id": "3.1-001"}, golden_dir=tmp_path)
    ids = [r["record_id"] for r in out["ground_truth_records"]]
    assert ids == ["338240-2026", "340106-2026"]
    assert not out.get("empty_reason")

    # --- empty golden ---
    empty_dir = tmp_path / "3.4-002"
    empty_dir.mkdir()
    (empty_dir / "golden.json").write_text(json.dumps({
        "case_id": "3.4-002",
        "records": [],
        "empty_reason": "ANAC returned no award for this SA in the snapshot window",
    }))
    out2 = ggt.generate_ground_truth({"id": "3.4-002"}, golden_dir=tmp_path)
    assert out2["ground_truth_records"] == []
    assert out2["empty_reason"]


def test_generate_ground_truth_requires_source_and_record_id(tmp_path):
    case_dir = tmp_path / "3.2-001"
    case_dir.mkdir()
    (case_dir / "golden.json").write_text(json.dumps({
        "case_id": "3.2-001",
        "records": [{"source": "consip", "record_id": "rda-52841", "status": "aperto"}],
    }))
    out = ggt.generate_ground_truth({"id": "3.2-001"}, golden_dir=tmp_path)
    rec = out["ground_truth_records"][0]
    assert rec["source"] == "consip"
    assert rec["record_id"] == "rda-52841"
    assert rec["status"] == "aperto"  # passthrough fields preserved
