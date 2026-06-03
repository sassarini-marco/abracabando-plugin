# Strategia strumenti — preferenza pro con fallback free

Tutte le skill seguono questa strategia di invocazione strumenti:

Preferisci sempre gli strumenti **pro** (prefisso `mcp__industrial-mcp-pro__`).

Usa gli strumenti **free** (prefisso `mcp__industrial-mcp-free__`) **solo** come fallback se:
- lo strumento pro fallisce con errore;
- oppure restituisce errore HTTP (400, 500, timeout);
- oppure restituisce zero risultati quando ci si aspetterebbe almeno un risultato.

Questa strategia bilancia affidabilità (pro) con resilienza (free come fallback).

## Meccanica del fallback

Quando una delle condizioni sopra si verifica, **ri-invoca lo strumento free
equivalente con gli stessi identici parametri** (stesso nome di strumento senza
il prefisso, stessi argomenti). Esempio: se `mcp__industrial-mcp-pro__ted_search`
restituisce timeout, richiama `mcp__industrial-mcp-free__ted_search` con i
parametri invariati. Non modificare la query nel passaggio da pro a free: così
la differenza eventuale nei risultati è attribuibile alla fonte, non alla query.

Il server pro è attualmente un placeholder e risulta spesso disconnesso: in
quel caso il passaggio a free è atteso e non va segnalato come anomalia.

Registra sempre nell'`## Audit trail` quale livello hai effettivamente usato
(`tool_preferito: "pro" | "free"`) e se il fallback è scattato
(`fallback_attivato: "si" | "no"`).