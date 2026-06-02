---
name: digest-pregara
description: Analizza il mercato di pre-gara per un settore CPV o una regione. Usa questa skill quando l'utente chiede di monitorare opportunità rilevate da programmazione regionale, TED PIN e PNRR, e vuole un digest in italiano con piena provenienza e livelli di confidenza.
argument-hint: "[CPV] [regione] [anno]"
disable-model-invocation: true
allowed-tools:
  - mcp__industrial-mcp-pro__programmazione_search_biennale
  - mcp__industrial-mcp-pro__ted_pin_italy
  - mcp__industrial-mcp-pro__openpnrr_list
  - mcp__industrial-mcp-pro__openpnrr_get
  - mcp__industrial-mcp-free__programmazione_search_biennale
  - mcp__industrial-mcp-free__ted_pin_italy
  - mcp__industrial-mcp-free__openpnrr_list
  - mcp__industrial-mcp-free__openpnrr_get
---

# Digest Pre-Gara

Usa questa skill solo per richieste su:
- analisi mercato di pre-gara per settore CPV o regione;
- opportunità rilevate da programmazione regionale, TED PIN e PNRR;
- digest con provenienza e livelli di confidenza.

## Obiettivo

Produrre un digest di mercato pre-gara in italiano formale che:
1. rilevi opportunità da programmazione regionale, TED PIN e PNRR;
2. le ordini per lead time crescente (opportunità più vicine prima);
3. assegni livelli di confidenza standardizzati (Alta / Media / Bassa);
4. fornisca fonte verificabile (URL) per ogni opportunità;
5. includa metodologia e audit trail.

## Regole essenziali

Vedi [../shared/regole-comuni.md](../shared/regole-comuni.md).

## Vocabolario di Confidenza

Usa **esattamente** queste tre espressioni — nessun numero percentuale:

- **Alta confidenza**: dato presente esplicitamente nella fonte con corrispondenza diretta alla query
- **Media confidenza**: dato presente ma richiede inferenza (es. CPV correlato, importo stimato)
- **Bassa confidenza**: dato assente; stima basata su precedenti storici o analogie di settore

## Estrazione input

Estrai:
- `cpv`: codice CPV (es. `71000000` per servizi di ingegneria) oppure `null`;
- `regione`: nome della regione italiana (es. `Puglia`) oppure `null`;
- `anno`: anno del ciclo di programmazione (es. `2025`) oppure `null`;
- `nuts_code`: codice NUTS-2 o NUTS-1 corrispondente alla regione (es. `ITF4` per Puglia, `ITF` per tutto il Sud) oppure `null`.

Se regione è `null` o non specificata, usa il titolo con `· Italia` e ometti il filtro NUTS.

### Derivazione `sopra_soglia`

Determina se la query TED PIN va eseguita:
- Se `importo` dalle voci di programmazione ≥ EUR 140 000 (servizi/forniture) o ≥ EUR 5 538 000 (lavori) → `sopra_soglia = true`.
- Se importo non disponibile: `sopra_soglia = true` per CPV 72xxxx (IT services), 71xxxx (ingegneria), 45xxxx (lavori); per tutti gli altri usa `false` come default conservativo.
- Documenta il ragionamento in `## Dati non disponibili`.

## Strategia strumenti

Vedi [../shared/strategia-strumenti.md](../shared/strategia-strumenti.md).

### Sequenza di interrogazione

1. **Programmazione regionale** (SEMPRE):
   - `programmazione_search_biennale(cpv=<cpv>, regione=<regione>, anno=<anno>)`
   - Campo utile per lead time: `anno` (anno del ciclo di programmazione).

2. **PIN TED** (CONDIZIONALE — esegui SE `sopra_soglia` è `true`):
   - `ted_pin_italy(cpv_codes=[<cpv>], nuts_region=<nuts_code>, limit=25)`
   - Campo utile per lead time: `deadline` (scadenza consultazione PIN — proxy della data prevista bando).
   - Se `sopra_soglia` è `false`, ometti e segnala in `## Dati non disponibili`.

3. **Milestone PNRR** (SEMPRE):
   - Primary: `openpnrr_list(endpoint="scadenze", limit=25)` per recuperare milestone con date.
   - Fallback se scadenze non restituisce risultati rilevanti: `openpnrr_list(endpoint="misure")`.
   - Campo utile per lead time: `raw.data` o data presente nei campi dell'item (se disponibile).
   - Nota nella sezione `## Metodologia` quali endpoint sono stati chiamati.

### Derivazione lead time

Il campo "Lead time" nella tabella è una **stima in mesi** derivata come segue:

| Fonte | Campo proxy | Calcolo |
|-------|-------------|---------|
| Programmazione regionale | `anno` | `(anno - anno_corrente) * 12` mesi; se `anno` = anno corrente → 0-6 mesi (stima generica) |
| TED PIN | `deadline` | Mesi tra oggi e `deadline` (scadenza consultazione) |
| PNRR scadenze | data da `raw` | Mesi tra oggi e la scadenza milestone più rilevante |

Se nessuna data è disponibile, indica `"n.d."` nella colonna Lead time e usa **Bassa confidenza**.

## Formato dell'output

Segui il formato definito in references/output-format.md.

Per la mappatura NUTS, consulta references/nuts-mapping.md.

## Regole invarianti

- La prima riga dell'output è sempre: `Dati letti il YYYY-MM-DD`
- Titolo: se regione è assente → `# Digest Pre-Gara — [CPV o settore] · Italia`.
- Ogni voce nella tabella deve avere formato fonte: `(fonte: [nome](URL))` — sempre un link cliccabile.
- Ordina opportunità per **Lead time crescente** (n.d. in fondo).
- Usa il vocabolario di confidenza a tre livelli — mai percentuali o punteggi.
- Non esporre i nomi degli strumenti MCP nell'output finale.
- Le sezioni `## Metodologia`, `## Dati non disponibili` e `## Audit trail` sono sempre presenti.
