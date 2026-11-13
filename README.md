# roomve-plugins

Marketplace di plugin per Claude della suite Roomve. Oggi contiene un plugin: **roomve-mcp**.

*Claude plugin marketplace of the Roomve suite. One plugin today, `roomve-mcp`: the connector to Roomve MCP
(image generation with Gemini, a personal headless Blender driven by free Python) and the skills to use it.*

## roomve-mcp

| Parte | Che cosa fa |
|---|---|
| Connettore `roomve` | Il server MCP `https://mcp.roomve.it/mcp`: immagini con Gemini, un Blender 5.2 personale con Python libero, uno spazio file per account |
| Skill `roomve-mcp` | Come funzionano sessione, coda, file e che cosa fare a ogni errore |
| Skill `roomve-blender` | Scrivere Python per Blender 5.2 senza errori: le API cambiate rispetto alle versioni vecchie, limiti di tempo e memoria, ricette provate, materiali PBR e bake delle mappe (base color, roughness, metallic, normal, AO) |
| Skill `roomve-images` | Parametri validi per ogni modello, riferimenti, sfondo trasparente, prompt |
| Skill `roomve-projects` | Lavorare sui progetti di Roomve Workspace: cartella condivisa del progetto, copie tra progetto e spazio dell'account, repo GitHub solo come nomi |

Serve un account su `mcp.roomve.it`: il servizio è privato e gli account li dà chi lo gestisce. Nel plugin non
c'è nessun segreto: l'accesso avviene con il login di Roomve, al primo uso.

## Installazione

### Claude Code

```
/plugin marketplace add riftbane/roomve-plugins
/plugin install roomve-mcp@roomve-plugins
```

Poi `/mcp` → `roomve` → *Authenticate*: si apre il login di Roomve e la pagina "Autorizza".

**Aggiornamenti automatici**: `/plugin` → *Marketplaces* → `roomve-plugins` → *Enable auto-update* (per i
marketplace aggiunti a mano è spento di default). A mano: `/plugin marketplace update roomve-plugins`.

### Claude (web, desktop, Cowork)

*Personalizza* → *Plugin* → *Aggiungi* → *Aggiungi marketplace*, e scrivere `riftbane/roomve-plugins`. Installare
`roomve-mcp`, poi nella scheda *Connettori* del plugin collegare `roomve` ed entrare con il login di Roomve.

**Aggiornamenti automatici**: attivare *Sincronizza automaticamente* sul marketplace; a mano c'è *Controlla
aggiornamenti*.

### Solo il connettore, senza plugin

Su claude.ai: *Impostazioni* → *Connettori* → *Aggiungi connettore personalizzato*, URL
`https://mcp.roomve.it/mcp`. Funziona, ma senza le skill.

## Come arrivano gli aggiornamenti

Claude tiene la copia installata di un plugin finché non cambia il numero `version` in
`roomve-mcp/.claude-plugin/plugin.json`. Quindi **ogni modifica al plugin va pubblicata alzando la versione**:
il controllo automatico del repository (`scripts/check.py`, workflow `check`) fallisce se i file del plugin
cambiano e la versione resta uguale.

| Cambia | Versione |
|---|---|
| Correzioni e ritocchi alle skill | `1.0.0` → `1.0.1` |
| Una skill nuova, una sezione nuova | `1.0.0` → `1.1.0` |
| Cambia l'indirizzo o il nome del connettore, si toglie una skill | `1.0.0` → `2.0.0` |

## Struttura

```
.claude-plugin/marketplace.json        il marketplace: nome e elenco dei plugin
roomve-mcp/
  .claude-plugin/plugin.json           nome, versione, descrizione
  .mcp.json                            il connettore (solo l'indirizzo)
  skills/roomve-mcp/SKILL.md
  skills/roomve-blender/SKILL.md       + references/recipes.md, references/api-changes.md
  skills/roomve-images/SKILL.md
  skills/roomve-projects/SKILL.md
scripts/check.py                       controlli su manifest, skill e versione
scripts/test_recipes.py                esegue in Blender ogni blocco di codice della skill Blender
```

## Prima di pubblicare una modifica

```sh
python3 scripts/check.py --base origin/main      # manifest, skill, versione alzata
claude plugin validate . && claude plugin validate roomve-mcp
```

Se cambia il codice in `roomve-mcp/skills/roomve-blender/references/recipes.md`, va rieseguito nel Blender del
servizio (stessa versione, 5.2): ogni blocco ```` ```python ```` deve passare. Il workflow `check` lo fa a ogni
push scaricando Blender, ma salta i blocchi che usano le funzioni `roomve.*` (bake PBR, viste): quelle esistono
solo nel servizio. In locale, con l'immagine del servizio, girano tutti:

```sh
docker run --rm --entrypoint /opt/blender/blender -v "$PWD":/repo:ro --tmpfs /work:exec -e HOME=/work \
  roomve-mcp-runner:latest -b --factory-startup -noaudio \
  --python /repo/scripts/test_recipes.py -- /work /repo/roomve-mcp/skills/roomve-blender/references/recipes.md
```

Le skill dicono solo cose provate: una riga nuova nelle tabelle delle API va prima verificata su Blender 5.2.
