# Esempio output — Trova Bando Compatibile

**Input simulato:** `/trova-bando-compatibile azienda metalmeccanica CPV 44000000, Lombardia, contratti 200k–800k EUR`

---

Dati letti il 2026-06-11
> Ambito: solo bandi aperti alla data odierna. Per includere gare storiche/chiuse, ripeti la richiesta con "incluse gare chiuse".

# Bandi Compatibili — Strutture metalliche (CPV 44000000) · Lombardia

## Profilo azienda analizzato
- **Settore CPV:** 44000000 — Strutture metalliche e materiali correlati
- **Regione:** Lombardia (NUTS: ITC4)
- **Taglio contratto:** 200.000–800.000 EUR
- **Certificazioni dichiarate:** non specificate

---

## 🟢 Bandi aperti — compatibilità Alta

### Fornitura carpenteria metallica per impianti industriali — Provincia di Varese
- **Ente:** Provincia di Varese
- **Scadenza:** 2026-07-15
- **Importo stimato:** EUR 450.000
- **CPV:** 44212000 — Strutture e parti di strutture
- **Fonte:** [(fonte: https://ted.europa.eu/udl?uri=TED:NOTICE:123456-2026) — Dati letti il 2026-06-11]
- **Compatibilità complessiva:** Alta
  - CPV: Alta (prefisso 4421 ⊂ 44000000)
  - Geografia: Alta (Varese, Lombardia)
  - Taglio importo: Alta (EUR 450k dentro range 200k–800k)
  - Idoneità: Alta (nessun requisito di certificazione specifico pubblicato)

---

### Opere metalliche per ristrutturazione sede comunale — Comune di Bergamo
- **Ente:** Comune di Bergamo
- **Scadenza:** 2026-07-28
- **Importo stimato:** EUR 290.000
- **CPV:** 44316000 — Lavori di fabbro
- **Fonte:** [(fonte: https://www.consip.it/imprese/bandi/bando-xy) — Dati letti il 2026-06-11]
- **Compatibilità complessiva:** Alta
  - CPV: Alta (44316000 ⊂ 44000000)
  - Geografia: Alta (Bergamo, Lombardia)
  - Taglio importo: Alta (EUR 290k dentro range)
  - Idoneità: non valutabile (requisiti non pubblicati nel bando Consip)

---

## 🔵 Bandi aperti — compatibilità Media

### Fornitura strutture in acciaio per infrastrutture — ANAS S.p.A.
- **Ente:** ANAS S.p.A. (bando nazionale)
- **Scadenza:** 2026-08-10
- **Importo stimato:** EUR 1.200.000
- **CPV:** 44212100 — Strutture in acciaio
- **Fonte:** [(fonte: https://ted.europa.eu/udl?uri=TED:NOTICE:234567-2026) — Dati letti il 2026-06-11]
- **Compatibilità complessiva:** Media
  - CPV: Alta (prefisso 44212 ⊂ 44000000)
  - Geografia: Media (bando nazionale, non specificamente Lombardia)
  - Taglio importo: Bassa (EUR 1,2M oltre il massimo dichiarato di EUR 800k)
  - Idoneità: non valutabile (certificazioni richieste non note)
  - ⚠️ Taglio importo: importo bando (EUR 1,2M) supera il massimo dichiarato (EUR 800k) — valuta se presentare in RTI.

---

## 📅 Opportunità pianificate (programmazione biennale)

| Titolo | Ente / Regione | CPV | Anno previsto | Importo stimato | Compatibilità | Fonte |
|---|---|---|---|---|---|---|
| Piano infrastrutture industriali | Regione Lombardia | 44000000 | 2027 | n.d. | Media | [(fonte: https://programmazione.regione.lombardia.it/...) — Dati letti il 2026-06-11] |

---

## Fonti

| Fonte | Identificatori | URL | Data lettura |
|---|---|---|---|
| TED (EU) | 123456-2026, 234567-2026 | https://ted.europa.eu | 2026-06-11 |
| Consip | bando-xy | https://www.consip.it/imprese/bandi | 2026-06-11 |
| Programmazione regionale | — | https://programmazione.regione.lombardia.it | 2026-06-11 |

---

## Dati non disponibili

- Certificazioni richieste non pubblicate in alcuni bandi Consip: idoneità classificata come "non valutabile".
- Importo non disponibile per 1 bando in programmazione biennale; classificato con Bassa confidenza.

---

## Audit trail

```
query_ted: "cpv=44000000 AND place-of-performance=ITA AND nuts-code=ITC4", scope=ACTIVE, limit=10
query_consip: "strutture metalliche", stage="bando"
query_programmazione: cpv=44000000, regione=Lombardia, anno=2026
ateco_to_cpv_inference: non applicabile (CPV fornito direttamente)
ambito_temporale: "solo_aperti"
server_tier: "free"
tool_preferito: "free"
fallback_attivato: "no"
data_lettura: 2026-06-11
timestamp: 2026-06-11T10:30:00Z
```
