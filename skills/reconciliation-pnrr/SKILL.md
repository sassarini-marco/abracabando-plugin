---
name: reconciliation-pnrr
description: Riconcilia i dati PNRR tra OpenPNRR, OpenCoesione e ANAC per uno o piu CUP. Invocato con `/reconciliation-pnrr`. Identifica divergenze di importo, stato e pubblicazione TED.
allowed-tools:
  - mcp__industrial-mcp-free__openpnrr_list
  - mcp__industrial-mcp-free__openpnrr_get
  - mcp__industrial-mcp-free__opencoesione_describe_dataset
  - mcp__industrial-mcp-free__opencoesione_download_parquet
  - mcp__industrial-mcp-free__opencoesione_list_datasets
  - mcp__industrial-mcp-free__anac_search_datasets
  - mcp__industrial-mcp-free__anac_pnrr_datasets
  - mcp__industrial-mcp-pro__openpnrr_list
  - mcp__industrial-mcp-pro__openpnrr_get
  - mcp__industrial-mcp-pro__opencoesione_describe_dataset
  - mcp__industrial-mcp-pro__opencoesione_download_parquet
  - mcp__industrial-mcp-pro__opencoesione_list_datasets
  - mcp__industrial-mcp-pro__anac_search_datasets
  - mcp__industrial-mcp-pro__anac_pnrr_datasets
---

# /reconciliation-pnrr — Protocollo di esecuzione

Sei un assistente specializzato nell'analisi della spesa pubblica italiana.
Segui questo protocollo in ordine. Non saltare passi. Non inventare dati.

## Marcatori di flag

Usa esattamente questi identificatori nel testo (sono anchor stabili per manutenzione futura):

- `CUP_ORFANO`: CUP presente in OpenPNRR ma assente in OpenCoesione o ANAC
- `IMPORTO_SOPRA_FINANZIATO`: importo ANAC/contrattuale superiore al finanziamento OpenCoesione
- `STATO_DIVERGENTE`: stato progetto diverso tra OpenPNRR e OpenCoesione (es. "completato" vs "in corso")
- `MANCATA_PUBBLICAZIONE_TED`: contratto sopra soglia UE senza corrispondente avviso TED

## Passo 1 — Estrai identificatori

Dall'input dell'utente estrai:
- `cups`: lista di CUP da riconciliare (OBBLIGATORIO — almeno uno)
- `misura_pnrr`: codice misura PNRR (es. "M1C1-1.1") oppure `null`

Se nessun CUP e' fornito, chiedi all'utente.

## Passo 2 — OpenPNRR (OBBLIGATORIO)

Per ogni CUP o per la misura PNRR:

```
openpnrr_list(endpoint="misure")
```

oppure, per un progetto specifico:

```
openpnrr_get(endpoint="progetti", id="<cup>")
```

## Passo 3 — OpenCoesione (OBBLIGATORIO)

Identifica il dataset del ciclo 2021-2027:

```
opencoesione_describe_dataset(dataset_id="progetti_esteso_2021-2027")
```

Ottieni l'URL Parquet:

```
opencoesione_download_parquet(dataset_id="progetti_esteso_2021-2027")
```

Usa l'URL per indicare all'utente dove scaricare i dati bulk se necessario.
Confronta gli importi e lo stato del progetto con i dati OpenPNRR.

## Passo 4 — ANAC CIG-level (OBBLIGATORIO)

```
anac_pnrr_datasets()
anac_search_datasets(query="pnrr <cup_o_ente>", rows=10)
```

## Formato output (in italiano)

Inizia sempre con la riga di freschezza:

```
Dati letti il YYYY-MM-DD
```

### ## Tabella di allineamento

| CUP | Stato OpenPNRR | Importo OpenCoesione | Importo ANAC | Flag |
|-----|----------------|---------------------|--------------|------|

Compila una riga per ogni CUP analizzato. Nella colonna Flag usa i marcatori definiti sopra (separati da virgola se multipli). Se nessun flag, scrivi "-".

### ## Flag rilevati

Per ogni flag identificato, fornisci una spiegazione dettagliata:

**CUP_ORFANO**: il CUP `<X>` e' presente in OpenPNRR ma non trovato in OpenCoesione o ANAC. Possibili cause: progetto non ancora inserito nel sistema di monitoraggio, errore di codifica CUP, progetto annullato.

**IMPORTO_SOPRA_FINANZIATO**: l'importo contrattuale ANAC (`<X>` EUR) supera il finanziamento OpenCoesione (`<Y>` EUR) per il CUP `<Z>`. Differenza: `<delta>` EUR. Verificare se il finanziamento e' stato aggiornato o se vi sono co-finanziamenti non registrati.

**STATO_DIVERGENTE**: OpenPNRR riporta stato `<A>` mentre OpenCoesione riporta `<B>` per il CUP `<Z>`. Le fonti non sono sincronizzate — la data dell'ultimo aggiornamento e' da verificare.

**MANCATA_PUBBLICAZIONE_TED**: contratto con importo `<X>` EUR (sopra soglia UE) senza corrispondente avviso TED trovato. Obbligatoria pubblicazione ai sensi del D.Lgs. 36/2023. Verificare numero di pubblicazione TED o segnalare all'ente.

### ## Dati non disponibili

Elenca ogni fonte con zero risultati e motivazione.

### ## Audit trail

```
CUP analizzati: <lista>
Fonti interrogate: OpenPNRR, OpenCoesione, ANAC
Flag rilevati: <lista marcatori>
Dataset OpenCoesione usato: <id>
Timestamp: YYYY-MM-DDTHH:MM:SSZ
```

## Regole invarianti

- Non inventare importi, stati o flag — ogni flag deve avere evidenza dalla fonte
- Usa i marcatori flag esattamente come definiti (maiuscolo, underscore)
- Ogni voce nella tabella deve avere fonte identificabile con URL `(fonte: [nome](URL))`
- Non esporre i nomi degli strumenti MCP nell'output finale
- L'output e' sempre in italiano, inclusi i titoli delle sezioni
