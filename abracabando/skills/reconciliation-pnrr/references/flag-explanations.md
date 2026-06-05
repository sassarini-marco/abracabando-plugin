# Spiegazioni dettagliate dei flag — Reconciliation PNRR

Per ogni flag identificato, fornisci una spiegazione dettagliata usando il formato seguente:

---

## CUP_ORFANO

**Formato:**

`**CUP_ORFANO**: il CUP <X> è presente in OpenPNRR ma non trovato in OpenCoesione o ANAC. Possibili cause: progetto non ancora inserito nel sistema di monitoraggio, errore di codifica CUP, progetto annullato.`

**Esempio:**

`**CUP_ORFANO**: il CUP J81B22000540006 è presente in OpenPNRR ma non trovato in OpenCoesione o ANAC. Possibili cause: progetto non ancora inserito nel sistema di monitoraggio, errore di codifica CUP, progetto annullato.`

---

## IMPORTO_SOPRA_FINANZIATO

**Formato:**

`**IMPORTO_SOPRA_FINANZIATO**: l'importo contrattuale ANAC (<X> EUR) supera il finanziamento OpenCoesione (<Y> EUR) per il CUP <Z>. Differenza: <delta> EUR. Verificare se il finanziamento è stato aggiornato o se vi sono co-finanziamenti non registrati.`

**Esempio:**

`**IMPORTO_SOPRA_FINANZIATO**: l'importo contrattuale ANAC (1.500.000 EUR) supera il finanziamento OpenCoesione (1.200.000 EUR) per il CUP J81B22000540006. Differenza: 300.000 EUR. Verificare se il finanziamento è stato aggiornato o se vi sono co-finanziamenti non registrati.`

---

## STATO_DIVERGENTE

**Formato:**

`**STATO_DIVERGENTE**: OpenPNRR riporta stato <A> mentre OpenCoesione riporta <B> per il CUP <Z>. Le fonti non sono sincronizzate — la data dell'ultimo aggiornamento è da verificare.`

**Esempio:**

`**STATO_DIVERGENTE**: OpenPNRR riporta stato "completato" mentre OpenCoesione riporta "in corso" per il CUP J81B22000540006. Le fonti non sono sincronizzate — la data dell'ultimo aggiornamento è da verificare.`

---

## MANCATA_PUBBLICAZIONE_TED

**Formato:**

`**MANCATA_PUBBLICAZIONE_TED**: contratto con importo <X> EUR (sopra soglia UE) senza corrispondente avviso TED trovato. Obbligatoria pubblicazione ai sensi del D.Lgs. 36/2023. Verificare numero di pubblicazione TED o segnalare all'ente.`

**Esempio:**

`**MANCATA_PUBBLICAZIONE_TED**: contratto con importo 1.500.000 EUR (sopra soglia UE) senza corrispondente avviso TED trovato. Obbligatoria pubblicazione ai sensi del D.Lgs. 36/2023. Verificare numero di pubblicazione TED o segnalare all'ente.`

**Nota importante — verifica euristica:**

Questo flag è basato su una ricerca per buyer-name + soglia importo su TED. I dati TED non contengono CIG o CUP — non è possibile una corrispondenza esatta per identificatore nazionale italiano. Una risposta vuota da TED può indicare: (a) l'avviso non è stato pubblicato; (b) l'ente è registrato su TED con una denominazione diversa da quella ANAC; (c) l'avviso è stato pubblicato ma non è recuperabile con la query buyer-name. Prima di segnalare formalmente, verificare manualmente su TED con il nome ufficiale dell'ente.
