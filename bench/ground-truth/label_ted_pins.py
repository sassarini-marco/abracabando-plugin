"""label_ted_pins.py — Label TED PIN records with follow-on CN/CAN conversion data.

For each Italian Prior Information Notice (PIN) published on TED in Oct–Nov 2025,
this script checks whether a Contract Notice (CN) or Contract Award Notice (CAN)
followed within 30–180 days from the same buyer and CPV, then writes one labelled
JSON record per PIN.

Usage
-----
    python label_ted_pins.py [--cpv 48] [--limit 50] [--dry-run] [--output path.json]

Notes on the actual TED function signatures
-------------------------------------------
``search_pin_italy`` in industrial_mcp.sources.ted accepts:
    cpv_codes: list[str] | None
    nuts_region: str | None
    deadline_before: str | None
    limit: int  (default 25)
    page: int   (default 1)

It does NOT accept ``scope``, ``date_from``, or ``date_to`` parameters.
Date filtering is achieved by appending a ``publication-date`` clause to the
underlying ``search_notices`` query (which is what we do in ``fetch_pins``).

``search_notices`` in industrial_mcp.sources.ted accepts:
    query: str  (TED expert-search syntax)
    fields: list[str] | None
    limit: int  (default 25)
    page: int   (default 1)
    scope: str  (default "ACTIVE"; use "ALL" for historical data)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher
from typing import Any

# ---------------------------------------------------------------------------
# Resolve the industrial_mcp package from the sibling repo when it is not
# installed as a package.  The path is injected before any import so that
# ``from industrial_mcp.sources.ted import …`` always resolves correctly.
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", ".."))
_MCP_SRC = os.path.join(_REPO_ROOT, "industrial-data-mcp", "src")
if _MCP_SRC not in sys.path:
    sys.path.insert(0, _MCP_SRC)

# search_pin_italy is re-exported here so tests can patch it on this module.
from industrial_mcp.sources.ted import search_notices, search_pin_italy  # noqa: E402, F401

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PIN_DATE_FROM = "20260101"
PIN_DATE_TO = "20260531"

# TED v3 API uses lowercase-hyphenated notice-type codes.
# Prior Information Notices: "pin-buyer", "pin-tran"
# Contract Notices:          "cn-standard", "cn-social", "cn-desg", …
# Contract Award Notices:    "can-standard", "can-social", "can-modif", …
PIN_NOTICE_TYPES = ("pin-buyer", "pin-tran")
FOLLOW_ON_NOTICE_TYPES = ("cn-standard", "cn-social", "cn-desg", "can-standard", "can-social", "can-modif")
FOLLOW_ON_MIN_DAYS = 30
FOLLOW_ON_MAX_DAYS = 180

BUYER_SIMILARITY_THRESHOLD = 0.75  # SequenceMatcher ratio for "close" match


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_date(value: str | None) -> date | None:
    """Parse a YYYY-MM-DD or YYYYMMDD date string, returning None on failure."""
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _buyer_similarity(a: str | None, b: str | None) -> float:
    """Return a name-similarity ratio in [0, 1]."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _cpv_prefix_match(pin_cpvs: list[str], cn_cpvs: list[str], prefix_len: int = 2) -> bool:
    """Return True if any PIN CPV shares its first ``prefix_len`` digits with any CN CPV."""
    pin_prefixes = {c[:prefix_len] for c in pin_cpvs if len(c) >= prefix_len}
    cn_prefixes = {c[:prefix_len] for c in cn_cpvs if len(c) >= prefix_len}
    return bool(pin_prefixes & cn_prefixes)


def _exact_cpv_match(pin_cpvs: list[str], cn_cpvs: list[str]) -> bool:
    """Return True if there is at least one CPV in common (exact or prefix-8)."""
    pin_set = set(pin_cpvs)
    cn_set = set(cn_cpvs)
    return bool(pin_set & cn_set) or _cpv_prefix_match(pin_cpvs, cn_cpvs, prefix_len=8)


def _determine_confidence(
    buyer_sim: float,
    cpv_match_exact: bool,
    cpv_match_prefix: bool,
) -> str:
    """Determine match_confidence from individual signal scores."""
    buyer_ok = buyer_sim >= BUYER_SIMILARITY_THRESHOLD
    if buyer_ok and cpv_match_exact:
        return "exact"
    if buyer_ok or cpv_match_exact or cpv_match_prefix:
        return "ambiguous"
    return "none"


# ---------------------------------------------------------------------------
# Core async logic
# ---------------------------------------------------------------------------

async def fetch_pins(cpv_prefix: str | None, limit: int) -> list[dict[str, Any]]:
    """Query TED for Italian PINs published in Oct–Nov 2025.

    Returns the raw item dicts from the Page response.
    """
    # Build a date-filtered query by calling search_notices directly,
    # because search_pin_italy does not accept date_from / date_to parameters.
    date_clause = f"publication-date>={PIN_DATE_FROM} AND publication-date<={PIN_DATE_TO}"
    # TED v3 uses lowercase-hyphenated notice-type values; OR-join the PIN types.
    pin_type_clause = " OR ".join(f"notice-type={t}" for t in PIN_NOTICE_TYPES)
    base_query = f"({pin_type_clause}) AND place-of-performance=ITA AND {date_clause}"

    if cpv_prefix:
        # TED expert search supports trailing wildcards on CPV codes.
        base_query = f"{base_query} AND classification-cpv={cpv_prefix}*"

    page = await search_notices(query=base_query, limit=limit, page=1, scope="ALL")
    return page.items


async def fetch_follow_on(
    buyer: str | None,
    cpv_codes: list[str],
    pin_date: date,
) -> list[dict[str, Any]]:
    """Search for CN/CAN notices from the same buyer + CPV within the follow-on window."""
    date_from = (pin_date + timedelta(days=FOLLOW_ON_MIN_DAYS)).strftime("%Y%m%d")
    date_to = (pin_date + timedelta(days=FOLLOW_ON_MAX_DAYS)).strftime("%Y%m%d")

    # Build notice-type clause (TED v3 lowercase-hyphenated values)
    nt_clause = " OR ".join(f"notice-type={nt}" for nt in FOLLOW_ON_NOTICE_TYPES)
    date_clause = f"publication-date>={date_from} AND publication-date<={date_to}"

    query_parts = [f"({nt_clause})", "place-of-performance=ITA", date_clause]

    # Add CPV filter if available (use first CPV only to keep query simple)
    if cpv_codes:
        cpv_clause = " OR ".join(f"classification-cpv={c}" for c in cpv_codes[:3])
        query_parts.append(f"({cpv_clause})" if len(cpv_codes) > 1 else f"classification-cpv={cpv_codes[0]}")

    query = " AND ".join(query_parts)
    page = await search_notices(query=query, limit=50, page=1, scope="ALL")
    return page.items


def label_pin(pin: dict[str, Any], follow_ons: list[dict[str, Any]]) -> dict[str, Any]:
    """Produce the labelled output record for a single PIN.

    Iterates over candidate follow-on notices, picks the best-matching one,
    and determines conversion status and confidence.
    """
    pub_number: str = pin.get("publication_number", "")
    cpv_list: list[str] = pin.get("cpv") or []
    cpv_str: str = cpv_list[0] if cpv_list else ""
    buyer: str | None = pin.get("buyer")
    pin_date_str: str | None = pin.get("publication_date")

    best_cn: dict[str, Any] | None = None
    best_confidence = "none"
    best_sim = 0.0

    for candidate in follow_ons:
        cn_buyer = candidate.get("buyer")
        cn_cpvs: list[str] = candidate.get("cpv") or []

        buyer_sim = _buyer_similarity(buyer, cn_buyer)
        cpv_exact = _exact_cpv_match(cpv_list, cn_cpvs)
        cpv_prefix = _cpv_prefix_match(cpv_list, cn_cpvs, prefix_len=2)
        confidence = _determine_confidence(buyer_sim, cpv_exact, cpv_prefix)

        if confidence == "none":
            continue

        # Prefer "exact" over "ambiguous", then higher buyer similarity
        if best_confidence == "none" or (
            confidence == "exact" and best_confidence != "exact"
        ) or (
            confidence == best_confidence and buyer_sim > best_sim
        ):
            best_cn = candidate
            best_confidence = confidence
            best_sim = buyer_sim

    converted = best_cn is not None
    return {
        "publication_number": pub_number,
        "cpv": cpv_str,
        "buyer_name": buyer,
        "pin_date": pin_date_str,
        "converted_to_cn": converted,
        "cn_publication_date": best_cn.get("publication_date") if best_cn else None,
        "cn_publication_number": best_cn.get("publication_number") if best_cn else None,
        "match_confidence": best_confidence if converted else "none",
    }


async def run_labelling(
    cpv_prefix: str | None = None,
    limit: int = 50,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Fetch PINs, optionally look up follow-ons, and return labelled records."""
    pins = await fetch_pins(cpv_prefix=cpv_prefix, limit=limit)

    if dry_run:
        print(f"[dry-run] Found {len(pins)} PIN(s). Skipping follow-on lookups.")
        return []

    records: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for pin in pins:
        cpv_list: list[str] = pin.get("cpv") or []
        buyer: str | None = pin.get("buyer")
        pin_date = _parse_date(pin.get("publication_date"))

        if pin_date is None:
            # No (parseable) publication_date -> the follow-on window cannot be
            # built. Skip the PIN cleanly with a named reason instead of calling
            # fetch_follow_on with an unbound/None pin_date.
            skipped.append({
                "publication_number": pin.get("publication_number"),
                "skip_reason": "missing_publication_date",
            })
            continue

        follow_ons = await fetch_follow_on(
            buyer=buyer,
            cpv_codes=cpv_list,
            pin_date=pin_date,
        )
        records.append(label_pin(pin, follow_ons))

    if skipped:
        print(
            f"[label_ted_pins] skipped {len(skipped)} PIN(s) with "
            f"missing_publication_date: "
            f"{[s['publication_number'] for s in skipped]}",
            file=sys.stderr,
        )

    return records


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Label TED PIN records with follow-on CN/CAN conversion data. "
            "Queries Oct–Nov 2025 Italian PINs and checks for subsequent "
            "contract notices within 30–180 days."
        )
    )
    parser.add_argument(
        "--cpv",
        default=None,
        metavar="PREFIX",
        help="CPV prefix to filter PINs (e.g. '48' for software). Omit for all CPVs.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of PINs to process (default: 50).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the number of PINs found but skip follow-on lookups.",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="PATH",
        help="Write JSON output to this file (default: stdout).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """CLI entry point — parse arguments and run the labelling pipeline."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    records = asyncio.run(
        run_labelling(
            cpv_prefix=args.cpv,
            limit=args.limit,
            dry_run=args.dry_run,
        )
    )

    if args.dry_run:
        return

    output = json.dumps(records, indent=2, ensure_ascii=False)

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output)
        print(f"Wrote {len(records)} record(s) to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
