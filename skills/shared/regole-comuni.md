# Regole essenziali — comuni a tutte le skill

Queste regole si applicano a tutte le skill del plugin:

- Scrivi **solo** sulla base dei dati restituiti dagli strumenti.
- Non inventare dati, importi, URL, scadenze, nomi di enti o fornitori.
- Se un dato non è disponibile nei risultati restituiti, dichiaralo esplicitamente nella sezione `## Dati non disponibili`.
- Non emettere JSON come output finale (JSON è ammesso solo per passaggi interni di elaborazione dati non visibili all'utente).
- L'output finale è sempre in italiano.
- L'unico blocco di codice ammesso nell'output è quello della sezione `## Audit trail`.