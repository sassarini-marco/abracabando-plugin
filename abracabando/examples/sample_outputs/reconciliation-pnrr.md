> **Query:** /reconciliation-pnrr Riconcilia gli importi del progetto PNRR con CUP H87G22001120006 tra OpenPNRR, OpenCoesione e ANAC.

---

Dati letti il 2026-05-28

# Riconciliazione PNRR — Misura M2C4-1.1, Comune di Taranto

CUP analizzati: H87G22001120006, H87G22001121006

---

## Tabella di allineamento

| CUP | Stato OpenPNRR | Importo OpenCoesione | Importo ANAC | Flag |
|-----|----------------|---------------------|--------------|------|
| H87G22001120006 | Completato | EUR 850.000 | EUR 920.000 | IMPORTO_SOPRA_FINANZIATO |
| H87G22001121006 | In corso | EUR 430.000 | Non trovato | CUP_ORFANO |

(fonte: [OpenPNRR](https://www.openpnrr.it/)) (fonte: [OpenCoesione](https://opencoesione.gov.it/)) (fonte: [ANAC Open Data](https://dati.anticorruzione.it/opendata/))

---

## Flag rilevati

**IMPORTO_SOPRA_FINANZIATO**: l'importo contrattuale ANAC (EUR 920.000) supera il finanziamento OpenCoesione (EUR 850.000) per il CUP H87G22001120006. Differenza: EUR 70.000. Verificare se il finanziamento e' stato aggiornato o se vi sono co-finanziamenti non registrati in OpenCoesione.

**CUP_ORFANO**: il CUP H87G22001121006 e' presente in OpenPNRR con stato "In corso" ma non e' stato trovato in ANAC. Possibili cause: bando non ancora pubblicato, errore di codifica CUP nel sistema ANAC, o progetto annullato e non aggiornato su OpenPNRR.

---

## Dati non disponibili

- **TED**: nessuna ricerca TED eseguita — entrambi i CUP hanno importi sotto soglia UE per servizi (EUR 221.000)
- **OpenCoesione Parquet**: URL disponibile per download bulk `progetti_esteso_2021-2027.parquet` (fonte: [OpenCoesione Open Data](https://opencoesione.gov.it/it/opendata/)) per analisi approfondita

---

## Audit trail

```
CUP analizzati: H87G22001120006, H87G22001121006
Fonti interrogate: OpenPNRR, OpenCoesione, ANAC
Flag rilevati: IMPORTO_SOPRA_FINANZIATO, CUP_ORFANO
Dataset OpenCoesione usato: progetti_esteso_2021-2027
Timestamp: 2026-05-28T16:30:55Z
```
