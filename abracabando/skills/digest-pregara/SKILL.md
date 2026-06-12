---
name: digest-pregara
description: Analizza il mercato di pre-gara per un settore CPV o una regione, incrociando programmazione regionale biennale, TED PIN e PNRR, e produce un digest in italiano con piena provenienza e livelli di confidenza. Usa questa skill ogni volta che l'utente vuole una panoramica delle opportunità in arrivo in un settore o regione, chiede "cosa bolle in pentola" o "cosa sta per uscire", vuole un quadro di pre-gara con lead time e confidenza incrociando programmazione, avvisi TED e fondi PNRR — anche se nomina una sola di queste fonti.
argument-hint: "[CPV] [regione] [anno]"
allowed-tools:
  - mcp__industrial-mcp-pro__server_capabilities
  - mcp__industrial-mcp-pro__programmazione_search_biennale
  - mcp__industrial-mcp-pro__ted_pin_italy
  - mcp__industrial-mcp-pro__openpnrr_list
  - mcp__industrial-mcp-pro__openpnrr_get
  - mcp__industrial-mcp-free__server_capabilities
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

Determina se la query TED PIN va eseguita (soglie vigenti in [../shared/soglie-ue.md](../shared/soglie-ue.md)). Applica la prima regola che corrisponde, senza esitare sui casi limite — l'importante è dichiarare poi l'assunzione:
1. `importo` ≥ EUR 140 000 (servizi/forniture) o ≥ EUR 5 404 000 (lavori) → `sopra_soglia = true`.
2. `importo` presente ma sotto soglia → `sopra_soglia = false`.
3. `importo` non disponibile e CPV nelle famiglie 72xxxx (IT), 71xxxx (ingegneria) o 45xxxx (lavori) → `sopra_soglia = true`.
4. `importo` non disponibile e CPV in qualsiasi altra famiglia → `sopra_soglia = false` (default conservativo: per queste famiglie le opportunità sopra-soglia su TED sono rare e una query a vuoto aggiunge solo rumore).

Documenta sempre quale regola hai applicato e l'eventuale assunzione in `## Dati non disponibili`.

## Strategia strumenti

Vedi [../shared/strategia-strumenti.md](../shared/strategia-strumenti.md).

### Sequenza di interrogazione

1. **Programmazione regionale** (SEMPRE):
   - `programmazione_search_biennale(cpv=<cpv>, regione=<regione>, anno=<anno>)`
   - Campo utile per lead time: `anno` (anno del ciclo di programmazione).

2. **PIN TED** (CONDIZIONALE — esegui SE `sopra_soglia` è `true`):
   - `ted_pin_italy(cpv_codes=[<cpv>], nuts_region=<nuts_code>, limit=25)`
     (`scope="ACTIVE"` è il default del tool — restituisce solo PIN attivi.)
   - Campo utile per lead time: `deadline` (scadenza consultazione PIN — proxy della data prevista bando).
   - Se `sopra_soglia` è `false`, ometti e segnala in `## Dati non disponibili`.

3. **Milestone PNRR** (FACOLTATIVO — arricchimento secondario):
   - Il PNRR è in fase di chiusura (scadenze principali 2026); ha valore residuale
     di look-ahead per progetti ancora in fase di appalto.
   - Interroga SOLO se: (a) il budget consente almeno 2 chiamate aggiuntive dopo
     programmazione e PIN, **oppure** (b) l'utente nomina esplicitamente
     PNRR / Next Generation EU / missioni M1–M6.
   - Primary: `openpnrr_list(endpoint="scadenze", limit=25)` per milestone con date.
   - Fallback se scadenze non restituisce risultati rilevanti: `openpnrr_list(endpoint="misure")`.
   - Campo utile per lead time: `raw.data` o data presente nei campi dell'item (se disponibile).
   - **Se ometti il PNRR**, annota in `## Metodologia`: "PNRR omesso: programma in
     chiusura, basso valore look-ahead per questo CPV/regione." Non aprire
     `## Dati non disponibili` solo per questa omissione.
   - **Se interrogato e vuoto**, una riga in `## Metodologia` è sufficiente.
   - Nota nella sezione `## Metodologia` quali endpoint sono stati chiamati.

### Derivazione lead time

Il campo "Lead time" nella tabella è una **stima in mesi** derivata come segue:

| Fonte | Campo proxy | Calcolo |
|-------|-------------|---------|
| Programmazione regionale | `anno` | `(anno - anno_corrente) * 12` mesi; se `anno` = anno corrente → 0-6 mesi (stima generica) |
| TED PIN | `deadline` | Mesi tra oggi e `deadline` (scadenza consultazione) |
| PNRR scadenze (se disponibile) | data da `raw` | Mesi tra oggi e la scadenza milestone più rilevante |

Se nessuna data è disponibile, indica `"n.d."` nella colonna Lead time e usa **Bassa confidenza**.

## Formato dell'output

Segui il formato definito in references/output-format.md.

Per la mappatura NUTS, consulta references/nuts-mapping.md (è un collegamento simbolico alla tabella condivisa in `../pin-radar/references/nuts-mapping.md`: modifica quel file per aggiornare entrambe le skill).

## Regole invarianti

- La prima riga dell'output è sempre: `Dati letti il YYYY-MM-DD`
- Titolo: se regione è assente → `# Digest Pre-Gara — [CPV o settore] · Italia`.
- Ogni voce nella tabella deve avere formato fonte: `(fonte: [nome](URL))` — sempre un link cliccabile.
- Ordina opportunità per **Lead time crescente** (n.d. in fondo).
- Usa il vocabolario di confidenza a tre livelli — mai percentuali o punteggi.
- Non esporre i nomi degli strumenti MCP nell'output finale.
- Le sezioni `## Metodologia`, `## Dati non disponibili` e `## Audit trail` sono sempre presenti.
- Il PNRR può essere omesso: in tal caso `## Metodologia` deve contenere la motivazione dell'omissione.
- `## Audit trail` include `ambito_temporale: "solo_aperti"` (programmazione e PIN restituiscono dati futuri per definizione).
- `## Audit trail` contiene un **blocco fenced** (` ``` `), non una tabella markdown.
