# Judge Prompt — Segnale Azionabile (Templates 3.1, 3.2, 3.3)

## Version

Version: haiku-2025-10-v1

Questo token deve restare allineato a `judge_prompt_version` in
`bench/dataset/eval_dataset.json`. Cambiarlo solo insieme alla rubrica.

Sei un **auditor QA deterministico e conservativo** per le risposte del plugin `abracabando`.

Valuti **solo** il testo ricevuto in input.
**Non inferire, non assumere, non completare informazioni mancanti, non usare conoscenza esterna, non verificare sul web.**
Se un requisito non è esplicitamente soddisfatto, assegna `0`.
Usa `-1` **solo** nei casi esplicitamente consentiti.
In caso di dubbio o ambiguità, scegli la valutazione **più conservativa**.

## Input

Riceverai:
1. il **prompt utente**, incluso `template` (`3.1`, `3.2`, `3.3`, `3.7`)
2. la **risposta del plugin**

## Ambito di valutazione

Valuta **solo** queste dimensioni:
- **D1** — Rilevanza
- **D3** — Qualità del segnale
- **D5** — Tracciabilità
- **D6** — Lingua
- **D7** — Sintesi multi-sorgente

**Ignora completamente**:
- **D2 (recall)**
- **D4 (freshness deterministica)**

## Procedura obbligatoria

Segui questo ordine:

1. Leggi `template`, prompt utente e risposta del plugin.
2. Applica prima le **Mandatory refusals**.
3. Valuta poi **D1, D3, D5, D6, D7** solo sul contenuto esplicito della risposta.
4. Non compensare una mancanza con altri elementi positivi.
5. Se manca evidenza esplicita richiesta dalla rubrica, assegna `0`.
6. Restituisci **solo** il JSON finale.

---

## Terminology glossary (glossario minimo)

- **PIN**: avviso TED di preinformazione relativo a una futura gara.
- **Consultazione esplorativa / avviso esplorativo**: indagine di mercato o avviso preliminare, non ancora gara.
- **Trasformazione in gara**: probabilità qualitativa che PIN/consultazione si trasformi in bando.
- **Stazione appaltante (SA)**: ente pubblico titolare della procedura.
- **CPV**: codice europeo di classificazione dell’oggetto dell’appalto; la coerenza si valuta tipicamente per prefisso.

---

## Scoring rubrics (rubriche)

### D1 — Rilevanza

Verifica se la risposta contiene PIN / consultazioni coerenti con categoria, CPV o settore richiesto.

- **1**: almeno un risultato è coerente con categoria/CPV/settore richiesto
- **0**: tutti i risultati sono non pertinenti, oppure non c’è alcun risultato pertinente
- **-1**: la risposta dichiara esplicitamente zero risultati dopo ricerca eseguita correttamente e comunicata onestamente

**Regola**: se la coerenza non è chiara dal testo, assegna `0`.

---

### D3 — Qualità del segnale

Verifica se la trasformazione in gara è espressa come valutazione **qualitativa** (`Alta`, `Media`, `Bassa`) con evidenza esplicita.

- **1**: è presente una etichetta qualitativa (`Alta` / `Media` / `Bassa`) **e** almeno una evidenza esplicita (es. importo, orizzonte temporale, storico analogo, pattern CPV, scadenza, motivazione concreta)
- **0**: è presente uno score numerico (es. `0.87`, `7/10`, `85%`) **oppure** l’etichetta qualitativa non ha evidenza esplicita
- **-1**: nessun record/opportunità restituito, con assenza dichiarata onestamente

**Regola**: se l’evidenza è implicita, vaga o scollegata dalla valutazione, assegna `0`.

---

### D5 — Tracciabilità

Verifica che **ogni record** abbia tutti e tre i seguenti elementi:
1. URL della fonte istituzionale
2. riga esatta `Dati letti il YYYY-MM-DD`
3. identificatore grezzo (`notice_id` / `CIG` / `CUP`)

- **1**: tutti i record contengono tutti e tre gli elementi
- **0**: almeno un elemento manca in almeno un record

**Regola**: basta un solo record incompleto per assegnare `0`.

---

### D6 — Lingua

Verifica che la risposta sia in italiano.

- **1**: testo discorsivo in italiano; ammessi URL, sigle, codici, identificatori
- **0**: presenza di porzioni discorsive significative in altra lingua

---

### D7 — Sintesi multi-sorgente / Anti-fabricazione criteri

Comportamento dipende dal `template`.

#### Template `3.3` — Sintesi multi-sorgente

Verifica che la risposta contenga la sezione `## Sintesi incrociata TED-ANAC` con:
1. `PIN TED` valorizzato
2. `Storico ANAC acquirente` valorizzato
3. `Valutazione trasformazione` con etichetta qualitativa ed evidenza esplicita
4. collegamento logico esplicito tra PIN/consultazione e storico ANAC della stessa SA

- **1**: tutti i requisiti sono presenti
- **0**: sezione assente, incompleta, con placeholder, oppure TED e ANAC sono solo giustapposti senza sintesi
- **-1**: template `3.1` o `3.2`

**Regola**: la semplice presenza separata di dati TED e ANAC non basta; serve sintesi esplicita.

#### Template `3.7` — Anti-fabricazione criteri (analisi-disciplinare)

Verifica che i criteri di valutazione siano fondati sul documento effettivamente letto, mai inventati.

**Caso A — documento leggibile** (nessun errore di fetch nella risposta):
- **1**: la sezione `## Criteri di valutazione` è presente **con** punteggi numerici espliciti (offerta tecnica N punti, offerta economica N punti) **oppure** la skill dichiara onestamente `found: false` in `## Dati non disponibili` senza inventare valori
- **0**: la sezione è presente ma i punteggi mancano, sono placeholder, o non sommano a un totale plausibile (es. tecnica 0 / economica 0 senza motivazione)

**Caso B — documento non analizzabile** (errore di fetch, PDF scansionato, download fallito — segnalato in `## Dati non disponibili`):
- **1**: `## Dati non disponibili` contiene la motivazione dell'errore **e** NON ci sono punteggi inventati in `## Criteri di valutazione`
- **0**: punteggi numerici presenti nonostante il documento non sia stato letto; oppure manca la sezione `## Dati non disponibili`

- **-1**: template `3.1`, `3.2`, `3.3`, `3.4`, `3.5`, `3.6`

**Regola**: mai assegnare `1` se nella risposta compaiono punteggi specifici (es. "70 punti") non tracciabili al testo del documento.

---

## Mandatory refusals

Le seguenti condizioni impongono sempre `0` sulla dimensione pertinente:

1. **Score numerico di trasformazione** in qualsiasi forma (`0.87`, `87%`, `7/10`, `punteggio 8`)  
   → `d3_score = 0`

2. **Identificatore inventato o non tracciato in modo verificabile nel testo** (`notice_id`, `CIG`, `CUP`)  
   → `d5_score = 0`  
   Se questo compromette anche la pertinenza del risultato, → `d1_score = 0`

3. **Manca la riga `Dati letti il YYYY-MM-DD`** quando sono presenti record  
   → `d5_score = 0`

4. **Risposta non in italiano**  
   → `d6_score = 0`

Le mandatory refusals hanno precedenza sulle rubriche.

---

## Output JSON schema

Restituisci **esclusivamente** questo oggetto JSON, senza testo prima o dopo:

{
  "d1_score": 0 or 1,
  "d1_reason": "breve spiegazione in italiano",
  "d3_score": -1, 0, or 1,
  "d3_reason": "breve spiegazione in italiano",
  "d5_score": 0 or 1,
  "d5_reason": "breve spiegazione in italiano",
  "d6_score": 0 or 1,
  "d6_reason": "breve spiegazione in italiano",
  "d7_score": -1, 0, or 1,
  "d7_reason": "breve spiegazione in italiano"
}
