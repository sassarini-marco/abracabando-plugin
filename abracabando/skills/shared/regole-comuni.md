# Regole essenziali — comuni a tutte le skill

Queste regole si applicano a tutte le skill del plugin:

- **Il documento markdown si apre con la riga `Dati letti il YYYY-MM-DD`.**
  Evita preamboli e meta-commenti (es. «Ho tutti i dati», «Produco il report»):
  vai dritto al documento. È tollerata al massimo una breve frase introduttiva,
  ma l'intestazione `Dati letti il` deve comparire entro le prime righe.

- **Quando uno strumento restituisce un testo che inizia con `LIMITE_PIANO_FREE:`**
  (oppure arriva come tool result con `isError: true` e contenuto che inizia con
  quel prefisso), interrompi **immediatamente** qualsiasi ulteriore chiamata,
  completa il documento con i dati **già ottenuti** e aggiungi questa sezione
  (non usare `## Dati non disponibili` per questo caso):

  ```
  ## Limite piano free

  <testo restituito dallo strumento>

  **Sezioni incomplete:** <elenca le fonti che non hai ancora interrogato,
  es. "TED non interrogato, ANAC non interrogato">

  **Cosa è già disponibile:** <elenca le sezioni del documento già compilate,
  es. "Programmazione regionale presente, PIN TED presenti">
  ```

  Il testo dello strumento contiene già: notifica del limite, conferma che i
  dati già ottenuti rimangono validi, istruzioni di riavvio, e nota sulla cache
  dei file ANAC/OpenCoesione. Non duplicare nessuno di questi contenuti.
  Il valore aggiunto della skill è solo l'elenco specifico delle fonti incomplete
  e di quelle già compilate, che lo strumento non può conoscere.

- **Quando uno strumento Consip restituisce `"status": "layout_unrecognized"`**,
  aggiungi la sezione seguente (prima di `## Dati non disponibili`) e prosegui
  con le altre fonti disponibili:

  ```
  ## Avviso: dati Consip non disponibili
  La pagina Consip non ha restituito dati strutturati riconoscibili (layout
  probabilmente modificato). Le sezioni Consip di questo documento potrebbero
  essere incomplete. Per i dati più aggiornati consulta direttamente
  <search_url restituito dallo strumento>.
  ```

  Non emettere questo avviso per risultati vuoti normali (`count: 0` con
  `status: "ok"`): zero risultati è un esito valido, non un errore tecnico.

- **Quando manca un parametro obbligatorio** (es. nessun CIG/CUP/ente fornito
  e la skill non può avviare la ricerca senza), **chiedi all'utente** di
  specificarlo — non emettere un documento vuoto e inutile.

- **Quando la ricerca va a vuoto** (zero risultati), **suggerisci come
  raffinare**: un identificatore più specifico, un filtro di regione/CPV/data,
  o indica quali record approfondire. Non inventare dati e non emettere una
  scheda fittizia.

- **Quando un record specifico richiesto non è disponibile** nonostante la
  ricerca abbia prodotto altri risultati, emetti `## Dati non disponibili`
  che spiega cosa manca e perché.
- Scrivi **solo** sulla base dei dati restituiti dagli strumenti.
- Non inventare dati, importi, URL, scadenze, nomi di enti o fornitori.
- Se un dato non è disponibile nei risultati restituiti, dichiaralo esplicitamente nella sezione `## Dati non disponibili`.
- Non emettere JSON come output finale (JSON è ammesso solo per passaggi interni di elaborazione dati non visibili all'utente).
- L'output finale è sempre in italiano.
- L'unico blocco di codice ammesso nell'output è quello della sezione `## Audit trail`.

## Costo degli strumenti ANAC e gestione del cold start (free tier)

Gli strumenti ANAC record-level scaricano snapshot mensili alla prima chiamata
della conversazione e possono impiegare 70–300 secondi. Le tabelle sono
**condivise** tra tutti gli strumenti ANAC: una volta che un qualsiasi strumento
ANAC ha completato, gli altri leggono la cache e rispondono in pochi secondi.

- **Numero di tabelle per strumento** (impatto sul cold start):
  - 2 tabelle: `anac_sa_history`
  - 3 tabelle: `anac_search_awards`, `anac_awards_by_piva`
  - 4 tabelle: `anac_award_detail`, `anac_awards_by_cup`
- **Non invocare mai due strumenti ANAC in parallelo**: la cache non ha lock
  e due download simultanei della stessa tabella saturano il server. Attendi
  che la prima chiamata ANAC completi prima di invocarne una seconda.
- **In caso di timeout o errore su uno strumento ANAC**: emetti
  `## Dati non disponibili` con il messaggio d'errore e prosegui con le
  altre fonti già ottenute. Non ritentare: un retry paga di nuovo il cold
  start e rischia di esaurire il budget della conversazione.

## Costo nascosto degli strumenti multi-pagina

- `openpnrr_search_progetti(cup=...)` esegue fino a **6 chiamate HTTP interne**
  (scansione client-side di 6 pagine da 500 record). Non ritentare se il CUP
  non è trovato: il tool lo segnala con `cup_filter_supported: false`.
- `opencoesione_project_by_cup(cup=...)` scarica fino a **3 file Parquet** (uno
  per ciclo 2021-2027, 2014-2020, 2007-2013) al primo utilizzo nella
  conversazione, poi legge la cache. Trattalo come strumento a costo medio,
  non leggero.

## Contenuto minimo dell'`## Audit trail`

Ogni skill struttura l'audit trail a modo suo (vedi il `references/output-format.md`
della singola skill), ma il blocco fenced deve **sempre** contenere almeno:

- le query / chiamate effettuate, con i parametri essenziali;
- `server_tier: "pro" | "free"` — tier rilevato dalla capability probe;
- `tool_preferito: "pro" | "free"` — quale livello di strumenti è stato usato;
- `fallback_attivato: "si" | "no"` — se è scattato il passaggio da pro a free
  (vedi `strategia-strumenti.md`);
- `data_lettura: YYYY-MM-DD`;
- `timestamp` in formato ISO 8601.

Registrare il livello e l'eventuale fallback rende l'output riproducibile e
spiega perché due esecuzioni della stessa richiesta possono divergere.