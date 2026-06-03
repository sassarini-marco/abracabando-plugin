# Formato output — PIN Radar

L'output è una nota di intelligence sugli appalti pubblici redatta in italiano formale, strutturata in markdown.

## Prima riga
`Dati letti il YYYY-MM-DD`

## Titolo
`# Radar PIN TED — [categoria o CPV ricercato] · [area geografica]`  
`[N] PIN attivi individuati · Fonte: TED (Tenders Electronic Daily) · [N] ad alta priorità, [N] a media priorità`

## Riepilogo esecutivo
Blocco citazione (blockquote) con:
- Segnale più urgente per scadenza imminente;
- Segnale più rilevante per importo;
- Totale per fascia di priorità.

Se nessun PIN trovato: dichiaralo esplicitamente, precisando filtri applicati e suggerendo CPV alternativi o ampliamenti geografici.

---

## `## PIN ad alta priorità — azione entro breve termine`

Includi solo se esistono PIN classificati ad Alta priorità.

Per ciascun PIN analizzato in esteso:

### [N]. [Denominazione ufficiale completa della stazione appaltante]
**Tipologia ente:** [es. Società in house regionale / Azienda Ospedaliero-Universitaria / Comune capoluogo di regione]  
**Area geografica:** [Regione · Codice NUTS-2]  
**Oggetto dell'avviso:** [Titolo integrale dell'avviso come pubblicato su TED, senza abbreviazioni]

**Descrizione dell'opportunità**

Paragrafo di almeno 4-6 frasi che illustra:
- **CHE COSA** si intende acquisire (oggetto preciso, non solo il titolo abbreviato; categoria merceologica e CPV con descrizione ufficiale TED; caratteristiche tecniche principali se indicate);
- **QUANDO** è attesa la procedura di gara (stima motivata basata su data pubblicazione PIN, scadenza consultazione, pattern storici per tipologia ente e CPV);
- **DOVE** (denominazione ufficiale stazione appaltante; tipologia giuridica ente; regione e area NUTS-2; codice IPA o P.IVA se disponibile).

| Campo | Dettaglio |
|-------|-----------|
| **Probabilità di trasformazione in gara** | Alta |
| **Finestra di gara stimata** | [stima motivata, es. "entro Q3 2026 — stimato 60-90 giorni dalla scadenza consultazione del 2026-06-30"] |
| **Scadenza della consultazione** | [YYYY-MM-DD oppure "non indicata nell'avviso"] |
| **CPV** | [codice] — [descrizione ufficiale TED] |
| **Importo indicativo** | [EUR X.XXX.XXX oppure "non indicato nel PIN"] |
| **Numero di pubblicazione TED** | [[NNNNNN-YYYY]]([URL restituito dallo strumento — non costruire dalla memoria]) |
| **Data di lettura** | [YYYY-MM-DD] |

**Motivazione della valutazione Alta**

Paragrafo di 3-5 frasi che argomenta la classificazione:
- Tipo di atto pubblicato (consultazione preliminare ex art. 66 D.Lgs. 36/2023, avviso di preinformazione diretto, indagine di mercato ex art. 68 CAD);
- Storico dell'ente su procedure analoghe;
- Prossimità scadenza fase consultiva;
- Indicazione esplicita di procedura prevista o importo a base d'asta;
- Piena coerenza CPV con settore richiesto.

**Azione commerciale raccomandata**

Paragrafo di 2-3 frasi con indicazione del tempo residuo rispetto alla scadenza:
- Come/se rispondere alla consultazione preliminare;
- Se contattare ufficio acquisti/direzione per incontro pre-gara;
- Se verificare requisiti di qualificazione (SOA, ISO, referenze);
- Se valutare costituzione RTI con operatori complementari.

---

## `## PIN da monitorare — segnali di media rilevanza`

Includi solo se esistono PIN classificati a Media priorità.

Stesso formato della sezione precedente, con badge `Media` nella tabella.

La motivazione deve esplicitare il fattore di incertezza:
- Scadenza non imminente;
- Importo non indicato;
- Ente che pubblica raramente procedure competitive sopra soglia;
- CPV parzialmente pertinente;
- PIN pubblicato da oltre 3 mesi senza aggiornamenti.

---

## `## Segnali deboli — bassa rilevanza`

Includi solo se esistono PIN classificati a Bassa priorità.

Tabella riassuntiva (non schede estese) con una riga per ciascun avviso:

| Stazione appaltante | Oggetto (titolo integrale dell'avviso) | Scadenza | Motivazione priorità Bassa | Fonte TED · Data lettura |
|---------------------|----------------------------------------|----------|----------------------------|--------------------------|
| [denominazione] | [titolo completo] | [YYYY-MM-DD o n.d.] | [motivazione esplicita] | [[NNNNNN-YYYY]]([URL]) · [YYYY-MM-DD] |

---

## `## Copertura della ricerca e limiti`

Sezione sempre presente.

Paragrafo descrittivo che indica:
- Quali filtri sono stati applicati (CPV, area NUTS, finestra temporale);
- Cosa non è stato trovato e perché (presumibile);
- Eventuali CPV alternativi o complementari per ulteriori opportunità;
- Limitazioni note di TED per la categoria merceologica ricercata.

---

## `## Audit trail`

Sezione sempre presente.

Blocco di codice fenced con:
- Query esatta inviata a TED (parametri CPV, NUTS, finestra temporale, limit, page);
- Numero di pagine interrogate;
- Numero totale di PIN raccolti;
- `tool_preferito` (`pro` | `free`) e `fallback_attivato` (`si` | `no`) — vedi `../shared/strategia-strumenti.md`;
- Data di lettura (YYYY-MM-DD);
- Timestamp ISO 8601.

Esempio:
```text
Query TED PIN Italia:
  cpv_codes: ["72000000"]
  nuts_region: null
  deadline_before: "20261202"
  limit: 10 per pagina
  
Pagine interrogate: 2 (page=1, page=2)
PIN raccolti: 18 (10 da page1 + 8 da page2)
tool_preferito: "free"
fallback_attivato: "si"
Data lettura: 2026-06-02
Timestamp: 2026-06-02T14:30:00Z
```
