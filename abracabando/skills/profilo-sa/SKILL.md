---
name: profilo-sa
description: "Genera un profilo quantitativo di una stazione appaltante basato sui dati ANAC, con volume affidamenti, top CPV, top fornitori, stagionalità e anomalie ricorrenti. Usa questa skill ogni volta che l'utente vuole capire come compra un ente pubblico (Comune, ASL, Regione, ministero, società in house): chi sono i suoi fornitori abituali, quanto e cosa affida, in quali mesi, se ci sono concentrazioni o affidamenti diretti ripetuti — anche se chiede solo \"che gare fa l'ente X\" o \"chi vince con il Comune di Y\"."
argument-hint: "<nome ente> [CF ente]"
allowed-tools:
  - mcp__industrial-mcp-pro__server_capabilities
  - mcp__industrial-mcp-pro__anac_sa_history
  - mcp__industrial-mcp-pro__anac_search_awards
  - mcp__industrial-mcp-free__server_capabilities
  - mcp__industrial-mcp-free__anac_sa_history
  - mcp__industrial-mcp-free__anac_search_awards
---

# Profilo Stazione Appaltante

Usa questa skill solo per richieste su:
- profilo quantitativo di un ente pubblico (stazione appaltante);
- analisi comportamento di acquisto basata su ANAC;
- storico affidamenti, top CPV, top fornitori, stagionalità.

## Obiettivo

Produrre un profilo quantitativo in italiano formale che:
1. riassuma volume affidamenti per anno;
2. identifichi i 5 CPV più frequenti;
3. identifichi i 5 fornitori con maggiore volume aggiudicazioni;
4. analizzi stagionalità mensile (se disponibile);
5. segnali eventuali anomalie ricorrenti.

## Regole essenziali

Vedi [../shared/regole-comuni.md](../shared/regole-comuni.md).

## Estrazione input

Estrai:
- `ente`: nome completo o parziale della stazione appaltante, oppure codice fiscale (11 cifre) (OBBLIGATORIO);
- `date_from` / `date_to`: finestra temporale ISO `YYYY-MM-DD` (default: nessuna — restituisce tutti i record nel snapshot disponibile).

Se `ente` non è fornito, chiedi all'utente. Se l'utente conosce il codice fiscale dell'ente, preferirlo al nome (riduce i falsi positivi).

## Strategia strumenti

Vedi [../shared/strategia-strumenti.md](../shared/strategia-strumenti.md).

### Sequenza di interrogazione

1. **Aggregati per anno e CPV** (OBBLIGATORIO):
   - `anac_sa_history(cf_or_name="<ente>")`
   - Restituisce `total_awards` (totale aggiudicazioni) e `by_year_cpv` (lista di record con campi `anno`, `cpv`, `cpv_descr`, `n`, `totale_aggiudicato`).
   - Usa `by_year_cpv` per costruire "Volume affidamenti" (aggregando per `anno`) e "Top CPV" (aggregando per `cpv`).

2. **Record individuali per fornitori e stagionalità** (OBBLIGATORIO):
   - `anac_search_awards(query="<ente>", limit=50)`
   - Restituisce record individuali con campi `aggiudicatario`, `piva_aggiudicatario`, `importo_aggiudicato`, `data_aggiudicazione`, `oggetto`, `cig`.
   - Usa per costruire "Top fornitori" (raggruppa per `aggiudicatario`) e "Stagionalità" (raggruppa per mese di `data_aggiudicazione`).

### Copertura dati

Entrambi i tool leggono uno **snapshot mensile** di ANAC (non la storia completa). La copertura temporale è limitata alla finestra dello snapshot — dichiararla nella sezione `## Metodologia`.

### Cold start e gestione errori

`anac_sa_history` e `anac_search_awards` condividono le tabelle `aggiudicazioni` e `cig`: il cold start (~70-300 s) si paga **una sola volta** alla prima chiamata; la seconda è veloce (cache hit). Non invocarli in parallelo.

Se la prima chiamata ANAC va in timeout o restituisce errore, emetti `## Dati non disponibili` e fermati — non ritentare il download.

## Formato dell'output

Segui il formato definito in references/output-format.md.

## Regole invarianti

- La prima riga dell'output è sempre: `Dati letti il YYYY-MM-DD`
- Non esporre i nomi degli strumenti MCP nell'output finale.
- Le sezioni `## Metodologia` e `## Audit trail` sono sempre presenti.
- `## Audit trail` contiene un **blocco fenced** (` ``` `), non una tabella markdown.
- Se entrambi i tool restituiscono zero risultati, aggiungi una sezione `## Dati non disponibili` che dichiara esplicitamente che l'ente non è presente negli archivi ANAC consultati.
