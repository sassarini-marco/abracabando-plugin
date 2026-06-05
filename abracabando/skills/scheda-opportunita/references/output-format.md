# Formato output — Scheda Opportunità

L'output è una scheda di intelligence commerciale sugli appalti pubblici, redatta in italiano formale, strutturata come una nota informativa destinata a un direttore commerciale o account executive che deve decidere go/no-go su un'opportunità specifica.

## Prima riga
`Dati letti il YYYY-MM-DD`

## Titolo
`# Scheda opportunità — [Denominazione ufficiale completa dell'ente] · [Settore] (CPV [codice])`

---

## `## Sintesi incrociata TED-ANAC`

**Sezione obbligatoria, titolo esatto (mai numerato, mai rinominato).**

Contiene il verdetto complessivo e quattro campi di sintesi:

**PIN TED**: [numero di pubblicazione NNNNNN-YYYY oppure "nessuno trovato alla data di lettura"]  
**Storico ANAC acquirente**: [N aggiudicazioni CPV XX negli ultimi 24 mesi, importo aggregato EUR X.XXX.XXX]  
**Coerenza CPV**: [Alta / Media / Bassa] — [motivazione in una frase che spiega il grado di allineamento tra il CPV del PIN e lo storico di spesa dell'ente]  
**Valutazione trasformazione**: [Alta / Media / Bassa] — [evidenza esplicita: elementi che supportano la valutazione]  
Dati letti il [YYYY-MM-DD] · fonte TED  
Dati letti il [YYYY-MM-DD] · fonte ANAC

**VIETATO** per Coerenza CPV e Valutazione trasformazione:
- punteggi numerici (es. "9/10", "Score 95/100")
- percentuali (es. "82%")
- stelle
- aggettivi non corrispondenti ai tre valori ammessi

Usare **esclusivamente**: `Alta`, `Media`, `Bassa`.

### Paragrafo di valutazione complessiva
3-5 frasi:
- Verdetto go/no-go con motivazione principale;
- Come PIN TED e storico ANAC si integrano o contraddicono;
- Livello di rischio commerciale (concorrenza, importo incerto, tempistica non definita, ecc.).

### Paragrafo sulla finestra d'azione
2-3 frasi:
- Quanto tempo resta prima che la fase pre-gara si chiuda;
- Qual è il prossimo evento atteso (pubblicazione bando, scadenza consultazione, aggiudicazione gara in corso).

---

## `## Descrizione dell'opportunità`

Paragrafo di 4-6 frasi:
- **CHE COSA** si intende acquisire con precisione (oggetto della fornitura/servizio, non solo il CPV);
- **QUANDO** (finalità istituzionale e contesto organizzativo dell'ente);
- Con quale **importo indicativo o a base d'asta** se disponibile da TED o ANAC;
- Se esistono **lotti, fasi o opzioni di rinnovo**;
- Come l'oggetto si inserisce nella **programmazione pluriennale** dell'ente o in adempimenti normativi.

---

## `## Storico aggiudicazioni ANAC`

Fonte più credibile perché consuntiva.

### Paragrafo introduttivo
2-3 frasi che qualificano lo storico:
- Frequenza di acquisto (regolare in questo CPV o occasionale?);
- Importi medi;
- Tendenza crescente o decrescente nel biennio.

### Tabella delle aggiudicazioni più recenti
Fino a 10 record, ordinate per data decrescente:

| Periodo | CIG | Oggetto | Importo aggiudicato | Aggiudicatario | Fonte · Data lettura |
|---------|-----|---------|--------------------:|----------------|----------------------|
| [YYYY] | [CIG] | [oggetto] | EUR [importo] | [ragione sociale] | [URL ANAC] · [YYYY-MM-DD] |

Se > 10 aggiudicazioni: riportare le 10 più recenti e indicare il totale del biennio nel paragrafo introduttivo.

### Lettura per il responsabile commerciale
2-3 frasi:
- Cosa implica questo storico per la decisione go/no-go;
- Importo medio delle gare (accessibilità per operatori non-incumbent);
- Frequenza (quante opportunità all'anno in questo settore per questo ente).

---

## `## Intelligence competitiva`

**Includere solo se i dati ANAC restituiscono informazioni sugli aggiudicatari storici. Omettere se i dati non sono disponibili.**

### Tabella degli operatori economici
Che hanno aggiudicato contratti a questa stazione appaltante nel CPV di interesse negli ultimi 24 mesi:

| Operatore economico | Aggiudicazioni | Importo aggregato | Quota stimata |
|--------------------|---------------:|------------------:|--------------:|
| [ragione sociale] | [N] | EUR [importo] | [%] |

### Lettura per il responsabile commerciale
2-3 frasi:
- Concentrazione del mercato (monopolio, duopolio, mercato aperto);
- Se l'incumbent è scalzabile (quota < 60%) o fortemente consolidato;
- Strategia consigliata (offerta diretta, RTI con operatori complementari, lotto specialistico).

**Disclaimer obbligatorio:**  
*Nota: questa sezione si basa esclusivamente su dati storici pubblici ANAC e non contiene informazioni riservate o di mercato non pubbliche.*

---

## `## Copertura PNRR e fondi strutturali`

**Includere solo se pertinente** (OpenPNRR o OpenCoesione hanno restituito dati rilevanti).

Campi:
- Denominazione del progetto;
- CUP;
- Missione e componente PNRR o fondo strutturale;
- Importo assegnato;
- Stato di avanzamento;
- Eventuali milestone con scadenza.

Paragrafo: indicare in che modo la copertura finanziaria PNRR o FSE/FESR rafforza o modifica la valutazione di trasformazione in gara (il finanziamento obbliga l'ente a spendere entro una scadenza).

---

## `## Timeline attesa`

Tabella con le milestone stimate:

| Milestone | Data stimata | Base della stima |
|-----------|--------------|------------------|
| [evento, es. "Pubblicazione del bando formale"] | [Q o data] | [motivazione, es. "dichiarazione PIN + lead time tipico 60 gg"] |

Paragrafo finale (1-2 frasi): finestra d'azione BD — entro quando agire per essere nella posizione migliore al momento della pubblicazione del bando.

---

## `## Fonti`

Sezione obbligatoria.

Tabella che elenca tutte le fonti consultate per questa scheda:

| Fonte | Dato estratto | Identificatore | Letto il | URL |
|-------|---------------|----------------|----------|-----|
| TED | [es. "PIN attivo CPV 72000000-5, importo EUR 9,5M"] | [NNNNNN-YYYY] | [YYYY-MM-DD] | [URL TED restituito dallo strumento] |
| ANAC | [es. "14 aggiudicazioni CPV 72, importo aggregato EUR 41,2M"] | [C.F. o IPA dell'ente] | [YYYY-MM-DD] | https://dati.anticorruzione.it/opendata |
| OpenPNRR | [es. "CUP in attuazione, EUR 12M, M1C1"] | [CUP] | [YYYY-MM-DD] | [URL OpenPNRR restituito dallo strumento] |
| OpenCoesione | [es. "Progetto avviato, ciclo 2021-2027"] | [CUP] | [YYYY-MM-DD] | [URL OpenCoesione restituito dallo strumento] |

**Regola:** per ANAC senza URL specifico del contratto, usare `https://dati.anticorruzione.it/opendata`.

---

## `## Dati non disponibili`

Sezione sempre presente.

Elenco puntato esaustivo:
- Fonti non interrogate (con motivazione);
- Dati non restituiti dalle API;
- Campi con valori assenti o implausibili.

Includere sempre questa sezione, anche se il contenuto è `"(nessuna limitazione rilevata)"`.

Esempi di voci:
- CIG della gara futura non ancora esistente;
- Capitolato tecnico non disponibile in fase di PIN;
- Importo finale non confermato;
- OpenPNRR non interrogato perché nessun CUP disponibile;
- `data_aggiudicazione ANAC implausibile (valore grezzo: [valore]) — qualità del dato ANAC non sufficiente per la pubblicazione`.

---

## `## Prossimi passi consigliati`

Elenco numerato di azioni concrete con indicazione temporale:

1. **Entro [N] giorni** — [azione specifica con motivazione]
2. **Entro [N] giorni** — [azione specifica con motivazione]
3. ...

---

## `## Audit trail`

Sezione sempre presente.

Blocco di codice fenced con:
- Identificatori di input (CIG, CUP, ente, CPV);
- Numero totale di record trovati nelle fonti;
- `tool_preferito` (`pro` | `free`) e `fallback_attivato` (`si` | `no`) — vedi `../shared/strategia-strumenti.md`;
- Data di lettura (YYYY-MM-DD);
- Timestamp ISO 8601.

Esempio:
```text
Input:
  ente: "Regione Lazio"
  cpv: "72000000"
  cig: null
  cup: null

Risultati:
  ANAC: 14 aggiudicazioni trovate
  TED: 1 PIN attivo trovato
  OpenPNRR: 0 progetti trovati
  OpenCoesione: non interrogato (nessun CUP disponibile)

tool_preferito: "free"
fallback_attivato: "si"
Data lettura: 2026-06-02
Timestamp: 2026-06-02T16:23:45+02:00
```
