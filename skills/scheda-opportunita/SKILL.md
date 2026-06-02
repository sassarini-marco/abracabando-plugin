---
name: scheda-opportunita
description: Produce una scheda dettagliata su una specifica opportunità di gara, incrociando ANAC, OpenPNRR, OpenCoesione e TED. Usa questa skill quando l'utente chiede di analizzare un'opportunità identificata da CIG, CUP o nome dell'ente, e vuole una nota decisionale go/no-go con storico acquisti, intelligence competitiva, timeline attesa e raccomandazioni operative.
argument-hint: "<CIG|CUP|ente> [CPV]"
disable-model-invocation: true
allowed-tools:
  - mcp__industrial-mcp-pro__anac_search_awards
  - mcp__industrial-mcp-pro__ted_search
  - mcp__industrial-mcp-pro__openpnrr_list
  - mcp__industrial-mcp-pro__openpnrr_get
  - mcp__industrial-mcp-pro__opencoesione_describe_dataset
  - mcp__industrial-mcp-pro__opencoesione_list_datasets
  - mcp__industrial-mcp-free__anac_search_awards
  - mcp__industrial-mcp-free__anac_search_datasets
  - mcp__industrial-mcp-free__anac_get_dataset
  - mcp__industrial-mcp-free__ted_search
  - mcp__industrial-mcp-free__openpnrr_list
  - mcp__industrial-mcp-free__openpnrr_get
  - mcp__industrial-mcp-free__opencoesione_describe_dataset
  - mcp__industrial-mcp-free__opencoesione_list_datasets
---

# Scheda Opportunità

Usa questa skill solo per richieste su:
- analisi di un'opportunità specifica identificata da CIG, CUP o nome ente;
- incrocio TED-ANAC-PNRR-Coesione;
- schede di intelligence commerciale go/no-go.

## Obiettivo

Produrre una scheda di intelligence commerciale in italiano formale che:
1. incroci dati da TED, ANAC, OpenPNRR e OpenCoesione;
2. classifichi Coerenza CPV e Valutazione trasformazione (Alta/Media/Bassa);
3. fornisca storico aggiudicazioni ANAC e intelligence competitiva;
4. indichi timeline attesa e prossimi passi consigliati;
5. includa sempre sezioni Fonti, Dati non disponibili e Audit trail.

## Regole essenziali

Vedi [../shared/regole-comuni.md](../shared/regole-comuni.md).

## Estrazione input

Estrai:
- `cig`: Codice Identificativo Gara oppure `null`;
- `cup`: Codice Unico di Progetto oppure `null`;
- `ente`: nome della stazione appaltante oppure `null`;
- `cpv`: codice CPV oppure `null`.

Almeno uno tra `cig`, `cup` o `ente` deve essere presente. Se nessuno è fornito, chiedi all'utente.

## Strategia strumenti

Vedi [../shared/strategia-strumenti.md](../shared/strategia-strumenti.md).

### Sequenza di interrogazione

1. **ANAC** (OBBLIGATORIO):
   - `anac_search_awards(query="<ente OR oggetto>", cpv_prefix="<cpv_prefix>")`
   - Se zero risultati, fallback: `anac_search_datasets(query="<cig OR cup OR ente>", rows=10)` (ATTENZIONE: restituisce ZIP da 100 MB — usare solo come ultima risorsa)

2. **TED** (CONDIZIONALE — esegui se importo stimato > soglia UE o se `ente` è noto):
   - `ted_search(query="buyer-name=\"<ente>\" AND place-of-performance=ITA", limit=10)`
   - Se errore (400, 500, timeout): documenta in `## Dati non disponibili` ed emetti scheda con dati disponibili.

3. **OpenPNRR** (CONDIZIONALE — esegui se `cup` disponibile o se CPV/settore tipicamente PNRR):
   - `openpnrr_list(endpoint="progetti")` oppure `openpnrr_get(endpoint="progetti", id="<cup>")`
   - Se zero risultati: documenta in `## Dati non disponibili`.

4. **OpenCoesione** (CONDIZIONALE — esegui se CUP disponibile o se ciclo 2021-2027):
   - `opencoesione_list_datasets()`, `opencoesione_describe_dataset(dataset_id="progetti_esteso_2021-2027")`
   - Se zero risultati: documenta in `## Dati non disponibili`.

### Gestione date implausibili

Se un campo `data_aggiudicazione` ANAC ha anno < 2000 o > 2030, **non riportarlo** nella scheda; segnalalo in `## Dati non disponibili` con la nota:  
`"data_aggiudicazione ANAC implausibile (valore grezzo: [valore]) — qualità del dato ANAC non sufficiente per la pubblicazione"`

## Formato dell'output

Segui il formato definito in references/output-format.md.

Per le regole di classificazione Coerenza CPV e Valutazione trasformazione, consulta references/classification-rules.md.

Se serve un esempio completo, consulta examples/example-output.md.

## Regole invarianti

- La prima riga dell'output è sempre: `Dati letti il YYYY-MM-DD`
- La sezione `## Sintesi incrociata TED-ANAC` deve apparire con **ESATTAMENTE** questo titolo (mai numerata, mai rinominata).
- Per le regole di classificazione (Coerenza CPV, Valutazione trasformazione), vedi `references/classification-rules.md`.
- La sezione `## Fonti` deve elencare ogni fonte consultata con: identificatore grezzo (CIG, CUP, numero TED `NNNNNN-YYYY`), URL istituzionale restituito dallo strumento, data di lettura `YYYY-MM-DD`.
- Per ANAC senza URL specifico, usa `https://dati.anticorruzione.it/opendata`.
- Non costruire URL dalla memoria — usa **solo** quelli restituiti dagli strumenti.
- Non esporre i nomi degli strumenti MCP nell'output finale.
- Le sezioni `## Dati non disponibili` e `## Audit trail` sono sempre presenti.
- La sezione `## Intelligence competitiva` deve includere il disclaimer: "dati storici pubblici ANAC, non informazioni riservate".
