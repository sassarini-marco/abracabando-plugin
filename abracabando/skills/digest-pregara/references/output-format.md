# Formato output — Digest Pre-Gara

L'output è un digest di mercato pre-gara in italiano formale.

## Prima riga
`Dati letti il YYYY-MM-DD`

## Titolo
`# Digest Pre-Gara — [CPV o settore] · [Regione] · [Anno]`

Se solo alcuni parametri sono disponibili, adatta il titolo di conseguenza (es. `# Digest Pre-Gara — CPV 71000000 · Italia`).

---

## `## Opportunità rilevate`

Tabella markdown con colonne:

| Ente | Oggetto | Importo stimato | Fonte | Lead time | Confidenza |
|------|---------|-----------------|-------|-----------|------------|
| [denominazione ente] | [oggetto breve] | EUR [importo] | (fonte: [nome](URL)) | [N] mesi | Alta confidenza |

**Colonne:**

- **Ente**: denominazione ufficiale della stazione appaltante.
- **Oggetto**: descrizione breve dell'opportunità (max 100 caratteri).
- **Importo stimato**: importo indicativo se disponibile, altrimenti `"non indicato"`.
- **Fonte**: usa **sempre** il formato `(fonte: [nome](URL))` — link cliccabile.
- **Lead time**: stima in mesi dalla pubblicazione prevista del bando, derivata dal campo proxy per fonte (vedi SKILL.md — Derivazione lead time). Usa `"n.d."` se nessuna data è disponibile.
- **Confidenza**: usa il vocabolario a tre livelli definito in SKILL.md (Alta confidenza / Media confidenza / Bassa confidenza). Usa Bassa confidenza quando lead time è `"n.d."`.

**Ordinamento:**

Ordina per **Lead time crescente** (opportunità più vicine prima). Le voci con `"n.d."` vanno in fondo alla tabella.

---

## `## Metodologia`

Sezione sempre presente.

Descrivi brevemente:
- Quali strumenti sono stati interrogati (programmazione regionale, PIN TED, PNRR);
- Quali filtri CPV/regione/anno sono stati applicati;
- Quali misure PNRR sono state confrontate.

Esempio:

```text
Ricerca condotta su:
- Programmazione regionale biennale: filtro CPV 71000000, regione Puglia, anno 2025
- PIN TED: filtro CPV 71000000, NUTS ITF4, soglia UE verificata
- Misure PNRR: confrontate misure M1C1, M1C2, M2C3 per coerenza CPV 71

Fonti utilizzate: programmazione_search_biennale, ted_pin_italy, openpnrr_list.
```

---

## `## Dati non disponibili`

Sezione sempre presente.

Elenca esplicitamente ogni fonte non consultata e perché:
- PIN TED omessi (soglia non raggiunta o non determinabile);
- Regioni non coperte dal registro di programmazione;
- Dati non ancora pubblicati per l'anno richiesto.

Esempio:

```text
- PIN TED: non consultato perché importo stimato < soglia UE (EUR 221.000 per servizi)
- Programmazione regionale: regione Umbria non coperta dal registro biennale
- PNRR: nessuna misura correlata al CPV 71000000 trovata in OpenPNRR
```

---

## `## Audit trail`

Sezione sempre presente.

Blocco di codice fenced:

```text
Query programmazione: cpv=<X>, regione=<Y>, anno=<Z>
Query TED PIN: <query string completa oppure "non eseguita">
Misure PNRR confrontate: <lista ID misure>
tool_preferito: "pro" | "free"
fallback_attivato: "si" | "no"
data_lettura: YYYY-MM-DD
Timestamp: YYYY-MM-DDTHH:MM:SSZ
```

Esempio:

```text
Query programmazione: cpv=71000000, regione=Puglia, anno=2025
Query TED PIN: cpv_codes=["71000000"], nuts_region="ITF4", limit=25
Misure PNRR confrontate: M1C1, M1C2, M2C3
tool_preferito: "free"
fallback_attivato: "no"
data_lettura: 2026-06-02
Timestamp: 2026-06-02T17:12:45+02:00
```
