# industrial-procurement-plugin

**Plugin Claude Code per l'ecosistema della spesa pubblica italiana.** Interroga in linguaggio naturale contratti pubblici (ANAC), bandi europei (TED), progetti a fondi strutturali (OpenCoesione) e Piano Nazionale di Ripresa e Resilienza (OpenPNRR) — e ricevi risposte strutturate in italiano formale con piena provenance delle fonti.

Distribuisce **7 skill** e integra il server [`industrial-mcp`](https://github.com/fed3c3sa/industrial-data-mcp) (50+ tool) che gestisce l'accesso ai dati.

**Skill di punta — `/analisi-disciplinare`:**
```
"/analisi-disciplinare https://www.agcm.it/.../disciplinare.pdf CIG B16EFD0453"
```
→ scarica il PDF, estrae la tabella criteri completa (80 punti tecnica / 20 economica, 7 sub-criteri verificati), requisiti di partecipazione, formula economica — tutto citato con fonte e data.

---

## Architettura (due repository, un prodotto)

```
┌─────────────────────────────────────────┐     spawns (stdio)     ┌────────────────────────────┐
│  industrial-procurement-plugin           │ ─────────────────────► │  industrial-mcp  (server)  │
│  (questo repo — il plugin Claude Code)   │                        │  github.com/fed3c3sa/      │
│                                          │   mcp__industrial-     │  industrial-data-mcp       │
│  .claude-plugin/plugin.json   manifest   │   mcp-free__*  tool    │                            │
│  .claude-plugin/marketplace.json         │ ◄───────────────────── │  50+ tool su FastMCP:      │
│  .mcp.json   ─ dichiara i server MCP     │       risultati tool   │  ANAC · TED · OpenCoesione │
│  skills/     ─ 7 protocolli SKILL.md     │                        │  OpenPNRR · doc · CPV · …  │
└─────────────────────────────────────────┘                        └────────────────────────────┘
```

- **Il plugin** = orchestrazione e presentazione: skill che codificano protocolli di output professionali in italiano (sezioni, provenance, audit trail), più il `.mcp.json` che collega il server.
- **Il server MCP** = layer dati: scarica e interroga open data italiani ed europei, recupera e analizza documenti di gara (PDF/HTML), restituisce risultati tipizzati. Vive nel proprio repo per essere riutilizzabile da qualsiasi client MCP.
- **Claude legge, non regex**: l'analisi documentale (estrazione criteri, requisiti di partecipazione) è svolta da Claude che legge il testo completo del documento — senza pattern regex fragili. Funziona con qualsiasi layout di tabella PDF.

Il `.mcp.json` del plugin dichiara due server:
- `industrial-mcp-free` — stdio locale (`industrial-mcp` sul PATH). **Questo è quello che si usa.**
- `industrial-mcp-pro` — placeholder per un endpoint hosted futuro; appare come *disconnected* finché il servizio non esiste. Non crea problemi.

---

## Installazione

**Prerequisiti:** [Claude Code](https://claude.com/claude-code) ≥ 2.1, Python ≥ 3.11, [`uv`](https://docs.astral.sh/uv/).

### 1. Installa il server MCP (il motore dati)

```bash
# Dal repo del server (https://github.com/fed3c3sa/industrial-data-mcp)
git clone https://github.com/fed3c3sa/industrial-data-mcp.git
uv tool install ./industrial-data-mcp          # aggiunge `industrial-mcp` al PATH
industrial-mcp --help                          # verifica
```

### 2. Installa il plugin

```bash
git clone https://github.com/sassarini-marco/industrial-procurement-plugin.git

claude plugin marketplace add ./industrial-procurement-plugin
claude plugin install industrial-procurement@industrial-procurement-local
```

Riavvia Claude Code e verifica:

```bash
claude plugin list    # → industrial-procurement … ✔ enabled
claude mcp list       # → plugin:…:industrial-mcp-free … ✓ Connected
```

Nessuna API key richiesta — tutte le fonti sono pubbliche.

> **La prima interrogazione scarica ~280 MB** di dati ANAC/OpenCoesione in Parquet nella cartella `~/.cache/industrial-mcp/` (una tantum; le interrogazioni successive sono veloci). Elimina la cartella per forzare un aggiornamento.

---

## Utilizzo

### Interrogazione in linguaggio naturale

I tool MCP si attivano automaticamente:

```
"Tutte le aggiudicazioni della P.IVA 02895590962 sopra 1M, valida la P.IVA su VIES
 e dammi il link al Registro Imprese."

"Progetti FESR 2021-2027 in Lombardia su OpenCoesione: totale finanziato,
 impegnato, pagato e top 5 beneficiari."

"Cerca su TED le procedure italiane sopra 5 M€ con CPV 45 pubblicate negli ultimi 90 giorni."
```

### Le 7 skill (output italiano strutturato con provenance)

| Comando | Funzione |
|---|---|
| `/analisi-disciplinare <URL> [CIG]` | Scarica e analizza un disciplinare/capitolato PDF: criteri di valutazione completi con verifica della somma, requisiti di partecipazione, formula economica |
| `/pin-radar <CPV / regione>` | Monitora gli avvisi di preinformazione TED (PIN) per l'Italia, mappati su regioni NUTS |
| `/scheda-opportunita <CIG \| CUP \| ente>` | Scheda di intelligence su un'opportunità: ANAC + OpenPNRR + OpenCoesione + TED |
| `/profilo-sa <stazione appaltante>` | Profilo quantitativo di una stazione appaltante dai dati ANAC |
| `/reconciliation-pnrr <CUP>` | Riconcilia un CUP tra OpenPNRR / OpenCoesione / ANAC e segnala discrepanze |
| `/digest-pregara <settore / CPV / regione>` | Digest pre-gara: programmazione regionale + PIN TED + PNRR |
| `/consultazioni-radar <settore>` | Monitora consultazioni esplorative Consip/TED e bandi formali aperti |

Vedi `examples/sample_outputs/` per output reali con la query che li ha generati.

---

## Esempio reale 

<details open>
<summary><b>Analisi disciplinare — AGCM, sorveglianza sanitaria (CIG B16EFD0453)</b></summary>

> **Query:** `/analisi-disciplinare https://www.agcm.it/dotcmsdoc/gare/2024/CIG_B16EFD0453_Disciplinare_di_gara_sorveglianza_sanitaria_signed.pdf CIG B16EFD0453`

**Output (estratto):**

**Criterio di aggiudicazione:** OEPV — tecnica **80 punti** / economica **20 punti** · Confidenza: **Alta**

| Criterio | Punti max | Metodo |
|---|---:|---|
| Offerta tecnica (totale) | **80** | |
| — a Struttura organizzativa (a1+a2+a3) | 15 | Discrezionale |
| — b Conduzione del servizio (b1+b2) | 20 | Discrezionale |
| — c Piano sorveglianza sanitaria / Medico competente | 13 | Discrezionale |
| — d Corsi di formazione — progettazione | 15 | Discrezionale |
| — e Selezione docenti + proposte migliorative | 10 | Discrezionale |
| — f Esperienze (f1 RSPP: 3 + f2 Medico: 2) | 5 | Discrezionale |
| — g Certificazioni (g1 ISO 9001: 1 + g2 parità di genere: 1) | 2 | Tabellare |
| Offerta economica — formula lineare PE_i = 20 × R_i/R_max | **20** | Formula |
| **TOTALE** | **100** | |

**Verifica:** 15+20+13+15+10+5+2 = **80 ✓**

**Requisiti:** iscrizione CCIAA + 1 contratto analogo ≥ EUR 100.000 nell'ultimo quinquennio + curricula RSPP/Medico Competente (3 nominativi ciascuno) + abilitazione MEPA.

*(fonte: PDF AGCM) — Dati letti il 2026-06-04*
</details>

<details>
<summary><b>PIN Radar — avvisi di preinformazione TED, servizi IT</b></summary>

> **Query:** `/pin-radar Trova PIN TED attivi per servizi informatici (CPV 72000000), probabili gare entro 6 mesi, Italia.`

**Output (estratto):** 10 PIN attivi trovati su 46 totali. Esempi:

| Ente | PIN | CPV | Scadenza | Probabilità |
|---|---|---|---|---|
| Politecnico di Torino | 380487-2025 | 72000000 | 2025-07-31 | Alta |
| ASL Toscana Nord Ovest | 530725-2025 | 72200000 | n.d. | Media |

*(fonte: TED Search API v3) — Dati letti il 2026-06-04*
</details>

<details>
<summary><b>Scheda opportunità — Azienda Zero, CPV 72</b></summary>

> **Query:** `/scheda-opportunita Azienda Zero su servizi informatici (CPV 72)`

Valutazione trasformazione **Alta** · 7 PIN TED attivi (ultimo: 338240-2026, 18/05/2026) · 5 aggiudicazioni ANAC CPV 72 negli ultimi 24 mesi (aggregato EUR 8,2M) · mercato competitivo, nessun incumbent dominante · bando atteso Q3-Q4 2026.
</details>

<details>
<summary><b>Profilo stazione appaltante — ASL Bari</b></summary>

> **Query:** `/profilo-sa ASL Bari`

| Anno | N. affidamenti | Importo totale | Importo medio |
|---|---:|---:|---:|
| 2023 | 312 | EUR 48.700.000 | EUR 156.000 |
| 2024 | 287 | EUR 41.200.000 | EUR 143.000 |

Top CPV: 33000000 (dispositivi medici), 72000000 (IT), 79000000 (servizi). Top fornitore: Siemens Healthineers (3 aggiudicazioni, EUR 4,1M).
</details>

<details>
<summary><b>Riconciliazione PNRR — CUP con discrepanza importi</b></summary>

> **Query:** `/reconciliation-pnrr CUP H87G22001120006`

Flag **IMPORTO_SOPRA_FINANZIATO** — importo aggiudicato ANAC (EUR 1.250.000) supera il finanziamento OpenCoesione (EUR 850.000). Flag **CUP_ORFANO** su CUP H87G22001121006 — presente su OpenCoesione, nessun CIG ANAC trovato.
</details>

---

## Cosa fa bene — e i limiti onesti

**Punti di forza:**
- `/analisi-disciplinare`: estrae criteri di valutazione completi da qualsiasi PDF digitale (non scansionato). Claude legge il documento intero — nessun parser parziale.
- Ricerca per-record su ANAC (per regione/importo/data/CPV, per CUP, per P.IVA).
- Aggregati OpenCoesione, ricerca TED, navigazione misure/milestone OpenPNRR.
- Validazione VIES e link Registro Imprese.
- Riconciliazione cross-source CUP↔CIG↔beneficiario.
- **Ogni cifra è citata con fonte e data. Il plugin non inventa mai dati.**

**Limiti dichiarati** (indicati inline nell'output):
- `/analisi-disciplinare` richiede PDF nativo digitale (testo selezionabile). PDF scansionati: dichiarato esplicitamente con suggerimento OCR.
- I dati ANAC sono uno **snapshot mensile recente**, non un archivio storico pluriennale.
- OpenPNRR espone **allocazioni pianificate**, non la spesa effettiva percentuale.
- Le aggiudicazioni ANAC non hanno un tag queryabile per misura PNRR specifica.

---

## Sviluppo

```bash
# Test manifest + struttura skill + harness eval
python3 -m pytest tests/ -q

# Valida il manifest del plugin
claude plugin validate industrial-procurement-plugin

# Eval frozen (deterministico, senza API key)
python3 bench/eval_runner.py --frozen

# Eval live su una singola skill
python3 bench/eval_runner.py --skill analisi-disciplinare --live

# Eval su un singolo caso
python3 bench/eval_runner.py --case 3.7-004 --live

# Report eval
python3 bench/eval_report.py
```

---

## Autori e licenza

Marco Sassarini · Federico Cesarini. MIT — vedi [`LICENSE`](LICENSE).

Vedi [`CHANGELOG.md`](CHANGELOG.md) per la cronologia delle modifiche.
