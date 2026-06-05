# Formato output — Consultazioni Radar

L'output è una nota di intelligence in italiano formale, strutturata in markdown.

## Prima riga
`Dati letti il YYYY-MM-DD`

## Titolo
- Se sono presenti settore e tecnologia:
  `# Consultazioni Radar — [settore] · [tecnologia]`
- Se è presente solo settore:
  `# Consultazioni Radar — [settore]`
- Se è presente solo tecnologia:
  `# Consultazioni Radar — [tecnologia]`

## Riga di sintesi
`[N] risultati totali · [N] consultazioni aperte · [N] bandi aperti · [N] consultazioni chiuse`

## Azione prioritaria
Una riga in grassetto:
- scegli il segnale aperto con scadenza più vicina;
- a parità, preferisci quello più aderente alla richiesta dell'utente;
- a ulteriore parità, preferisci una consultazione aperta a un bando aperto;
- se non ci sono segnali aperti, indica il segnale chiuso più recente da monitorare.

---

## `## 🟢 Consultazioni aperte — rispondere ora`

Includi solo se esistono consultazioni o avvisi esplorativi aperti.

Per ciascun record analizzato in esteso:

### [Ente o centrale di committenza]
**Titolo dell'avviso:** [titolo integrale o miglior titolo disponibile]  
**Identificativo:** [ID] · **Tipo documento:** [tipo restituito]  
**Stato:** [stato restituito] · **Termine per le risposte:** [YYYY-MM-DD oppure "dato non disponibile"] ([giorni rimanenti se calcolabili])

**Descrizione dell'iniziativa**

Paragrafo sintetico ma sostanziale che copra, se disponibili:
- oggetto;
- contesto operativo desumibile dal testo;
- eventuali importi, lotti, modalità di partecipazione o requisiti;
- implicazione commerciale.

| Campo | Dettaglio |
|-------|-----------|
| **Probabilità di trasformazione in gara formale** | Alta / Media / Bassa |
| **Finestra di gara stimata** | [stima motivata oppure `Non stimabile dai risultati restituiti`] |
| **Fonte** | [[ID avviso]]([URL restituito dallo strumento]) |
| **Data di lettura** | [YYYY-MM-DD] |

**Motivazione della probabilità di trasformazione**

Paragrafo breve fondato solo sugli elementi disponibili.

**Azione raccomandata**

Paragrafo breve e pratico.  
Se mancano dettagli operativi, scrivi:  
`Le modalità puntuali di partecipazione non sono esplicitate nei risultati restituiti e richiedono verifica sulla fonte.`

---

## `## 🔵 Bandi e RdA formali aperti — presentare offerta`

Includi solo se esistono bandi o RdA aperti.

Per ciascun record analizzato in esteso:

### [Ente o centrale di committenza]
**Titolo del bando:** [titolo integrale o miglior titolo disponibile]  
**Identificativo:** [ID] · **Tipo documento:** [tipo restituito]  
**Stato:** [stato restituito] · **Scadenza offerte:** [YYYY-MM-DD oppure "dato non disponibile"] ([giorni rimanenti se calcolabili])

**Descrizione dell'opportunità**

Paragrafo sintetico ma sostanziale che copra, se disponibili:
- oggetto;
- lotti;
- importi;
- requisiti;
- criteri;
- accessibilità commerciale sulla base del testo disponibile.

| Campo | Dettaglio |
|-------|-----------|
| **Probabilità di aggiudicazione utile** | Alta / Media / Bassa |
| **Importo a base d'asta** | [valore restituito oppure `Dato non disponibile nei risultati restituiti`] |
| **Scadenza offerte** | [YYYY-MM-DD oppure `Dato non disponibile`] |
| **Prossimo passo atteso** | [dato restituito oppure `Dato non disponibile nei risultati restituiti`] |
| **Fonte** | [[ID bando]]([URL restituito dallo strumento]) |
| **Data di lettura** | [YYYY-MM-DD] |

**Motivazione della valutazione**

Paragrafo breve fondato solo sugli elementi disponibili.

**Azione raccomandata**

Paragrafo breve che indichi verifica requisiti, documentazione e presidio immediato della fonte.

---

## `## ⚪ Consultazioni chiuse — contesto per la programmazione`

Includi solo se esistono consultazioni chiuse.

Per ciascun record analizzato in esteso:

### [Ente] — [Titolo avviso]
**Identificativo:** [ID] · **Tipo:** [tipo restituito] · **Stato:** chiuso  
**Termine scaduto il:** [YYYY-MM-DD oppure "dato non disponibile"]

Paragrafo breve che descriva:
- oggetto della consultazione;
- possibile rilevanza prospettica;
- azione consigliata di monitoraggio.

| Campo | Dettaglio |
|-------|-----------|
| **Probabilità di gara futura** | Alta / Media / Bassa |
| **Finestra di gara stimata** | [stima motivata oppure `Non stimabile dai risultati restituiti`] |
| **Fonte** | [[ID]]([URL restituito dallo strumento]) |
| **Data di lettura** | [YYYY-MM-DD] |

---

## `## Altri risultati trovati ma non analizzati in esteso`

Includi questa sezione solo se almeno una categoria supera il limite di 5 record analizzati in esteso.

Usa sottosezioni:
- `### Ulteriori consultazioni aperte`
- `### Ulteriori bandi aperti`
- `### Ulteriori consultazioni chiuse`

Ogni riga:
`- [Ente] — [Titolo breve] · ID [identificativo] · Stato [stato] · Scadenza [YYYY-MM-DD oppure "n.d."] · Fonte: [URL]`

---

## `## Dati non disponibili`

Sezione sempre presente.

Elenca in forma puntata:
- filtri non disponibili come campi strutturati;
- tecnologia applicata come filtro testuale;
- campi non restituiti dagli strumenti;
- eventuali ambiguità di classificazione;
- eventuali fallback attivati;
- eventuali risultati omessi dall'analisi estesa ma riportati sinteticamente.

---

## `## Audit trail`

Sezione sempre presente.

Usa un solo blocco di codice fenced:

```text
query_consultazioni: "<query usata>"
risultati_consultazioni: <N>
query_bandi: "<query usata>"
risultati_bandi: <N>
tool_preferito: "pro" | "free"
fallback_attivato: "si" | "no"
data_lettura: YYYY-MM-DD
timestamp_iso8601: YYYY-MM-DDTHH:MM:SS±HH:MM
```
