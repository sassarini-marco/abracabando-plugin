# Mappatura NUTS per l'Italia

Usa questa tabella per convertire nomi di regione/area in codici NUTS-2:

| Area | Codice NUTS | Regioni incluse |
|------|-------------|-----------------|
| Nord-Ovest | ITC* | Piemonte (ITC1), Valle d'Aosta (ITC2), Liguria (ITC3), Lombardia (ITC4) |
| Nord-Est | ITH* | Trentino-Alto Adige (ITH1), Veneto (ITH3), Friuli-Venezia Giulia (ITH4), Emilia-Romagna (ITH5) |
| Centro | ITI* | Toscana (ITI1), Umbria (ITI2), Marche (ITI3), Lazio (ITI4) |
| Sud | ITF* | Abruzzo (ITF1), Molise (ITF2), Campania (ITF3), Puglia (ITF4), Basilicata (ITF5), Calabria (ITF6) |
| Isole | ITG* | Sicilia (ITG1), Sardegna (ITG2) |

## Regole

- **NUTS-1 macro-aree ora supportate**: i prefissi NUTS-1 (`ITC`, `ITH`, `ITI`, `ITF`, `ITG`) sono automaticamente espansi dal tool MCP ai loro codici NUTS-2 figli. Usa NUTS-1 per sweep di macro-area (es. `ITI` per tutto il Centro Italia).
- Se l'utente indica una regione specifica, usa il codice NUTS-2 puntuale (es. `ITC4` per Lombardia) per maggiore precisione.
- Se indica "Italia" o nessuna regione, usa `nuts_region=null`.
