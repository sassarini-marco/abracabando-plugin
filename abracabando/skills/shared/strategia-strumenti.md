# Strategia strumenti — preferenza pro con fallback free

## Passo 0 — Capability probe (CONSIGLIATO, prima di qualsiasi altra chiamata)

Il server applica i limiti di budget autonomamente lato server: quando il
budget è esaurito restituisce un messaggio `LIMITE_PIANO_FREE:` che la skill
deve gestire come descritto in `regole-comuni.md`.

La probe è comunque consigliata perché permette alla skill di pianificare in
anticipo l'utilizzo del budget (es. dare priorità alle fonti più rilevanti) e
di registrare `server_tier` nell'audit trail. È esente dal conteggio del budget.

**Sequenza:**

1. Tenta `mcp__industrial-mcp-pro__server_capabilities` (nessun argomento).
   - Se risponde con JSON valido → tier **pro**, usa i valori restituiti.
2. Se fallisce, tenta `mcp__industrial-mcp-free__server_capabilities` (nessun argomento).
   - Se risponde con JSON valido → tier **free**, usa i valori restituiti.
3. Se entrambi falliscono (server precedente senza questo strumento) →
   applica i **default free** hardcoded.

**Struttura della risposta:**

```json
{
  "tier": "free",
  "max_results_per_call": 10,
  "max_total_calls": 30,
  "blocked_tools": [],
  "data_freshness_days": 30
}
```

**Default free** (fallback se il tool non esiste):

| Campo | Free | Pro |
|---|---|---|
| `max_results_per_call` | `10` | `50` |
| `max_total_calls` | `30` | `200` |
| `blocked_tools` | `[]` | `[]` |
| `data_freshness_days` | `30` | `7` |

**Come applicare i limiti:**

- Usa `max_results_per_call` come valore del parametro `limit` / `rows` in ogni
  chiamata successiva. Non superarlo mai.
- Conta ogni chiamata MCP (inclusa la probe). Fermati quando raggiungi `max_total_calls`.
- Non invocare mai uno strumento il cui nome breve (parte dopo `__`) compare in
  `blocked_tools`. Se era previsto nella strategia della skill, segna la sezione
  corrispondente come `## Dati non disponibili`.
- Registra `server_tier` nell'`## Audit trail`.

---

## Passo 0.5 — Pianificazione delle chiamate (prima di iniziare)

Dopo la probe, pianifica l'intera sequenza prima di invocare qualsiasi strumento dati.

### Salta il tentativo pro se tier=free

Se la probe restituisce `tier: "free"`, **chiama direttamente gli strumenti free**
senza tentare prima il pro. Il server pro è un placeholder disconnesso: il
tentativo pro aggiunge solo latenza senza mai produrre dati.

Se la probe restituisce `tier: "pro"`, segui il Passo 1 (pro → fallback free).

### Ordine di priorità: leggero prima, bulk dopo

Con il budget limitato, chiama prima gli strumenti che rispondono in meno di 2
secondi e non richiedono download bulk. Lascia gli strumenti bulk per ultimi,
solo se il budget lo consente.

**Strumenti leggeri** (API dirette, nessun download, <2 s, chiamare per primi):

| Categoria | Strumenti |
|---|---|
| TED (EU) | `ted_search`, `ted_pin_italy`, `ted_get_notice_xml` |
| Consip | `consip_search_bandi`, `consip_search_consultazioni`, `consip_chiarimenti` |
| OpenPNRR (lista/dettaglio interno) | `openpnrr_list`, `openpnrr_get` |
| OpenCoesione catalogo | `opencoesione_list_datasets`, `opencoesione_describe_dataset`, `opencoesione_project_url` |
| ANAC catalogo | `anac_list_datasets`, `anac_get_dataset`, `anac_search_datasets`, `anac_pnrr_datasets`, `anac_ocds_bulk_url` |
| Altro | `cpv_*`, `mef_*`, `dati_*`, `imprese_*`, `programmazione_*`, `italiadomani_*` |

**Strumenti a costo medio** (più chiamate HTTP interne o download parquet su cold start):

| Categoria | Strumenti | Costo nascosto |
|---|---|---|
| OpenPNRR per CUP | `openpnrr_search_progetti(cup=...)` | fino a 6 chiamate HTTP interne (6 pagine × 500 record); **non ritentare** se CUP non trovato |
| OpenCoesione lookup | `opencoesione_project_by_cup`, `opencoesione_search_projects` | scansiona fino a 3 file Parquet (uno per ciclo) al primo uso; poi cache |

**Strumenti bulk** (scaricano snapshot mensili su cold start, 70–300 s; tabelle ANAC condivise tra tool):

| Categoria | Strumenti | Tabelle |
|---|---|---|
| ANAC aggiudicazioni | `anac_sa_history` | 2 |
| ANAC aggiudicazioni | `anac_search_awards`, `anac_awards_by_piva` | 3 |
| ANAC aggiudicazioni | `anac_award_detail`, `anac_awards_by_cup` | 4 |
| OpenCoesione dati | `opencoesione_download_parquet` | — |

Le tabelle ANAC sono **condivise**: la prima chiamata paga il cold start per tutte; le successive leggono la cache. Non invocare mai due strumenti ANAC in parallelo (vedi `regole-comuni.md`).

### Regola di deduplica

Non invocare mai due strumenti diversi per ottenere lo stesso dato. Se un
risultato leggero contiene già un CIG o CUP, non ri-cercarlo con uno strumento
bulk — usa il valore già ottenuto.

---

## Passo 1 — Preferenza pro con fallback free

Tutte le skill seguono questa strategia di invocazione strumenti (applicabile
solo quando tier=pro dalla probe; se tier=free, vai direttamente al free):

Preferisci sempre gli strumenti **pro** (prefisso `mcp__industrial-mcp-pro__`).

Usa gli strumenti **free** (prefisso `mcp__industrial-mcp-free__`) **solo** come fallback se:
- lo strumento pro fallisce con errore;
- oppure restituisce errore HTTP (400, 500, timeout);
- oppure restituisce zero risultati quando ci si aspetterebbe almeno un risultato.

Questa strategia bilancia affidabilità (pro) con resilienza (free come fallback).

## Meccanica del fallback

Quando una delle condizioni sopra si verifica, **ri-invoca lo strumento free
equivalente con gli stessi identici parametri** (stesso nome di strumento senza
il prefisso, stessi argomenti). Esempio: se `mcp__industrial-mcp-pro__ted_search`
restituisce timeout, richiama `mcp__industrial-mcp-free__ted_search` con i
parametri invariati. Non modificare la query nel passaggio da pro a free: così
la differenza eventuale nei risultati è attribuibile alla fonte, non alla query.

Il server pro è attualmente un placeholder e risulta spesso disconnesso: in
quel caso il passaggio a free è atteso e non va segnalato come anomalia.

Registra sempre nell'`## Audit trail` quale livello hai effettivamente usato
(`tool_preferito: "pro" | "free"`) e se il fallback è scattato
(`fallback_attivato: "si" | "no"`).