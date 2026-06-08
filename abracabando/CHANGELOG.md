# Changelog

---

## [Unreleased]

### Changed

- **`bench/` filesystem restructure** — directories reorganised for open-repo clarity:
  - `dataset/` + `ground-truth/golden/` + `baseline.json` merged into `cases/` (dataset, schema, baseline, and per-case oracle in one place)
  - `ground-truth/capture_golden.py` + `generate_ground_truth.py` promoted to `scripts/`
  - `mcp.json` → `config/mcp_live.json`; `mcp_replay.json` → `config/mcp_replay.json`
  - All `test_*.py` consolidated under `tests/`
  - All path constants in `eval_runner.py`, `eval_report.py`, `mcp_probe.py`, `mcp_preflight.py`, and the moved scripts/tests updated accordingly
  - `bench/README.md` rewritten with full directory map, tier table, and layer attribution reference
  - `CLAUDE.md` test command updated to cover `bench/tests/` in addition to `abracabando/tests/`
  - Added `bench/probe_results/` to `.gitignore`

### Fixed

- **Broken OpenPNRR CUP lookup in two skills** (`reconciliation-pnrr`, `scheda-opportunita`):
  both skills called `openpnrr_get(endpoint="progetti", item_id="<cup>")` but
  `openpnrr_get` resolves resources by internal integer pk — passing a CUP always
  returns 404. Replaced with `openpnrr_search_progetti(cup="<cup>")`, the correct
  client-side CUP scanner (verified live: returns `cup_filter_supported` flag and
  up to 3000 projects scanned). Intermediate fix `id→item_id` was necessary but
  not sufficient; this replaces it entirely.

- **Wrong ANAC tool for CUP reconciliation** (`reconciliation-pnrr`): the skill
  used `anac_search_awards(query="<ente beneficiario>")` to find CIGs for a CUP —
  a lossy free-text match on entity name. Replaced with `anac_awards_by_cup(cup=)`
  which joins the ANAC `cup` table directly for an exact CUP→CIG resolution.
  `anac_awards_by_cup` added to `allowed-tools`; `anac_search_awards` removed from
  the CUP-resolution step. Verified live: 23 CIGs returned for CUP B56E23004900006.

- **OpenCoesione section in `scheda-opportunita` could not return project data**:
  the skill called `opencoesione_list_datasets()` and `opencoesione_describe_dataset()`
  which return catalog metadata only (dataset titles, URLs) — no importo, beneficiario,
  or stato. Replaced with `opencoesione_project_by_cup(cup=)` (primary) and
  `opencoesione_search_projects(cup=)` (fallback). Updated `allowed-tools` accordingly.
  Steps 3 and 4 now fire only when a `cup` is available, not on the vague
  "CPV/settore tipicamente PNRR" trigger.

### Changed

- **Shared cost model for ANAC and multi-page tools** (`skills/shared/regole-comuni.md`,
  `skills/shared/strategia-strumenti.md`): added explicit rules derived from
  adversarial code review of the MCP server:
  - ANAC table counts per tool: `anac_sa_history` = 2, `anac_search_awards`/`anac_awards_by_piva` = 3, `anac_award_detail`/`anac_awards_by_cup` = 4. Tables are shared — cold start paid once per conversation.
  - New rule: never invoke two ANAC tools in parallel (no download lock was in the server cache; lock added server-side in the same release but the skill rule remains for safety).
  - New rule: on ANAC timeout/error, emit `## Dati non disponibili` and do not retry.
  - `openpnrr_search_progetti(cup=...)` documented as up to 6 internal HTTP calls; do not retry if CUP not found.
  - `opencoesione_project_by_cup` documented as up to 3 parquet downloads on cold cache.
  - New medium-cost tier in the tool table between light and bulk.
  - `opencoesione_describe_dataset` corrected from bulk to light (catalog-only, no download).

- **`profilo-sa` error handling**: added note that both ANAC tools share tables
  (cold start paid once), and explicit guidance to stop and emit `## Dati non
  disponibili` on timeout rather than retrying.

---

## [0.1.0] — 2026-06-05
also 
### Nuova skill

**`/analisi-disciplinare`** — skill di punta del plugin.

Dato l'URL di un disciplinare o capitolato tecnico (PDF o HTML), la skill scarica il documento, legge il testo intero e produce una scheda strutturata con:
- tabella criteri di valutazione completa (offerta tecnica/economica + tutti i sub-criteri con verifica della somma)
- criterio di aggiudicazione (OEPV o minor prezzo) con formula economica se presente
- requisiti di partecipazione (fatturato, certificazioni, contratti analoghi, DURC, piattaforme)
- sezione `## Dati non disponibili` per PDF scansionati, testo troncato o CIG assente in ANAC
- audit trail fenced con passi eseguiti e timestamp

Testata su disciplinare AGCM reale (CIG B16EFD0453): 80/80 punti estratti, 7 sub-criteri verificati, confidenza Alta.

### Eval harness

- Aggiunto **template 3.7** al judge prompt con rubrica D7 anti-fabricazione: verifica che le tabelle punteggi siano ancorate al testo del documento e che documenti non leggibili non producano mai valori inventati.
- Aggiunti **4 casi eval** per `analisi-disciplinare`:
  - `3.7-001` (live): TED PIN 338240-2026 — correctly identified as pre-information notice, no scoring criteria expected
  - `3.7-002` (frozen): PDF scansionato — `## Dati non disponibili` senza punteggi inventati
  - `3.7-003` (frozen): documento 90 pagine troncato — criteri estratti da fixture
  - `3.7-004` (live, flagship): disciplinare AGCM reale — 80/80 punti, Confidenza Alta
- Aggiunta regola deterministica **`check_no_criteria_fabrication`** in `output_rules.py`: se il documento è dichiarato illeggibile in D-n-d, nessun valore numerico di punti può comparire nella sezione criteri.
- Aggiunto flag **`--case <id>`** a `eval_runner.py` per esecuzioni su singolo caso.
- Fix **`_load_tools_list`** in `mcp_replay.py`: merge tra tool condivisi e tool per-caso invece di ignorare il file per-caso. Sblocca il replay frozen per skill con tool MCP nuovi.
- `eval_dataset_schema.json` ed `eval_runner.py` estesi per template `3.7` e skill `analisi-disciplinare`.

### Esempi

- Tutti i `examples/sample_outputs/*.md` ora includono la query generante come `> **Query:** ...` in testa.
- `analisi-disciplinare.md` — output reale da run live su disciplinare AGCM (80/80 punti, sub-criteri verificati, formula economica, audit trail completo).
- `pin-radar.md` e `consultazioni-radar.md` — rigenerati da run live (erano placeholder).

### Test

31 test passano. Aggiornamenti principali:
- `test_eval_dataset.py`: 7 skill (era 6), template `3.7` nello schema
- `test_skill_structure.py`: prefisso query obbligatorio nei sample, pattern provenance rilassato per accettare sia `(fonte:` che `**Fonte:**`
