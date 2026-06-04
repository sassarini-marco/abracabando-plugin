# Regole essenziali — comuni a tutte le skill

Queste regole si applicano a tutte le skill del plugin:

- **Il documento markdown si apre con la riga `Dati letti il YYYY-MM-DD`.**
  Evita preamboli e meta-commenti (es. «Ho tutti i dati», «Produco il report»):
  vai dritto al documento. È tollerata al massimo una breve frase introduttiva,
  ma l'intestazione `Dati letti il` deve comparire entro le prime righe.

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

## Contenuto minimo dell'`## Audit trail`

Ogni skill struttura l'audit trail a modo suo (vedi il `references/output-format.md`
della singola skill), ma il blocco fenced deve **sempre** contenere almeno:

- le query / chiamate effettuate, con i parametri essenziali;
- `tool_preferito: "pro" | "free"` — quale livello di strumenti è stato usato;
- `fallback_attivato: "si" | "no"` — se è scattato il passaggio da pro a free
  (vedi `strategia-strumenti.md`);
- `data_lettura: YYYY-MM-DD`;
- `timestamp` in formato ISO 8601.

Registrare il livello e l'eventuale fallback rende l'output riproducibile e
spiega perché due esecuzioni della stessa richiesta possono divergere.