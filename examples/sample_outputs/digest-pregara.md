Dati letti il 2026-05-28

# Digest pre-gara — Servizi di ingegneria e architettura, Puglia

Query: CPV 71000000, Regione Puglia, Anno 2025

---

## Opportunita rilevate

| Ente | Oggetto | Importo stimato | Fonte | Lead time | Confidenza |
|------|---------|-----------------|-------|-----------|------------|
| Regione Puglia — Sez. Lavori Pubblici | Programma Triennale OO.PP. 2024-2026 — lotti infrastrutturali | Non pubblicato | (fonte: [Regione Puglia Trasparenza](https://www.regione.puglia.it/web/trasparenza/-/programma-triennale-delle-opere-pubbliche)) | 3-6 mesi | Media confidenza |
| Autorita Idrica Pugliese (AIP) | Programma Biennale Acquisti 2025-2026 — forniture e servizi tecnici | Non pubblicato | (fonte: [AIP Trasparenza](https://www.aip.puglia.it/index.php/trasparenza/beni-immobili-e-gestione-patrimonio)) | 2-4 mesi | Media confidenza |
| Autorita di Sistema Portuale del Mare Adriatico Meridionale | PIN — Servizi di progettazione portuale | >= EUR 500.000 (stima) | (fonte: [TED PIN 445231-2025](https://ted.europa.eu/en/notice/-/detail/445231-2025)) | 1-2 mesi | Alta confidenza |

---

## Metodologia

Fonti interrogate:
- **Programmazione regionale**: registro biennale/triennale filtrato per regione Puglia, anno 2025
- **TED PIN Italia**: filtro `notice-type=PIN AND place-of-performance=ITA AND classification-cpv=71000000`
- **OpenPNRR Misure**: confronto con misure PNRR M2C4 (digitalizzazione e infrastrutture) e M5C2 (coesione territoriale)

Misure PNRR confrontate: M1C1-1, M2C4-1.1, M5C2-2.2

---

## Dati non disponibili

- **TED PIN con filtro NUTS ITF4 (Puglia)**: nessun PIN trovato con restrizione geografica NUTS-2 specifica; ricerca allargata a `place-of-performance=ITA`
- **Consip**: servizi di ingegneria non inclusi nelle convenzioni attive verificate alla data di interrogazione

---

## Audit trail

```
Query programmazione: cpv=71000000, regione=Puglia, anno=2025
Query TED PIN: notice-type=PIN AND place-of-performance=ITA AND classification-cpv=71000000
Misure PNRR confrontate: openpnrr_list(endpoint="misure") — 47 misure restituite
Timestamp: 2026-05-28T10:23:15Z
```
