# Digest Pre-Gara — CPV 71000000 · Puglia

Dati letti il 2025-01-15

| Opportunità | Ente | Importo stimato | Lead time (mesi) | Confidenza | Fonte |
|-------------|------|-----------------|------------------|------------|-------|
| Programmazione 2025-2027 — Servizi di ingegneria per infrastrutture viarie | Regione Puglia | EUR 4 500 000 | 6 | Alta | (fonte: [Programmazione biennale 2025-2027 Puglia](https://example.gov.it/programmazione/2025-puglia.zip)) |
| PIN TED — Engineering services for new hospital complex | ASL Bari | EUR 12 000 000 | 8 | Alta | (fonte: [TED PIN 123456-2025](https://ted.europa.eu/udl?uri=TED:NOTICE:123456-2025)) |
| PNRR Milestone M1C1-1.2 — Progettazione impianti energetici scuole | Provincia di Lecce | EUR 1 800 000 | 14 | Media | (fonte: [OpenPNRR scadenza M1C1-1.2](https://openpnrr.it/scadenze/M1C1-1.2)) |
| Programmazione 2026-2028 — Riqualificazione urbana centro storico | Comune di Taranto | EUR 950 000 | 18 | Media | (fonte: [Programmazione biennale 2026-2028 Puglia](https://example.gov.it/programmazione/2026-puglia.zip)) |
| PNRR Milestone M2C3-2.1 — Bonifica siti industriali dismessi | Provincia di Foggia | n.d. | n.d. | Bassa | (fonte: [OpenPNRR misura M2C3-2.1](https://openpnrr.it/misure/M2C3-2.1)) |

## Metodologia

**Fonti interrogate:**

1. **Programmazione regionale:** `programmazione_search_biennale(cpv="71000000", regione="Puglia", anno=null)` — restituisce voci dai piani biennali/triennali pubblicati dalle PA regionali e locali.
2. **PIN TED:** `ted_pin_italy(cpv_codes=["71000000"], nuts_region="ITF4", limit=25)` — Prior Information Notices pubblicati su Tenders Electronic Daily per la regione Puglia (NUTS-2 ITF4). Query eseguita perché CPV 71000000 rientra tipicamente sopra soglia UE per appalti di ingegneria.
3. **Milestone PNRR:** `openpnrr_list(endpoint="scadenze", limit=25)` — scadenze milestone PNRR rilevanti per il settore. Fallback a `openpnrr_list(endpoint="misure")` per voci senza data specifica.

**Derivazione lead time:**

- Programmazione regionale: `(anno - anno_corrente) * 12` mesi; se anno = anno corrente, stima generica 0-6 mesi.
- TED PIN: mesi tra oggi (2025-01-15) e la scadenza consultazione (`deadline` del PIN).
- PNRR scadenze: mesi tra oggi e la data milestone più rilevante (`raw.data`).

**Confidenza:**

- **Alta:** dato presente esplicitamente (es. importo e data da PIN TED, anno da programmazione).
- **Media:** dato richiede inferenza (es. importo stimato da CPV correlato, data milestone PNRR proxy).
- **Bassa:** dato assente; stima basata su analogie di settore (es. PNRR misura senza scadenza nota).

**Copertura NUTS:** ITF4 (Puglia). Per macro-area Sud usare NUTS-1 ITF (ora supportato con espansione automatica NUTS-2).

## Dati non disponibili

- PNRR misura M2C3-2.1: scadenza milestone non disponibile in OpenPNRR `endpoint="scadenze"`, fallback a `endpoint="misure"` ha restituito solo titolo generico senza data. Lead time: n.d., confidenza Bassa.
- TED PIN: la query è stata eseguita perché CPV 71000000 (servizi di ingegneria) rientra tipicamente sopra soglia UE (≥ EUR 5 404 000 per lavori, ≥ EUR 140 000 per servizi). Non è stato possibile derivare importi esatti da tutte le voci di programmazione regionale; dove assente, confidenza ridotta a Media.

## Audit trail

```yaml
tool: programmazione_search_biennale
params: {cpv: "71000000", regione: "Puglia", anno: null}
timestamp: 2025-01-15T11:12:34Z
result: 2 entries (anni 2025, 2026)

tool: ted_pin_italy
params: {cpv_codes: ["71000000"], nuts_region: "ITF4", limit: 25}
timestamp: 2025-01-15T11:13:02Z
result: 1 PIN (publication 123456-2025, deadline 2025-09-15)

tool: openpnrr_list
params: {endpoint: "scadenze", limit: 25}
timestamp: 2025-01-15T11:13:28Z
result: 1 scadenza rilevante (M1C1-1.2, data 2026-03-31)

tool: openpnrr_list
params: {endpoint: "misure", limit: 25}
timestamp: 2025-01-15T11:13:55Z
result: 1 misura senza data (M2C3-2.1)
```