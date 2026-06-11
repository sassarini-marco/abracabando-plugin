---
name: pin-radar
description: Monitora i Prior Information Notice (PIN) pubblicati su TED per l'Italia, filtrabili per CPV e macro-regione NUTS, e produce una nota decisionale con priorità operative, risultati analizzati in esteso, audit trail e mappatura NUTS. Usa questa skill ogni volta che l'utente parla di avvisi preliminari o di preinformazione europei, segnali o scouting pre-gara su TED, indagini di mercato sopra-soglia UE, "pre-gare europee", o vuole capire quali gare sopra-soglia stanno per uscire in Italia in un certo settore o regione — anche se non nomina esplicitamente "PIN" o "TED".
argument-hint: "[CPV] [regione/NUTS]"
disable-model-invocation: true
allowed-tools:
  - mcp__industrial-mcp-pro__server_capabilities
  - mcp__industrial-mcp-pro__ted_pin_italy
  - mcp__industrial-mcp-free__server_capabilities
  - mcp__industrial-mcp-free__ted_pin_italy
  - Bash
---

# PIN Radar

Usa questa skill solo per richieste su:
- Prior Information Notice (PIN) pubblicati su TED;
- avvisi preliminari di gara europea;
- segnali pre-gara per appalti sopra-soglia EU in Italia;
- consultazioni preliminari di mercato pubblicate su TED.

## Obiettivo

Produrre una nota di intelligence in italiano formale che:
1. recuperi PIN rilevanti da TED per l'Italia;
2. li classifichi per priorità operativa (Alta / Media / Bassa);
3. evidenzi le azioni commerciali raccomandate;
4. distingua chiaramente tra risultati analizzati in esteso e quelli tabulari;
5. includa sempre limiti della ricerca e audit trail.

## Regole essenziali

Vedi [../shared/regole-comuni.md](../shared/regole-comuni.md).

## Estrazione input

Estrai:
- `cpv_codes`: lista di codici CPV (es. `["72000000"]`) oppure `null`;
- `nuts_region`: codice NUTS-1 (es. `"ITI"` per tutto il Centro) o NUTS-2 (es. `"ITC4"` per Lombardia) oppure `null`;
- `deadline_before`: data limite consultazione in formato `YYYYMMDD` oppure `null` (se `null`, nessun filtro sulla scadenza — il tool restituisce tutti i PIN ACTIVE; specificare un valore se si vuole limitare l'orizzonte temporale).

Se nessun parametro è fornito, chiedi almeno un CPV o una regione.

### Mappatura NUTS

Usa la tabella in references/nuts-mapping.md per convertire nomi di regione in codici NUTS-2.

### Verifica famiglia CPV

Usa la tabella in references/cpv-families.md per verificare che il CPV corrisponda al settore dichiarato dall'utente.

Se il CPV non corrisponde (es. utente chiede "software gestionale" ma il CPV è `48210000` = "Networking software package" su TED), aggiungi una nota in `## Copertura della ricerca e limiti` ma prosegui con il CPV fornito.

## Strategia strumenti

Vedi [../shared/strategia-strumenti.md](../shared/strategia-strumenti.md).

### Parametri fissi
- `limit`: 10 per pagina (evita overflow parsing);
- `page`: 1. **Recupera SOLO la prima pagina.** Non scorrere automaticamente le
  pagine successive: analizzare decine di PIN in un'unica esecuzione è lento e
  raramente utile.

### Troppi risultati — chiedi all'utente di raffinare

Se la prima pagina è piena (10 PIN restituiti) e la risposta indica altri
risultati disponibili (`next_offset` valorizzato o `total` molto maggiore di 10),
**non** recuperare altre pagine. Invece:

1. analizza e classifica solo i PIN della prima pagina;
2. aggiungi una sezione `## Affina la ricerca` che riporta il numero totale
   stimato di PIN e invita l'utente a restringere il lookup, indicando le leve
   disponibili: un **CPV più specifico** (es. `72212000` invece di `72000000`),
   una **regione NUTS**, una **scadenza** (`deadline_before`), oppure di indicare
   **quali PIN approfondire** tra quelli elencati.

Così l'utente decide su quali PIN concentrare l'analisi, invece di ricevere una
nota dispersiva su decine di risultati.

### Gestione output file troppo grande

Se `ted_pin_italy` restituisce un **file path** invece di dati diretti (segnale: tool result contiene "Output has been saved to /path/to/file"), usa Bash+jq:

```bash
jq '.items[:10] | .[] | {publication_number, buyer: (.buyer // "n/a"), cpv: (.cpv[0] // "n/a"), title, publication_date, deadline}' <file_path>
```

Estrae: primi 10 PIN con campi essenziali.

Se result è un oggetto Page normale (contiene `.items` direttamente), usa `result.items`.

### Gestione errori

Se `ted_pin_italy` restituisce errore (400, 500, timeout), documenta in `## Copertura della ricerca e limiti` ed emetti output markdown completo con sezioni PIN vuote.

## Classificazione risultati

Classifica ogni PIN in una sola categoria:
- `Alta priorità`
- `Media priorità`
- `Bassa priorità`

Criteri:
- **Alta**: scadenza imminente (< 30 giorni), importo indicato, CPV pienamente coerente, ente storico per il settore;
- **Media**: scadenza non imminente, importo non indicato, CPV parzialmente pertinente, ente che pubblica raramente;
- **Bassa**: PIN pubblicato da oltre 3 mesi senza aggiornamenti, CPV marginale, ente non rilevante.

## Selezione dei risultati

Per ogni categoria di priorità:
- **Alta priorità**: analizza in esteso i **primi 5** PIN; gli ulteriori PIN (se presenti) appaiono in `### Altri PIN ad alta priorità non analizzati in esteso` con formato tabellare (una riga per PIN: ente, oggetto breve, scadenza, fonte).
- **Media priorità**: analizza in esteso i **primi 5** PIN; gli ulteriori PIN (se presenti) appaiono in `### Altri PIN a media priorità non analizzati in esteso` con formato tabellare.
- **Bassa priorità**: **sempre** tabella riassuntiva, nessuna scheda estesa.

## Formato dell'output

Segui il formato definito in references/output-format.md.

Se serve un esempio completo, consulta examples/example-output.md.

## Regole invarianti

- La prima riga dell'output è sempre: `Dati letti il YYYY-MM-DD`
- Le sezioni di priorità appaiono sempre in questo ordine:
  1. `## PIN ad alta priorità — azione entro breve termine`
  2. `## PIN da monitorare — segnali di media rilevanza`
  3. `## Segnali deboli — bassa rilevanza`
- Una sezione senza risultati viene omessa.
- `## Dati non disponibili` e `## Audit trail` sono sempre presenti.
- `## Audit trail` contiene un **blocco fenced** (` ``` `), non una tabella markdown.
- `## Audit trail` include `ambito_temporale: "solo_aperti"` (`ted_pin_italy` restituisce PIN ACTIVE per default).
- Ogni PIN citato deve riportare: numero di pubblicazione TED (`NNNNNN-YYYY`), URL fonte restituito dallo strumento, data di lettura.
- Non esporre i nomi degli strumenti MCP nell'output finale.
- Se TED restituisce zero risultati, emetti comunque il documento completo con intestazione, sezioni vuote, `## Dati non disponibili` e `## Audit trail`.
