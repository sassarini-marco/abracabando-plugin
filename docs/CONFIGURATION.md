# Configurazione del plugin industrial-procurement

## Modalita free (locale)

La modalita free usa il server MCP locale `industrial-data-mcp` via stdio.
Non richiede variabili d'ambiente aggiuntive.

**Prerequisiti:**

1. Installa il server MCP locale:
   ```bash
   pip install industrial-mcp
   ```
2. Verifica che il comando `industrial-mcp` sia nel PATH:
   ```bash
   industrial-mcp --help
   ```
3. Installa il plugin in Claude Code:
   ```bash
   claude plugin install <path-al-plugin>
   ```

Il server locale si avvia automaticamente quando Claude Code carica il plugin.

## Modalita pro (hosted HTTP)

La modalita pro si connette a un server hosted con dati arricchiti e aggiornamenti piu frequenti.
Richiede un account e un token API.

**Prerequisiti:**

Imposta le variabili d'ambiente **prima** di avviare Claude Code:

```bash
export INDUSTRIAL_MCP_PRO_URL="https://api.industrial-mcp.io"
export INDUSTRIAL_MCP_PRO_TOKEN="<il-tuo-token>"
```

Su sistemi Linux/macOS puoi aggiungere queste righe al tuo `~/.bashrc` o `~/.zshrc`.

## Riferimento variabili d'ambiente

| Variabile | Tipo | Default | Descrizione |
|-----------|------|---------|-------------|
| `INDUSTRIAL_MCP_PRO_URL` | URL | `https://api.industrial-mcp.io` | URL base del server pro hosted |
| `INDUSTRIAL_MCP_PRO_TOKEN` | stringa | *(nessuno)* | Token Bearer per autenticazione al server pro |

> **Nota tecnica**: il plugin usa `headersHelper` (invece del campo `headers` standard di `.mcp.json`) per iniettare il token di autenticazione. Questo e' un workaround per il bug Claude Code #51581 in cui `${VAR}` nel campo `headers` non viene sostituito correttamente. Il comportamento esterno e' identico.

## Verifica della configurazione

Per verificare che il server free sia raggiungibile:

```bash
industrial-mcp --help
```

Per verificare che il token pro sia valido, avvia Claude Code e usa il comando:

```
/pin-radar servizi ingegneria Puglia
```

Se il server pro risponde, vedrai dati aggiornati nella risposta.
