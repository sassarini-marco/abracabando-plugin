#!/usr/bin/env python3
"""Deterministic output-contract linter for abracabando skill output.

Single source of truth for the rules encoded in
``skills/shared/regole-comuni.md`` and the project CLAUDE.md "Skill output
rules". Shared by pytest (``bench/test_output_rules.py``) and the eval runner
(``bench/eval_runner.py``) so the contract is checked identically in both places.

Every check is phrasing-robust: it keys on structure/patterns, not on exact
wording, so it stays stable across model output variance.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Identifier patterns we treat as "raw upstream record ids".
TED_ID_RE = re.compile(r"\b\d{6}-\d{4}\b")
CIG_RE = re.compile(r"\b[A-Z0-9]{10}\b")
CUP_RE = re.compile(r"\b[A-Z0-9]{15}\b")
MCP_TOOL_RE = re.compile(r"mcp__")
URL_RE = re.compile(r"https?://\S+")
DATALETTI_RE = re.compile(r"^\*{0,2}Dati letti il \d{4}-\d{2}-\d{2}")

# Distinctly-English function words. Italian prose effectively never uses these;
# a handful of them together signals an answer that slipped into English.
ENGLISH_MARKERS = re.compile(
    r"\b(the|and|with|your|please|here are|search results|available|results for|"
    r"following|below|we found|this is|these are)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    passed: bool
    detail: str
    # All linter rule failures are warnings — they never block overall_pass.
    # overall_pass is determined solely by layer attribution + D2 + D4.
    severity: str = "soft"


# How many leading non-empty lines may precede `Dati letti il`. Headless LLM
# output reliably prepends a short conversational lead-in ("Ho tutti i dati…")
# that no prompt fully suppresses; the contract is relaxed to tolerate a brief
# preamble as long as the document opens with `Dati letti il` near the top.
FIRST_LINE_GRACE = 3


_SEPARATOR_RE = re.compile(r"^[-*=]{2,}$")


def _first_nonempty_lines(text: str, k: int) -> list[str]:
    """Return up to k non-empty, non-separator lines from the start of text."""
    out = []
    for line in text.splitlines():
        s = line.strip()
        if s and not _SEPARATOR_RE.match(s):
            out.append(s)
            if len(out) >= k:
                break
    return out


def check_first_line_dataletti(text: str) -> RuleResult:
    """The document must open with ``Dati letti il YYYY-MM-DD`` within the first
    ``FIRST_LINE_GRACE`` non-empty lines (a brief conversational lead-in is
    tolerated; anything deeper, or its absence, fails)."""
    head = _first_nonempty_lines(text, FIRST_LINE_GRACE)
    ok = any(DATALETTI_RE.match(line) for line in head)
    if ok:
        detail = "ok" if DATALETTI_RE.match(head[0]) else "ok (tolerated leading preamble)"
    else:
        first = head[0] if head else ""
        detail = f"no 'Dati letti il' in first {FIRST_LINE_GRACE} lines; starts {first[:60]!r}"
    return RuleResult("first_line", ok, detail)


def check_italian_only(text: str) -> RuleResult:
    """Discursive prose must be Italian. Conservative: fail only on a cluster of
    unambiguously-English markers (URLs/codes/identifiers are exempt)."""
    # Strip URLs and fenced code so identifiers/links don't trip the detector.
    prose = URL_RE.sub("", text)
    prose = re.sub(r"```.*?```", "", prose, flags=re.DOTALL)
    markers = {m.group(0).lower() for m in ENGLISH_MARKERS.finditer(prose)}
    ok = len(markers) < 2
    detail = "ok" if ok else f"English markers present: {sorted(markers)}"
    return RuleResult("italian_only", ok, detail)


def check_provenance(text: str) -> RuleResult:
    """Provenance present: at least one ``fonte:`` URL + a ``Dati letti il`` date,
    OR the answer is an explicit no-data answer (nothing to attribute)."""
    no_data = "Dati non disponibili" in text
    has_source = ("fonte:" in text.lower()) and bool(URL_RE.search(text))
    has_date = bool(re.search(r"Dati letti il \d{4}-\d{2}-\d{2}", text))
    ok = no_data or (has_source and has_date)
    if ok:
        detail = "no-data answer" if no_data and not has_source else "ok"
    else:
        detail = f"missing provenance (fonte+url={has_source}, dataletti={has_date})"
    return RuleResult("provenance", ok, detail)


def check_qualitative_confidence(text: str) -> RuleResult:
    """Confidence must be qualitative (Alta/Media/Bassa), never a percentage or
    numeric score on the same line as the word 'confidenz'.

    Patterns matched: percentages (87%), ratios (3/5 or 3.5/5), bare decimals
    between 0 and 1 (0.87 or 0,87). Italian thousands-separator notation like
    '85.763 caratteri' is intentionally NOT matched — only decimals with a
    leading zero qualify (0.87), since 'confidenza 85.763' is not a probability.
    """
    bad_lines = []
    for line in text.splitlines():
        if "confidenz" in line.lower() and re.search(
            r"\d+\s*%|\b\d+(?:[.,]\d+)?\s*/\s*\d+|\b0[.,]\d+\b", line
        ):
            bad_lines.append(line.strip())
    ok = not bad_lines
    detail = "ok" if ok else f"numeric confidence: {bad_lines}"
    return RuleResult("qualitative_confidence", ok, detail)


def check_no_exposed_tool_names(text: str) -> RuleResult:
    """No raw MCP tool names (``mcp__...``) may leak into user-facing output.

    The ``## Audit trail`` fenced block is excluded: skills may document the
    tool tier prefix there for provenance, but ``mcp__`` must not appear in
    the narrative body of the response.
    """
    audit_idx = text.find("## Audit trail")
    body = text[:audit_idx] if audit_idx != -1 else text
    hits = MCP_TOOL_RE.findall(body)
    ok = not hits
    detail = "ok" if ok else f"{len(hits)} 'mcp__' occurrence(s) exposed"
    return RuleResult("no_tool_names", ok, detail)


def check_audit_trail_block(text: str) -> RuleResult:
    """An ``## Audit trail`` heading followed by structured content must exist.

    Accepts either a fenced code block (``` ... ```) or a markdown pipe table
    (``| col | col |``). Both are valid structured formats for audit data;
    ``check_audit_parseable`` then validates the content inside.
    """
    idx = text.find("## Audit trail")
    if idx == -1:
        return RuleResult("audit_trail", False, "missing '## Audit trail' fenced block")
    trail = text[idx:]
    has_fence = "```" in trail
    has_table = bool(re.search(r"^\|.+\|", trail, re.MULTILINE))
    ok = has_fence or has_table
    detail = "ok" if ok else "missing '## Audit trail' fenced block"
    return RuleResult("audit_trail", ok, detail)


def _extract_record_ids(text: str) -> set[str]:
    ids = set(TED_ID_RE.findall(text))
    ids |= set(CUP_RE.findall(text))
    # CIGs only when they don't already match the (longer) CUP/(TED) patterns.
    for cig in CIG_RE.findall(text):
        ids.add(cig)
    return ids


def check_no_fabricated_ids(
    text: str, ground_truth_ids: list[str], prompt_text: str = ""
) -> RuleResult:
    """No raw record id (TED publication number / CIG / CUP) may appear in the
    output unless it is present in the known ground-truth id set OR was provided
    by the user in the prompt (echoing a user-supplied id is legitimate)."""
    allowed = set(ground_truth_ids)
    # Ids the user explicitly provided in the prompt are not fabrication.
    if prompt_text:
        allowed |= set(TED_ID_RE.findall(prompt_text))
        allowed |= set(CUP_RE.findall(prompt_text))
    # Only enforce on TED-shaped and CUP-shaped ids — bare 10-char CIG tokens are
    # too easily matched by ordinary alphanumeric words to gate on safely.
    found = set(TED_ID_RE.findall(text)) | set(CUP_RE.findall(text))
    fabricated = sorted(found - allowed)
    ok = not fabricated
    detail = "ok" if ok else f"ids not in ground truth: {fabricated}"
    return RuleResult("no_fabricated_ids", ok, detail)


def _ground_truth_ids(ground_truth: object) -> list[str]:
    """Accept either a list of record dicts or a list of id strings."""
    if not ground_truth:
        return []
    out: list[str] = []
    for item in ground_truth:  # type: ignore[union-attr]
        if isinstance(item, dict):
            rid = item.get("record_id")
            if rid:
                out.append(str(rid))
        elif item:
            out.append(str(item))
    return out


def check_audit_parseable(text: str) -> RuleResult:
    """The ``## Audit trail`` fenced block must contain parseable structured rows.

    Accepts two formats:
    - Key-value lines: ``key: value`` (current default skill output)
    - Pipe-separated table rows: ``tool | args | n``

    An empty block or lines that match neither format raise the explicit
    ``AUDIT_UNPARSEABLE`` state so a skill cannot under-report calls in
    unstructured prose and slip through the gate.
    """
    idx = text.find("## Audit trail")
    if idx == -1:
        return RuleResult("audit_parseable", False,
                          "AUDIT_UNPARSEABLE: no '## Audit trail' section")

    trail = text[idx:]
    fence_match = re.search(r"```[^\n]*\n(.*?)```", trail, re.DOTALL)
    if not fence_match:
        return RuleResult("audit_parseable", False,
                          "AUDIT_UNPARSEABLE: no fenced block after '## Audit trail'")

    block = fence_match.group(1)
    content_lines = [ln for ln in block.splitlines() if ln.strip()]
    if not content_lines:
        return RuleResult("audit_parseable", False,
                          "AUDIT_UNPARSEABLE: fenced block is empty")

    bad: list[str] = []
    for line in content_lines:
        line_s = line.strip()
        # Skip markdown table separators (--- or ===).
        if re.fullmatch(r"[-|=: ]+", line_s):
            continue
        # Accept key:value, pipe-separated, key=value, or arrow (→) rows.
        if ":" not in line_s and "|" not in line_s and "=" not in line_s and "→" not in line_s:
            bad.append(line_s[:60])
    ok = not bad
    detail = "ok" if ok else f"AUDIT_UNPARSEABLE: unparseable rows: {bad[:2]}"
    # Formatting-only failures are soft: the audit trail is present but not perfectly structured.
    return RuleResult("audit_parseable", ok, detail, severity="soft")


def check_no_criteria_fabrication(text: str) -> RuleResult:
    """When a document is declared unreadable in 'Dati non disponibili', the
    'Criteri di valutazione' section must not contain fabricated point values.

    Only fires when the D-n-d section explicitly mentions a document-level
    failure (scanned, not reachable, download error). Ignored otherwise.
    """
    dnd_idx = text.find("## Dati non disponibili")
    if dnd_idx == -1:
        return RuleResult("no_criteria_fabrication", True, "no Dati non disponibili section")

    dnd_snippet = text[dnd_idx : dnd_idx + 600].lower()
    unreadable_signals = (
        "scansionato", "no text layer", "non analizzabile", "non raggiungibile",
        "download", "errore", "pdf has no text", "corrupt",
    )
    doc_unreadable = any(s in dnd_snippet for s in unreadable_signals)
    if not doc_unreadable:
        return RuleResult("no_criteria_fabrication", True, "document readable — skip")

    crit_idx = text.find("## Criteri di valutazione")
    if crit_idx == -1:
        return RuleResult("no_criteria_fabrication", True, "no Criteri section — ok")

    crit_snippet = text[crit_idx : crit_idx + 1000]
    fabricated = re.findall(r"\b(\d{1,3})\s+punti\b", crit_snippet, re.IGNORECASE)
    ok = not fabricated
    detail = "ok" if ok else f"punti values present while doc declared unreadable: {fabricated}"
    return RuleResult("no_criteria_fabrication", ok, detail)


def run_all_rules(
    text: str, ground_truth: object = None, prompt: str = ""
) -> list[RuleResult]:
    """Run every deterministic output rule and return the results."""
    gt_ids = _ground_truth_ids(ground_truth)
    return [
        check_first_line_dataletti(text),
        check_italian_only(text),
        check_provenance(text),
        check_qualitative_confidence(text),
        check_no_exposed_tool_names(text),
        check_audit_trail_block(text),
        check_audit_parseable(text),
        check_no_fabricated_ids(text, gt_ids, prompt_text=prompt),
        check_no_criteria_fabrication(text),
    ]


__all__ = [
    "RuleResult",
    "check_first_line_dataletti",
    "check_italian_only",
    "check_provenance",
    "check_qualitative_confidence",
    "check_no_exposed_tool_names",
    "check_audit_trail_block",
    "check_audit_parseable",
    "check_no_fabricated_ids",
    "check_no_criteria_fabrication",
    "run_all_rules",
]
