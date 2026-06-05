> **Query:** /consultazioni-radar Trova consultazioni Consip/avvisi esplorativi ancora aperti su servizi cloud (IaaS/PaaS).

---

Genero il report con le informazioni disponibili e i dati mancanti chiaramente dichiarati.

Dati letti il 2026-06-04

## 🔵 Bandi e RdA formali aperti — presentare offerta

Consip ha restituito **2 Richieste di Adesione (RdA)** su servizi infrastrutturali in cloud computing con caratteristiche IaaS e PaaS. Data la limitazione della piattaforma Consip (contenuti caricati dinamicamente), l'analisi si basa sui metadati di ricerca disponibili.

### RdA 52841 — Public Cloud IaaS e PaaS 2, AWS Lotto 1

**Ente:** Consip S.p.A.  
**Titolo completo:** Servizi infrastrutturali in cloud computing — Adesione AQ "Public Cloud IaaS e PaaS 2 — Servizi IaaS e PaaS AWS", Lotto 1, ID 2746  
**Tipo:** Richiesta di Adesione (RdA)  
**URL:** https://www.consip.it/bandi/rda-52841  
**Fonte:** https://www.consip.it/imprese/bandi?search_api_fulltext=cloud IaaS PaaS servizi (fonte: Consip) — Dati letti il 2026-06-04

**Valutazione qualitativa — Probabilità di aggiudicazione utile:** Media

**Rationale:** RdA su AQ pre-costituito per servizi cloud AWS su un lotto specifico (ID 2746) con tecnica consolidata presso Consip. Partecipazione subordinata a qualificazione fornitore AWS o partner autorizzato. Scadenza e stato dettagliato non disponibili dal sito Consip (caricamento dinamico).

---

### RdA 51125 — Public Cloud IaaS e PaaS (apertura generica)

**Ente:** Consip S.p.A.  
**Titolo completo:** Acquisizione servizi infrastrutturali in cloud computing — adesione all'AQ Public Cloud IAAS e PAAS  
**Tipo:** Richiesta di Adesione (RdA)  
**URL:** https://www.consip.it/bandi/rda-51125  
**Fonte:** https://www.consip.it/imprese/bandi?search_api_fulltext=cloud IaaS PaaS servizi (fonte: Consip) — Dati letti il 2026-06-04

**Valutazione qualitativa — Probabilità di aggiudicazione utile:** Media

**Rationale:** RdA generica di accreditamento su accordo quadro Consip per infrastrutture cloud (IaaS/PaaS) senza vincolo di vendor specifico. Più aperta della RdA 52841 dal punto di vista della concorrenza. Scadenza e stato dettagliato non disponibili dal sito Consip (caricamento dinamico).

---

## Dati non disponibili

- **Scadenze:** Il sito Consip carica i dati di scadenza e status tramite JavaScript post-rendering. Le due RdA sono state estratte per rilevanza sul tema (cloud IaaS/PaaS), ma **data di chiusura, stato operativo (aperto/proroga/chiuso) e link diretti ai documenti tecnici non sono stati recuperabili** dalla risposta HTTP statica.
- **Importi a base d'asta / aggiudicati:** Non forniti da Consip nella pagina di ricerca.
- **Numero e identità dei fornitori già qualificati:** Non disponibile pubblicamente.
- **Confronto con altre PA e TED:** Questa skill copre solo Consip. Per un quadro completo su EU tender (TED) e appalti ANAC, suggeriamo di usare le skill `pin-radar` e `scheda-opportunita`.

**Azione consigliata:** Visitare direttamente https://www.consip.it/bandi/rda-52841 e https://www.consip.it/bandi/rda-51125 per consultare le scadenze attuali, i requisiti di qualificazione e la documentazione tecnica (spesso in formato PDF/allegato).

---

## Audit trail

| Timestamp | Strumento | Query | Risultato |
|-----------|-----------|-------|-----------|
| 2026-06-04T00:00:00Z | `consip_search_consultazioni` | `cloud IaaS PaaS servizi` | 0 risultati (consultazioni di mercato) |
| 2026-06-04T00:00:00Z | `consip_search_bandi` | `cloud IaaS PaaS servizi` | 3 risultati, 2 unici dopo dedup (RdA 52841, RdA 51125) |
| 2026-06-04T00:00:00Z | `download_file` (RdA 52841) | https://www.consip.it/bandi/rda-52841 | HTTP 200, ~45 KiB HTML (stato/scadenza caricati dinamicamente, non estratti) |
| 2026-06-04T00:00:00Z | `download_file` (RdA 51125) | https://www.consip.it/bandi/rda-51125 | HTTP 200, ~44 KiB HTML (stato/scadenza caricati dinamicamente, non estratti) |

---

**Confidenza complessiva del report:** Media — ampiezza della ricerca, numero di risultati, e classificazione per tipo garantiti; dettagli di scadenza e status richiedono accesso diretto al sito o API Consip non pubblicamente disponibile.