import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from mcp_preflight import (  # noqa: E402
    MCPEmptyError,
    PreflightResult,
    assert_mcp_nonempty,
    attribute_layer,
)

GOLDEN = [
    {"source": "ted", "record_id": "338240-2026", "buyer": "Azienda Zero"},
    {"source": "ted", "record_id": "340106-2026", "buyer": "CSI Piemonte"},
]
ANSWER_BOTH = "Dati letti il 2026-06-02\nPIN 338240-2026 e 340106-2026 attivi."
NO_DATA_ANSWER = "Dati letti il 2026-06-02\n## Dati non disponibili\nNessun PIN attivo."


def test_attribute_layer_separates_mcp_from_skill_failures():
    # golden has records, MCP returned nothing
    assert attribute_layer(ANSWER_BOTH, [], GOLDEN) == "mcp_layer_empty"

    # MCP records diverge in value from golden
    divergent = [
        {"source": "ted", "record_id": "338240-2026", "buyer": "Qualcun Altro"},
        {"source": "ted", "record_id": "340106-2026", "buyer": "CSI Piemonte"},
    ]
    assert attribute_layer(ANSWER_BOTH, divergent, GOLDEN) == "mcp_layer_wrong"

    # MCP == golden but the answer drops a record
    answer_missing = "Dati letti il 2026-06-02\nSolo PIN 338240-2026 attivo."
    assert attribute_layer(answer_missing, GOLDEN, GOLDEN) == "skill_layer_bug"

    # everyone agrees there's nothing and the skill said so correctly
    assert attribute_layer(NO_DATA_ANSWER, [], []) == "skill_ok_no_data"


def test_attribute_layer_happy_and_stale():
    assert attribute_layer(ANSWER_BOTH, GOLDEN, GOLDEN) == "skill_ok"
    # golden empty but MCP surfaced records the oracle lacks -> stale golden
    assert attribute_layer(ANSWER_BOTH, GOLDEN, []) == "stale_ground_truth"


def test_assert_mcp_nonempty_raises_on_empty():
    with pytest.raises(MCPEmptyError):
        assert_mcp_nonempty("ted_search", {"q": "x"}, call_tool=lambda t, p: {"items": []})


def test_assert_mcp_nonempty_returns_result():
    res = assert_mcp_nonempty(
        "ted_search", {"q": "x"}, call_tool=lambda t, p: {"items": [{"record_id": "1-2026"}]}
    )
    assert isinstance(res, PreflightResult)
    assert res.record_count == 1
