# Changelog

---

## [0.3.0] — 2026-06-12

### Fixed

- **Skills now auto-invoke correctly**: removed `disable-model-invocation: true` from
  all 8 skill frontmatter blocks. This flag was preventing Claude from auto-invoking
  skills when user requests matched the trigger patterns in the `description` field.
  Previously, Claude bypassed the skill wrapper and called MCP tools directly, losing
  the Italian markdown output, provenance rules, confidence scoring, and audit trail
  format. Skills now trigger automatically on natural-language requests (e.g.,
  "quale gara fa per la mia azienda" → `/trova-bando-compatibile`).

---

## [0.2.2] — 2026-06-12

### Added

- **Automated plugin packaging via GitHub Actions** (`.github/workflows/release.yml`):
  triggers on git tag push (`v*`), builds the plugin zip from `abracabando/` directory
  (excluding tests and bench), and creates a GitHub release with the zip attached as
  a downloadable asset. Version is extracted from git tag.

- **Local build script** (`scripts/build-plugin.sh`): builds the plugin package
  locally, extracting version from `.claude-plugin/plugin.json`. Validates the
  package structure before zipping.

- **Platform badges**: added Claude Desktop and Claude Cowork badges to marketplace
  README.

---

## [0.2.0] — 2026-06-12

### Added

- **New skill `trova-bando-compatibile`** (`skills/trova-bando-compatibile/`):
  given a company/factory profile (CPV or ATECO sector, region, contract size
  range, certifications), finds open compatible public tenders and ranks them by
  compatibility. Each bando is scored across four dimensions — CPV match,
  geography, contract size, and eligibility — using Alta/Media/Bassa labels;
  the overall score is the modal value with explicit named warnings for any Bassa
  dimension. ATECO codes are mapped to CPV by model inference (labelled Media
  confidenza in the audit trail). PNRR sources are excluded (programme closing).
  Includes `references/output-format.md`, `references/nuts-mapping.md` symlink,
  and `examples/example-output.md`.

- **Eval harness extended for `trova-bando-compatibile`** (`bench/`): template
  `3.8` and skill slug added to `eval_dataset_schema.json` enums,
  `TEMPLATE_TO_SKILL` dict and `--template` argparse choices in `eval_runner.py`,
  and D7 `-1` (not-applicable) list in `judge_prompt_v1.md`. Three frozen eval
  cases added (`3.8-001` happy-path, `3.8-002` missing-data, `3.8-003` edge /
  ATECO-only). `SKILL_TO_PREFIX` in `tests/test_eval_dataset.py` and a new
  `test_trova_bando_compatibile_structure()` function in
  `tests/test_skill_structure.py` updated accordingly.

### Fixed

- **CONSIP silent failure now surfaced to the user** (`skills/shared/regole-comuni.md`,
  `skills/consultazioni-radar/SKILL.md`): the MCP `consip_*` tools previously
  returned an empty list whether the Consip website failed structurally or simply
  had no matching records. Skills now check the new `status` field returned by the
  MCP and emit `## Avviso: dati Consip non disponibili` (with a direct link to
  consip.it) when `status: "layout_unrecognized"` — distinct from a legitimate
  zero-result response which produces no avviso.

- **`test_mcp_json_has_both_servers` wrong type assertion** (`tests/test_manifests.py`):
  the test expected `"type": "streamable-http"` but `.mcp.json` correctly uses
  `"type": "http"` (the current Claude Code MCP transport identifier). Updated
  the assertion to match.

### Changed

- **Free-tier limit message enriched** (`skills/shared/regole-comuni.md`,
  `skills/shared/strategia-strumenti.md`): the `## Limite piano free` section
  template now instructs the skill to list which sources were not yet queried
  ("Sezioni incomplete") and which are already compiled ("Cosa è già disponibile"),
  giving the user actionable context for the next session. Added a note that the
  `LIMITE_PIANO_FREE:` sentinel may arrive as `isError: true` — the prefix in the
  content is the determinant, not the error flag.

- **Open-bando default documented per skill** (`skills/consultazioni-radar/SKILL.md`,
  `skills/scheda-opportunita/SKILL.md`, `skills/digest-pregara/SKILL.md`,
  `skills/pin-radar/SKILL.md`): discovery skills now explicitly default to open
  opportunities only (`ted_search` scope is already `ACTIVE` at the MCP layer;
  `consip_search_bandi` now passes `stage="bando"` server-side to filter open
  bandi only). Each skill adds `ambito_temporale: "solo_aperti"` to its audit
  trail and a disclosure line to the output. Historical/closed data is available
  on explicit user request. Changed per-skill, not in the shared file, to avoid
  corrupting skills that legitimately need historical ANAC award data
  (`scheda-opportunita`, `profilo-sa`). ANAC awards are clarified as historical
  by definition and not presented as open bandi.

- **PNRR deprioritised in `digest-pregara`** (`skills/digest-pregara/SKILL.md`):
  the PNRR milestone step changed from **SEMPRE** to **FACOLTATIVO**. The PNRR
  programme is closing (main deadlines 2026); its look-ahead value is now
  secondary to regional programming and TED PIN. The skill interrogates PNRR only
  when budget allows after the primary sources, or when the user explicitly mentions
  PNRR/Next Generation EU/missions M1–M6. Omissions are noted in `## Metodologia`
  rather than flagged as `## Dati non disponibili`. `scheda-opportunita` adds a
  note that PNRR absence does not block or reduce output quality.

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
