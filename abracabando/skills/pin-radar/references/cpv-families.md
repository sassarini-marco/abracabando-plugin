# Famiglie CPV principali su TED

Usa questa tabella per verificare che il CPV fornito corrisponda al settore dichiarato dall'utente:

| CPV prefix | Categoria TED |
|------------|---------------|
| `48000000` | Pacchetti software e sistemi di informazione (generico) |
| `48210000` | Networking software package (DNS/DHCP/IPAM) — **NON** software database |
| `48610000` / `48611000` | Database systems / Database software package |
| `72xxxxxx` | Servizi IT e informatica |
| `30xxxxxx` | Hardware e attrezzature informatiche |
| `35xxxxxx` | Apparecchiature di sicurezza |
| `71xxxxxx` | Servizi di ingegneria e architettura |
| `45xxxxxx` | Lavori di costruzione |
| `80xxxxxx` | Servizi di istruzione e formazione |
| `85xxxxxx` | Servizi sanitari e sociali |

## Regole

- Se il CPV non corrisponde al settore dichiarato (es. utente chiede "software gestionale energia" ma il CPV è `48210000` = "Networking software package"), aggiungi in `## Copertura della ricerca e limiti`:  
  `"CPV 48210000 = 'Networking software package' su TED — verifica se è il CPV corretto per 'software gestionale energia'"`
- Prosegui comunque con il CPV fornito; **non inventare** un CPV alternativo.
