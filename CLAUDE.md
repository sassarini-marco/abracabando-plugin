# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Claude Code plugin giving natural-language access to the Italian public-spending ecosystem (ANAC contracts, TED EU tenders, OpenCoesione, OpenPNRR, regional planning). The repo root is the marketplace (`.claude-plugin/marketplace.json`); the actual plugin lives in `abracabando/` (`.claude-plugin/plugin.json`, `skills/`, `.mcp.json`). The `industrial-mcp` server is a separate repo, installed via `uv tool install` and exposed on PATH — it is NOT in this repo.

## Skill output rules (critical — skills must not violate these)

These are enforced by `skills/shared/regole-comuni.md` and checked by the eval harness. When editing or adding a skill:

- **Output is always Italian markdown.** Never English; never JSON in the final user-facing result (JSON is internal-processing only).
- **No fabricated data.** Never invent importi, scadenze, names, or CIG/CUP. If data is missing, emit an explicit `## Dati non disponibili` section.
- **Full provenance.** Every figure carries `(fonte: <URL>) — Dati letti il <date>`. The output opens with `Dati letti il YYYY-MM-DD` (a brief conversational lead-in is tolerated — headless models prepend one and no prompt fully suppresses it; the linter allows `Dati letti il` within the first few lines), and the last block is a `## Audit trail` listing tool calls + timestamps.
- **Confidence is qualitative**, exactly three levels: "Alta confidenza" / "Media confidenza" / "Bassa confidenza" — never percentages.
- **Never expose tool names** (e.g. `mcp__industrial-mcp-free__...`) to the user.
- Skills call `industrial-mcp-pro` first, falling back to `industrial-mcp-free`. The pro server is a placeholder and shows as disconnected until the hosted service exists.

## Commands

```bash
python3 -m pytest abracabando/tests abracabando/bench/tests -q -m "not live"  # unit tests (offline, fast)
claude plugin validate ./abracabando                                            # validate plugin manifest
python abracabando/bench/eval_runner.py --check-staleness                      # check if eval ground-truth is stale
ANTHROPIC_API_KEY=<key> python abracabando/bench/eval_runner.py                # full eval (slow, uses Haiku Batch judge)
python abracabando/bench/eval_report.py                                        # report from latest bench/eval_results/
```

Run `pytest abracabando/tests abracabando/bench/tests -q -m "not live"` after changes. The `bench/` eval harness is slow and API-key-gated — only run it when explicitly asked.

## Layout

```
/                              ← repo root = marketplace
├── .claude-plugin/
│   └── marketplace.json       ← marketplace catalog (points to ./abracabando)
├── README.md                  ← marketplace README (install instructions)
├── LICENSE
└── abracabando/               ← plugin root
    ├── .claude-plugin/
    │   └── plugin.json        ← plugin manifest
    ├── plugin.json            ← root-level manifest (validated by test suite)
    ├── .mcp.json              ← MCP server declarations
    ├── skills/<name>/SKILL.md ← 7 skill protocols; skills/shared/ holds common rules
    ├── bench/                 ← eval harness (21 cases, 7 dimensions D1–D7; see bench/README.md)
    └── tests/                 ← unit tests (manifests, skill structure, dataset schema)
```

## Gotchas

- **Skills emit markdown directly** (the old JSON+renderer architecture was removed). Plain-text prompts ignore SKILL.md — a skill only runs when invoked as `/skill-name`.
- **First MCP query downloads ~280 MB** of bulk data into `$INDUSTRIAL_MCP_CACHE_DIR` (default `~/.cache/industrial-mcp`). ANAC data is a monthly snapshot, not a full multi-year archive.
- **TED fallback:** `ted_pin_italy` may return a file path instead of JSON for large result sets — skills parse it with Bash+jq.

## Repo etiquette

Work on `feature/*` branches and open a PR to `main`; don't commit directly to `main`.