# Formato output — Analisi Disciplinare

L'output è una scheda di analisi del documento di gara, redatta in italiano formale, strutturata come nota tecnica destinata a un responsabile commerciale o al responsabile offerta che deve valutare la partecipazione e impostare la risposta alla gara.

## Prima riga

`Dati letti il YYYY-MM-DD`

## Titolo

`# Analisi disciplinare — [oggetto della gara o nome file documento]`

Se disponibile il contesto ANAC: `# Analisi disciplinare — [oggetto ANAC] · CIG [codice]`

---

## `## Contesto gara` *(solo se CIG fornito e anac_award_detail restituisce dati)*

Tabella sintetica:

| Campo | Valore |
|-------|--------|
| Stazione appaltante | [denominazione] |
| Oggetto | [descrizione] |
| Importo a base d'asta | EUR [importo] |
| CIG | [codice] |
| Fonte · Letto il | [URL ANAC] · [YYYY-MM-DD] |

---

## `## Criterio di aggiudicazione`

Una riga che riporta il criterio rilevato:

- **Offerta economicamente più vantaggiosa (OEPV)** — punteggio max: tecnica [N] punti / economica [N] punti
- **Minor prezzo / Massimo ribasso** — nessuna suddivisione tecnica/economica
- **Non rilevato** — il documento non contiene un criterio di aggiudicazione riconoscibile (vedi § Dati non disponibili)

Confidenza: [Alta / Media / Bassa]

---

## `## Criteri di valutazione`

**Includere solo se il testo del documento contiene esplicitamente punteggi per l'offerta tecnica e/o economica.**

### Tabella riassuntiva

| Criterio | Punti massimi |
|----------|-------------:|
| Offerta tecnica (totale) | [N] |
| — [sub-criterio 1] | [N] |
| — [sub-criterio 2] | [N] |
| … | … |
| Offerta economica (totale) | [N] |
| **TOTALE** | **100** |

*Nota: riportare solo i valori esplicitamente scritti nel documento. Non inferire o stimare punteggi non dichiarati. Se i sub-criteri non coprono il totale tecnica, aggiungere una riga ⚠️ con il delta mancante.*

Se la somma dei punteggi tecnica + economica non è 100, aggiungere sotto la tabella:

> ⚠️ La somma dei punteggi tecnica + economica non è 100. Verificare il disciplinare originale — possibile tabella parziale o criteri aggiuntivi non rilevati.

### Note di lettura

1-2 frasi: peso relativo dell'offerta tecnica rispetto all'economica e implicazione per l'impostazione dell'offerta (es. "con 70 punti tecnici su 100, la qualità della proposta è determinante rispetto al prezzo").

---

## `## Requisiti di partecipazione`

**Includere solo le voci effettivamente trovate nel testo del documento.**

Elenco puntato, per categoria:

**Requisiti economici e finanziari:**
- [es. Fatturato globale minimo degli ultimi 3 esercizi: EUR X.XXX.XXX]
- [es. Fatturato specifico nel settore: EUR X.XXX.XXX]

**Requisiti tecnici e professionali:**
- [es. Certificazione ISO 9001]
- [es. Almeno N contratti analoghi negli ultimi N anni, importo ≥ EUR X]
- [es. Categoria SOA: OG1 classifica III]

**Requisiti generali:**
- [es. Iscrizione CCIAA / Albo professionale]
- [es. DURC regolare]

Se nessun requisito è identificabile nel testo (documento troppo breve, testo troncato, o sezione assente): emetti solo la sezione `## Dati non disponibili` con la motivazione.

---

## `## Dati non disponibili`

Sezione sempre presente.

Elenco puntato esaustivo di:
- Errori di fetch (documento non raggiungibile, PDF scansionato, testo troncato);
- Sezioni del disciplinare non trovate nel testo estratto;
- Criteri non riconosciuti dal parser (confidenza Bassa);
- Dati ANAC non disponibili (se CIG non fornito o `anac_award_detail` non restituisce risultati).

Includere sempre questa sezione, anche se il contenuto è `"(nessuna limitazione rilevata)"`.

---

## `## Audit trail`

Sezione sempre presente. Blocco di codice fenced con:

```text
Input:
  url: "<URL documento>"
  cig: "<CIG o null>"

Passi eseguiti:
  1. anac_award_detail(cig="..."): [N campi restituiti | non eseguito]
  2. document_fetch_text(url="..."): [kind=pdf|html, size_bytes=N, pages=N, truncated=true|false | errore: <messaggio>]
  3. Analisi diretta del testo: [criterio=OEPV|minor prezzo, tecnica=N, economica=N, sub-criteri=N | criteri non trovati]

tool_preferito: "pro" | "free"
fallback_attivato: "si" | "no"
Data lettura: YYYY-MM-DD
Timestamp: YYYY-MM-DDThh:mm:ss+hh:mm
```
