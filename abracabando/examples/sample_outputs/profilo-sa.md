> **Query:** /profilo-sa Costruisci il profilo della stazione appaltante ASL Bari dallo storico aggiudicazioni ANAC.

---

Dati letti il 2026-05-28

# Profilo stazione appaltante — ASL Bari

---

## Volume affidamenti

| Anno | N. affidamenti | Importo totale (EUR) | Importo medio (EUR) |
|------|---------------|----------------------|--------------------|
| 2022 | 312 | 48.700.000 | 156.000 |
| 2023 | 287 | 52.100.000 | 181.600 |
| 2024 | 341 | 61.400.000 | 180.100 |

(fonte: [ANAC Open Data](https://dati.anticorruzione.it/opendata/))

---

## Top CPV

| CPV | Descrizione | N. affidamenti | Importo totale |
|-----|-------------|---------------|----------------|
| 33000000 | Attrezzature mediche e farmaceutiche | 187 | EUR 35.200.000 |
| 85000000 | Servizi sanitari e assistenziali | 124 | EUR 28.900.000 |
| 72000000 | Servizi informatici e connessi | 89 | EUR 14.600.000 |
| 45000000 | Lavori di costruzione | 67 | EUR 18.300.000 |
| 79000000 | Servizi alle imprese | 81 | EUR 16.400.000 |

---

## Top fornitori

| Fornitore | N. aggiudicazioni | Importo totale | CPV prevalente |
|-----------|-------------------|----------------|----------------|
| Siemens Healthineers Italia S.p.A. | 23 | EUR 8.200.000 | 33000000 |
| Engineering Ingegneria Informatica S.p.A. | 18 | EUR 5.600.000 | 72000000 |
| Medtronic Italia S.p.A. | 15 | EUR 4.100.000 | 33000000 |
| Tesi S.p.A. | 12 | EUR 3.800.000 | 72000000 |
| Ge Healthcare Italia S.r.l. | 11 | EUR 3.200.000 | 33000000 |

---

## Stagionalita

Distribuzione mensile degli affidamenti (media 2022-2024):
- Picco principale: novembre-dicembre (31% degli affidamenti annuali)
- Picco secondario: marzo-aprile (22%)
- Periodo di minima attivita: agosto (3%)

Pattern ricorrente: concentrazione a fine anno tipica per utilizzo residui di bilancio.

---

## Importo medio per categoria

| Categoria | Importo medio | Range tipico |
|-----------|---------------|-------------|
| Attrezzature mediche | EUR 188.000 | EUR 50.000 - EUR 2.100.000 |
| Servizi IT | EUR 164.000 | EUR 30.000 - EUR 800.000 |
| Lavori edili | EUR 273.000 | EUR 80.000 - EUR 1.500.000 |

---

## Anomalie ricorrenti

- **Affidamenti diretti ripetuti**: 14 affidamenti diretti allo stesso fornitore per servizi di manutenzione elettromedicale nel 2023-2024 — verificare se rientrano nella soglia ex art. 50 D.Lgs. 36/2023
- **Frazionamento sospetto**: 7 affidamenti per lavori di ristrutturazione padiglione C nel 2024, tutti sotto EUR 40.000 — possibile elusione soglie

---

## Metodologia

L'identificazione della stazione appaltante avviene tramite **corrispondenza per denominazione** sui dataset ANAC. Questo approccio puo generare falsi positivi in presenza di enti con denominazione simile (es. "ASL Bari" e possibili omonimi in altri contesti). I risultati si riferiscono esclusivamente agli affidamenti in cui la denominazione dell'ente corrisponde alla query "ASL Bari".

Specificare il codice fiscale dell'ente (80012650721) nella query migliora la precisione.

---

## Audit trail

```
Query ANAC: "ASL Bari"
Dataset identificati: cig-smart-2022, cig-smart-2023, cig-smart-2024
Anni coperti: 2022, 2023, 2024
Timestamp: 2026-05-28T15:44:22Z
```
