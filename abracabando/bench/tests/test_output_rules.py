import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from output_rules import (  # noqa: E402
    RuleResult,
    check_audit_trail_block,
    check_first_line_dataletti,
    check_no_exposed_tool_names,
    check_no_fabricated_ids,
    check_provenance,
    check_qualitative_confidence,
    run_all_rules,
)

GOOD_ANSWER = """Dati letti il 2026-06-02

# Radar PIN TED — servizi informatici

- PIN **338240-2026** — Azienda Zero Padova, CPV 72253000
  (fonte: https://ted.europa.eu/it/notice/-/detail/338240-2026) — Dati letti il 2026-06-02.
  Probabilità di trasformazione in gara: **Alta confidenza**.

## Audit trail
```
tool_preferito: "free"
fallback_attivato: "no"
query: ted_pin_italy cpv=72000000
data_lettura: 2026-06-02
timestamp: 2026-06-02T09:15:00Z
```
"""

BAD_ANSWER = (
    "# Results\n\n"
    "Here are the search results from mcp__industrial-mcp-free__ted_search "
    "for your query. The data is available below.\n"
)

GROUND_TRUTH = [{"source": "ted", "record_id": "338240-2026"}]


def test_run_all_rules_flags_each_violation():
    bad = {r.rule_id: r for r in run_all_rules(BAD_ANSWER, GROUND_TRUTH)}
    assert bad["first_line"].passed is False
    assert bad["no_tool_names"].passed is False

    good = run_all_rules(GOOD_ANSWER, GROUND_TRUTH)
    assert all(r.passed for r in good), [r for r in good if not r.passed]
    assert all(isinstance(r, RuleResult) for r in good)


def test_individual_rules_on_good_answer():
    assert check_first_line_dataletti(GOOD_ANSWER).passed
    assert check_no_exposed_tool_names(GOOD_ANSWER).passed
    assert check_provenance(GOOD_ANSWER).passed
    assert check_qualitative_confidence(GOOD_ANSWER).passed
    assert check_audit_trail_block(GOOD_ANSWER).passed
    assert check_no_fabricated_ids(GOOD_ANSWER, ["338240-2026"]).passed


def test_first_line_dataletti_relaxed():
    # opens with Dati letti il -> pass
    assert check_first_line_dataletti("Dati letti il 2026-06-02\n# Titolo").passed is True
    # a brief conversational lead-in before Dati letti il is tolerated
    assert check_first_line_dataletti(
        "Ho tutti i dati. Compongo il report.\n\nDati letti il 2026-06-02"
    ).passed is True
    # buried deep (beyond the grace window) -> fail
    assert check_first_line_dataletti(
        "riga1\nriga2\nriga3\nriga4\nDati letti il 2026-06-02"
    ).passed is False
    # absent entirely -> fail
    assert check_first_line_dataletti("# Titolo\nnessuna data").passed is False


def test_no_exposed_tool_names_detects_mcp_prefix():
    assert check_no_exposed_tool_names("uso mcp__industrial-mcp-free__ted_search").passed is False


def test_qualitative_confidence_rejects_percentage():
    txt = "Dati letti il 2026-06-02\nconfidenza: 87%"
    assert check_qualitative_confidence(txt).passed is False


def test_no_fabricated_ids_flags_unknown_ted_number():
    txt = "Dati letti il 2026-06-02\nPIN 999999-2099 trovato."
    assert check_no_fabricated_ids(txt, ["338240-2026"]).passed is False
    assert check_no_fabricated_ids(txt, ["999999-2099"]).passed is True


def test_audit_trail_requires_fenced_block():
    assert check_audit_trail_block("## Audit trail\nnessun blocco").passed is False
