---
name: analisi-disciplinare
description: Scarica e analizza un disciplinare o capitolato tecnico di gara (PDF o HTML), estrae i criteri di valutazione (punteggi offerta tecnica/economica), identifica i requisiti di partecipazione e produce una scheda strutturata in italiano con piena provenance. Usa questa skill ogni volta che l'utente ha l'URL di un documento di gara e vuole capire come viene valutata l'offerta, quanti punti valgono i singoli criteri tecnici/economici, o se l'azienda può partecipare — anche se chiede "analizza questo capitolato", "quanti punti vale l'offerta tecnica?", "dimmi i requisiti di partecipazione".
argument-hint: "<URL documento> [CIG per contesto]"
disable-model-invocation: true
allowed-tools:
  - mcp__industrial-mcp-pro__document_fetch_text
  - mcp__industrial-mcp-pro__anac_award_detail
  - mcp__industrial-mcp-free__document_fetch_text
  - mcp__industrial-mcp-free__anac_award_detail
---

# Analisi Disciplinare

Usa questa skill solo per richieste su:
- analisi di un documento di gara (disciplinare, capitolato tecnico, lettera di invito);
- estrazione dei criteri di valutazione e dei punteggi tecnica/economica;
- verifica dei requisiti di partecipazione (fatturato, certificazioni, SOA).

## Obiettivo

Produrre una scheda di analisi del documento di gara in italiano formale che:
1. estragga e tabelli i criteri di valutazione (punteggi offerta tecnica / economica) **leggendo direttamente il testo del documento**;
2. identifichi il criterio di aggiudicazione (OEPV o minor prezzo);
3. raccolga i requisiti di partecipazione rilevanti dal testo;
4. segnali esplicitamente quando dati non sono presenti o riconoscibili nel documento;
5. includa sempre le sezioni Dati non disponibili e Audit trail.

## Regole essenziali

Vedi [../shared/regole-comuni.md](../shared/regole-comuni.md).

**Regole critiche di questa skill — non derogabili:**
- **Non inventare mai punteggi, requisiti o criteri.** Riporta esclusivamente valori esplicitamente scritti nel testo del documento. Se un numero di punti non è dichiarato nel testo, non inferirlo.
- **Esaustività:** leggi l'intero testo restituito da `document_fetch_text` e cerca tutti i criteri di valutazione, incluse tabelle flattened dove il numero precede la parola "punti" (es. "max 15\npunti\n(D)"), criteri inline (es. "(max punti 3)"), e clausole premiali (parità di genere, certificazioni).
- **Somma di verifica:** dopo aver estratto tutti i sub-criteri dell'offerta tecnica, sommali e confronta con il totale dichiarato. Se non coincidono, segnalalo esplicitamente nella tabella con una riga ⚠️ — non aggiustare i numeri.
- **Confidenza:** usa `Alta` se hai estratto il totale tecnica + economica e sommano a 100; `Media` se estratti parzialmente; `Bassa` se il documento non è un disciplinare o non contiene criteri.
- Se il documento è scansionato o `document_fetch_text` restituisce `error`, dichiara l'impossibilità in `## Dati non disponibili` e suggerisci alternative.
- Non costruire URL dalla memoria — usa solo quelli restituiti dagli strumenti o forniti dall'utente.
- L'`## Audit trail` è **sempre** un blocco di codice fenced (` ```text ... ``` `), mai una tabella markdown.

## Estrazione input

Estrai:
- `url`: URL diretto al documento (PDF o pagina HTML). **Obbligatorio.** Se assente, chiedi all'utente.
- `cig`: Codice Identificativo Gara, opzionale. Se presente, usa `anac_award_detail` per arricchire il contesto (oggetto, stazione appaltante, importo).

Se non è fornito alcun URL, non procedere: chiedi all'utente di incollare il link al documento.

## Strategia strumenti

Vedi [../shared/strategia-strumenti.md](../shared/strategia-strumenti.md).

### Sequenza di interrogazione

1. **(OPZIONALE) Contesto ANAC** — esegui solo se `cig` è fornito:
   - `anac_award_detail(cig="<cig>")` per recuperare oggetto, stazione appaltante, importo base d'asta.

2. **(OBBLIGATORIO) Fetch del documento**:
   - `document_fetch_text(url="<url>")` con parametri di default.
   - Se restituisce `error`: documenta in `## Dati non disponibili` con il messaggio d'errore. **Interrompi qui.**
   - Se `truncated: true`: segnalalo — i criteri nelle ultime pagine potrebbero mancare.

3. **(OBBLIGATORIO) Lettura e analisi diretta del testo**:
   - Leggi il campo `text` restituito da `document_fetch_text`.
   - Identifica la sezione criteri di valutazione (di solito "Criteri di aggiudicazione", "Offerta tecnica", "Tabella valutazione").
   - Estrai: criterio OEPV/minor prezzo, punteggi totali tecnica/economica, tutti i sub-criteri con punteggio esplicito.
   - Cerca pattern multipli: tabelle flattened (numero prima di "punti"), clausole inline ("(max punti N)"), clausole premiali.
   - Identifica sezioni requisiti: "Requisiti di idoneità", "Capacità tecnica e professionale", "Capacità economica e finanziaria".

## Formato dell'output

Segui il formato definito in references/output-format.md.

## Regole invarianti

- La prima riga dell'output è sempre: `Dati letti il YYYY-MM-DD`
- Le sezioni `## Dati non disponibili` e `## Audit trail` sono sempre presenti.
- Non esporre i nomi degli strumenti MCP nell'output finale.
- Non emettere JSON nell'output visibile all'utente.
- La confidenza usa esclusivamente i valori `Alta`, `Media`, `Bassa` — mai percentuali o numeri.
