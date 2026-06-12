[![Version](https://img.shields.io/badge/version-0.3.0-blue)](https://github.com/sassarini-marco/abracabando-plugin/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Claude%20Code-orange)](https://claude.ai/code)

# AbracaBando

<div align="center">
  <img src="assets/hero.png" width="500" alt="AbracaBando — intelligence sulla spesa pubblica italiana">
</div>

**Quello che ti costa 3 ore, ad AbracaBando bastano 3 minuti. Tutto citato, tutto verificabile, zero invenzioni.**

---

Ogni anno la PA italiana aggiudica oltre 100 miliardi di euro in contratti, finanzia migliaia di progetti con fondi PNRR ed europei, pubblica centinaia di bandi su TED. Questi dati esistono, sono open data, sono ufficiali.

Sono anche distribuiti su cinque portali separati — ANAC, TED, OpenCoesione, OpenPNRR, Consip — con formati incompatibili, API diverse e zero integrazione tra loro.

Chi lavora su gare d'appalto, fondi pubblici o intelligence di mercato lo sa: **trovare, incrociare e verificare questi dati costa ore ogni settimana**. Ore spese su export Excel, copia-incolla tra portali, ricerche manuali che non si chiudono mai del tutto.

AbracaBando collega Claude direttamente a tutte queste fonti. Scrivi in italiano cosa ti serve. Ricevi una risposta strutturata e professionale, con fonte istituzionale e data di lettura per ogni singolo dato. In secondi.

### A chi serve

| Sei... | Ti permette di... |
|---|---|
| **Un'azienda che partecipa a gare** | Sapere chi ha vinto in passato, a quanto, con quale profilo tecnico — prima di decidere se concorrere |
| **Un'ESCo o società di efficientamento** | Intercettare opportunità prima del bando: PIN TED, programmazione regionale, misure PNRR non ancora a gara |
| **Un advisor o commerciale** | Costruire una scheda intelligence completa su un'opportunità in un minuto, non in un'ora |
| **Un auditor o ufficio compliance** | Riconciliare CUP, CIG e fondi PNRR automaticamente — con flag automatici su discrepanze e importi anomali |
| **Un giornalista o ricercatore** | Navigare la spesa pubblica con piena tracciabilità: ogni cifra ha fonte istituzionale e data di lettura |

---

## Installazione

**Prerequisiti:** [Claude Code](https://claude.ai/code) ≥ 2.1.

1. Installa il plugin:
   ```bash
   /plugin marketplace add sassarini-marco/abracabando-plugin
   /plugin install abracabando@abracabando
   ```
2. Riavvia Claude Code e verifica:
   ```bash
   claude plugin list    # → abracabando … ✔ enabled
   ```

Nessuna API key. Il server dati è ospitato — nessuna installazione aggiuntiva necessaria.

---

## Le 8 skill

| Skill | Cosa fa |
|---|---|
| `/abracabando:analisi-disciplinare <URL> [CIG]` | Scarica e analizza un disciplinare PDF: tabella criteri completa con verifica della somma, requisiti di partecipazione, formula economica — tutto estratto dal documento, niente inventato |
| `/abracabando:trova-bando-compatibile <profilo azienda>` | Trova bandi pubblici aperti compatibili con il profilo di un'azienda (settore CPV/ATECO, regione, dimensione contratti, certificazioni) e li classifica per compatibilità |
| `/abracabando:pin-radar <CPV / regione>` | Trova gli avvisi di preinformazione TED attivi per l'Italia: gare probabili nei prossimi mesi, prima che il bando ufficiale venga pubblicato |
| `/abracabando:scheda-opportunita <CIG \| CUP \| ente>` | Scheda intelligence completa su un'opportunità: storico aggiudicazioni ANAC, finanziamento PNRR, fondi OpenCoesione, bandi TED — tutto in un documento |
| `/abracabando:profilo-sa <stazione appaltante>` | Radiografia di una stazione appaltante: volumi per anno, CPV prevalenti, fornitori storici, importo medio, stagionalità degli acquisti |
| `/abracabando:reconciliation-pnrr <CUP>` | Verifica la coerenza di un progetto PNRR tra le fonti: segnala importi sopra finanziato, CUP orfani, stati divergenti e mancate pubblicazioni TED |
| `/abracabando:digest-pregara <settore / CPV / regione>` | Panoramica pre-gara su un settore o territorio: cosa è in programmazione, cosa è in consultazione, cosa sta per uscire su TED |
| `/abracabando:consultazioni-radar <settore>` | Monitora le consultazioni esplorative Consip e TED: il segnale debole che anticipa il bando formale |

### Esempi d'uso

```
/abracabando:analisi-disciplinare https://www.agcm.it/.../disciplinare.pdf CIG B16EFD0453

/abracabando:trova-bando-compatibile azienda metalmeccanica Veneto CPV 42900000 contratti 100k-500k ISO9001

/abracabando:pin-radar servizi informatici (CPV 72000000) probabili gare entro 6 mesi Italia

/abracabando:scheda-opportunita Azienda Zero CPV 72

/abracabando:profilo-sa ASL Bari

/abracabando:reconciliation-pnrr CUP H87G22001120006

/abracabando:digest-pregara efficientamento energetico Lombardia sopra 200k prossimi 12 mesi

/abracabando:consultazioni-radar servizi IT pubblica amministrazione
```

Puoi anche scrivere direttamente a Claude in linguaggio naturale — i tool MCP si attivano in automatico:

```
"Tutte le aggiudicazioni della P.IVA 02895590962 sopra 1M — valida la P.IVA su VIES e dammi il link al Registro Imprese."

"Progetti FESR 2021-2027 in Lombardia su OpenCoesione: totale finanziato, impegnato, pagato, top 5 beneficiari."

"Cerca su TED le procedure italiane sopra 5M€ con CPV 45 pubblicate negli ultimi 90 giorni."
```

---

## Fonti dati

| Fonte | Cosa contiene | Affidabilità |
|---|---|---|
| ANAC (OCDS) | Contratti pubblici, aggiudicazioni, stazioni appaltanti | Alta — snapshot mensile ufficiale |
| TED Search API v3 | Bandi europei sopra soglia UE, PIN, avvisi di aggiudicazione | Alta — API ufficiale EU |
| OpenPNRR | Misure, milestone, progetti e allocazioni PNRR | Alta — dati MEF ufficiali |
| OpenCoesione | Fondi strutturali EU, CUP, beneficiari, pagamenti | Alta — dati IGRUE ufficiali |
| Consip | Bandi, consultazioni esplorative, accordi quadro centrali | Media — scraping portale |
| Registro Imprese | Link a scheda azienda per P.IVA | Media — link generati, non API diretta |
| VIES | Validazione P.IVA intracomunitaria | Alta — API Commissione Europea |

### Affidabilità per componente

| Componente | Affidabilità | Note |
|---|---|---|
| Ricerca ANAC per CIG / P.IVA / CUP | Alta | Record-level su bulk Parquet mensile |
| Ricerca TED full-text e per CPV | Alta | REST API v3, SLA pubblico |
| OpenPNRR misure e milestone | Alta | API ufficiale, aggiornamento frequente |
| OpenCoesione progetti e pagamenti | Alta | API ufficiale IGRUE |
| PIN radar TED | Alta | Subset filtrato dell'API TED |
| Analisi disciplinare PDF | Alta (PDF digitali) / N.A. (PDF scansionati) | Claude legge testo nativo; scansioni dichiarate esplicitamente |
| Consip bandi e consultazioni | Media | Portale soggetto a variazioni di layout |
| Dati storici ANAC pluriennali | Bassa | Snapshot mensile recente, non archivio storico |

---

## Limiti

- `/abracabando:analisi-disciplinare` richiede PDF nativi digitali (testo selezionabile). I PDF scansionati vengono segnalati esplicitamente con suggerimento OCR.
- I dati ANAC non includono un tag queryabile per misura PNRR specifica — la riconciliazione usa il CUP come chiave di join.
- OpenPNRR espone allocazioni pianificate, non la percentuale di spesa effettiva.
- Consip: alcune pagine sono soggette a rate limiting intermittente.

---

## Sviluppo

```bash
python3 -m pytest tests/ -q                           # test manifest + struttura skill
claude plugin validate .                               # valida il manifest del plugin
python3 bench/eval_runner.py --frozen                 # eval deterministico, senza API key
ANTHROPIC_API_KEY=<key> python3 bench/eval_runner.py  # eval live (Haiku Batch)
python3 bench/eval_report.py                          # report dall'ultima run
```

---

## Autore e licenza

Marco Sassarini · Federico Cesarini — [abracabando.ai@gmail.com](mailto:abracabando.ai@gmail.com)

MIT — Vedi [LICENSE](LICENSE) per i termini completi · [CHANGELOG](CHANGELOG.md)

---

## Disclaimer

AbracaBando aggrega open data istituzionali italiani ed europei. Tutti gli output:

- Sono basati su dati pubblici soggetti a ritardi di aggiornamento (snapshot mensili ANAC, API di terze parti).
- Non costituiscono parere legale, fiscale o finanziario.
- Richiedono verifica indipendente prima di qualsiasi decisione commerciale o procedurale.
- Possono contenere imprecisioni dovute alla qualità dei dati upstream.

Ogni cifra riportata include fonte e data di lettura. Il plugin non inventa mai dati — le lacune vengono dichiarate esplicitamente nella sezione `## Dati non disponibili`.
