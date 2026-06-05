---
name: consultazioni-radar
description: Monitora consultazioni di mercato, avvisi esplorativi e bandi Consip rilevanti per un settore o una tecnologia, e produce una nota decisionale con priorità operative, risultati analizzati in esteso, risultati aggiuntivi sintetici e audit trail. Usa questa skill ogni volta che l'utente parla di consultazioni esplorative o preliminari di mercato, avvisi esplorativi, "call for input" Consip, RdA, bandi o accordi quadro Consip aperti, monitoraggio di forniture o opportunità Consip su un settore/categoria/vendor — anche se non nomina esplicitamente "Consip" o "consultazione".
argument-hint: "<settore> [tecnologia]"
disable-model-invocation: true
allowed-tools:
  - mcp__industrial-mcp-pro__server_capabilities
  - mcp__industrial-mcp-pro__consip_search_consultazioni
  - mcp__industrial-mcp-pro__consip_search_bandi
  - mcp__industrial-mcp-free__server_capabilities
  - mcp__industrial-mcp-free__consip_search_consultazioni
  - mcp__industrial-mcp-free__consip_search_bandi
---

# Consultazioni Radar

Usa questa skill solo per richieste su:
- consultazioni di mercato;
- avvisi esplorativi;
- bandi Consip;
- Richieste di Adesione (RdA) su settore, categoria o tecnologia.

## Obiettivo

Produrre una nota di intelligence in italiano formale che:
1. recuperi consultazioni e bandi rilevanti;
2. li classifichi per stato operativo;
3. evidenzi le priorità commerciali;
4. distingua chiaramente tra risultati analizzati in esteso e risultati aggiuntivi elencati in forma sintetica;
5. includa sempre dati mancanti e audit trail.

## Regole essenziali

Vedi [../shared/regole-comuni.md](../shared/regole-comuni.md).

## Estrazione input

Estrai:
- `settore`: categoria merceologica, dominio di acquisto o ambito di spesa;
- `tecnologia`: prodotto, vendor o parola chiave tecnica specifica.

Se mancano sia `settore` sia `tecnologia`, chiedi all'utente di specificare almeno uno dei due.

Non è disponibile un filtro geografico: gli strumenti Consip non lo espongono. La ricerca copre le consultazioni e i bandi Consip a livello nazionale; se l'utente chiede un taglio regionale, dichiaralo come limite in `## Dati non disponibili`.

### Costruzione query

- se sono presenti `settore` e `tecnologia`: query base = `"<settore> <tecnologia>"`
- se è presente solo `settore`: query base = `"<settore>"`
- se è presente solo `tecnologia`: query base = `"<tecnologia>"`

## Strategia strumenti

Vedi [../shared/strategia-strumenti.md](../shared/strategia-strumenti.md).

### Strumenti consentiti

**Usa esclusivamente** `consip_search_consultazioni` e `consip_search_bandi`.
Non chiamare strumenti ANAC (`anac_*`), TED (`ted_*`), download (`download_*`) o
altri: questa skill copre solo il perimetro Consip. Se l'utente chiede un
confronto con ANAC o TED, dichiara il limite in `## Dati non disponibili` e
suggerisci di usare la skill `scheda-opportunita` o `pin-radar`.

### Sequenza di interrogazione

Interroga sempre, in questo ordine:
1. consultazioni di mercato (`consip_search_consultazioni`);
2. bandi / RdA (`consip_search_bandi`).

Usa la stessa query base per entrambi.

## Classificazione risultati

Classifica ogni record in una sola categoria:
- `consultazione_aperta`
- `bando_aperto`
- `consultazione_chiusa`

Usa solo:
- tipo documento restituito;
- stato restituito;
- scadenza se disponibile.

Regole:
- consultazione o avviso esplorativo con termine non trascorso → `consultazione_aperta`
- consultazione o avviso esplorativo con termine trascorso → `consultazione_chiusa`
- bando / RdA / accordo quadro / avviso di gara con termine non trascorso → `bando_aperto`
- documento senza data di scadenza disponibile → classificalo per tipo (consultazione/avviso esplorativo → `consultazione_aperta`; bando/RdA → `bando_aperto`), non assumere che il termine sia trascorso, e annota la scadenza mancante in `## Dati non disponibili`.

Se la classificazione resta ambigua, scegli l'interpretazione più prudente (tipicamente "aperta", per non escludere un'opportunità ancora valida) e dichiaralo in `## Dati non disponibili`.

## Deduplica e ordinamento

Deduplica:
1. per identificativo;
2. se manca l'identificativo, per combinazione di ente + titolo + scadenza.

Mantieni il record con URL più completo o metadati più ricchi.

Ordina:
- consultazioni aperte: per scadenza crescente;
- bandi aperti: per scadenza crescente;
- consultazioni chiuse: per chiusura più recente.

## Selezione dei risultati

Per ogni categoria:
- analizza in esteso al massimo 5 record;
- tutti gli altri devono comparire nella sezione `## Altri risultati trovati ma non analizzati in esteso`.

Per ciascun risultato omesso dall'analisi estesa, indica almeno:
- ente;
- titolo breve;
- identificativo;
- stato;
- scadenza se disponibile;
- URL fonte.

## Regole di valutazione qualitativa

Usa solo etichette qualitative:
- `Alta`
- `Media`
- `Bassa`

Mai usare percentuali, numeri, punteggi o score.

Per consultazioni:
- valuta la **Probabilità di trasformazione in gara formale**

Per bandi:
- valuta la **Probabilità di aggiudicazione utile**

Se gli elementi disponibili non bastano per sostenere con certezza `Alta` o `Bassa`, usa `Media` e dichiara i limiti informativi.

Per la rubrica dettagliata, consulta references/ranking-rules.md.

## Formato dell'output

Segui il formato definito in references/output-format.md.

Se serve un esempio completo, consulta examples/example-output.md.

## Regole invarianti

- La prima riga dell'output è sempre: `Dati letti il YYYY-MM-DD`
- Le sezioni di segnale appaiono sempre in questo ordine:
  1. `## 🟢 Consultazioni aperte — rispondere ora`
  2. `## 🔵 Bandi e RdA formali aperti — presentare offerta`
  3. `## ⚪ Consultazioni chiuse — contesto per la programmazione`
- Una sezione senza risultati viene omessa.
- `## Dati non disponibili` e `## Audit trail` sono sempre presenti.
- Se esistono risultati oltre il limite di analisi estesa, `## Altri risultati trovati ma non analizzati in esteso` è obbligatoria.
- Non esporre i nomi degli strumenti MCP nell'output finale.
- Se consultazioni e bandi restituiscono entrambi zero risultati, emetti comunque il documento completo con intestazione, `## Dati non disponibili` e `## Audit trail`.
