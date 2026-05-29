# Session handoff — industrial-procurement-plugin

**Data sessione**: 2026-05-28
**Stato**: Implementazione completa del piano approvato (12/12 task)

---

## Cosa e' stato fatto

### Contesto

Il progetto e' un Claude Code plugin che permette query in linguaggio naturale all'ecosistema della spesa pubblica italiana, con output professionali in italiano e piena provenienza delle fonti. L'architettura e' divisa in due repo:

- `industrial-data-mcp/` — server MCP FastMCP 2.x con 12+ moduli sorgente
- `industrial-procurement-plugin/` — plugin Claude Code con 5 skill e relativa configurazione

Il piano completo e' in `.claude/plans/procurement-plugin-mcp-first-detailed-skills.md`.

---

### Sprint 1 — Estensioni MCP (`industrial-data-mcp`)

Tutti i gap identificati rispetto alle skill del plugin sono stati colmati.

#### Nuovi file

| File | Cosa fa |
|------|---------|
| `src/industrial_mcp/sources/programmazione.py` | Registro biennale/triennale regionale; `programmazione_search_biennale` (in-memory, no HTTP) |

#### File modificati

| File | Cosa e' stato aggiunto |
|------|----------------------|
| `src/industrial_mcp/sources/ted.py` | `build_pin_italy_query()` (funzione pura, importabile nei test) + `ted_pin_italy` tool |
| `src/industrial_mcp/sources/opencoesione.py` | `describe_dataset()` + `download_parquet_url()` con `ValueError` esplicito; registrati come `opencoesione_describe_dataset` e `opencoesione_download_parquet` |
| `src/industrial_mcp/sources/environment.py` | `REGIONAL_PORTALS` dict (Veneto, Lombardia, Piemonte, Lazio) + `env_regional_search_link` tool |
| `src/industrial_mcp/server.py` | Import e registrazione di `programmazione` nel loop `build_mcp()` |
| `tests/test_url_builders.py` | Test per `programmazione`, `opencoesione_describe`, `opencoesione_download_parquet`, `env_regional` |
| `tests/test_ted_mocked.py` | Test per `build_pin_italy_query` (3 test case) |
| `tests/test_server.py` | Set `expected` esteso con i 5 nuovi tool name |

**Risultato test**: 26/26 pass (esclusi test `live` che richiedono rete)

#### Ambiente di sviluppo MCP

Il repo non aveva un virtualenv. E' stato creato:

```bash
cd industrial-data-mcp
python3.12 -m venv .venv --without-pip
curl -sS https://bootstrap.pypa.io/get-pip.py | .venv/bin/python3.12
.venv/bin/pip install -e ".[dev]"
```

Usare sempre `.venv/bin/pytest` (non il pytest globale) — il progetto richiede Python >= 3.11 e `fastmcp>=2.3,<3`.

---

### Sprint 2 — Plugin scaffold (`industrial-procurement-plugin`)

#### Nuovi file

| File | Cosa fa |
|------|---------|
| `plugin.json` | Manifest del plugin (name, version, license, skills dir, minServerVersion) |
| `.mcp.json` | Due server MCP: `industrial-mcp-free` (stdio) e `industrial-mcp-pro` (streamable-http + `headersHelper`) |
| `skills/digest-pregara/SKILL.md` | Protocollo Italian per analisi pre-gara (programmazione + TED PIN + OpenPNRR) |
| `skills/pin-radar/SKILL.md` | Protocollo per monitoraggio PIN TED Italia con mappatura NUTS |
| `skills/scheda-opportunita/SKILL.md` | Protocollo per scheda dettagliata gara (ANAC + OpenPNRR + OpenCoesione + TED) |
| `skills/profilo-sa/SKILL.md` | Protocollo per profilo stazione appaltante da dataset ANAC |
| `skills/reconciliation-pnrr/SKILL.md` | Protocollo riconciliazione PNRR con 4 flag marker stabili |
| `docs/CONFIGURATION.md` | Guida configurazione free/pro con tabella variabili d'ambiente |
| `examples/sample_outputs/digest-pregara.md` | Output sintetico di esempio con provenienza e audit trail |
| `examples/sample_outputs/pin-radar.md` | idem |
| `examples/sample_outputs/scheda-opportunita.md` | idem |
| `examples/sample_outputs/profilo-sa.md` | idem |
| `examples/sample_outputs/reconciliation-pnrr.md` | idem |
| `tests/test_manifests.py` | Verifica schema `plugin.json` e struttura `.mcp.json` |
| `tests/test_skill_structure.py` | Verifica presenza sezioni e anchor nelle 5 SKILL.md + sample outputs |

**Risultato test**: 8/8 pass

---

## Cosa resta da fare nella prossima sessione

### Alta priorita — Verifica live

Questi due punti erano "open questions" nel piano e non sono stati risolti programmaticamente. Devono essere verificati manualmente o con una sessione di ricerca.

#### 1. Sintassi TED API v3 per notice-type=PIN

**Problema**: il valore `notice-type=PIN` e' stato implementato basandosi sulla documentazione trovata durante la pianificazione. L'API TED v3 potrebbe usare il codice form `F01` oppure un valore diverso.

**Come verificare**:
```bash
curl -s -X POST https://api.ted.europa.eu/v3/notices/search \
  -H "Content-Type: application/json" \
  -d '{"query":"notice-type=PIN AND place-of-performance=ITA","limit":3,"fields":["publication-number","notice-type"]}' \
  | python3 -m json.tool
```

Se la risposta e' vuota o errore, provare con `notice-type=F01`.

**File da aggiornare se necessario**: `industrial-data-mcp/src/industrial_mcp/sources/ted.py` — funzione `build_pin_italy_query()`

#### 2. URL portali regionali VAS/VIA

**Problema**: i 4 URL in `REGIONAL_PORTALS` (Veneto, Lombardia, Piemonte, Lazio) sono stime plausibili ma non verificate live.

**URL attuali nel codice** (`environment.py`):
- Veneto: `https://www.regione.veneto.it/web/ambiente-e-sicurezza/valutazione-impatto-ambientale`
- Lombardia: `https://silvia.regione.lombardia.it/`
- Piemonte: `https://www.regione.piemonte.it/web/temi/ambiente-territorio/valutazioni-ambientali/valutazione-impatto-ambientale-via`
- Lazio: `https://www.regione.lazio.it/rl_ambiente/web/via/`

**Come verificare**: aprire ciascun URL in un browser e confermare che sia raggiungibile e mostri il portale VIA/VAS corretto.

**File da aggiornare se necessario**: `industrial-data-mcp/src/industrial_mcp/sources/environment.py` — dict `REGIONAL_PORTALS`

---

### Media priorita — Test end-to-end

Il plugin non e' stato testato installato in Claude Code. Per validare il flusso completo:

1. Installare `industrial-mcp` locale:
   ```bash
   cd industrial-data-mcp && pip install -e .
   ```
2. Installare il plugin in Claude Code:
   ```bash
   claude plugin install /home/marco/personal/industrial-procurement/industrial-procurement-plugin
   ```
3. Testare ciascuna delle 5 skill con un input reale:
   - `/digest-pregara servizi di ingegneria in Puglia CPV 71000000`
   - `/pin-radar servizi informatici Lombardia`
   - `/scheda-opportunita CUP J81B22000540006`
   - `/profilo-sa ASL Bari`
   - `/reconciliation-pnrr CUP H87G22001120006`

Verificare che:
- Il server MCP si avvii correttamente via stdio
- I tool call appaiano nell'output di debug
- Le sezioni richieste dal protocollo (`## Opportunita rilevate`, `## Audit trail`, ecc.) siano presenti nell'output
- Non vengano esposti i nomi degli strumenti MCP nell'output finale

---

### Bassa priorita — Miglioramenti futuri

| Area | Descrizione |
|------|-------------|
| `programmazione.py` — dati | Il `DATASET_REGISTRY` ha 4 voci sintetiche. Aggiungere dataset reali: cercare su portali regionali e ANAC i programmi biennali pubblicati per Lombardia, Puglia, Veneto, Lazio, Toscana |
| Server pro | Il server `industrial-mcp-pro` dichiarato in `.mcp.json` non esiste ancora. Quando viene costruito, aggiornare l'URL in `.mcp.json` |
| `consip.py` | Il modulo Consip esistente espone `consip_search_bandi` ma non e' usato da nessuna skill. Valutare se aggiungere ricerca Consip a `/digest-pregara` |
| VIES | `imprese_check_vat` e' disponibile — potrebbe essere utile per verificare i fornitori in `/profilo-sa` |
| Soglie UE | Le soglie EUR 221.000 / EUR 5.538.000 usate in `digest-pregara` vanno aggiornate ogni 2 anni (revisione CE). Prossima revisione: 2026 |
| Marketplace | Prima di pubblicare sul marketplace Claude Code, verificare i requisiti di submission: sample outputs, README, license, test coverage |

---

## Struttura repo finale

```
industrial-procurement-plugin/
├── .claude/
│   ├── plans/
│   │   └── procurement-plugin-mcp-first-detailed-skills.md  # piano completo
│   ├── SESSION_HANDOFF.md                                    # questo file
│   └── settings.json
├── .mcp.json
├── plugin.json
├── docs/
│   ├── CONFIGURATION.md
│   └── industrial_procurement_plugin_context.md
├── examples/
│   └── sample_outputs/
│       ├── digest-pregara.md
│       ├── pin-radar.md
│       ├── profilo-sa.md
│       ├── reconciliation-pnrr.md
│       └── scheda-opportunita.md
├── skills/
│   ├── digest-pregara/SKILL.md
│   ├── pin-radar/SKILL.md
│   ├── profilo-sa/SKILL.md
│   ├── reconciliation-pnrr/SKILL.md
│   └── scheda-opportunita/SKILL.md
└── tests/
    ├── test_manifests.py
    └── test_skill_structure.py

industrial-data-mcp/
├── .venv/                    # Python 3.12, fastmcp 2.14.7
├── src/industrial_mcp/
│   ├── server.py             # registra 12 moduli incluso programmazione
│   └── sources/
│       ├── programmazione.py # NUOVO
│       ├── ted.py            # +build_pin_italy_query, +ted_pin_italy
│       ├── opencoesione.py   # +describe_dataset, +download_parquet_url
│       └── environment.py    # +REGIONAL_PORTALS, +env_regional_search_link
└── tests/
    ├── test_url_builders.py  # +programmazione, +opencoesione, +environment
    ├── test_ted_mocked.py    # +build_pin_italy_query (3 test)
    └── test_server.py        # +5 nuovi tool name nel set expected
```
