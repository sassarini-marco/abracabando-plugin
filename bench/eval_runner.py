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

BENCH = Path(__file__).resolve().parent
PLUGIN = BENCH.parent
EVAL_RESULTS = BENCH / "eval_results"

TEMPLATE_TO_SKILL: dict[str, str] = {
    "3.1": "pin-radar",
    "3.2": "consultazioni-radar",
    "3.3": "scheda-opportunita",
}

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




def check_d2_recall(answer: str, ground_truth_records: list[dict]) -> float:
    """Return fraction of expected record IDs found in the rendered answer.

    Matching is per-source:
      - ted:    publication number pattern \\d{6}-\\d{4} (e.g. '735506-2025')
      - consip: case-insensitive substring match of the record_id
      - anac:   CIG pattern [A-Z0-9]{10} present in the answer; if record_id
                looks like a real CIG, matches exactly; otherwise any CIG counts
      - other:  case-insensitive substring match

    Returns 1.0 when there are no expected IDs (vacuously correct).
    """
    expected = [r for r in ground_truth_records if r.get("record_id")]
    if not expected:
        return 1.0

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


def check_d4_freshness(answer: str, reference_date: str, max_days: int = 45) -> bool:
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




def run_case(case: dict, plugin_dir: Path, mcp_config: Path, timeout: int = 900, model: str = "sonnet") -> str:
    """Run a single eval case through Claude Code.

    Returns the markdown answer text emitted by the skill.
    """
    cmd = [
        "claude", "-p", case["prompt"],
        "--plugin-dir", ".",
        "--model", model,
        "--mcp-config", "bench/mcp.json", "--strict-mcp-config",
        "--allowedTools", "mcp__industrial-mcp-free__*",
        "--disallowedTools", "Bash",
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

    result_text = None
    for line in raw.splitlines():
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get("type") == "result":
            result_text = o.get("result")
            break

    if timed_out:
        return f"[TIMEOUT after {timeout}s] {result_text or ''}"

    return result_text or ""


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
        description="Evaluation harness for segnale-azionabile templates 3.1, 3.2, 3.3."
    )
    ap.add_argument(
        "--template",
        choices=["3.1", "3.2", "3.3"],
        help="Run only cases for this template.",
    )
    ap.add_argument(
        "--check-staleness",
        action="store_true",
        help="Print staleness table and exit 1 if any case is stale.",
    )
    ap.add_argument(
        "--model",
        default="sonnet",
        help="Model to use for eval runs (default: sonnet). Overrides skill frontmatter.",
    )
    ap.add_argument(
        "--delay",
        type=int,
        default=10,
        help="Seconds to wait between cases (default: 10). Use to avoid rate limits.",
    )
    args = ap.parse_args()

    dataset = json.loads((BENCH / "dataset" / "eval_dataset.json").read_text())
    cases = dataset["cases"]

    if args.template:
        cases = [c for c in cases if c["template"] == args.template]

    if args.check_staleness:
        rows = check_staleness(cases)
        print_staleness_table(rows)
        if any(r["stale"] for r in rows):
            sys.exit(1)
        return

    # Try to import the Anthropic SDK for the judge step.
    try:
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print(
                "WARNING: ANTHROPIC_API_KEY not set — judge step (D1/D3/D5/D6/D7) "
                "will be skipped. Only D2/D4 scores will be written.",
                file=sys.stderr,
            )
            anthropic_client = None
        else:
            anthropic_client = anthropic.Anthropic(api_key=api_key)
    except ImportError:
        print(
            "WARNING: 'anthropic' package not installed — judge step (D1/D3/D5/D6/D7) "
            "will be skipped. Install with: pip install anthropic",
            file=sys.stderr,
        )
        anthropic_client = None

    judge_prompt = (BENCH / "judge_prompt_v1.md").read_text()

    EVAL_RESULTS.mkdir(exist_ok=True)

    today_iso = date.today().isoformat()

    # Collect answers and deterministic scores.
    answers: dict[str, str] = {}
    partial_results: dict[str, dict] = {}

    print(f"Running {len(cases)} case(s)...\n")
    for i, case in enumerate(cases):
        cid = case["id"]
        if i > 0 and args.delay > 0:
            print(f"  [pause {args.delay}s between cases to avoid rate limit...]")
            time.sleep(args.delay)
        print(f"  [{cid}] Running via Claude Code...")
        answer = run_case(case, PLUGIN, BENCH / "mcp.json", model=args.model)
        answers[cid] = answer

        d2 = check_d2_recall(answer, case["ground_truth_records"])
        d4 = check_d4_freshness(answer, today_iso)

        partial_results[cid] = {
            "id": cid,
            "template": case["template"],
            "d2_recall": d2,
            "d4_freshness": d4,
            "answer": answer,
        }
        d2_str = "N/A" if d2 is None else f"{d2:.2f}"
        print(f"         D2 recall={d2_str}  D4 freshness={d4}")

    # Submit judge batch if SDK is available.
    if anthropic_client is not None:
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

    # Merge and write results.
    for case in cases:
        cid = case["id"]
        result = dict(partial_results[cid])
        if cid in judge_results:
            result.update(judge_results[cid])
        out_path = EVAL_RESULTS / f"{cid}.json"
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"  [{cid}] Written -> {out_path}")

    print(f"\nDone. Results in {EVAL_RESULTS}")


if __name__ == "__main__":
    main()
