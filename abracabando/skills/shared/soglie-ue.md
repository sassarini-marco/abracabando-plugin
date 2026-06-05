# Soglie UE — fonte unica per tutte le skill

Queste soglie determinano quando un appalto è "sopra-soglia comunitaria" e
quindi quando ha senso interrogare TED. Sono centralizzate qui perché vengono
aggiornate periodicamente con regolamento della Commissione europea: aggiorna
**solo questo file** e tutte le skill restano allineate.

Soglie vigenti per il biennio **2026-2027**, in vigore dal 1° gennaio 2026
(regolamenti delegati UE 2025/2150, 2025/2151 e 2025/2152 del 22 ottobre 2025;
recepite in Italia tramite l'art. 14 del D.Lgs. 36/2023, che rinvia ai valori UE):

### Settori ordinari — Direttiva 2014/24/UE

| Tipo di appalto | Soglia UE |
|---|---|
| Servizi e forniture — amministrazioni aggiudicatrici centrali | EUR 140 000 |
| Servizi e forniture — amministrazioni sub-centrali | EUR 216 000 |
| Lavori | EUR 5 404 000 |
| Servizi sociali e altri servizi specifici (Allegato XIV) | EUR 750 000 |

### Settori speciali — Direttiva 2014/25/UE

| Tipo di appalto | Soglia UE |
|---|---|
| Servizi e forniture | EUR 432 000 |
| Lavori | EUR 5 404 000 |

## Come usarle

- Per il filtro "sopra-soglia" prudenziale (decidere se eseguire una query TED)
  usa la soglia più bassa applicabile: **EUR 140 000** per servizi/forniture,
  **EUR 5 404 000** per lavori. Sotto questi valori l'avviso difficilmente
  compare su TED.
- Se l'importo non è disponibile, applica il default conservativo previsto
  dalla singola skill e dichiara l'assunzione in `## Dati non disponibili`.
- Le soglie cambiano nel tempo: quando citi un valore nell'output, indica che
  è la soglia vigente alla data di lettura.
