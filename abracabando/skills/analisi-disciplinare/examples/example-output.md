# Esempio output — Analisi Disciplinare

Questo esempio mostra un output completo per la richiesta:
> "Analizza il disciplinare a questo URL: https://www.comune.esempio.it/gare/disciplinare-servizi-it.pdf — CIG 9876543210"

---

Dati letti il 2026-06-04

# Analisi disciplinare — Servizi di sviluppo e manutenzione del sistema informativo comunale · CIG 9876543210

## Contesto gara

| Campo | Valore |
|-------|--------|
| Stazione appaltante | Comune di Esempio |
| Oggetto | Servizi di sviluppo e manutenzione del sistema informativo comunale |
| Importo a base d'asta | EUR 480.000,00 |
| CIG | 9876543210 |
| Fonte · Letto il | https://dati.anticorruzione.it/opendata · 2026-06-04 |

## Criterio di aggiudicazione

**Offerta economicamente più vantaggiosa (OEPV)** — punteggio max: tecnica 70 punti / economica 30 punti

Confidenza: Alta

## Criteri di valutazione

### Tabella riassuntiva

| Criterio | Punti massimi |
|----------|-------------:|
| Offerta tecnica (totale) | 70 |
| — Metodologia e approccio | 25 |
| — Competenze del team | 20 |
| — Piano di progetto e tempi | 15 |
| — Strumenti e tecnologie proposte | 10 |
| Offerta economica (totale) | 30 |
| **TOTALE** | **100** |

### Note di lettura

Con 70 punti tecnici su 100, la qualità della proposta è determinante rispetto al prezzo: un'offerta economica mediocre può essere compensata da un'eccellente proposta tecnica. Il sotto-criterio "Metodologia e approccio" da 25 punti è il peso più rilevante — merita la maggiore attenzione nella stesura.

## Requisiti di partecipazione

**Requisiti economici e finanziari:**
- Fatturato globale medio degli ultimi tre esercizi finanziari: non inferiore a EUR 300.000,00
- Fatturato specifico in servizi informatici per la pubblica amministrazione negli ultimi tre anni: non inferiore a EUR 150.000,00

**Requisiti tecnici e professionali:**
- Certificazione ISO 9001:2015 in corso di validità
- Almeno 2 contratti analoghi (sviluppo/manutenzione sistemi informativi per PA) negli ultimi 5 anni, con importo unitario ≥ EUR 100.000,00
- Disponibilità di almeno 3 figure professionali certificate (es. Project Manager con almeno 5 anni di esperienza)

**Requisiti generali:**
- Iscrizione al Registro delle Imprese (CCIAA)
- DURC regolare alla data di presentazione dell'offerta
- Assenza cause di esclusione art. 94-98 D.Lgs. 36/2023

## Dati non disponibili

- Allegati tecnici (capitolato speciale prestazionale) non inclusi nel documento analizzato — verificare se disponibili nella stessa piattaforma di gara
- Criteri di valutazione dell'offerta economica (formula di riparametrazione) non rilevati nel testo estratto
- Scadenza presentazione offerte non trovata nel testo — consultare il bando integrale

## Audit trail

```text
Input:
  url: "https://www.comune.esempio.it/gare/disciplinare-servizi-it.pdf"
  cig: "9876543210"

Passi eseguiti:
  1. anac_award_detail(cig="9876543210"): 8 campi restituiti
  2. document_fetch_text(url="https://www.comune.esempio.it/gare/disciplinare-servizi-it.pdf"): kind=pdf, size_bytes=412.800, pages=24, truncated=false
  3. document_extract_criteria(text=<estratto>): found=true, confidence=Alta, tecnica=70, economica=30

tool_preferito: "free"
fallback_attivato: "si"
Data lettura: 2026-06-04
Timestamp: 2026-06-04T10:32:17+02:00
```

---

## Esempio caso: documento scansionato

Quando `document_fetch_text` restituisce errore per PDF scansionato:

---

Dati letti il 2026-06-04

# Analisi disciplinare — https://www.ente.it/gare/disciplinare.pdf

## Dati non disponibili

- **Documento non analizzabile**: il PDF all'URL fornito non contiene un livello testo (probabilmente scansionato). L'estrazione automatica dei criteri di valutazione non è possibile.
- Per procedere con l'analisi, fornire il testo del disciplinare direttamente nella chat (copia-incolla dal documento), oppure verificare se è disponibile una versione digitale nativa.

## Audit trail

```text
Input:
  url: "https://www.ente.it/gare/disciplinare.pdf"
  cig: null

Passi eseguiti:
  1. anac_award_detail: non eseguito (CIG non fornito)
  2. document_fetch_text(url="https://www.ente.it/gare/disciplinare.pdf"): errore — "PDF has no text layer (likely scanned); OCR not supported"
  3. document_extract_criteria: non eseguito (fetch fallito)

tool_preferito: "free"
fallback_attivato: "si"
Data lettura: 2026-06-04
Timestamp: 2026-06-04T11:05:44+02:00
```
