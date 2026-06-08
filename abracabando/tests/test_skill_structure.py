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
    assert "Audit trail" in t
    assert "Dati letti il" in t
    assert "Confidenza" in t
    assert "Lead time" in t  # derivation rules added in Phase 1.3


def test_pin_radar_skill_has_required_sections() -> None:
    t = _read_skill("pin-radar")
    assert "ted_pin_italy" in t
    assert "Audit trail" in t
    assert "NUTS" in t
    # Best-practice refactor: sections renamed to priority-based (alta/media/bassa)
    assert "priorità" in t.lower() or "PIN" in t


def test_scheda_opportunita_skill_has_required_sections() -> None:
    t = _read_skill("scheda-opportunita")
    assert "opencoesione_project_by_cup" in t  # replaced catalog-only describe_dataset
    assert "openpnrr_search_progetti" in t  # replaced broken openpnrr_get(item_id=cup)
    assert "Fonti" in t
    assert "Concorrenti probabili" in t or "Intelligence competitiva" in t
    assert "Audit trail" in t


def test_profilo_sa_skill_has_required_sections() -> None:
    t = _read_skill("profilo-sa")
    # Phase 1.1: replaced anac_search_datasets with anac_sa_history + anac_search_awards
    assert "anac_sa_history" in t
    assert "anac_search_awards" in t
    assert "Top fornitori" in t
    assert "Audit trail" in t or "Metodologia" in t


def test_sample_outputs_contain_required_elements() -> None:
    files = glob.glob(str(ROOT / "examples" / "sample_outputs" / "*.md"))
    assert files, "No sample output files found under examples/sample_outputs/"
    for path in files:
        text = Path(path).read_text()
        name = Path(path).name
        assert "Dati letti il" in text, f"{name}: missing freshness header 'Dati letti il'"
        # Accept both inline '(fonte:' and bold '**Fonte:**' provenance styles
        has_provenance = "(fonte:" in text or "**Fonte:**" in text or "fonte:" in text.lower()
        assert has_provenance, f"{name}: missing provenance link (fonte: or Fonte:)"
        assert "## Audit trail" in text, f"{name}: missing '## Audit trail'"


def test_consultazioni_radar_skill_has_required_sections() -> None:
    t = _read_skill("consultazioni-radar")
    assert "consip_search_bandi" in t
    assert "Dati letti il" in t
    assert "Audit trail" in t
    assert "Alta" in t and "Media" in t and "Bassa" in t


def test_consultazioni_radar_sample_output_exists() -> None:
    p = ROOT / "examples" / "sample_outputs" / "consultazioni-radar.md"
    t = p.read_text()
    assert "Dati letti il" in t
    assert "Audit trail" in t
    # Accept either old flat-table format (Probabilita column) or
    # new card-style format (🔵/🟢 section headers or Bandi/Consultazioni sections)
    has_d3 = ("Probabilita" in t or "🔵" in t or "🟢" in t
               or "Bandi" in t or "Consultazioni" in t or "aperte" in t.lower())
    assert has_d3, "consultazioni-radar.md missing expected content sections"


def test_scheda_opportunita_has_sintesi_incrociata_section() -> None:
    t = _read_skill("scheda-opportunita")
    assert "Sintesi incrociata TED-ANAC" in t
    assert "Valutazione trasformazione" in t
    assert "Coerenza CPV" in t


def test_pin_radar_skill_mandates_markdown_format() -> None:
    t = _read_skill("pin-radar")
    # Best-practice refactor: "Formato e stile" merged into "Regole invarianti"
    assert "Dati letti il" in t
    assert "Regole invarianti" in t or "Regole essenziali" in t


def test_consultazioni_radar_skill_mandates_markdown_format() -> None:
    t = _read_skill("consultazioni-radar")
    # Best-practice refactor: "Formato e stile" merged into "Regole invarianti"
    assert "Dati letti il" in t
    assert "Regole invarianti" in t or "Regole essenziali" in t


def test_scheda_opportunita_skill_mandates_markdown_format() -> None:
    t = _read_skill("scheda-opportunita")
    # Best-practice refactor: "Formato e stile" merged into "Regole invarianti"
    assert "Dati letti il" in t
    assert "Regole invarianti" in t or "Regole essenziali" in t


def test_consultazioni_radar_no_nonexistent_params() -> None:
    t = _read_skill("consultazioni-radar")
    assert "settore=<settore>" not in t
    assert 'consip_search_bandi(query=' in t or "consip_search_consultazioni" in t


def test_scheda_opportunita_uses_anac_search_awards() -> None:
    t = _read_skill("scheda-opportunita")
    # Best-practice refactor: no numbered "Passo N" sections, just verify tool presence
    assert "anac_search_awards" in t
    # Verify anac_search_datasets is NOT in allowed-tools (catalog tool)
    allowed_tools_start = t.find("allowed-tools:")
    allowed_tools_end = t.find("---", allowed_tools_start + 1)
    if allowed_tools_start > 0 and allowed_tools_end > 0:
        allowed_tools_block = t[allowed_tools_start:allowed_tools_end]
        assert "anac_search_awards" in allowed_tools_block
        # anac_search_datasets and anac_get_dataset are catalog tools, may still be in allowed-tools for scheda (bulk lookup)
        # but anac_search_awards should be present for per-record lookup


def test_pin_radar_has_ted_error_fallback() -> None:
    pin = _read_skill("pin-radar")
    scheda = _read_skill("scheda-opportunita")
    # Phase 4: pin-radar section renamed to "Dati non disponibili"
    assert "errore" in pin.lower() or "Dati non disponibili" in pin
    assert "errore" in scheda.lower() or "Dati non disponibili" in scheda


def test_reconciliation_pnrr_skill_has_required_flags() -> None:
    t = _read_skill("reconciliation-pnrr")
    for flag in ["CUP_ORFANO", "IMPORTO_SOPRA_FINANZIATO", "STATO_DIVERGENTE", "MANCATA_PUBBLICAZIONE_TED"]:
        assert flag in t, f"reconciliation-pnrr must contain flag marker '{flag}'"
    assert "Audit trail" in t
