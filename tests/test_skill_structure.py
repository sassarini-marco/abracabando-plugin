"""Verify that each SKILL.md contains the required sections and tool references."""
from __future__ import annotations

import glob
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _read_skill(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text()


def test_digest_pregara_skill_has_required_sections() -> None:
    t = _read_skill("digest-pregara")
    assert "programmazione_search_biennale" in t
    assert "Opportunita rilevate" in t
    assert "Audit trail" in t
    assert "Dati letti il" in t
    assert "Confidenza" in t


def test_pin_radar_skill_has_required_sections() -> None:
    t = _read_skill("pin-radar")
    assert "ted_pin_italy" in t
    assert "PIN attivi" in t
    assert "Audit trail" in t
    assert "NUTS" in t


def test_scheda_opportunita_skill_has_required_sections() -> None:
    t = _read_skill("scheda-opportunita")
    assert "opencoesione_describe_dataset" in t
    assert "Fonti incrociate" in t
    assert "Concorrenti probabili" in t
    assert "Audit trail" in t


def test_profilo_sa_skill_has_required_sections() -> None:
    t = _read_skill("profilo-sa")
    assert "anac_search_datasets" in t
    assert "Top fornitori" in t
    assert "Audit trail" in t
    # false-positive warning phrase — must appear somewhere in the skill
    assert any(
        phrase in t
        for phrase in [
            "corrispondenza per denominazione",
            "falsi positivi",
            "denominazione simile",
        ]
    ), "profilo-sa must warn about name-matching false positives"


def test_sample_outputs_contain_required_elements() -> None:
    import glob
    files = glob.glob(str(ROOT / "examples" / "sample_outputs" / "*.md"))
    assert files, "No sample output files found under examples/sample_outputs/"
    for path in files:
        text = Path(path).read_text()
        name = Path(path).name
        assert "Dati letti il" in text, f"{name}: missing freshness header 'Dati letti il'"
        assert "(fonte:" in text, f"{name}: missing provenance link '(fonte:'"
        assert "## Audit trail" in text, f"{name}: missing '## Audit trail'"


def test_reconciliation_pnrr_skill_has_required_flags() -> None:
    t = _read_skill("reconciliation-pnrr")
    for flag in ["CUP_ORFANO", "IMPORTO_SOPRA_FINANZIATO", "STATO_DIVERGENTE", "MANCATA_PUBBLICAZIONE_TED"]:
        assert flag in t, f"reconciliation-pnrr must contain flag marker '{flag}'"
    assert "Audit trail" in t
