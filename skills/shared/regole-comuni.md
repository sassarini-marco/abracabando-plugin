# Regole essenziali — comuni a tutte le skill

Queste regole si applicano a tutte le skill del plugin:

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