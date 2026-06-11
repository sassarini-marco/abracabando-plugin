# Formato output — Trova Bando Compatibile

## Struttura documento

```
Dati letti il YYYY-MM-DD
> Ambito: solo bandi aperti alla data odierna. Per includere gare storiche/chiuse, ripeti la richiesta con "incluse gare chiuse".

# Bandi Compatibili — [settore] · [regione o Italia]

## Profilo azienda analizzato
- **Settore CPV:** [cpv] — [descrizione]
- **ATECO:** [ateco] (se fornito; inferenza CPV → [cpv] — *Media confidenza, da verificare*)
- **Regione:** [regione o "Italia"]
- **Taglio contratto:** [min]–[max] EUR (se fornito)
- **Certificazioni dichiarate:** [lista o "non specificate"]

## 🟢 Bandi aperti — compatibilità Alta

### [Titolo bando]
- **Ente:** [nome stazione appaltante]
- **Scadenza:** [data o n.d.]
- **Importo stimato:** [EUR importo o n.d.]
- **CPV:** [codice — descrizione]
- **Fonte:** [(fonte: [URL]) — Dati letti il YYYY-MM-DD]
- **Compatibilità complessiva:** Alta
  - CPV: Alta (prefisso esatto)
  - Geografia: Alta (regione richiesta)
  - Taglio importo: Alta (dentro range dichiarato)
  - Idoneità: Alta (requisiti compatibili con profilo)

---

## 🔵 Bandi aperti — compatibilità Media

### [Titolo bando]
- **Ente:** [nome]
- **Scadenza:** [data]
- **Importo stimato:** [EUR o n.d.]
- **CPV:** [codice]
- **Fonte:** [(fonte: [URL]) — Dati letti il YYYY-MM-DD]
- **Compatibilità complessiva:** Media
  - CPV: Alta
  - Geografia: Media (regione confinante: Piemonte)
  - Taglio importo: non valutabile (importo non pubblicato)
  - Idoneità: Media
  - ⚠️ Idoneità: verifica certificazione SOA OG1 cat. III richiesta (da verificare)

---

## 📅 Opportunità pianificate (programmazione biennale)

Questi sono piani regionali di spesa, non bandi ancora pubblicati. Compatibilità
stimata sul CPV e regione; lead time indicativo.

| Titolo | Ente / Regione | CPV | Anno previsto | Importo stimato | Compatibilità | Fonte |
|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | Media | (fonte: [URL]) |

---

## Altri bandi trovati ma non analizzati
(sezione presente solo se > 10 bandi)

| Titolo | Ente | Scadenza | Fonte |
|---|---|---|---|
| ... | ... | ... | ... |

---

## Avviso: dati Consip non disponibili
(sezione presente solo se status="layout_unrecognized")

---

## Fonti

| Fonte | Identificatore | URL | Data lettura |
|---|---|---|---|
| TED | [notice_id] | [url] | YYYY-MM-DD |
| Consip | — | [url] | YYYY-MM-DD |
| Programmazione | — | [url] | YYYY-MM-DD |

---

## Dati non disponibili

[Spiegazione di ciò che manca e perché. Es. "Importo non pubblicato per N bandi TED".]

---

## Audit trail

```
query_ted: "cpv=44000000 AND place-of-performance=ITA"
query_consip: "strutture metalliche", stage="bando"
query_programmazione: cpv=44000000, regione=Lombardia, anno=2026
ateco_to_cpv_inference: "25.11 → CPV 44000000 (Media confidenza)"  # ometti se non applicabile
ambito_temporale: "solo_aperti"
server_tier: "free"
tool_preferito: "free"
fallback_attivato: "no"
data_lettura: YYYY-MM-DD
timestamp: YYYY-MM-DDTHH:MM:SSZ
```
```
