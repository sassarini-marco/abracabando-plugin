# Formato output — Reconciliation PNRR

L'output è un report di riconciliazione in italiano formale.

## Prima riga
`Dati letti il YYYY-MM-DD`

## Titolo
`# Reconciliation PNRR — [N] CUP analizzati`

---

## `## Tabella di allineamento`

| CUP | Stato OpenPNRR | Importo OpenCoesione | Importo ANAC | Flag |
|-----|----------------|---------------------|--------------|------|
| [CUP] | [stato] | EUR [importo] | EUR [importo] | [flag] |

Compila una riga per ogni CUP analizzato.

Nella colonna **Flag** usa i marcatori definiti (separati da virgola se multipli). Se nessun flag, scrivi `"-"`.

---

## `## Flag rilevati`

Per ogni flag identificato, fornisci una spiegazione dettagliata.

Consulta references/flag-explanations.md per il formato delle spiegazioni.

---

## `## Dati non disponibili`

Sezione sempre presente.

Elenca ogni fonte con zero risultati e motivazione.

Esempio:
- OpenPNRR: CUP X non trovato — possibile errore di codifica o progetto non ancora inserito;
- OpenCoesione: dataset ciclo 2021-2027 non restituito — verifica disponibilità dataset;
- ANAC: nessun CIG trovato per CUP Y — il bando potrebbe non essere ancora stato pubblicato.

---

## `## Audit trail`

Sezione sempre presente.

Blocco di codice fenced:

```text
CUP analizzati: <lista>
Fonti interrogate: OpenPNRR, OpenCoesione, ANAC
Flag rilevati: <lista marcatori>
Dataset OpenCoesione usato: <id>
Timestamp: YYYY-MM-DDTHH:MM:SSZ
```
