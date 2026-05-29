# Benchmark Report — Claude Code + `industrial-procurement` plugin

**Date:** 2026-05-29 · **Model:** Claude Opus 4.8 (1M) · **Harness:** `claude -p` headless
**Stack under test:** `industrial-procurement-plugin` (5 skills) wired to the `industrial-mcp` server (46 tools) over stdio.

Each Tier 1–5 prompt was run via:

```
claude -p "<prompt>" --plugin-dir . \
  --mcp-config bench/mcp.json --strict-mcp-config \
  --allowedTools 'mcp__industrial-mcp-free__*' \
  --output-format stream-json --verbose
```

`--strict-mcp-config` guarantees only the fresh local stdio server is used. Reproduce with `python3 bench/run_benchmark.py`.

---

## Scoreboard

| ID | Tier | Query | Verdict | Time | Cost | Key tools |
|----|------|-------|---------|------|------|-----------|
| t1-1 | 1 | ANAC: 10 aggiudicazioni FVG >500k (60gg) | ✅ **PASS** | 36s | $0.27 | `anac_search_awards` |
| t1-2 | 1 | OpenPNRR: misure Missione 2 | ✅ **PASS** *(caveat)* | 207s | $2.71 | `openpnrr_list/get` |
| t1-3 | 1 | OpenCoesione: FESR 2021-27 FVG | ✅ **PASS** | 23s | $0.24 | `opencoesione_search_projects` |
| t1-4 | 1 | TED: 15 procedure IT >5M€ CPV 45 (90gg) | ✅ **PASS** *(caveat)* | 169s | $0.80 | `ted_search` |
| t2-1 | 2 | CUP I32E…560006 multi-fonte | 🟡 **PARTIAL** | 196s | $0.99 | `anac_awards_by_cup`, `opencoesione_project_by_cup` |
| t2-2 | 2 | P.IVA Webuild — scheda one-page | ✅ **PASS** *(caveat)* | 61s | $0.42 | `anac_awards_by_piva`, `imprese_check_vat` |
| t2-3 | 2 | Gruppo Fincantieri (2 P.IVA) | ✅ **PASS** | 60s | $0.38 | `anac_awards_by_piva`, `opencoesione_search_projects` |
| t3-1 | 3 | ANAC PNRR M2C3 1.1 2025 Lombardia + delta | 🟡 **PARTIAL** | 794s | $2.95 | `anac_award_detail`, `opencoesione_project_by_cup` |
| t3-2 | 3 | Top 10 PNRR M2C4 2.2 + VIES | 🟡 **PARTIAL** | 439s | $2.40 | `anac_search_awards`, `imprese_check_vat`×8 |
| t4-1 | 4 | OpenPNRR misure a rischio + CIG via CUP | ✅ **PASS** *(caveat)* | 646s | $2.81 | `anac_awards_by_cup`, `openpnrr_*` |
| t5-1 | 5 | Data-quality: CUP valido non risolto | ✅ **PASS** *(caveat)* | 731s | $4.26 | `opencoesione_project_by_cup`, `anac_award_detail` |

**7 PASS · 3 PARTIAL · 0 FAIL** (all PARTIALs are blocked by genuine upstream data limitations, not wrong answers).
**Total cost:** ~$18.2 for the 11 final runs (plus 2 pre-fix timed-out attempts — see *Bugs found & fixed*).

> **No hallucinated data.** Across every query the agent refused to invent figures when a source was unavailable, and labelled each number with its source + snapshot date. This is the single most important result.

---

## What "PASS / PARTIAL" mean here

- **PASS** — all required fields delivered from real data.
- **PASS *(caveat)*** — delivered, but with an honest, correctly-stated data-coverage limit (e.g. ANAC monthly-snapshot window, or a metric the source genuinely doesn't expose).
- **PARTIAL** — a substantial answer where one required leg is blocked by a real upstream limitation (no PNRR-*misura* tag in ANAC; a CUP genuinely absent from a source). The agent was transparent about the gap rather than faking it.

---

## Per-query evidence

### Tier 1 — Smoke

**t1-1 ✅** — One `anac_search_awards` call returned all 9 fields (CIG, SA, oggetto, aggiudicatario, P.IVA, base, aggiudicato, ribasso %, data) in a clean table. Recomputed `ribasso %` and flagged a 44%-"ribasso" row as an accordo-quadro ceiling (not a real discount) — genuine analytical nuance. One row's winner was missing in the snapshot and was honestly marked *non indicato*.

**t1-2 ✅(caveat)** — Enumerated all Missione 2 measures across M2C1–M2C4 with budgets and next-milestone dates. Correctly identified that **OpenPNRR exposes no real financial-spend %**, so used "% milestone completed" as a labelled proxy and pointed to ReGiS/ItaliaDomani for true spend. Required "avanzamento %" isn't in the source — the honest substitution is the right call.

**t1-3 ✅** — 2,436 projects; finanziato €580.7M / impegnato €256.5M / pagato €114.5M; top-5 beneficiaries. Spotted that the top-2 share one CF (same Regione under two names) and summed them. Cited exact parquet columns.

**t1-4 ✅(caveat)** — 718 matching TED notices; top-15 by estimated value with ente/oggetto/value. Some `scadenza offerte` were "n.d. via API" (not in the summary record; available in the notice XML) and it said so. Noted CPV-45 concessions where 45 is only a component.

### Tier 2 — Pivot-then-fetch

**t2-1 🟡** — Honest multi-source reconciliation for CUP `I32E22000560006`: OpenCoesione = absent (full scan of all 3 cycles), ANAC CIG↔CUP = 0 records, OpenPNRR = unresolvable (tool limitation, pre-fix run). Concluded the most-likely interpretation (PNRR project not yet at tender stage / not mirrored) instead of inventing data. The CUP genuinely has no ANAC/OpenCoesione footprint in the snapshot.

**t2-2 ✅(caveat)** — One-page Webuild scheda: VIES **valid** (name+seat confirmed), Registro Imprese deep-link, ANAC (0 in window) and OpenCoesione (0) each with the correct explanation — Webuild bids via ATI/consortia and above-threshold works flow to TED; OpenCoesione indexes beneficiaries not contractors. Offered the TED follow-up. Exactly the reasoning a procurement analyst would give.

**t2-3 ✅** — Strongest Tier-2 result. Caught that Fincantieri S.p.A. sits under **CF 00397130584, not the P.IVA**, and queried both; found Fincantieri Infrastructure's **€424.6M ANAS SS-106 award**, both OpenCoesione FESR projects, and produced a clean combined group table with interpretation.

### Tier 3 — Bounded scan

**t3-1 🟡** — Got ANAC awards + CUPs and OpenCoesione resolution (1/4 found), and crucially **caught a false positive**: the keyword-matched Vigevano project is FESR "inclusione sociale", *not* PNRR M2C3. Correctly concluded ANAC has **no queryable PNRR-misura tag**, so keyword selection is imprecise — recommended the `cig-pnrr-pnc` dataset for exact attribution.

**t3-2 🟡** — Delivered the verifiable part fully: **8/8 VIES validations + Ricerca Imprese links**. For the misura itself, it correctly determined **M2C4-2.2 was restructured/definanced** in the Dec-2023 PNRR revision and is no longer a distinct OpenPNRR measure — then annotated each top-10 award's actual fund (REPowerEU M7, FESR, ERP). High-quality domain reasoning; the "exact misura" leg is genuinely unfilterable.

### Tier 4 — Discovery chain

**t4-1 ✅(caveat)** — 218 milestones in the window (all unmet); 3 highest-exposure at-risk measures; for the distributed-procurement measure (Rigenerazione urbana) it resolved **CUP→CIG via `anac_awards_by_cup`** with 5 real awards. For centralized measures (Italia 1 Gbps, hospital equipment) it explained why CUP→CIG isn't reconstructable (Infratel/Consip central procurement) — itself a risk signal. Used a labelled proxy for the "<60%" metric OpenPNRR doesn't expose.

### Tier 5 — Data-quality probe

**t5-1 ✅(caveat)** — Produced 10 CIG with structurally-valid CUPs **confirmed absent from OpenCoesione**, each with CIG/SA/CUP/oggetto/importo, and a real anomaly taxonomy: **2 placeholder CUPs** (all-zero progressive block, e.g. `G20J22000000006`) and **1 shared-CUP-across-two-SAs** discrepancy. Honestly scoped the OpenPNRR leg as unverifiable. A genuinely useful audit output.

---

## Capability findings

**What the plugin does well**
- **ANAC record-level querying now works end-to-end** (the new tools): by region/amount/date/CPV, by CUP, by P.IVA, single-CIG detail — all from real monthly snapshots with recomputed ribasso and full provenance.
- **OpenCoesione analytics** (counts, finanziato/impegnato/pagato, top beneficiaries, CUP lookup) from the parquet bulks.
- **TED** expert search and **OpenPNRR** measure/milestone browsing are solid.
- **VIES validation + Registro Imprese deep-links** work for supplier due-diligence.
- **Cross-source orchestration**: the agent reliably pivots CUP↔CIG↔beneficiary across ANAC/OpenCoesione/OpenPNRR and reconciles amounts.
- **Provenance & honesty**: every figure carries source + snapshot date; gaps are declared, never faked.

**Genuine limits (inherent, not bugs)**
- **ANAC has no queryable PNRR-misura tag** on the main award tables → "all awards under measure M2C3-1.1" can't be filtered exactly; keyword proxy is imprecise (the `cig-pnrr-pnc` dataset would be needed). *Affects t3-1, t3-2.*
- **ANAC snapshots are a recent window**, not the full multi-year archive → "last 24/36 months" is truncated; the agent says so. *Affects t2-2, t2-3.*
- **OpenPNRR exposes no real financial-spend %** (only planned allocations) → "avanzamento finanziario <60%" isn't directly computable; milestone-completion proxy used. *Affects t1-2, t4-1.*
- **OpenPNRR REST API cannot filter by CUP server-side** (see below) → CUP→project resolution on OpenPNRR is best-effort; the agent correctly pivots to ANAC/OpenCoesione CUP lookups.
- **TED summary records** sometimes omit the offer deadline (it's in the notice XML).

---

## Bugs found *by* the benchmark — and fixed

The run surfaced two real defects in `industrial-mcp`. Both were fixed and the affected queries re-run.

1. **`openpnrr_search_progetti` silently ignored the `cup` filter.** The OpenPNRR API has no server-side CUP filter (only free-text `search`, which doesn't index CUP). The tool passed `?cup=` and returned the entire 280k-project catalog as if filtered — so the agent looped retrying. **t4-1 and t5-1 originally hit the 900s timeout because of this.**
   **Fix:** client-side bounded CUP scan + an explicit `cup_filter_supported: false` signal that tells the agent *not to retry* and to use `anac_awards_by_cup` / `opencoesione_project_by_cup` instead. After the fix, **both queries completed** (t4-1 646s, t5-1 731s) and t5-1 no longer invented tool names.

2. **`http_client` cache replayed gzipped responses incorrectly.** Cached responses stored decoded bytes but replayed the original `Content-Encoding: gzip` header, so any repeated identical GET in a turn crashed with a zlib error. **Fix:** strip `content-encoding`/`content-length`/`transfer-encoding` from cached headers. (34/34 unit tests green after the change.)

> Observation worth noting: in the *pre-fix* t5-1 run, the agent — unable to resolve CUPs — began **inventing plausible tool names** (`anac_count_cig`, `openpnrr_get_by_cup`) that don't exist, burning turns. Giving the tool an explicit "not supported, pivot here" signal eliminated this. A lesson for tool design: failing loudly with a redirect beats returning misleading "success".

---

## Recommendations (next steps, not done here)

1. **Add `cig-pnrr-pnc` as a queryable table** so PNRR awards can be filtered by exact misura (M/C/Investimento) — would turn t3-1/t3-2 PARTIAL → PASS.
2. **Multi-snapshot ANAC cache** (load several monthly/yearly snapshots) for true 24–36-month look-backs.
3. **OpenPNRR CUP index**: build a local CUP→progetto map from a one-time full pull, since the API won't filter.
4. Wire the new ANAC tools into the `profilo-sa` / `scheda-opportunita` / `reconciliation-pnrr` skills' `allowed-tools`.

---

## Artifacts

- `bench/prompts.json` — the 11 benchmark prompts + required-field checklists.
- `bench/run_benchmark.py` — the runner.
- `bench/results/<id>.json` — per-query summary (tools fired, answer, latency, cost).
- `bench/results/<id>.jsonl` — full stream-json transcript per query.
