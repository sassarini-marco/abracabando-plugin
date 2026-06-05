# bench/ — Evaluation Infrastructure

This directory contains the evaluation harness for measuring skill quality across 7 dimensions (relevance, recall, signal quality, freshness, traceability, language, synthesis).

## Directory structure

```
bench/
├── README.md                    # This file
├── eval_runner.py               # Main harness: runs cases, computes D2/D4, submits judge batch
├── eval_report.py               # Generates summary table from eval_results/
├── test_eval_runner.py          # Unit tests for eval logic
├── judge_prompt_v1.md           # System prompt for Haiku judge (D1/D3/D5/D6/D7)
├── mcp.json                     # MCP server config for eval runs
├── REFRESH_PROCEDURE.md         # How to refresh dataset when cases go stale
├── dataset/                     # Test cases and schema
│   ├── eval_dataset.json        # 6 test cases (templates 3.1, 3.2, 3.3)
│   └── eval_dataset_schema.json # JSON Schema for eval_dataset.json
├── eval_results/                # Latest scores for all 6 cases (*.json)
├── ground-truth/                # TED PIN labeller and labelled data
│   ├── label_ted_pins.py        # Labels TED PINs with follow-on CN/CAN conversion
│   ├── test_label_ted_pins.py   # Tests for the labeller
│   └── ted_pin_labels_*.json    # Labelled TED records (Oct 2025–May 2026)
└── archive/                     # Historical benchmarks and reports
    └── benchmark-2026-05-29.md  # Old tier 1-5 benchmark (pre-eval-runner era)
```

## Quick start

### Run evaluation

```bash
# Check for stale cases first
python bench/eval_runner.py --check-staleness

# Run all 6 cases (takes ~10 min with default 10s delay between cases)
ANTHROPIC_API_KEY=<key> python bench/eval_runner.py

# Run only one template
python bench/eval_runner.py --template 3.1

# Faster model for testing (default: sonnet)
python bench/eval_runner.py --model haiku --delay 5
```

### Generate report

```bash
python bench/eval_report.py
```

### Run tests

```bash
pytest bench/test_eval_runner.py -v
```

## Evaluation dimensions

| Dim | Name | Type | Checker |
|-----|------|------|---------|
| D1 | Relevance | Judge | Haiku judges if response answers the user's question |
| D2 | Recall | Deterministic | `check_d2_recall()` — fraction of expected IDs found |
| D3 | Signal quality | Judge | Haiku judges if probabilities are qualitative (Alta/Media/Bassa) |
| D4 | Freshness | Deterministic | `check_d4_freshness()` — "Dati letti il" within 45 days |
| D5 | Traceability | Judge | Haiku judges if every data point has a date |
| D6 | Language | Judge | Haiku judges if output is in Italian |
| D7 | Multi-source synthesis | Judge | Haiku judges if scheda-opportunita has TED-ANAC cross-section |

**Deterministic** dimensions (D2, D4) are computed by `eval_runner.py` rule-based checks.
**Judge** dimensions (D1, D3, D5, D6, D7) are scored by Claude Haiku via Batch API using `judge_prompt_v1.md`.

## Templates

| ID | Template | Skill | Description |
|----|----------|-------|-------------|
| 3.1 | pin-radar | `/pin-radar` | Find active TED Prior Information Notices for Italy |
| 3.2 | consultazioni-radar | `/consultazioni-radar` | Monitor Consip consultations and bandi |
| 3.3 | scheda-opportunita | `/scheda-opportunita` | Detailed briefing on a specific opportunity (TED+ANAC+PNRR) |

Each template has 2 test cases in `eval_dataset.json` (e.g. 3.1-001, 3.1-002).

## Ground truth labeller

`ground-truth/label_ted_pins.py` queries TED to find PINs published in a given window, then searches for follow-on Contract Notices (CN) or Contract Award Notices (CAN) from the same buyer and CPV within 30–180 days.

The output (6 JSON files) can be used to:
- Validate D2 recall against real TED publication numbers
- Measure PIN→gara conversion rates (future metric)
- Refresh test cases when they go stale

**Usage:**
```bash
python ground-truth/label_ted_pins.py --cpv 48 --limit 50 --output labels.json
```

See `REFRESH_PROCEDURE.md` for the full workflow.

## Archive

`archive/benchmark-2026-05-29.md` documents the old tier 1-5 benchmark system that used `run_benchmark.py` (now deleted). Kept for reference on what the plugin could do before narrowing to "segnale azionabile" focus.

## Notes

- **Skills emit markdown directly** (as of 2026-06-02). The old JSON+renderer architecture was removed.
- **Eval prompts must include `/skill-name` prefix** to invoke the skill. Plain-text prompts run as general assistant and ignore SKILL.md.
- **Judge scores require ANTHROPIC_API_KEY** for Batch API. Without it, only D2/D4 deterministic scores run.
- **Eval results are stale** from JSON era — must be re-run with markdown architecture to establish baseline.
