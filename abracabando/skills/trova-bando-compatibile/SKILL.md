---
name: trova-bando-compatibile
description: "Data il profilo di un'azienda o stabilimento (settore CPV o ATECO, regione, dimensione, taglio contratti, certificazioni), trova i bandi pubblici aperti compatibili e li classifica per compatibilità. Usa questa skill ogni volta che l'utente chiede: quale gara fa per la mia azienda, bandi compatibili con il mio profilo, trova gare aperte per [settore], gare adatte a un'azienda [ATECO/settore], opportunità di gara per una fabbrica/PMI di [settore], quali appalti posso vincere — anche se non nomina esplicitamente CPV o ATECO."
argument-hint: "<CPV|ATECO> [regione] [taglio EUR min-max] [certificazioni]"
allowed-tools:
  - mcp__industrial-mcp-pro__server_capabilities
  - mcp__industrial-mcp-pro__ted_search
  - mcp__industrial-mcp-pro__consip_search_bandi
  - mcp__industrial-mcp-pro__programmazione_search_biennale
  - mcp__industrial-mcp-pro__anac_search_awards
  - mcp__industrial-mcp-free__server_capabilities
  - mcp__industrial-mcp-free__ted_search
  - mcp__industrial-mcp-free__consip_search_bandi
  - mcp__industrial-mcp-free__programmazione_search_biennale
  - mcp__industrial-mcp-free__anac_search_awards
---

# Trova Bando Compatibile

Usa questa skill solo per richieste su:
- ricerca di bandi aperti compatibili con il profilo di un'azienda o stabilimento;
- matching settore/CPV/ATECO → opportunità di gara attive;
- classificazione bandi per compatibilità con capacità e certificazioni aziendali.

NON usare questa skill per analisi di un singolo bando già identificato
(usa `scheda-opportunita`) o per monitoraggio avanzato di TED PIN (usa `pin-radar`).

## Obiettivo

Produrre una nota di intelligence commerciale in italiano formale che:
1. identifichi i bandi pubblici aperti alla data odierna compatibili con il profilo aziendale;
2. li classifichi per Compatibilità complessiva (Alta / Media / Bassa) con evidenza per dimensione;
3. li ordini per Compatibilità decrescente, poi per scadenza crescente;
4. indichi chiaramente le dimensioni con criticità (warning nominati);
5. includa fonti, dati non disponibili e audit trail.

## Regole essenziali

Vedi [../shared/regole-comuni.md](../shared/regole-comuni.md).

## Estrazione input

Estrai dal testo dell'utente:

- `settore_cpv`: codice CPV o famiglia (es. `44000000` fabbricazione strutture metalliche,
  `45000000` lavori, `72000000` IT) — **obbligatorio se non fornito ATECO**;
- `ateco`: codice ATECO dell'azienda (es. `25.11` = strutture metalliche) —
  **obbligatorio se non fornito CPV**;
- `regione`: nome regione italiana (es. `Lombardia`) o `null`;
- `nuts_code`: codice NUTS-2 corrispondente (es. `ITC4`) o `null` — derivalo
  dalla regione usando la tabella in references/nuts-mapping.md;
- `taglio_min_eur`: importo minimo gestibile in EUR o `null`;
- `taglio_max_eur`: importo massimo gestibile in EUR o `null`;
- `dimensione_impresa`: `micro` / `piccola` / `media` / `grande` o `null`;
- `certificazioni`: lista di certificazioni dichiarate (es. `["SOA OG1", "ISO 9001"]`) o `[]`.

**Se né `settore_cpv` né `ateco` sono forniti**, chiedi all'utente di specificare
almeno uno dei due prima di procedere.

### Inferenza ATECO → CPV

Se l'utente fornisce un codice ATECO ma non CPV, mappa al CPV più probabile usando
la tua conoscenza (es. ATECO 25 → CPV 44000000/45000000; ATECO 62 → CPV 72000000).
Segnala questa inferenza nell'output come **Media confidenza — da verificare** e
registrala nell'`## Audit trail` con il campo `ateco_to_cpv_inference`.

## Strategia strumenti

Vedi [../shared/strategia-strumenti.md](../shared/strategia-strumenti.md).

### Ambito temporale: solo bandi aperti per default

Questa skill restituisce **solo bandi aperti alla data odierna**. Includi risultati
storici solo se l'utente li richiede esplicitamente ("incluse gare chiuse", "storico").

Aggiungi questa riga all'inizio dell'output (subito dopo `Dati letti il`):
> Ambito: solo bandi aperti alla data odierna. Per includere gare storiche/chiuse,
> ripeti la richiesta con "incluse gare chiuse".

Registra nell'`## Audit trail`: `ambito_temporale: "solo_aperti"` oppure
`"incluso_storico"` se richiesto esplicitamente.

### Sequenza di interrogazione

1. **TED** (SEMPRE — priorità primaria):
   - `ted_search(query="cpv=<cpv_family> AND place-of-performance=ITA", limit=<max_results>)`
   - Se disponibile nuts_code: aggiungi `AND nuts-code=<nuts_code>` alla query
   - `scope="ACTIVE"` è il default — restituisce solo avvisi attivi; non modificarlo
     salvo richiesta esplicita storico.

2. **Consip bandi** (SEMPRE — bandi nazionali):
   - `consip_search_bandi(query="<settore_query>", stage="bando")`
   - `stage="bando"` filtra lato server ai soli bandi formalmente aperti.
   - Controlla il campo `status` del risultato: se `"layout_unrecognized"`, applica
     la regola `## Avviso: dati Consip non disponibili` di `regole-comuni.md`.

3. **Programmazione regionale** (SEMPRE — opportunità in arrivo):
   - `programmazione_search_biennale(cpv=<cpv>, regione=<regione>, anno=<anno_corrente>)`
   - Questi sono piani futuri, non bandi già pubblicati; classificali come
     "pianificato" con confidenza adeguata.

4. **ANAC storico** (FACOLTATIVO — solo per calibrare il taglio tipico):
   - Solo se il budget lo consente **dopo** i passi 1–3.
   - `anac_search_awards(cpv_prefix=<cpv_prefix>, region=<regione>, limit=<max_results>)`
   - I dati ANAC sono aggiudicazioni **già chiuse** — usa solo per stimare l'importo
     tipico dei contratti in quel settore/regione. NON presentarli come bandi aperti.

**PNRR**: non interrogare. Il programma è in fase di chiusura; le opportunità
rimanenti sono marginali rispetto a TED, Consip e programmazione.

## Regole di compatibilità

Valuta ogni bando lungo **quattro dimensioni**:

| Dimensione | Alta | Media | Bassa |
|---|---|---|---|
| **CPV match** | prefisso CPV esatto (≥ 6 cifre corrispondenti) | stessa famiglia (prime 2 cifre) | CPV correlato ma diversa famiglia |
| **Geografia** | regione richiesta (o nazionale se no regione) | regione confinante | fuori area dichiarata |
| **Taglio importo** | importo bando dentro `[taglio_min, taglio_max]` | entro ±50% dei limiti | fuori range dichiarato |
| **Idoneità** | requisiti compatibili con dimensione/certificazioni dichiarate | parzialmente compatibili | requisito chiave chiaramente incompatibile |

**Dati mancanti:** se una dimensione non è valutabile per mancanza di dati
(es. importo non pubblicato, certificazioni richieste non note), scrivi
`"non valutabile (dato assente)"` — NON inventare Bassa.

**Punteggio complessivo:**
- Calcola la moda delle dimensioni **valutate** (escludi "non valutabile").
- Se parità: `Alta` se ≥ 2 Alta, altrimenti `Media`.
- Se tutte le dimensioni sono "non valutabile": `Media confidenza` con nota.

**Warning nominati:** per ogni dimensione con giudizio `Bassa`, aggiungi un
avviso esplicito alla riga del bando, es.:
`⚠️ Idoneità: verifica certificazione SOA OG1 cat. IX richiesta (da verificare).`

Non affermare mai che l'azienda possiede o non possiede una certificazione
specifica — usa sempre "da verificare".

## Selezione e ranking

- Includi tutti i bandi con Compatibilità complessiva Alta e Media.
- Includi Bassa solo se non ci sono risultati Alta/Media, oppure come sezione
  separata `## Altri bandi trovati — compatibilità bassa`.
- Ordina: Compatibilità Alta → Media → Bassa; a parità, scadenza crescente (prima le più urgenti).
- Massimo 10 bandi analizzati in esteso. Se ne trovi di più, aggiungi
  `## Altri bandi trovati ma non analizzati` con elenco tabellare (titolo, ente, scadenza, fonte).

## Formato dell'output

Segui il formato definito in references/output-format.md.

Se serve un esempio completo, consulta examples/example-output.md.

## Regole invarianti

- La prima riga dell'output è sempre: `Dati letti il YYYY-MM-DD`
- Seconda riga (dopo `Dati letti il`): disclosure ambito temporale (vedi sopra).
- Per ogni bando: titolo, ente, scadenza, importo stimato (se disponibile), CPV,
  fonte URL restituita dallo strumento, Compatibilità complessiva, warning per
  dimensioni Bassa.
- Usa etichette qualitative: `Alta` / `Media` / `Bassa` — mai percentuali o punteggi.
- Non esporre i nomi degli strumenti MCP nell'output finale.
- Le sezioni `## Fonti`, `## Dati non disponibili` e `## Audit trail` sono sempre presenti.
- Se `status: "layout_unrecognized"` da Consip, aggiungi `## Avviso: dati Consip non disponibili` (da `regole-comuni.md`).
- Se zero bandi trovati: emetti documento completo con disclosure, `## Dati non disponibili` (spiega per quale fonte) e `## Audit trail`. Non inventare bandi.
- `## Audit trail` contiene un **blocco fenced** con almeno: query effettuate,
  `ateco_to_cpv_inference` (se applicabile), `ambito_temporale`, `server_tier`,
  `tool_preferito`, `fallback_attivato`, `data_lettura`, `timestamp`.
