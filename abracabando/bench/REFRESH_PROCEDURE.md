# REFRESH_PROCEDURE.md — maintaining the eval harness

This is the operator runbook for keeping the `bench/` eval harness trustworthy.
Read it end-to-end before refreshing ground truth, re-recording fixtures, or
bumping a skill's output contract.

The harness has **three tiers**. They are deliberately separated so the PR gate
stays fast, deterministic and offline while live-data drift is checked on a
schedule:

| Tier | Trigger | MCP source | API key | What it proves |
|------|---------|------------|---------|----------------|
| static | every PR | none | no | structure, schema, linters, replay unit tests |
| frozen | secret-gated / manual | `bench/config/mcp_replay.json` (recorded fixtures) | yes | the skills still emit a correct contract against frozen data |
| live | monthly cron + manual | `bench/config/mcp_live.json` (real `industrial-mcp`) | yes | upstream data + MCP server have not drifted |

The golden frozen records are the **independent oracle**. Both the skill answer
and the MCP output are checked against the golden, never against each other.

---

## 0. Quick map of the moving parts

- `bench/cases/eval_dataset.json` — the 21 cases (7 skills × {happy-path,
  missing-data, edge}). Each case carries `skill`, `template`, `tier`,
  `ground_truth_records`, `frozen_date`, `ttl_days`, `judge_prompt_version`.
- `bench/cases/eval_dataset_schema.json` — the schema the dataset validates against.
- `bench/cases/<case_id>/` — `golden.json` (hand-verified oracle) + `PROVENANCE.md`,
  captured independently of the MCP server. This is the oracle.
- `bench/scripts/capture_golden.py` — fetches the raw upstream responses.
- `bench/scripts/generate_ground_truth.py` — derives `ground_truth_records`
  from the committed golden (NOT from the MCP server).
- `bench/fixtures/<case_id>/` — recorded MCP call/response sequences for the frozen tier.
- `bench/mcp_replay.py` — the stdio record/replay server.
- `bench/eval_runner.py` — runs cases; `--frozen` (default) / `--live`.
- `bench/eval_report.py` — scoring report; `--gate` for the deterministic merge gate.
- `bench/cases/baseline.json` — the blessed deterministic baseline the gate compares against.

---

## 1. When to refresh

A case is **stale** when `today - frozen_date > ttl_days`. Check with:

```bash
python3 bench/eval_runner.py --check-staleness
```

Refresh stale cases before trusting a frozen-tier run. `ttl_days` is per-case
(shorter for fast-moving sources like Consip, longer for monthly ANAC snapshots).

## 2. Refresh the independent golden (the oracle)

For each stale case, re-capture the **raw upstream** API response — directly from
TED / ANAC / PNRR HTTP JSON, deliberately bypassing the MCP server so MCP
transform bugs cannot hide in the oracle:

```bash
python3 bench/scripts/capture_golden.py --case <case_id>
```

This writes `bench/cases/<case_id>/` plus a `PROVENANCE.md` row
recording the source URL and capture date.

**Hand-verification (mandatory, once per capture).** A human must open the
captured JSON and confirm the records are actually correct — that the PIN /
CIG / CUP exists, the status is what we claim, and the figures match the live
portal. The golden is only an oracle once a person has signed off on it. Record
who verified and when in `PROVENANCE.md`. Re-verify whenever upstream data ages
past its `ttl_days`.

## 3. Regenerate ground truth from the golden

```bash
python3 bench/scripts/generate_ground_truth.py --case <case_id>
```

`generate_ground_truth` derives `ground_truth_records` from the committed golden.
A genuinely empty golden yields `{"ground_truth_records": [], "empty_reason": ...}`
— that is the correct, expected shape for a missing-data case, not a failure.
Copy the result into the case in `bench/cases/eval_dataset.json` and bump its
`frozen_date` and `snapshot_date`.

## 4. Re-record the frozen fixtures

Fixtures are recorded against the **live** MCP, gated by the non-empty preflight
so an empty MCP payload is recorded as an explicit empty fixture (with
provenance), never skipped silently:

```bash
python3 bench/mcp_replay.py --record --case <case_id>   # proxies real industrial-mcp
```

This captures the full ordered tool-call sequence, including the pro→free
fallback and any `ted_pin_italy` retries. `ted_pin_italy` file-path responses
are captured by storing the referenced file content and reconstituting it on
replay. Commit the regenerated `bench/fixtures/<case_id>/`.

## 5. The frozen-vs-live refresh loop

The normal **iteration** loop when tuning a skill:

1. Edit `skills/<name>/SKILL.md`.
2. `python3 bench/eval_runner.py --frozen` — runs offline against recorded fixtures.
3. `python3 bench/eval_report.py` — read the per-dimension table (D1–D7).
4. Iterate on the skill until the deterministic dims (D2/D4 + output rules) pass
   and the judge dims (D1/D3/D5/D6/D7) look right.
5. When happy, bless the baseline: `python3 bench/eval_report.py --baseline`.

Only after the frozen loop is green do you run the **live** tier to confirm the
fixtures still match upstream:

```bash
python3 bench/eval_runner.py --live
```

A live run that reports `mcp_layer_empty` or `mcp_layer_wrong` is **not** a skill
bug — see §6.

## 6. Layer attribution — where a failure actually lives

`bench/mcp_preflight.py::attribute_layer` classifies every case against the golden:

- `skill_ok_no_data` — MCP and golden agree there are no records and the skill
  correctly emitted `## Dati non disponibili`. **This is a pass.**
- `mcp_layer_empty` — golden has records but the MCP returned nothing.
- `mcp_layer_wrong` — the MCP records diverge from the golden.
- `skill_layer_bug` — MCP matches the golden but the skill output dropped/garbled records.
- `stale_ground_truth` — the golden itself no longer matches reality (re-capture, §2).

**MCP-layer data defects (`mcp_layer_empty` / `mcp_layer_wrong`) are fixed in the
sibling `../industrial-data-mcp` repo, never by patching the fixtures or the
golden to match buggy MCP output.** Patching the oracle to agree with a broken
server defeats the entire point of an independent golden. Open the fix against
`../industrial-data-mcp`, re-record the fixture (§4), and re-run.

## 7. Evolving a skill schema

When a skill's output contract changes (new required section, renamed field,
new audit-trail key):

1. Bump `schema_version` in `eval_dataset.json` (and the schema file's `$id` if
   the case shape changed). Use semver: patch for additive, minor/major for
   breaking case-shape changes.
2. Update `bench/output_rules.py` — it is the single source of truth for the
   output contract, shared by pytest and `eval_runner.py`.
3. If the judge rubric changes, bump `judge_prompt_version` in both
   `eval_dataset.json` and the `## Version` token of `bench/judge_prompt_v1.md`
   (they must stay equal — a unit test enforces it).
4. Re-record fixtures (§4) so the recorded answers reflect the new contract.
5. Re-bless the baseline (`eval_report.py --baseline`).

## 8. Headless invocation fallback

The eval shells `claude -p "/<skill> ..."`. On the verified toolchain
(claude 2.1.161) `/skill-name` loads `SKILL.md` in headless mode. If a future
claude version does NOT load skills from `-p` (the smoke test
`bench/tests/test_headless_smoke.py` will fail), switch `run_case` to the documented
fallback:

```bash
claude -p "<prompt without slash>" --append-system-prompt-file skills/<name>/SKILL.md ...
```

This injects the skill body directly as a system prompt, independent of
interactive skill loading.

## Templates and skills index

| template | skill | scenarios |
|----------|-------|-----------|
| 3.1 | pin-radar | happy-path, missing-data, edge |
| 3.2 | consultazioni-radar | happy-path, missing-data, edge |
| 3.3 | scheda-opportunita | happy-path, missing-data, edge |
| 3.4 | digest-pregara | happy-path, missing-data, edge |
| 3.5 | profilo-sa | happy-path, missing-data, edge |
| 3.6 | reconciliation-pnrr | happy-path, missing-data, edge |
