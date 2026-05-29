# industrial-procurement-plugin

**A Claude Code plugin for the Italian public-spending ecosystem.** Ask questions in plain language about public contracts (ANAC), EU tenders (TED), cohesion-fund projects (OpenCoesione), and the National Recovery Plan (OpenPNRR) — and get structured, professional Italian-language answers with full source provenance.

It ships **5 skills** and bundles the [`industrial-mcp`](https://github.com/fed3c3sa/industrial-data-mcp) server (46 tools) that does the actual data work.

```
"Ultime 10 aggiudicazioni ANAC sopra 500.000 € in Friuli negli ultimi 60 giorni:
 CIG, aggiudicatario, P.IVA, importi, ribasso."
```
→ one tool call, a clean table, every figure tagged with its source and snapshot date.

---

## Architecture (two repos, one product)

```
┌─────────────────────────────────────────┐     spawns (stdio)     ┌────────────────────────────┐
│  industrial-procurement-plugin           │ ─────────────────────► │  industrial-mcp  (server)  │
│  (this repo — the Claude Code plugin)    │                        │  github.com/fed3c3sa/      │
│                                          │   mcp__industrial-     │  industrial-data-mcp       │
│  .claude-plugin/plugin.json   manifest   │   mcp-free__*  tools   │                            │
│  .claude-plugin/marketplace.json         │ ◄───────────────────── │  46 tools over FastMCP:    │
│  .mcp.json   ─ declares the MCP servers  │       tool results     │  ANAC · TED · OpenCoesione │
│  skills/     ─ 5 SKILL.md protocols      │                        │  OpenPNRR · VIES · …       │
└─────────────────────────────────────────┘                        └────────────────────────────┘
```

- **The plugin** = orchestration + presentation: skills that encode professional Italian output protocols (sections, provenance, audit trail), plus the `.mcp.json` that wires in the server.
- **The MCP server** = the data layer: downloads/queries Italian & EU open data and returns typed results. Lives in its own repo so it's reusable by any MCP client.

The plugin's `.mcp.json` declares two servers:
- `industrial-mcp-free` — local stdio (`industrial-mcp` on your PATH). **This is what you use.**
- `industrial-mcp-pro` — a placeholder for a future hosted endpoint; shows as *disconnected* until that service exists. Harmless.

---

## Install

**Prerequisites:** [Claude Code](https://claude.com/claude-code) ≥ 2.1, Python ≥ 3.11, and [`uv`](https://docs.astral.sh/uv/).

### 1. Install the MCP server (the data engine)

```bash
# From the server repo (https://github.com/fed3c3sa/industrial-data-mcp)
git clone https://github.com/fed3c3sa/industrial-data-mcp.git
uv tool install ./industrial-data-mcp          # puts `industrial-mcp` on your PATH
industrial-mcp --help                          # sanity check
```

### 2. Install this plugin

```bash
git clone https://github.com/sassarini-marco/industrial-procurement-plugin.git

# add it as a local marketplace, then install
claude plugin marketplace add ./industrial-procurement-plugin
claude plugin install industrial-procurement@industrial-procurement-local
```

Restart Claude Code. Verify:

```bash
claude plugin list           # → industrial-procurement … ✔ enabled
claude mcp list              # → plugin:…:industrial-mcp-free … ✓ Connected
```

That's it — no API keys (all sources are public).

> **First query downloads ~280 MB** of ANAC/OpenCoesione bulk data and caches it as Parquet under `~/.cache/industrial-mcp/` (one-time; later queries are fast). Delete that folder to force a refresh.

---

## Usage

### Just ask, in plain language
The MCP tools fire automatically:

```
"Tutte le aggiudicazioni della P.IVA 02895590962 sopra 1M, valida la P.IVA su VIES
 e dammi il link al Registro Imprese."

"Progetti FESR 2021-2027 in Lombardia su OpenCoesione: totale finanziato,
 impegnato, pagato e top 5 beneficiari."

"Cerca su TED le procedure italiane sopra 5 M€ con CPV 45 pubblicate negli ultimi 90 giorni."
```

### Or use the 5 skills (structured, provenance-rich Italian output)

| Slash command | What it does |
|---|---|
| `/digest-pregara <settore / CPV / regione>` | Pre-gara market scan: programmazione regionale + TED PIN + PNRR |
| `/pin-radar <CPV / regione>` | Monitor TED Prior Information Notices for Italy, mapped to NUTS regions |
| `/scheda-opportunita <CIG \| CUP \| ente>` | Full dossier on one opportunity across ANAC + OpenPNRR + OpenCoesione + TED |
| `/profilo-sa <stazione appaltante>` | Quantitative profile of a contracting authority from ANAC data |
| `/reconciliation-pnrr <CUP>` | Reconcile a CUP across OpenPNRR / OpenCoesione / ANAC and flag discrepancies |

See `examples/sample_outputs/` for what each produces.

---

## Esempi reali — domande e risposte (dal benchmark)

Questi sono casi presi dal benchmark Tier 1–5 (`bench/REPORT.md`), con **dati reali** restituiti dal plugin. Ogni cifra è etichettata con fonte e data dello snapshot; quando una fonte non copre il dato, il plugin **lo dichiara invece di inventarlo**.

<details open>
<summary><b>Tier 1 · ANAC — ultime aggiudicazioni per regione/importo/data</b></summary>

> **D:** *"Ultime 10 aggiudicazioni ANAC sopra 500.000 € in Friuli Venezia Giulia negli ultimi 60 giorni: CIG, stazione appaltante, oggetto, aggiudicatario, P.IVA, base d'asta, importo aggiudicato, ribasso %, data."*

**R (estratto):** una tabella con tutti i 9 campi richiesti, p.es.

| CIG | Data | Stazione appaltante | Aggiudicatario | P.IVA | Base € | Aggiud. € | Ribasso % |
|---|---|---|---|---|--:|--:|--:|
| B9C24FC1B6 | 28/04/2026 | ATER Gorizia | Marchiori Energie S.r.l. | 02780710303 | 19.380.911 | 17.421.224 | 10,11 |
| BB4DEEB215 | 16/04/2026 | Regione Aut. FVG | Vodafone Italia S.p.A. | 93026890017 | 2.780.400 | 2.780.400 | 0,0 |

*1 sola chiamata a `anac_search_awards`; ribasso ricalcolato; righe accordo-quadro segnalate come tali.*
</details>

<details>
<summary><b>Tier 1 · OpenCoesione — aggregati FESR per regione</b></summary>

> **D:** *"Conta i progetti FESR 2021-2027 in Friuli: totale finanziato, impegnato, pagato e top 5 beneficiari."*

**R:** **2.436 progetti** · finanziato **€ 580.697.473,96** · impegnato **€ 256.485.696,38** · pagato **€ 114.489.490,77**. Top beneficiario: Regione Autonoma FVG (€ 61,2 mln su 34 progetti, sommando le due denominazioni con lo stesso CF).
</details>

<details>
<summary><b>Tier 1 · TED — gare UE per CPV/valore/finestra</b></summary>

> **D:** *"15 procedure italiane sopra 5 M€ con CPV 45 (lavori) pubblicate negli ultimi 90 giorni: ente, oggetto, valore, scadenza."*

**R:** 718 bandi trovati, top-15 per valore — es. *Comune di Piacenza, concessione centro polisportivo, € 100,1 mln*; *RFI, adeguamento sagoma gallerie, € 42,6 mln (scad. 30/03/2026)*. Le scadenze mancanti nel record sintetico sono indicate come "n.d. via API" (presenti nell'XML del bando).
</details>

<details>
<summary><b>Tier 2 · P.IVA → scheda azienda + VIES + Registro Imprese</b></summary>

> **D:** *"P.IVA 02895590962 (Webuild): aggiudicazioni ANAC > 1M, progetti OpenCoesione, validazione VIES, link Registro Imprese. Scheda one-page."*

**R:** identità **VIES ✅ valida** (Webuild S.p.A., Rozzano MI), link diretto al Registro Imprese, e un caveat esplicito: 0 aggiudicazioni nello snapshot **non** significa nessun appalto (Webuild opera via ATI/sopra-soglia su TED) — con proposta di cross-check TED.
</details>

<details>
<summary><b>Tier 2 · Gruppo societario (due P.IVA aggregate)</b></summary>

> **D:** *"P.IVA 00629440322 (Fincantieri) vs 01294560329 (Fincantieri Infrastructure): aggiudicazioni ANAC + progetti OpenCoesione, output di gruppo."*

**R:** il plugin **scopre che Fincantieri è registrata sul Codice Fiscale 00397130584, non sulla P.IVA**, interroga entrambi, e produce la tabella di gruppo: valore aggiudicato combinato **€ 424,65 mln** (trainato dalla commessa ANAS SS-106 della controllata), più 2 progetti FESR Liguria (€ 1,3 mln) sulla capogruppo.
</details>

<details>
<summary><b>Tier 4–5 · Discovery & data-quality su CUP</b></summary>

> **D:** *"Misure PNRR a rischio (milestone mar–ago 2026, avanzamento < 60%) e ultimi CIG via CUP collegato."* · *"10 CIG PNRR con CUP valorizzato ma non risolto su OpenPNRR/OpenCoesione, classificati per anomalia."*

**R:** risolve la finestra milestone (218 nel 2026, tutte non conseguite), individua le 3 misure più esposte e ne ricava i CIG via `anac_awards_by_cup`; per la data-quality restituisce 10 CIG con CUP validi assenti da OpenCoesione e li classifica — incluso il rilevamento di **CUP segnaposto** (blocco progressivo tutto a zero) e di **uno stesso CUP condiviso da due stazioni appaltanti**.
</details>

> **Risultato complessivo del benchmark:** 11 query, **7 PASS · 3 PARTIAL · 0 FAIL**, nessun dato inventato. Dettaglio completo + tracce in [`bench/REPORT.md`](bench/REPORT.md).

---

## What it does well — and its limits

**Strengths:** record-level ANAC award search (by region/amount/date/CPV, by CUP, by P.IVA), OpenCoesione aggregates, TED search, OpenPNRR measure/milestone browsing, VIES validation + Registro Imprese links, and cross-source CUP↔CIG↔beneficiary reconciliation. **Every figure is sourced and dated; the agent never fabricates data.**

**Honest limits** (the agent states these in-line):
- ANAC awards have **no queryable PNRR-*misura* tag** → exact "all awards under measure M2C3-1.1" isn't filterable (keyword proxy only).
- ANAC data is a **recent monthly-snapshot window**, not the full multi-year archive.
- OpenPNRR exposes **planned allocations, not real spend %**.

A full Tier 1–5 capability benchmark (11 queries, 7 PASS / 3 PARTIAL / 0 FAIL, no hallucinated data) is in **[`bench/REPORT.md`](bench/REPORT.md)**. Reproduce with `python3 bench/run_benchmark.py`.

---

## Configuration

Optional environment variables (see [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md)):

| Variable | Default | Purpose |
|---|---|---|
| `INDUSTRIAL_MCP_CACHE_DIR` | `~/.cache/industrial-mcp` | Where bulk Parquet files are cached |
| `INDUSTRIAL_MCP_BULK_TTL` | `1209600` (14 days) | How long a cached snapshot is reused |
| `INDUSTRIAL_MCP_UA` | browser-style | User-Agent (Italian portals 403 generic bots) |
| `INDUSTRIAL_MCP_PRO_URL` / `_PRO_TOKEN` | — | Only if you run the hosted "pro" server |

---

## Development

```bash
# plugin manifest + skill-structure tests
python3 -m pytest industrial-procurement-plugin/tests -q

# validate the plugin / marketplace manifests
claude plugin validate industrial-procurement-plugin
```

## Authors & license

Marco Sassarini · Federico Cesarini. MIT — see [`LICENSE`](LICENSE).
