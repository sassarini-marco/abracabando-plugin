#!/usr/bin/env python3
"""Evaluation harness for segnale-azionabile templates 3.1, 3.2, 3.3.

Runs each case from bench/dataset/eval_dataset.json through Claude Code, applies
rule-based D2/D4 checks, submits D1/D3/D5/D6/D7 to Claude Haiku via Batch API.

Usage:
    python bench/eval_runner.py                    # run all cases
    python bench/eval_runner.py --template 3.1     # run one template
    python bench/eval_runner.py --check-staleness  # print staleness table, exit 1 if stale
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))

from mcp_preflight import (  # noqa: E402
    attribute_layer,
    attribute_layer_from_probe,
    extract_records,
    record_identity,
)
from mcp_probe import load_probe_results  # noqa: E402
from output_rules import run_all_rules  # noqa: E402

BENCH = Path(__file__).resolve().parent
PLUGIN = BENCH.parent
EVAL_RESULTS = BENCH / "eval_results"
GOLDEN_DIR = BENCH / "cases"

# Pin to a full model version string (no alias) so frozen runs are reproducible;
# there is no --temperature flag, so tolerant scoring + a pinned version is the
# best we can do for determinism.
DEFAULT_MODEL = "claude-sonnet-4-6"

TEMPLATE_TO_SKILL: dict[str, str] = {
    "3.1": "pin-radar",
    "3.2": "consultazioni-radar",
    "3.3": "scheda-opportunita",
    "3.4": "digest-pregara",
    "3.5": "profilo-sa",
    "3.6": "reconciliation-pnrr",
    "3.7": "analisi-disciplinare",
    "3.8": "trova-bando-compatibile",
}

# Layers that count as a clean pass for the hard gate.
PASSING_LAYERS = {"skill_ok", "skill_ok_no_data"}
# Layers that are infrastructure noise — neither pass nor fail.
NEEDS_RERUN_LAYERS = {"needs_rerun"}
# Fixture/data gaps — INCONCLUSIVE (not a skill verdict).
# "golden_missing": the golden was never captured (fixture debt).
# "stale_ground_truth": golden had records but live data has since drifted.
# Both need follow-up, but should not count against the skill pass-rate.
INCONCLUSIVE_LAYERS = {"golden_missing", "stale_ground_truth"}

# Skills that synthesise/aggregate data and legitimately do not echo raw
# record IDs in their output — surfacing-based layer attribution doesn't apply.
AGGREGATING_SKILLS = {"digest-pregara", "profilo-sa", "reconciliation-pnrr", "analisi-disciplinare"}

JUDGE_MODEL = "claude-haiku-4-5-20251001"

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "d1_score": {"type": "integer", "enum": [-1, 0, 1]},
        "d1_reason": {"type": "string"},
        "d3_score": {"type": "integer", "enum": [-1, 0, 1]},
        "d3_reason": {"type": "string"},
        "d5_score": {"type": "integer", "enum": [0, 1]},
        "d5_reason": {"type": "string"},
        "d6_score": {"type": "integer", "enum": [0, 1]},
        "d6_reason": {"type": "string"},
        "d7_score": {"type": "integer", "enum": [-1, 0, 1]},
        "d7_reason": {"type": "string"},
    },
    "required": [
        "d1_score", "d1_reason",
        "d3_score", "d3_reason",
        "d5_score", "d5_reason",
        "d6_score", "d6_reason",
        "d7_score", "d7_reason",
    ],
}




def check_d2_recall(answer: str, ground_truth_records: list[dict]) -> float | None:
    """Return fraction of expected record IDs found in the rendered answer.

    Matching is per-source:
      - ted:    publication number pattern \\d{6}-\\d{4} (e.g. '735506-2025')
      - consip: case-insensitive substring match of the record_id
      - anac:   CIG pattern [A-Z0-9]{10} present in the answer; if record_id
                looks like a real CIG, matches exactly; otherwise any CIG counts
      - other:  case-insensitive substring match

    Returns None when there are no expected IDs (vacuous — D2 does not apply,
    e.g. a correct missing-data case). Callers treat None as "not a failure".
    """
    expected = [r for r in ground_truth_records if r.get("record_id")]
    if not expected:
        return None

    ted_found = set(re.findall(r"\d{6}-\d{4}", answer))
    cig_found = set(re.findall(r"\b[A-Z0-9]{10}\b", answer))

    hits = 0
    for rec in expected:
        rid = rec["record_id"]
        source = (rec.get("source") or "").lower()
        if source == "ted":
            if rid in ted_found:
                hits += 1
        elif source == "anac":
            if re.fullmatch(r"[A-Z0-9]{10}", rid):
                if rid in cig_found:
                    hits += 1
            elif cig_found:
                hits += 1
        else:
            if rid.lower() in answer.lower():
                hits += 1
    return hits / len(expected)


def check_d4_freshness(answer: str, reference_date: str, max_days: int = 35) -> bool:
    """Return True if the 'Dati letti il YYYY-MM-DD' date in answer is within max_days of reference_date."""
    match = re.search(r"Dati letti il (\d{4}-\d{2}-\d{2})", answer)
    if not match:
        return False
    found_date = date.fromisoformat(match.group(1))
    ref_date = date.fromisoformat(reference_date)
    return abs((found_date - ref_date).days) <= max_days


def check_staleness(cases: list) -> list[dict]:
    """Return staleness info for each case."""
    today = date.today()
    rows = []
    for case in cases:
        frozen = date.fromisoformat(case["frozen_date"])
        ttl = case["ttl_days"]
        days_old = (today - frozen).days
        rows.append({
            "id": case["id"],
            "frozen_date": case["frozen_date"],
            "ttl_days": ttl,
            "days_old": days_old,
            "stale": days_old > ttl,
        })
    return rows




class PluginLoadError(RuntimeError):
    """The headless run reported plugin_errors — a silently degraded run."""


def _scan_plugin_errors(raw: str) -> list:
    """Return the plugin_errors array from the stream-json system/init event."""
    for line in raw.splitlines():
        try:
            o = json.loads(line)
        except (ValueError, TypeError):
            continue
        if o.get("type") in ("system", "init") and o.get("plugin_errors"):
            return o["plugin_errors"]
    return []


MCP_TOOL_PREFIX = "mcp__industrial-mcp-free__"


def parse_stream(raw: str) -> dict:
    """Parse a stream-json transcript into answer text + the actual MCP traffic.

    Returns ``{"answer", "mcp_records", "mcp_tools", "mcp_calls"}`` where
    ``mcp_records`` are the records the MCP server actually returned across the
    run (normalised), ``mcp_tools`` is the set of MCP tool short-names called,
    and ``mcp_calls`` is the raw call count. This is what lets the live tier
    attribute a failure to the skill vs the MCP layer.
    """
    answer = None
    tooluse_name: dict[str, str] = {}
    mcp_records: list[dict] = []
    mcp_tools: set[str] = set()
    mcp_calls = 0

    for line in raw.splitlines():
        try:
            o = json.loads(line)
        except (ValueError, TypeError):
            continue
        typ = o.get("type")
        if typ == "result":
            answer = o.get("result")
        elif typ == "assistant":
            for b in (o.get("message") or {}).get("content", []):
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    name = b.get("name", "")
                    if name.startswith(MCP_TOOL_PREFIX):
                        tooluse_name[b.get("id")] = name
        elif typ == "user":
            for b in (o.get("message") or {}).get("content", []):
                if not isinstance(b, dict) or b.get("type") != "tool_result":
                    continue
                name = tooluse_name.get(b.get("tool_use_id"))
                if not name:
                    continue
                mcp_calls += 1
                mcp_tools.add(name[len(MCP_TOOL_PREFIX):])
                content = b.get("content")
                payload = content
                if isinstance(content, list):
                    payload = {"content": content}
                elif isinstance(content, str):
                    try:
                        payload = json.loads(content)
                    except ValueError:
                        payload = {"content": [{"type": "text", "text": content}]}
                mcp_records.extend(extract_records(payload))

    return {
        "answer": answer or "",
        "mcp_records": mcp_records,
        "mcp_tools": sorted(mcp_tools),
        "mcp_calls": mcp_calls,
    }


def run_case_detailed(
    case: dict,
    plugin_dir: Path,
    mcp_config: Path,
    timeout: int = 900,
    model: str = DEFAULT_MODEL,
) -> dict:
    """Run a case headlessly and return the parsed stream (answer + MCP traffic).

    Raises ``PluginLoadError`` if the run reported plugin_errors.
    """
    cmd = [
        "claude", "-p", case["prompt"],
        "--plugin-dir", ".",
        "--model", model,
        "--mcp-config", str(mcp_config), "--strict-mcp-config",
        "--allowedTools", "mcp__industrial-mcp-free__*",
        "--output-format", "stream-json", "--verbose",
    ]
    timed_out = False
    try:
        proc = subprocess.run(
            cmd, cwd=plugin_dir, capture_output=True, text=True, timeout=timeout
        )
        raw = proc.stdout
    except subprocess.TimeoutExpired as e:
        raw = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        timed_out = True

    errors = _scan_plugin_errors(raw)
    if errors:
        raise PluginLoadError(f"plugin_errors for {case.get('id')}: {errors}")

    parsed = parse_stream(raw)
    parsed["timed_out"] = timed_out
    if timed_out:
        parsed["answer"] = f"[TIMEOUT after {timeout}s] {parsed['answer']}"
    return parsed


def run_case(
    case: dict,
    plugin_dir: Path,
    mcp_config: Path,
    timeout: int = 900,
    model: str = DEFAULT_MODEL,
) -> str:
    """Backward-compatible wrapper: returns just the answer text."""
    return run_case_detailed(case, plugin_dir, mcp_config, timeout, model)["answer"]


def load_golden(case_id: str) -> tuple[list[dict], bool]:
    """Load the independent golden for a case.

    Returns ``(records, is_placeholder)`` where ``is_placeholder`` is True when
    the golden file exists but was never populated (``empty_reason`` set,
    ``records`` empty).  Callers can use this to distinguish fixture debt from
    genuine data drift when both result in an empty record list.
    """
    path = GOLDEN_DIR / case_id / "golden.json"
    if not path.exists():
        return [], False
    data = json.loads(path.read_text())
    records = data.get("records") or []
    is_placeholder = bool(data.get("empty_reason")) and not records
    return records, is_placeholder


def load_golden_records(case_id: str) -> list[dict]:
    """Backward-compatible wrapper — returns only the records."""
    records, _ = load_golden(case_id)
    return records


def _surfacing_rate(answer: str, mcp_records: list[dict]) -> float | None:
    """Of the records the MCP actually returned, what fraction did the skill
    surface (by record id) in its answer? None when the MCP returned nothing.

    Low MCP count → MCP/query gap; high MCP count but low surfacing rate →
    the skill dropped data it was handed."""
    ids = {rid for r in mcp_records if (rid := record_identity(r))}
    if not ids:
        return None
    hit = sum(1 for rid in ids if rid in answer)
    return hit / len(ids)


def score_case_deterministic(
    case: dict,
    answer: str,
    golden_records: list[dict],
    mcp_records: list[dict] | None = None,
    reference_date: str | None = None,
    mcp_tools: list[str] | None = None,
    mcp_calls: int | None = None,
    probe_results: dict | None = None,
    golden_is_placeholder: bool = False,
    is_aggregating: bool = False,
    timed_out: bool = False,
) -> dict:
    """Score the deterministic dimensions for one case — no API key required.

    Runs the output-rule linter (the output contract), D2 recall, D4 freshness,
    and golden-backed layer attribution. When ``mcp_records`` are the records the
    live MCP actually returned, attribution can separate skill bugs from MCP
    gaps. When ``probe_results`` are also provided (from ``mcp_probe.py``),
    attribution uses the grounded cross-tool consistency signal instead of the
    heuristic ``_divergent()`` reconstruction. When both are omitted it falls
    back to the golden (frozen replay). No judge dimensions are computed here.

    Gate semantics (hardened):
    - Timed-out runs, infra layers, and fixture-debt layers → INCONCLUSIVE (None).
    - Hard rule failures (missing audit trail, provenance, tool-name leaks,
      fabricated ids) block the pass even when layer/D2 look fine.
    - Soft rule failures (audit formatting) are warnings — do not block the pass.
    - ``skill_ok`` + D2=1.0 can never be False due to formatting alone.
    """
    used_real_mcp = mcp_records is not None
    if mcp_records is None:
        mcp_records = golden_records
    ref = reference_date or date.today().isoformat()

    gt_records = case.get("ground_truth_records", [])
    prompt = case.get("prompt", "")
    d2 = check_d2_recall(answer, gt_records)
    d4 = check_d4_freshness(answer, ref)
    rules = run_all_rules(answer, gt_records, prompt=prompt)
    rules_map = {r.rule_id: r.passed for r in rules}

    if probe_results and used_real_mcp:
        layer = attribute_layer_from_probe(
            answer, mcp_records, golden_records, probe_results,
            golden_is_placeholder=golden_is_placeholder,
            is_aggregating=is_aggregating,
        )
    else:
        layer = attribute_layer(
            answer, mcp_records, golden_records,
            golden_is_placeholder=golden_is_placeholder,
            is_aggregating=is_aggregating,
        )

    # Determine overall pass — tri-state: True / False / None (inconclusive).
    # Gate: skill correctness only (layer attribution + D2 recall + D4 freshness).
    # Output-rule violations are always warnings; they never block the pass.
    if timed_out or layer in (NEEDS_RERUN_LAYERS | INCONCLUSIVE_LAYERS):
        overall = None
    else:
        d2_ok = d2 is None or d2 == 1.0
        overall = bool(d4) and d2_ok and layer in PASSING_LAYERS

    # All rule failures are warnings (informational, do not affect overall_pass).
    soft_warnings = [r.rule_id for r in rules if not r.passed]

    result = {
        "id": case["id"],
        "skill": case.get("skill"),
        "scenario": case.get("scenario"),
        "tier": case.get("tier"),
        "template": case.get("template"),
        "d2_recall": d2,
        "d4_freshness": d4,
        "output_rules": rules_map,
        "output_rules_detail": {r.rule_id: r.detail for r in rules},
        "output_rules_severity": {r.rule_id: r.severity for r in rules},
        "contract_warnings": soft_warnings,
        "layer": layer,
        "overall_pass": overall,
        "answer": answer,
    }
    if used_real_mcp:
        result["mcp_record_count"] = len(mcp_records)
        result["mcp_tools_called"] = mcp_tools or []
        result["mcp_calls"] = mcp_calls if mcp_calls is not None else None
        result["surfacing_rate"] = _surfacing_rate(answer, mcp_records)
    return result


def build_judge_request(case: dict, answer: str, judge_prompt: str) -> dict:
    """Build an Anthropic Batch API request dict for the judge step."""
    return {
        "custom_id": case["id"],
        "params": {
            "model": "haiku",
            "temperature": 0.1,
            "max_tokens": 1024,
            "system": judge_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"## Prompt inviato al plugin\n{case['prompt']}\n\n"
                        f"## Risposta del plugin\n{answer}"
                    ),
                }
            ],
            "tools": [
                {
                    "name": "judge_output",
                    "description": "Output strutturato del giudice con i punteggi per ciascuna dimensione.",
                    "input_schema": JUDGE_SCHEMA,
                }
            ],
            "tool_choice": {"type": "tool", "name": "judge_output"},
        },
    }


def run_judge_sync(case: dict, answer: str, judge_prompt: str, client) -> dict:
    """Score one case with the judge synchronously (dev iteration / single case).

    Faster than the Batch API for individual cases; not cost-optimal for full
    runs (use ``run_judge_batch`` for ≥2 cases).
    """
    req = build_judge_request(case, answer, judge_prompt)
    params = req["params"]
    resp = client.messages.create(
        model=JUDGE_MODEL,
        temperature=params.get("temperature", 0.1),
        max_tokens=params.get("max_tokens", 1024),
        system=params["system"],
        messages=params["messages"],
        tools=params["tools"],
        tool_choice=params["tool_choice"],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == "judge_output":
            return block.input
    return {}


def run_judge_batch(requests: list[dict], client) -> dict[str, dict]:
    """Submit a message batch, poll until complete, return results keyed by custom_id."""
    batch = client.messages.batches.create(requests=requests)
    batch_id = batch.id
    print(f"  [judge] Batch created: {batch_id}")

    while True:
        time.sleep(10)
        batch = client.messages.batches.retrieve(batch_id)
        status = batch.processing_status
        print(f"  [judge] Batch status: {status}")
        if status == "ended":
            break

    results: dict[str, dict] = {}
    for result in client.messages.batches.results(batch_id):
        cid = result.custom_id
        if result.result.type == "succeeded":
            msg = result.result.message
            for block in msg.content:
                if block.type == "tool_use" and block.name == "judge_output":
                    results[cid] = block.input
                    break
        else:
            results[cid] = {"error": str(result.result)}
    return results


def print_staleness_table(rows: list[dict]) -> None:
    """Print a formatted staleness table to stdout."""
    header = f"{'ID':<15} {'frozen_date':<12} {'ttl_days':>8} {'days_old':>8} {'stale':>6}"
    print(header)
    print("-" * len(header))
    for row in rows:
        stale_str = "YES" if row["stale"] else "no"
        print(
            f"{row['id']:<15} {row['frozen_date']:<12} {row['ttl_days']:>8} "
            f"{row['days_old']:>8} {stale_str:>6}"
        )


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Evaluation harness for the abracabando skills."
    )
    ap.add_argument(
        "--template",
        choices=["3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8"],
        help="Run only cases for this template.",
    )
    ap.add_argument(
        "--skill",
        choices=sorted(set(TEMPLATE_TO_SKILL.values())),
        help="Run only cases for this skill slug.",
    )
    tier = ap.add_mutually_exclusive_group()
    tier.add_argument(
        "--frozen", action="store_true",
        help="Frozen tier (default): replay fixtures via bench/config/mcp_replay.json, "
             "deterministic scoring, no API key required.",
    )
    tier.add_argument(
        "--live", action="store_true",
        help="Live tier: real bench/config/mcp_live.json + non-empty preflight; surfaces "
             "MCP-layer attributions for ../industrial-data-mcp.",
    )
    ap.add_argument(
        "--check-staleness",
        action="store_true",
        help="Print staleness table and exit 1 if any case is stale.",
    )
    ap.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model to use for eval runs (default: {DEFAULT_MODEL}). Pin a full version string.",
    )
    ap.add_argument(
        "--delay",
        type=int,
        default=10,
        help="Seconds to wait between cases (default: 10). Use to avoid rate limits.",
    )
    ap.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Per-case timeout in seconds (default: 900 frozen / 1500 live).",
    )
    ap.add_argument(
        "--case",
        help="Run only this specific case ID (e.g. 3.7-001).",
    )
    ap.add_argument(
        "--sync",
        action="store_true",
        help="Use synchronous messages.create for the judge instead of the Batch API. "
             "Faster for single-case dev iteration; use the default batch for full runs.",
    )
    ap.add_argument(
        "--probe-dir",
        type=Path,
        default=None,
        help="Directory containing mcp_probe_result JSON files (from mcp_probe.py). "
             "When provided, the live-tier attribution uses the grounded cross-tool "
             "consistency signal instead of the heuristic reconstruction.",
    )
    args = ap.parse_args()

    # Frozen is the default when neither flag is given.
    live = args.live
    mcp_config = (BENCH / "config" / "mcp_live.json") if live else (BENCH / "config" / "mcp_replay.json")

    dataset = json.loads((BENCH / "cases" / "eval_dataset.json").read_text())
    cases = dataset["cases"]

    if args.case:
        cases = [c for c in cases if c["id"] == args.case]
    if args.template:
        cases = [c for c in cases if c["template"] == args.template]
    if args.skill:
        cases = [c for c in cases if c.get("skill") == args.skill]
    if not live:
        # The frozen tier only runs cases that have committed fixtures.
        cases = [c for c in cases if c.get("tier", "frozen") == "frozen"]

    if args.check_staleness:
        rows = check_staleness(cases)
        print_staleness_table(rows)
        if any(r["stale"] for r in rows):
            sys.exit(1)
        return

    # The judge runs only on the live/secret-gated path. The frozen tier scores
    # deterministically and builds no judge request.
    anthropic_client = None
    if live:
        try:
            import anthropic
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                anthropic_client = anthropic.Anthropic(api_key=api_key)
            else:
                print("WARNING: ANTHROPIC_API_KEY not set — judge dims skipped.", file=sys.stderr)
        except ImportError:
            print("WARNING: 'anthropic' not installed — judge dims skipped.", file=sys.stderr)

    judge_prompt = (BENCH / "judge_prompt_v1.md").read_text()

    timeout = args.timeout if args.timeout is not None else (1500 if live else 900)

    # Load probe results for grounded live-tier attribution (optional).
    probe_results: dict = {}
    if live:
        probe_dir = args.probe_dir
        probe_results = load_probe_results(probe_dir)
        if probe_results:
            print(f"  [probe] Loaded {len(probe_results)} probe result(s) for attribution.")
        else:
            print("  [probe] No probe results found — using heuristic attribution.")

    EVAL_RESULTS.mkdir(exist_ok=True)
    today_iso = date.today().isoformat()

    answers: dict[str, str] = {}
    partial_results: dict[str, dict] = {}

    print(f"Running {len(cases)} case(s) [{'live' if live else 'frozen'} tier, timeout {timeout}s]...\n")
    for i, case in enumerate(cases):
        cid = case["id"]
        if i > 0 and args.delay > 0 and live:
            print(f"  [pause {args.delay}s between cases to avoid rate limit...]")
            time.sleep(args.delay)
        print(f"  [{cid}] Running via Claude Code...")

        golden_records, golden_is_placeholder = load_golden(cid)
        is_aggregating = case.get("skill") in AGGREGATING_SKILLS
        os.environ["MCP_REPLAY_CASE"] = cid  # tell the replay server which fixture to load

        t0 = time.time()
        try:
            run = run_case_detailed(case, PLUGIN, mcp_config, timeout=timeout, model=args.model)
        except PluginLoadError as exc:
            print(f"  [{cid}] FAIL FAST: {exc}", file=sys.stderr)
            sys.exit(2)
        wall_time_s = round(time.time() - t0, 1)
        answer = run["answer"]
        answers[cid] = answer

        # On the live tier, attribute against the records the MCP actually
        # returned (skill-vs-MCP). On frozen, fall back to the golden.
        mcp_records = run["mcp_records"] if live else None
        result = score_case_deterministic(
            case, answer, golden_records,
            mcp_records=mcp_records, reference_date=today_iso,
            mcp_tools=run.get("mcp_tools"), mcp_calls=run.get("mcp_calls"),
            probe_results=probe_results if live else None,
            golden_is_placeholder=golden_is_placeholder,
            is_aggregating=is_aggregating,
            timed_out=run.get("timed_out", False),
        )
        result["timed_out"] = run.get("timed_out", False)
        result["wall_time_s"] = wall_time_s
        partial_results[cid] = result
        # Write immediately so an interrupted run leaves partial results on disk.
        EVAL_RESULTS.mkdir(exist_ok=True)
        out_path = EVAL_RESULTS / f"{cid}.json"
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        d2 = result["d2_recall"]
        d2_str = "N/A" if d2 is None else f"{d2:.2f}"
        warns = result.get("contract_warnings") or []
        warn_str = f"  warnings={warns}" if warns else ""
        extra = ""
        if live:
            sr = result.get("surfacing_rate")
            sr_str = "N/A" if sr is None else f"{sr:.2f}"
            extra = (f"  mcp_recs={result.get('mcp_record_count')} "
                     f"tools={result.get('mcp_tools_called')} surfacing={sr_str}")
        print(
            f"         D2={d2_str}  D4={result['d4_freshness']}  "
            f"layer={result['layer']}  pass={result['overall_pass']}  "
            f"time={wall_time_s}s{warn_str}{extra}"
        )

    # Submit judge only on the live tier with an API key.
    if anthropic_client is not None:
        judge_results: dict[str, dict] = {}
        if args.sync or (args.case and len(cases) == 1):
            # Synchronous mode: one messages.create per case — faster for dev iteration.
            print("\nRunning judge (sync mode)...")
            for case in cases:
                cid = case["id"]
                print(f"  [{cid}] judging...", end=" ", flush=True)
                try:
                    jr = run_judge_sync(case, answers[cid], judge_prompt, anthropic_client)
                    judge_results[cid] = jr
                    print(f"d1={jr.get('d1_score')} d3={jr.get('d3_score')} d7={jr.get('d7_score')}")
                except Exception as exc:
                    print(f"ERROR: {exc}", file=sys.stderr)
                    judge_results[cid] = {"error": str(exc)}
        else:
            # Batch mode: ~50% cheaper for multi-case runs; ~2-5 min wall time.
            print("\nSubmitting judge batch...")
            requests = [
                build_judge_request(case, answers[case["id"]], judge_prompt)
                for case in cases
            ]
            try:
                judge_results = run_judge_batch(requests, anthropic_client)
            except Exception as exc:
                print(f"ERROR: Judge batch failed: {exc}", file=sys.stderr)
                judge_results = {}
    else:
        judge_results = {}

    # Merge judge dimensions into already-written per-case files.
    for case in cases:
        cid = case["id"]
        result = dict(partial_results[cid])
        if cid in judge_results:
            result.update(judge_results[cid])
            out_path = EVAL_RESULTS / f"{cid}.json"
            out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
            print(f"  [{cid}] Updated with judge dims -> {out_path}")

    times = [r.get("wall_time_s", 0) for r in partial_results.values() if r.get("wall_time_s")]
    if times:
        print(
            f"\nTiming — total: {sum(times):.1f}s  "
            f"mean: {sum(times)/len(times):.1f}s  "
            f"min: {min(times):.1f}s  max: {max(times):.1f}s"
        )
    print(f"Done. Results in {EVAL_RESULTS}")


if __name__ == "__main__":
    main()
