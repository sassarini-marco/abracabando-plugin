---
name: reconciliation-pnrr
description: Riconcilia i dati PNRR tra OpenPNRR, OpenCoesione e ANAC per uno o più CUP. Usa questa skill quando l'utente chiede di verificare allineamento tra fonti PNRR, identificare divergenze di importo, stato e pubblicazione TED, e ottenere un report con flag di anomalia.
argument-hint: "<CUP> [misura_pnrr]"
disable-model-invocation: true
allowed-tools:
  - mcp__industrial-mcp-pro__openpnrr_list
  - mcp__industrial-mcp-pro__openpnrr_get
  - mcp__industrial-mcp-pro__opencoesione_project_by_cup
  - mcp__industrial-mcp-pro__opencoesione_search_projects
  - mcp__industrial-mcp-pro__anac_search_awards
  - mcp__industrial-mcp-pro__anac_pnrr_datasets
  - mcp__industrial-mcp-pro__ted_search
  - mcp__industrial-mcp-free__openpnrr_list
  - mcp__industrial-mcp-free__openpnrr_get
  - mcp__industrial-mcp-free__opencoesione_project_by_cup
  - mcp__industrial-mcp-free__opencoesione_search_projects
  - mcp__industrial-mcp-free__anac_search_awards
  - mcp__industrial-mcp-free__anac_pnrr_datasets
  - mcp__industrial-mcp-free__ted_search
---

# Reconciliation PNRR

Usa questa skill solo per richieste su:
- riconciliazione dati PNRR tra fonti (OpenPNRR, OpenCoesione, ANAC);
- verifica allineamento importi, stati, pubblicazione TED;
- identificazione divergenze e anomalie per CUP specifici.

## Obiettivo

Produrre un report di riconciliazione in italiano formale che:
1. confronti dati da OpenPNRR, OpenCoesione e ANAC per uno o più CUP;
2. identifichi divergenze di importo, stato e pubblicazione TED;
3. assegni flag di anomalia standardizzati;
4. fornisca spiegazione dettagliata per ogni flag rilevato.

## Regole essenziali

Vedi [../shared/regole-comuni.md](../shared/regole-comuni.md).

## Marcatori di flag

Usa **esattamente** questi identificatori (maiuscolo, underscore — anchor stabili):

- `CUP_ORFANO`: CUP presente in OpenPNRR ma assente in OpenCoesione o ANAC
- `IMPORTO_SOPRA_FINANZIATO`: importo ANAC/contrattuale superiore al finanziamento OpenCoesione
- `STATO_DIVERGENTE`: stato progetto diverso tra OpenPNRR e OpenCoesione (es. "completato" vs "in corso")
- `MANCATA_PUBBLICAZIONE_TED`: contratto sopra soglia UE senza corrispondente avviso TED (verifica euristica)

Per il formato delle spiegazioni, consulta references/flag-explanations.md.

## Estrazione input

Estrai:
- `cups`: lista di CUP da riconciliare (OBBLIGATORIO — almeno uno);
- `misura_pnrr`: codice misura PNRR (es. "M1C1-1.1") oppure `null`.

Se nessun CUP è fornito, chiedi all'utente.

## Strategia strumenti

Vedi [../shared/strategia-strumenti.md](../shared/strategia-strumenti.md).

### Sequenza di interrogazione

1. **OpenPNRR** (OBBLIGATORIO):
   - Per un CUP specifico: `openpnrr_get(endpoint="progetti", id="<cup>")`
   - Per una misura PNRR: `openpnrr_list(endpoint="misure")`
   - Ricava: stato progetto, titolo, ente beneficiario.

2. **OpenCoesione** (OBBLIGATORIO):
   - Primary: `opencoesione_project_by_cup(cup="<cup>")`
   - Restituisce: `totale_finanziato`, `totale_impegnato`, `totale_pagato`, `stato_procedurale`, `stato_finanziario`.
   - Fallback se il CUP non è trovato: `opencoesione_search_projects(cup="<cup>")`.
   - Confronta importi e stato con OpenPNRR.

3. **ANAC CIG-level** (OBBLIGATORIO):
   - `anac_pnrr_datasets()` per individuare i dataset PNRR disponibili.
   - `anac_search_awards(query="<ente beneficiario>")` per trovare i contratti CIG correlati al CUP.
   - Ricava: importo aggiudicato, aggiudicatario, data aggiudicazione.

4. **TED** (CONDIZIONALE — solo se `importo_aggiudicato` ANAC ≥ soglia UE):
   - Soglie UE: servizi/forniture ≥ EUR 140 000; lavori ≥ EUR 5 538 000.
   - `ted_search(query='buyer-name="<ente beneficiario>" AND place-of-performance=ITA', scope="ALL", limit=10)`
   - Se nessun avviso TED trovato → flag `MANCATA_PUBBLICAZIONE_TED`.
   - **Nota**: la verifica è **euristica** (buyer-name + soglia importo). TED non contiene CIG o CUP — non è possibile una corrispondenza esatta per identificatore nazionale.

## Formato dell'output

Segui il formato definito in references/output-format.md.

## Regole invarianti

- La prima riga dell'output è sempre: `Dati letti il YYYY-MM-DD`
- Non esporre i nomi degli strumenti MCP nell'output finale.
- Le sezioni `## Dati non disponibili` e `## Audit trail` sono sempre presenti.
- Ogni voce nella tabella di allineamento deve avere fonte identificabile con URL.
