# Changelog

---

## [Unreleased]

### Fixed

- **`openpnrr_get` parameter name in skills** (`skills/reconciliation-pnrr/SKILL.md`, `skills/scheda-opportunita/SKILL.md`): both skills were calling `openpnrr_get(endpoint="progetti", id="<cup>")` but the MCP tool parameter is named `item_id`, not `id`. Calls with the wrong name cause a FastMCP validation error at runtime. Fixed to `item_id="<cup>"`.

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
