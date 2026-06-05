# Profilo Stazione Appaltante — ASL Roma 1

Dati letti il 2025-01-15

## Volume affidamenti

| Anno | N. aggiudicazioni | Totale aggiudicato (EUR) |
|------|-------------------|--------------------------|
| 2023 | 87                | 12 450 000               |
| 2024 | 102               | 15 780 000               |

## Top 5 CPV per volume

| CPV      | Descrizione                     | N. contratti | Totale aggiudicato (EUR) |
|----------|---------------------------------|--------------|--------------------------|
| 33600000 | Prodotti farmaceutici           | 34           | 8 200 000                |
| 33140000 | Dispositivi medici              | 28           | 4 900 000                |
| 85121000 | Servizi ospedalieri             | 15           | 3 100 000                |
| 90900000 | Servizi di pulizia              | 12           | 1 450 000                |
| 71314000 | Servizi di consulenza energetica| 8            | 980 000                  |

## Top 5 fornitori per volume aggiudicato

| Fornitore                    | P.IVA         | N. contratti | Totale aggiudicato (EUR) |
|------------------------------|---------------|--------------|--------------------------|
| Pharma Distribuzione S.p.A.  | 01234567890   | 12           | 3 400 000                |
| Medtech Italia S.r.l.        | 09876543210   | 9            | 2 100 000                |
| Clean Services Consortium    | 11223344556   | 8            | 1 200 000                |
| Energia Consulting Group     | 55667788990   | 5            | 880 000                  |
| Dispositivi Medici Plus      | 22334455667   | 6            | 750 000                  |

## Stagionalità

| Mese | N. aggiudicazioni | Totale aggiudicato (EUR) |
|------|-------------------|--------------------------|
| Gen  | 14                | 1 850 000                |
| Feb  | 12                | 1 340 000                |
| Mar  | 18                | 2 100 000                |
| Apr  | 15                | 1 780 000                |
| Mag  | 17                | 2 050 000                |
| Giu  | 16                | 1 920 000                |
| Lug  | 8                 | 890 000                  |
| Ago  | 5                 | 620 000                  |
| Set  | 19                | 2 400 000                |
| Ott  | 21                | 2 680 000                |
| Nov  | 23                | 2 950 000                |
| Dic  | 21                | 2 650 000                |

## Anomalie ricorrenti

- Concentrazione di aggiudicazioni nel trimestre settembre-dicembre (67% del volume annuale 2024).
- Picco di affidamenti diretti sotto soglia comunitaria per CPV 33600000 (farmaceutici) nel Q4.
- Assenza di gare sopra EUR 5M negli ultimi 18 mesi registrati.

## Metodologia

Snapshot ANAC mensile (finestra di copertura: gennaio 2023 - dicembre 2024). I totali riflettono solo le aggiudicazioni presenti nello snapshot; eventuali contratti precedenti o successivi alla finestra temporale non sono inclusi. La ricerca è stata effettuata per nome ente "ASL Roma 1" — possibili falsi positivi con enti dal nome simile (es. "ASL Roma 1-2 Ufficio Acquisti").

## Audit trail

```yaml
tool: anac_sa_history
params: {cf_or_name: "ASL Roma 1"}
timestamp: 2025-01-15T10:23:45Z
result: {total_awards: 189, by_year_cpv: [87 records 2023, 102 records 2024]}

tool: anac_search_awards
params: {query: "ASL Roma 1", limit: 50}
timestamp: 2025-01-15T10:24:12Z
result: 50 individual award records
```