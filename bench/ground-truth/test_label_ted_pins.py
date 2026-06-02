"""Tests for label_ted_pins.py.

Run from the project root:
    python -m pytest bench/scripts/test_label_ted_pins.py -x -q
"""
from __future__ import annotations

import importlib
import importlib.util
import os
import sys
from datetime import date, timedelta
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

# ---------------------------------------------------------------------------
# Ensure the script is importable from the project root regardless of how
# pytest is invoked.
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# We also need industrial_mcp on the path (the script inserts it itself, but
# we import it before the script runs path manipulation in module scope):
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPTS_DIR, "..", "..", ".."))
_MCP_SRC = os.path.join(_REPO_ROOT, "industrial-data-mcp", "src")
if _MCP_SRC not in sys.path:
    sys.path.insert(0, _MCP_SRC)


# ---------------------------------------------------------------------------
# Helper: load label_ted_pins as a module by file path so the test does not
# depend on the package being installed.
# ---------------------------------------------------------------------------

def _load_module():
    script_path = os.path.join(_SCRIPTS_DIR, "label_ted_pins.py")
    spec = importlib.util.spec_from_file_location("label_ted_pins", script_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Test 1 — importability
# ---------------------------------------------------------------------------

def test_label_script_importable():
    """The script must be importable and expose a ``main`` callable."""
    mod = _load_module()
    assert hasattr(mod, "main"), "label_ted_pins must expose a main() function"
    assert callable(mod.main), "main must be callable"


# ---------------------------------------------------------------------------
# Test 2 — PIN converted label
# ---------------------------------------------------------------------------

def _make_page(items: list[dict[str, Any]]):
    """Return a minimal Page-like object (duck-typed)."""
    class _Page:
        def __init__(self, its):
            self.items = its
    return _Page(items)


def test_pin_converted_label():
    """A PIN followed by a CN 60 days later from the same buyer+CPV should be
    labelled converted_to_cn=True with match_confidence in {"exact", "ambiguous"}.
    """
    mod = _load_module()

    pin_date = date(2025, 10, 15)
    cn_date = pin_date + timedelta(days=60)

    pin_record = {
        "publication_number": "123456-2025",
        "cpv": ["48000000"],
        "buyer": "Comune di Roma",
        "publication_date": pin_date.strftime("%Y-%m-%d"),
        "notice_type": "PIN",
    }

    cn_record = {
        "publication_number": "234567-2026",
        "cpv": ["48000000"],
        "buyer": "Comune di Roma",
        "publication_date": cn_date.strftime("%Y-%m-%d"),
        "notice_type": "CN",
    }

    # Patch the two async functions that the script imports from industrial_mcp.
    # We patch them on the module object that label_ted_pins already imported.
    with (
        patch.object(mod, "search_pin_italy", new=AsyncMock(return_value=_make_page([pin_record]))),
        patch.object(mod, "search_notices", new=AsyncMock(side_effect=[
            # First call: fetch_pins (uses search_notices directly)
            _make_page([pin_record]),
            # Second call: fetch_follow_on
            _make_page([cn_record]),
        ])),
    ):
        import asyncio
        records = asyncio.run(mod.run_labelling(cpv_prefix="48", limit=1, dry_run=False))

    assert len(records) == 1, f"Expected 1 record, got {len(records)}"
    rec = records[0]

    assert rec["converted_to_cn"] is True, (
        f"Expected converted_to_cn=True, got {rec['converted_to_cn']}"
    )
    assert rec["match_confidence"] in {"exact", "ambiguous"}, (
        f"Unexpected match_confidence: {rec['match_confidence']!r}"
    )
    assert rec["cn_publication_number"] == "234567-2026"
    assert rec["publication_number"] == "123456-2025"
