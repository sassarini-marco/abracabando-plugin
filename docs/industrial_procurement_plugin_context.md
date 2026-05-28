# industrial-procurement-plugin — Context Document

> Documento di contesto per Claude Code, repository `industrial-procurement-plugin`. Definisce missione, capability, principi UX, struttura, distribuzione e principi di esecuzione. Da usare come briefing per pianificare lo sviluppo del plugin.

---

## 1. Cos'è questo repository

`industrial-procurement-plugin` è il **plugin Claude Code** che permette a un utente di interrogare l'ecosistema della spesa pubblica italiana in linguaggio naturale, ottenendo output strutturati di qualità professionale.

**Non è** un MCP server. È il consumer di un MCP server (`industrial-mcp`, repository separato) che aggiunge:

- Slash command discoverable nel terminale
- Skill orchestrate che concatenano i tool MCP per produrre output strutturati
- Sub-agent specializzati per workflow complessi
- Configurazione utente (profili, preferenze di output, scelta tra MCP server free e pro)
- Documentazione e onboarding

Il plugin **è il punto di contatto con l'utente finale**. Il valore percepito dall'utente passa quasi tutto da qui, anche se il valore *prodotto* sta nel server.

### Relazione con gli altri repository

```
┌──────────────────────────────────────────┐
│  industrial-procurement-plugin (qui)     │
│  - commands/                              │
│  - skills/                                │
│  - agents/                                │
│  - .claude-plugin/                        │
│  Licenza: MIT (pubblico)                  │
└──────────────┬───────────────────────────┘
               │ depende da
               ▼
┌──────────────────────────────────────────┐
│  industrial-mcp                          │
│  Server MCP "core" — wrapper sorgenti    │
│  Licenza: MIT (pubblico)                  │
└──────────────┬───────────────────────────┘
               │ può essere sostituito da
               ▼
┌──────────────────────────────────────────┐
│  industrial-mcp-pro (futuro)             │
│  Server MCP con DB + dataset curato      │
│  Hosted, accesso via Bearer token         │
│  Licenza: proprietaria                    │
└──────────────────────────────────────────┘
```

L'utente installa il plugin. Il plugin punta a un MCP server. Quale server (core locale o pro hosted) è configurazione dell'utente.

---

## 2. Le cinque capability esposte

Il plugin espone esattamente **cinque capability**. Ognuna corrisponde a uno scenario d'uso reale dell'utente finale (sales lead in ESCo, account manager, consulente PNRR, auditor).

### 2.1 Digest pre-gara

**Slash command suggerito**: `/digest-pregara`

L'utente chiede a Claude una lista ranked di opportunità di affidamento intercettate prima della pubblicazione del bando, filtrata per profilo (CPV, regione, soglia importo, orizzonte temporale).

**Trigger conversazionale tipico**:
> "Dammi le opportunità di efficientamento energetico in Lombardia sopra 200k per i prossimi 12 mesi"

**Output atteso**: lista di 10-20 voci ranked, in formato leggibile (markdown table o struttura prosaica con bullet), con per ciascuna voce: ente, oggetto previsionale, importo stimato, fonte, link verificabile, anticipo stimato, livello di confidenza.

### 2.2 PIN radar

**Slash command suggerito**: `/pin-radar`

Recupera e analizza Prior Information Notices TED Italia matchando un profilo di interesse.

**Trigger conversazionale tipico**:
> "Mostrami i PIN attivi nel settore sanitario del Triveneto dell'ultimo trimestre"

**Output atteso**: lista di PIN attivi con titolo, ente, oggetto, scadenza consultazione, link diretto al notice TED in italiano. Numero typical: 5-30 voci. Quando rilevante, segnalare anche se l'ente ha un buyer history rilevante.

### 2.3 Scheda opportunità

**Slash command suggerito**: `/scheda-opportunita`

Brief monografico costruito a partire da un identificatore (CUP, CIG previsionale, ID notice TED).

**Trigger conversazionale tipico**:
> "Fai una scheda completa di questo CUP: I32E22000560006"

**Output atteso**: documento one-pager strutturato con sezioni: descrizione, ente proponente, importo, fonti incrociate (cosa dice OpenPNRR, cosa dice OpenCoesione, cosa dice ANAC), storico ente, concorrenti probabili (top 5 vincitori storici per CPV+regione), timeline attesa, link verificabili.

### 2.4 Profilo stazione appaltante

**Slash command suggerito**: `/profilo-sa`

Pattern storico-comportamentale di una specifica PA.

**Trigger conversazionale tipico**:
> "Profila la storia degli acquisti di ASL Napoli 1 negli ultimi 5 anni nel CPV 33"

**Output atteso**: scheda 2-3 pagine con: volume affidamenti/anno, top CPV, top fornitori storici, stagionalità, importo medio per categoria, ribasso medio, anomalie ricorrenti.

### 2.5 Reconciliation PNRR

**Slash command suggerito**: `/reconciliation-pnrr`

Tabella di allineamento tra OpenPNRR, OpenCoesione e ANAC per una misura o un CUP, con flag automatici di incoerenze.

**Trigger conversazionale tipico**:
> "Verifica la coerenza tra le fonti per la Misura M2C3 I1.1 in Lombardia"

**Output atteso**: tabella con CUP, stato OpenPNRR, importo finanziato OpenCoesione, importo aggiudicato ANAC, e una colonna "flag" che segnali incoerenze: CUP orfani (esistono da >18 mesi senza CIG), importo sopra finanziato, stato divergente, mancata pubblicazione TED sopra soglia.

### 2.6 Capability esplicitamente fuori scope

Per chiarezza nel marketplace e nelle aspettative dell'utente, il plugin **non** offre:

- Network analysis su amministratori, soci, beneficial owner
- Anomaly detection automatizzata cross-source
- Scoring integrato ESG e rischio di credito

Sono candidate per versioni successive ma devono essere assenti dalla descrizione del plugin e dalle skill esposte.

---

## 3. Principi UX e di output

Le cinque capability rispettano sette principi di qualità nell'output. Sono la promessa al cliente e il differenziatore.

### 3.1 Provenance verificabile

Ogni fatto citato deve avere un link diretto alla fonte istituzionale. Le skill devono istruire l'agente a non sintetizzare senza tracciabilità.

**Forma raccomandata** nell'output: ogni claim chiude con `(fonte: [ANAC OCDS, dataset cig-2025](https://...))`.

### 3.2 Confidence dichiarata

Dove esiste incertezza (matching per denominazione simile, importo previsionale, scadenza stimata), esplicitarla in linguaggio naturale. **No score numerici inventati**.

**Forma raccomandata**: "match esatto su P.IVA", "match probabile per denominazione, possibili omonimie", "importo dichiarato dall'ente in programmazione, non ancora confermato da CIG ANAC".

### 3.3 Freshness datata

Ogni record dichiara quando è stato pubblicato dalla fonte e quando è stato letto dal plugin.

**Forma raccomandata** nell'header dell'output: "Dati letti il YYYY-MM-DD. Ultima pubblicazione ANAC ingerita: YYYY-MM-DD."

### 3.4 Audit trail completo

Le skill devono restituire (anche se in sezione "dettagli tecnici" in coda) gli identificatori grezzi: CUP, CIG, dataset_id, notice_id, IPA della SA. Un terzo deve poter ricostruire l'analisi indipendentemente.

### 3.5 Lingua e contesto italiani

Tutti gli output sono in italiano. Codici tassonomici nativi (CPV, NUTS, IPA, codici misura PNRR). Riferimenti normativi corretti (D.Lgs 36/2023 artt. 37, 76, 77).

Le **slash command, descrizioni e metadata del plugin nel marketplace possono essere in inglese** per discoverability, ma i prompt delle skill e l'output sono italiani.

### 3.6 Riproducibilità

Stessa query con stessi parametri produce stesso risultato fino al successivo aggiornamento upstream. Le skill non devono introdurre randomness né dipendenze dall'ora del giorno.

### 3.7 Non-invenzione

Quando una fonte è muta o un identificatore non risolve, dichiararlo apertamente. L'assenza di dato è informazione utile.

**Forma raccomandata**: "Il CUP I32E22000560006 risulta presente su OpenPNRR ma non ha CIG associati su ANAC al momento della lettura. Questo può indicare: (a) progetto in fase di programmazione pre-bando, (b) CUP cancellato, (c) ritardo di trasmissione ANAC. Non è possibile distinguere tra queste ipotesi automaticamente."

---

## 4. Struttura del repository

### 4.1 Layout proposto

```
industrial-procurement-plugin/
├── .claude-plugin/
│   ├── plugin.json           # manifest del plugin
│   └── marketplace.json      # se anche marketplace (vedi 5.2)
├── commands/                 # slash command, uno per capability
│   ├── digest-pregara.md
│   ├── pin-radar.md
│   ├── scheda-opportunita.md
│   ├── profilo-sa.md
│   └── reconciliation-pnrr.md
├── skills/                   # skill discovery-on-demand
│   └── procurement-italy/
│       └── SKILL.md
├── agents/                   # sub-agent specializzati
│   └── pre-gara-analyst.md
├── docs/
│   ├── INSTALLATION.md
│   ├── CONFIGURATION.md       # come puntare a server pro vs core
│   ├── PROMPT_PATTERNS.md     # esempi di trigger conversazionali
│   └── PRINCIPI.md             # i 7 principi di output
├── examples/
│   └── sample_outputs/         # esempi reali di output per ogni capability
├── README.md
├── CHANGELOG.md
└── LICENSE                     # MIT
```

### 4.2 Cosa va in `commands/` vs `skills/` vs `agents/`

- **commands**: entry point discoverable. Brevi, parametrici, ognuno chiama una skill o un agent. L'utente li vede in `/`.
- **skills**: la *logica di orchestrazione* di una capability. Lunghi, dettagliati, in italiano. Documentano per Claude come concatenare i tool MCP del server, come strutturare l'output, come gestire i casi edge (fonti mute, ID non risolvibili).
- **agents**: sub-agent invocabili quando una capability richiede ragionamento multi-step esteso o quando si vuole isolare il contesto. Esempio: `pre-gara-analyst` per il digest settimanale, che può fare 20-30 tool call e produce un report lungo.

### 4.3 Il manifesto `plugin.json`

Deve dichiarare:

- **name**, **version**, **description** (in inglese per marketplace)
- **author**
- **mcpServers**: dichiarazione dei MCP server di cui il plugin ha bisogno (almeno `industrial-mcp`)
- **commands**, **skills**, **agents**: path alle rispettive directory
- **keywords** per discoverability
- **license**: MIT

---

## 5. Distribuzione

### 5.1 Tre canali

1. **Marketplace ufficiale Claude Code** (curato da Anthropic). Inclusione discrezionale, ma è il canale con più visibilità.
2. **Marketplace community** (in-app submission form). Inclusione standard. Tipicamente il primo step.
3. **GitHub diretto** (`claude plugin install owner/repo`). Sempre disponibile, utile per beta tester e early adopter.

### 5.2 Marketplace.json (se il repo è anche marketplace)

Il plugin può essere distribuito anche dal suo proprio repository come marketplace. Pattern utile per:

- Bootstrap prima di essere accettato nel marketplace community
- Distribuzione a clienti beta con `claude plugin install`
- Self-hosting per clienti enterprise che vogliono evitare il marketplace pubblico

### 5.3 Cosa serve per "ship-ready"

Prima di pubblicare nel marketplace:

- [ ] README chiaro con installation, configurazione, esempi
- [ ] Almeno un sample output per ogni capability in `examples/`
- [ ] Versione semantica (0.1.0 per il primo rilascio)
- [ ] CHANGELOG iniziale
- [ ] LICENSE MIT
- [ ] Test manuale di ogni slash command con MCP server core attivo
- [ ] Documentazione su come configurare il puntamento a un server pro hosted (anche se il server pro non esiste ancora, predisporre la sezione)
- [ ] Screenshot o demo gif di un output realistico

### 5.4 Configurazione free vs pro

Il plugin supporta due modalità di funzionamento:

**Modalità free (default)**: punta a `industrial-mcp` installato localmente. L'utente installa il MCP server con `pip install industrial-mcp` e avvia in stdio. Funziona, è lento, capability limitate (no DB locale → query lente, no entity resolution avanzata).

**Modalità pro (futura)**: punta a `https://api.tuodominio.it/mcp/` con `Authorization: Bearer <token>`. Velocità istantanea, dataset arricchito, tutte le capability piene.

Documentare in `docs/CONFIGURATION.md` come switchare. Non bloccare l'utente nel free se il pro non è ancora live: predisporre l'infrastruttura di configurazione fin dall'inizio per non rompere compatibilità in futuro.

---

## 6. Strategia commerciale del plugin

### 6.1 Il plugin è marketing

Il plugin è **sempre open MIT**. Non c'è ragione di chiuderlo: i prompt sono ricostruibili in un pomeriggio e un plugin chiuso non viene accettato nel marketplace community con la stessa facilità.

Il plugin è la vetrina e il lead generator. Più persone lo installano, più discovery, più feedback, più contatti commerciali per il server pro.

### 6.2 La leva di conversione

Il plugin in modalità free funziona ma con limiti percepibili:

- Query lente (ogni capability fa N chiamate upstream ad ANAC/TED/OpenPNRR)
- Capability Reconciliation PNRR è lenta o limitata a 1 misura per query
- Buyer profile richiede 30+ tool call e brucia token
- Niente cross-source entity resolution avanzata

In modalità pro (server hosted con DB):

- Query istantanee
- Reconciliation su misure intere o regioni
- Buyer profile in singola chiamata
- Entity resolution con confidence score

L'utente sperimenta i limiti del free → upgrade al pro. Modello validato da Bigdata.com/RavenPack.

### 6.3 Cosa NON aggiungere al plugin per proteggere il pro

Tentazione da evitare: aggiungere logica di parsing dei bulk ANAC dentro le skill del plugin. Diventerebbe lento e instabile, ma soprattutto **regalerebbe gratuitamente la logica che giustifica il server pro**.

La regola: il plugin orchestra, il server fornisce. Se una capability è troppo lenta nel free, è normale e voluto. Non risolverlo client-side.

---

### 7.1 Trappole da evitare

- Pubblicare con 5 capability tutte mediocri invece di 1 capability eccellente
- Mettere logica di parsing dati nelle skill (deve stare nel MCP server)
- Bloccare l'utente nel free perché il pro non esiste ancora
- Promettere capability "fuori scope" (network analysis, ESG scoring) nella descrizione del marketplace
- Sovraingegnerizzare i sub-agent prima di averli usati su un workflow reale
- Aggiungere dipendenze ad altri MCP server senza necessità

### 7.2 Quattro regole non negoziabili

1. **Mai pubblicare una capability che non rispetta i 7 principi UX**
2. **Mai aggiungere capability nuove prima di aver migliorato quelle esistenti**
3. **Il plugin segue il MCP server, non lo guida** (se serve un dato che il MCP non espone, prima si estende il MCP, poi si aggiunge la skill)
4. **L'utente del plugin non deve mai vedere i nomi dei tool MCP sottostanti** — l'astrazione conversazionale è il prodotto

---

## 8. Compatibilità con il MCP server

### 8.1 Versionamento e dipendenze

Il plugin dichiara la versione minima del server `industrial-mcp` con cui è compatibile. Il MCP server segue semver:

- Patch (0.1.1): bug fix, schema dei tool invariato → plugin non richiede modifiche
- Minor (0.2.0): nuovi tool aggiunti, vecchi invariati → plugin può ignorare o estendersi
- Major (1.0.0): breaking change nei tool esistenti → plugin richiede aggiornamento

### 8.2 Cosa il plugin si aspetta dal MCP server

Le skill del plugin assumono l'esistenza di certi tool MCP. Mantenere allineato:

**Già esistenti** (utilizzabili da subito):
- `anac_*` per dataset/CIG search
- `ted_search`, `ted_get_notice_xml`
- `openpnrr_*` per missioni, misure, scadenze, progetti
- `opencoesione_*` per URL builder
- `consip_search_bandi`
- `dati_search`, `dati_get_dataset`

**Da implementare nel MCP** per le capability piene (vedi context document `industrial-mcp`):
- `anac_search_records`, `anac_get_record`, `anac_sa_history` (record-level)
- `opencoesione_search_progetti`, `opencoesione_get_progetto`
- `programmazione_search_biennale`, `programmazione_search_triennale_lavori`
- `ted_pin_italy` (convenience filter)

Le skill possono essere scritte in modalità degraded: usano i tool esistenti per ora, con la nota che alcune sotto-sezioni dell'output sono limitate finché il MCP non aggiunge i tool record-level.

### 8.3 Convenzioni di output dei tool MCP

Le skill assumono che ogni tool MCP restituisca:

- Dati strutturati JSON (no markdown libero, no testo non parsabile)
- Un campo `provenance` con URL e dataset_id ove applicabile
- Un campo `ingested_at` o `read_at` per la freshness
- Errori espliciti (`{"error": "...", "fallback": null}`) invece di silent fail

Se il MCP server non rispetta queste convenzioni, va segnalato come bug nel repo `industrial-mcp` invece di workaround nel plugin.

---

## 9. Checklist per Claude Code di pianificazione

Quando si pianifica un sprint o una feature su questo repository, porsi queste domande prima di iniziare:

### 9.1 Domande di prodotto

1. La feature riguarda una delle 5 capability MVP o ne propone una nuova?
2. Se nuova: è dentro le 3 explicit "fuori scope" (network, anomaly, ESG)? Se sì, riconsiderare.
3. Quale trigger conversazionale tipico la attiva? Documentarlo prima del codice.
4. Quale output atteso? Esiste un sample da scrivere prima della skill?

### 9.2 Domande architetturali

1. La feature richiede un tool MCP che esiste nel server `industrial-mcp`?
2. Se no, va prima estesa il server (PR su quel repo) o si può degradare la capability?
3. Quale slash command la attiva? Va aggiunta a `commands/`?
4. Va in skill esistente o richiede skill nuova?
5. Coinvolge un sub-agent o sta in una skill diretta?

### 9.3 Domande UX

1. L'output rispetta i 7 principi (provenance, confidence, freshness, audit, lingua, riproducibilità, non-invenzione)?
2. È in italiano fluente, non traduzione meccanica?
3. È leggibile senza conoscere i nomi dei tool MCP sottostanti?
4. Esiste un sample realistico in `examples/`?
5. Cosa fa la skill se la fonte è muta? Genera errore, restituisce risultato vuoto con spiegazione, o "non disponibile"?

### 9.4 Domande di distribuzione

1. La feature è disponibile in modalità free (server locale) o solo pro?
2. Se solo pro: c'è un fallback degraded per il free?
3. La descrizione del plugin nel marketplace va aggiornata?
4. Va aggiunta una entry al CHANGELOG?
5. La version del `plugin.json` va bumpata?

### 9.5 Trappole specifiche del plugin

- Non scrivere prompt in inglese se l'output è in italiano
- Non promettere capability che il MCP server core non può supportare nemmeno parzialmente
- Non esporre nomi di tool MCP all'utente nell'output ("Ho chiamato `anac_search_records`...") — è dettaglio implementativo
- Non aggiungere parsing/business logic nelle skill — sta nel server
- Non rompere la modalità free per migliorare il pro (il free deve restare utilizzabile)
- Non assumere che tutti gli utenti abbiano configurato il server pro — il default deve essere il free locale
- Non dimenticare di tradurre i messaggi di errore del MCP server in linguaggio user-friendly italiano

---

## 10. Riferimenti incrociati

- Repository fratello `industrial-mcp` (https://github.com/fed3c3sa/industrial-data-mcp) : vedi `docs/industrial_procurement_context.md` per architettura backend, scelte di DB, principi ship-first generali del progetto.
- Marketplace Claude Code: documentazione ufficiale Anthropic per submission, manifest, struttura plugin.
