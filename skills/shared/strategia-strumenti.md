# Strategia strumenti — preferenza pro con fallback free

Tutte le skill seguono questa strategia di invocazione strumenti:

Preferisci sempre gli strumenti **pro** (prefisso `mcp__industrial-mcp-pro__`).

Usa gli strumenti **free** (prefisso `mcp__industrial-mcp-free__`) **solo** come fallback se:
- lo strumento pro fallisce con errore;
- oppure restituisce errore HTTP (400, 500, timeout);
- oppure restituisce zero risultati quando ci si aspetterebbe almeno un risultato.

Questa strategia bilancia affidabilità (pro) con resilienza (free come fallback).