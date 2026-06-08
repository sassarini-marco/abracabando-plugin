#!/usr/bin/env python3
"""Tool contract table for MCP Layer 0 smoke/full tests.

Each row defines one tool call the eval harness exercises.  The ``smoke`` tier
uses ≤8 calls and fits within the free-tier 10-call/session budget.  The
``full`` tier covers all remaining tools and requires an unmetered/pro config.

``return_kind`` values:
  json_records   — tool returns a list of record dicts; ``min_records`` and
                   ``required_fields`` are asserted.
  file_path      — tool may return a filesystem path for large result sets
                   (e.g. ted_pin_italy); path existence and parseability are
                   asserted, never record count.
  link_only      — tool does no HTTP and returns a URL/struct; no record-count
                   assertion (programmazione_*, env_*).
"""
from __future__ import annotations

CONTRACTS: list[dict] = [
    # ── SMOKE TIER ────────────────────────────────────────────────────────────
    # ≤8 calls; covers every tool the 22 dataset cases exercise.

    {
        "tool": "anac_search_awards",
        "declared_args": {"q": "software", "rows": 5},
        "return_kind": "json_records",
        "tier": "smoke",
        "min_records": 1,
        "required_fields": ["cig", "importo", "aggiudicatario"],
    },
    {
        "tool": "ted_pin_italy",
        "declared_args": {"cpv_codes": ["72000000"], "limit": 5},
        "return_kind": "file_path",  # may return path for large result sets
        "tier": "smoke",
        "min_records": 1,
        "required_fields": ["publication_number"],
    },
    {
        "tool": "ted_search",
        "declared_args": {"query": "cpv=72000000", "limit": 5},
        "return_kind": "json_records",
        "tier": "smoke",
        "min_records": 1,
        "required_fields": ["publication_number"],
    },
    {
        "tool": "anac_sa_history",
        "declared_args": {"cf_or_name": "Roma"},
        "return_kind": "json_records",
        "tier": "smoke",
        "min_records": 1,
        "required_fields": ["anno"],
    },
    {
        "tool": "openpnrr_list",
        "declared_args": {"endpoint": "missioni", "limit": 5},
        "return_kind": "json_records",
        "tier": "smoke",
        "min_records": 1,
        "required_fields": ["id"],
    },
    {
        "tool": "consip_search_bandi",
        "declared_args": {"query": "software", "page": 1},
        "return_kind": "json_records",
        "tier": "smoke",
        "min_records": 1,
        "required_fields": ["title"],
    },
    {
        "tool": "opencoesione_project_by_cup",
        "declared_args": {"cup": "B17F21001590006"},
        "return_kind": "json_records",
        "tier": "smoke",
        "min_records": 1,
        "required_fields": ["totale_finanziato"],
    },
    {
        # In-memory lookup + link builder: no HTTP, no record count assertion.
        "tool": "programmazione_search_biennale",
        "declared_args": {"regione": "Emilia-Romagna"},
        "return_kind": "link_only",
        "tier": "smoke",
        "min_records": 0,
        "required_fields": [],
    },

    # ── FULL TIER ─────────────────────────────────────────────────────────────
    # All remaining tools; run with --pro (unmetered).

    {
        "tool": "openpnrr_search_progetti",
        "declared_args": {"q": "banda larga", "limit": 5},
        "return_kind": "json_records",
        "tier": "full",
        "min_records": 1,
        "required_fields": ["id"],
    },
    {
        "tool": "anac_awards_by_cup",
        "declared_args": {"cup": "B17F21001590006"},
        "return_kind": "json_records",
        "tier": "full",
        "min_records": 0,  # may be empty for this CUP
        "required_fields": [],
    },
    {
        # CIG is filled dynamically by the cross-tool consistency check.
        "tool": "anac_award_detail",
        "declared_args": {"cig": "PLACEHOLDER_CIG"},
        "return_kind": "json_records",
        "tier": "full",
        "min_records": 1,
        "required_fields": ["cig", "importo"],
    },
    {
        "tool": "consip_search_consultazioni",
        "declared_args": {"query": "cloud", "page": 1},
        "return_kind": "json_records",
        "tier": "full",
        "min_records": 0,
        "required_fields": [],
    },
    {
        "tool": "server_capabilities",
        "declared_args": {},
        "return_kind": "json_records",
        "tier": "full",
        "min_records": 0,  # liveness only
        "required_fields": [],
    },
    {
        "tool": "anac_pnrr_datasets",
        "declared_args": {},
        "return_kind": "json_records",
        "tier": "full",
        "min_records": 0,
        "required_fields": [],
    },
    {
        "tool": "env_va_search_link",
        "declared_args": {"procedure_type": "VIA", "region": "Lombardia"},
        "return_kind": "link_only",
        "tier": "full",
        "min_records": 0,
        "required_fields": [],
    },
    {
        "tool": "env_er_search_link",
        "declared_args": {"procedure_type": "VIA"},
        "return_kind": "link_only",
        "tier": "full",
        "min_records": 0,
        "required_fields": [],
    },
    {
        "tool": "registro_imprese_by_piva",
        "declared_args": {"piva": "01664422000"},  # ENI SpA
        "return_kind": "json_records",
        "tier": "full",
        "min_records": 1,
        "required_fields": [],
    },
    {
        "tool": "openpnrr_get",
        "declared_args": {"endpoint": "missioni", "item_id": "M1"},
        "return_kind": "json_records",
        "tier": "full",
        "min_records": 1,
        "required_fields": [],
    },
]
