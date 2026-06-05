# Formato output — Profilo Stazione Appaltante

L'output è un profilo quantitativo in italiano formale.

## Prima riga
`Dati letti il YYYY-MM-DD`

## Titolo
`# Profilo Stazione Appaltante — [Nome ente]`

---

## `## Volume affidamenti`

Deriva da `anac_sa_history.by_year_cpv`: aggrega per `anno` sommando `n` e `totale_aggiudicato`.

| Anno | N. affidamenti | Importo totale (EUR) | Importo medio (EUR) |
|------|---------------|----------------------|--------------------|
| [YYYY] | [n aggregato] | EUR [totale_aggiudicato aggregato] | EUR [media] |

---

## `## Top CPV`

I 5 codici CPV più frequenti negli affidamenti dell'ente.

Deriva da `anac_sa_history.by_year_cpv`: aggrega per `cpv` sommando `n` e `totale_aggiudicato`. Ordina per `n` decrescente.

| CPV | Descrizione | N. affidamenti | Importo totale |
|-----|-------------|---------------|----------------|
| [cpv] | [cpv_descr] | [n] | EUR [totale_aggiudicato] |

---

## `## Top fornitori`

I 5 fornitori con maggiore volume di aggiudicazioni.

Deriva da `anac_search_awards`: raggruppa per `aggiudicatario` sommando `importo_aggiudicato` e contando le righe. Ordina per importo totale decrescente.

| Fornitore | N. aggiudicazioni | Importo totale | P.IVA |
|-----------|-------------------|----------------|-------|
| [aggiudicatario] | [N] | EUR [importo] | [piva_aggiudicatario] |

---

## `## Stagionalità`

Distribuzione mensile degli affidamenti.

Deriva da `anac_search_awards`: raggruppa per mese di `data_aggiudicazione`. Se `data_aggiudicazione` non è disponibile per la maggior parte dei record, ometti questa sezione e segnalalo in `## Metodologia`.

Identifica i mesi con picchi di attività e possibili pattern ricorrenti (es. picco di dicembre per chiusura esercizio finanziario).

---

## `## Importo medio per categoria`

Raggruppa i record `anac_search_awards` per prefisso CPV (prime 2 cifre) e calcola la media di `importo_aggiudicato`.

| Categoria | Importo medio | Range tipico |
|-----------|---------------|-------------|
| [prefisso CPV — descrizione] | EUR [importo] | EUR [min] - [max] |

---

## `## Anomalie ricorrenti`

Segnala eventuali pattern anomali identificati nei dati:
- Affidamenti diretti ripetuti allo stesso fornitore (stesso `aggiudicatario` su CIG multipli a basso importo);
- Concentrazione elevata su pochi CPV (un singolo CPV > 60% degli affidamenti);
- Variazioni anomale di importo anno su anno (variazione > 50% YoY).

Se nessuna anomalia rilevata, scrivi: `"Nessuna anomalia rilevata nei dati disponibili."`

---

## `## Metodologia`

Sezione sempre presente.

Includi:
1. **Identificazione ente**: "L'identificazione della stazione appaltante avviene tramite corrispondenza per denominazione (ILIKE) sui dati ANAC, o per codice fiscale esatto se fornito. Questo approccio può generare falsi positivi in presenza di enti con denominazione simile (es. 'ASL Roma 1' vs 'ASL Roma 1-2'). I risultati si riferiscono esclusivamente agli affidamenti in cui la denominazione corrisponde al testo della query. Specificare il codice fiscale migliora la precisione."
2. **Copertura snapshot**: "I dati provengono da uno snapshot mensile di ANAC. La copertura temporale è limitata alla finestra dello snapshot disponibile al momento della lettura — non necessariamente l'intera storia dell'ente. La data di riferimento dello snapshot è indicata nel campo `provenance` restituito dai tool."

---

## `## Audit trail`

Sezione sempre presente.

Blocco di codice fenced:

```text
Input ente: "<nome o CF>"
Tool 1 (anac_sa_history): total_awards=<N>, by_year_cpv_rows=<N>
Tool 2 (anac_search_awards): awards_returned=<N>
Snapshot coverage: <data provenance restituita dal tool>
Timestamp: YYYY-MM-DDTHH:MM:SSZ
```
