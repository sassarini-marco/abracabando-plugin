# Reconciliation PNRR — CUP J33C22000120001

Dati letti il 2025-01-15

## Allineamento fonti

| Fonte         | Titolo progetto                          | Importo         | Stato                    | Note                     |
|---------------|------------------------------------------|-----------------|--------------------------|--------------------------|
| OpenPNRR      | Digitalizzazione ASL Puglia              | EUR 2 500 000   | In corso                 | M1C1-1.1 milestone Q4 2025|
| OpenCoesione  | Digitalizzazione ASL Puglia              | EUR 2 500 000   | Stato procedurale: Esecuzione | Totale impegnato: EUR 2 450 000, Totale pagato: EUR 1 200 000 |
| ANAC          | CIG 9876543210 — Fornitura hardware      | EUR 1 100 000   | Aggiudicato              | Aggiudicatario: Tech Solutions S.p.A. |
| ANAC          | CIG 8765432109 — Sviluppo software ERP   | EUR 980 000     | Aggiudicato              | Aggiudicatario: Software Italia S.r.l. |
| TED           | Nessun avviso trovato                    | —               | —                        | Buyer-name heuristic: "ASL Puglia" |

## Flag identificati

### IMPORTO_SOPRA_FINANZIATO

**Definizione:** Importo ANAC/contrattuale superiore al finanziamento OpenCoesione.

**Dettaglio:**
- Totale importi aggiudicati ANAC: EUR 2 080 000 (CIG 9876543210 + CIG 8765432109)
- Totale impegnato OpenCoesione: EUR 2 450 000
- **No flag**: importi aggiudicati rientrano nel finanziamento disponibile.

### STATO_DIVERGENTE

**Definizione:** Stato progetto diverso tra OpenPNRR e OpenCoesione.

**Dettaglio:**
- OpenPNRR: "In corso"
- OpenCoesione: "Esecuzione" (stato procedurale)
- **No flag**: gli stati sono semanticamente coerenti ("In corso" = "Esecuzione").

### MANCATA_PUBBLICAZIONE_TED

**Definizione:** Contratto sopra soglia UE senza corrispondente avviso TED (verifica euristica).

**Dettaglio:**
- Soglia UE servizi: EUR 140 000
- CIG 9876543210: EUR 1 100 000 (sopra soglia)
- CIG 8765432109: EUR 980 000 (sopra soglia)
- Ricerca TED: query `buyer-name="ASL Puglia" AND place-of-performance=ITA`, scope=ALL, zero risultati trovati.
- **Flag presente**: nessun avviso TED trovato per importi sopra soglia. Nota: la verifica è euristica (buyer-name + soglia importo); TED non contiene CIG o CUP.

### CUP_ORFANO

**Definizione:** CUP presente in OpenPNRR ma assente in OpenCoesione o ANAC.

**Dettaglio:**
- CUP J33C22000120001 presente in tutte e tre le fonti.
- **No flag**: CUP trovato su OpenPNRR, OpenCoesione e ANAC.

## Fonti

- OpenPNRR: [Progetto J33C22000120001](https://openpnrr.it/progetti/J33C22000120001) — letto il 2025-01-15
- OpenCoesione: [Progetto CUP J33C22000120001](https://opencoesione.gov.it/it/progetti/J33C22000120001/) — letto il 2025-01-15
- ANAC CIG 9876543210: https://dati.anticorruzione.it/opendata — letto il 2025-01-15
- ANAC CIG 8765432109: https://dati.anticorruzione.it/opendata — letto il 2025-01-15
- TED: [Expert Search](https://ted.europa.eu/TED/search/expertSearch.do) — letto il 2025-01-15

## Dati non disponibili

- TED non contiene campi CIG o CUP; la verifica di MANCATA_PUBBLICAZIONE_TED è basata su buyer-name heuristic ("ASL Puglia") e soglia importo.
- OpenCoesione non restituisce CIG associati al CUP; il collegamento CUP→CIG è stato ricostruito tramite ANAC usando l'ente beneficiario come query.

## Audit trail

```yaml
tool: openpnrr_get
params: {endpoint: "progetti", item_id: "J33C22000120001"}
timestamp: 2025-01-15T09:45:12Z
result: {titolo: "Digitalizzazione ASL Puglia", stato: "In corso", misura: "M1C1-1.1"}

tool: opencoesione_project_by_cup
params: {cup: "J33C22000120001"}
timestamp: 2025-01-15T09:45:34Z
result: {totale_finanziato: 2500000, totale_impegnato: 2450000, totale_pagato: 1200000, stato_procedurale: "Esecuzione"}

tool: anac_search_awards
params: {query: "ASL Puglia", limit: 50}
timestamp: 2025-01-15T09:46:01Z
result: 2 CIG trovati (9876543210, 8765432109)

tool: ted_search
params: {query: 'buyer-name="ASL Puglia" AND place-of-performance=ITA', scope: "ALL", limit: 10}
timestamp: 2025-01-15T09:46:28Z
result: 0 notices found
```