# bench/ — Evaluation Infrastructure

This directory contains the evaluation harness for measuring skill quality across 7 dimensions (relevance, recall, signal quality, freshness, traceability, language, synthesis).

## Directory structure

```
bench/
├── README.md                    # This file
├── REFRESH_PROCEDURE.md         # Operator runbook for refreshing dataset / fixtures
├── eval_runner.py               # Main harness: runs cases, computes D2/D4, submits judge batch
├── eval_report.py               # Generates summary table + regression gate from eval_results/
├── output_rules.py              # Deterministic output-contract linter (shared by tests + runner)
├── mcp_preflight.py             # Layer attribution: skill_ok / mcp_layer_* / needs_rerun
├── mcp_probe.py                 # Layer 0: live MCP tool smoke / full probes
├── mcp_replay.py                # MCP stdio record/replay server for frozen tier
├── tool_contracts.py            # Declarative MCP tool contract table (smoke + full tiers)
├── judge_prompt_v1.md           # System prompt for Haiku judge (D1/D3/D5/D6/D7)
├── cases/                       # One entry per test case
│   ├── eval_dataset.json        # 21 test cases (7 skills × 3 scenarios each)
│   ├── eval_dataset_schema.json # JSON Schema for eval_dataset.json
│   ├── baseline.json            # Blessed deterministic scores (regression gate baseline)
│   └── <case-id>/               # e.g. 3.1-001/
│       ├── golden.json          # Independent frozen oracle (hand-verified upstream data)
│       └── PROVENANCE.md        # Capture date, source URL, hand-verification checklist
├── fixtures/                    # Frozen MCP replay fixtures (committed; deterministic gate)
│   ├── tools_list.json          # Shared tool schemas for all replay runs
│   └── <case-id>/               # calls.json + tools_list.json per case
├── config/                      # MCP server configuration
│   ├── mcp_live.json            # Live tier: real industrial-mcp server
│   └── mcp_replay.json          # Frozen tier: replay server (bench/mcp_replay.py)
├── scripts/                     # Operator scripts (not run by CI)
│   ├── capture_golden.py        # Fetch raw upstream API responses for the oracle
│   └── generate_ground_truth.py # Derive ground_truth_records from the golden
├── tests/                       # Pytest suite
│   ├── test_eval_runner.py      # Unit tests for D2/D4 scoring + deterministic flow
│   ├── test_eval_report.py      # Regression gate logic
│   ├── test_output_rules.py     # Linter rule unit tests
│   ├── test_mcp_preflight.py    # Layer attribution unit tests
│   ├── test_mcp_replay.py       # Replay fixture roundtrip tests
│   ├── test_generate_ground_truth.py  # Proves oracle derivation never calls industrial_mcp
│   ├── test_tool_contracts.py   # Layer 0 live smoke tests (tagged @live, skipped in CI)
│   ├── test_headless_smoke.py   # Headless claude invocation smoke test (secret-gated)
│   └── test_ci_workflows.py     # CI workflow YAML content assertions
└── eval_results/                # Latest scores for all cases (gitignored, transient)
```

## Quick start

### Run the eval

```bash
# Check for stale cases first
python3 bench/eval_runner.py --check-staleness

# Run all cases — frozen tier (deterministic, no API key)
python3 bench/eval_runner.py

# Run one template
python bench/eval_runner.py --template 3.1

# Live tier (real MCP + judge, needs ANTHROPIC_API_KEY)
ANTHROPIC_API_KEY=<key> python bench/eval_runner.py --live
```

### Generate report

```bash
python bench/eval_report.py
python bench/eval_report.py --gate --baseline-path bench/cases/baseline.json
```

### Run unit tests

```bash
pytest abracabando/bench/tests -q -m "not live"  # offline (fast)
pytest abracabando/bench/tests -q                # includes live Layer 0 smoke
```

## Eval tiers

| Tier | Trigger | MCP source | API key | What it proves |
|------|---------|------------|---------|----------------|
| static | every PR | none | no | structure, schema, linters, replay unit tests |
| frozen | secret-gated / manual | `bench/config/mcp_replay.json` (fixtures) | yes | skills emit correct contract against frozen data |
| live | monthly cron + manual | `bench/config/mcp_live.json` (real MCP) | yes | upstream data + MCP server have not drifted |

## Eval dimensions

| Dim | Name | Type | How scored |
|-----|------|------|------------|
| D1 | Relevance | Judge | Haiku judges if response answers the user's question |
| D2 | Recall | Deterministic | fraction of expected IDs found in the answer |
| D3 | Signal quality | Judge | Haiku judges if confidence is qualitative (Alta/Media/Bassa) |
| D4 | Freshness | Deterministic | `Dati letti il` date within 35 days of today |
| D5 | Traceability | Judge | Haiku judges if every figure has a `fonte:` URL |
| D6 | Language | Judge | Haiku judges if output is in Italian |
| D7 | Multi-source synthesis | Judge | Haiku judges TED-ANAC cross-section in scheda-opportunita |

**Deterministic** dimensions (D2, D4) never need an API key.
**Judge** dimensions (D1, D3, D5, D6, D7) are scored via Claude Haiku Batch API.

## Layer attribution

Each scored case gets a `layer` label that routes failures to the right repo:

| Layer | Meaning |
|-------|---------|
| `skill_ok` | MCP data present and skill surfaced it correctly |
| `skill_ok_no_data` | Genuinely no data; skill said so explicitly |
| `mcp_layer_empty` | MCP returned nothing despite oracle expecting data |
| `mcp_layer_partial` | MCP returned some but not all golden records |
| `mcp_layer_wrong` | Cross-tool consistency check flagged divergence |
| `skill_layer_bug` | MCP data was present but skill dropped or fabricated it |
| `stale_ground_truth` | Oracle says empty but MCP found data — oracle needs refresh |
| `needs_rerun` | Infrastructure noise (cold start, file-path deferral) |

## Templates

| ID | Skill | Description |
|----|-------|-------------|
| 3.1 | `pin-radar` | Find active TED Prior Information Notices for Italy |
| 3.2 | `consultazioni-radar` | Monitor Consip consultations and bandi |
| 3.3 | `scheda-opportunita` | Detailed briefing on a specific opportunity (TED+ANAC+PNRR) |
| 3.4 | `digest-pregara` | Pre-tender digest for a specific opportunity |
| 3.5 | `profilo-sa` | Spending profile for a contracting authority |
| 3.6 | `reconciliation-pnrr` | PNRR fund reconciliation for a project |
| 3.7 | `analisi-disciplinare` | Disciplinary document analysis |

Each template has 3 scenarios: `happy-path`, `missing-data`, `edge`.

## Refreshing the oracle

See `REFRESH_PROCEDURE.md` for the full runbook. Quick version:

```bash
# Capture fresh upstream data for a case
python bench/scripts/capture_golden.py --case 3.1-001

# Verify + fill bench/cases/3.1-001/golden.json by hand
# Then regenerate ground truth
python bench/scripts/generate_ground_truth.py --case 3.1-001
```
