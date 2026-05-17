---
name: mac-mini-telegram-remote-exec
description: |
  Telegram-basierte Remote-Ausführung von Shell-Befehlen auf dem Mac Mini
  über den Hermes Gateway /run Endpunkt. Ermöglicht direkte Host-Operationen
  (df, docker, ps, etc.) aus dem Telegram-Chat ohne SSH.
version: 1.0.0
category: devops
requires: []
author: KlausDIG
---

# mac-mini-telegram-remote-exec

Telegram-basierte Fernsteuerung des Hermes Stacks auf dem Mac Mini.
Erlaubt direkte Befehlsausführung (`/run <cmd>`) im Telegram-Chat,
die über den Gateway-Container als Whitelist-gesicherter Subprozess ausgeführt wird.

## Architektur

```
[Telegram Chat] → /run df -h
       ↓
[Telegram Bot Container] → POST http://control-gateway:8092/run {"cmd":"df -h"}
       ↓
[Gateway Container] → run_addon.py → subprocess.run(["bash","-lc","df -h"])
       ↓
[Mac Mini Host] → stdout/stderr → JSON Response → Telegram-Antwort
```

## Voraussetzungen

- Hermes Stack läuft auf Mac Mini (12 Container aktiv)
- Gateway-Container: `hermes-devops-ai-environment-control-gateway-1`
- Telegram-Bot-Container: `hermes-devops-ai-environment-telegram-bot-1`
- Interne API-URL: `http://control-gateway:8092`
- SSH-Zugriff auf Mac Mini via Hostinger Jumphost (Tailscale `100.93.33.84`)

## Dateien & Pfade

| Datei | Pfad (Host) | Container-Ziel |
|-------|-------------|----------------|
| Gateway App | `~/hermes-devops-ai-environment/gateway/app.py` | `/app/gateway/app.py` |
| Run Addon | `~/hermes-devops-ai-environment/run_addon.py` | `/app/run_addon.py` |
| Telegram Bot | `~/hermes-devops-ai-environment/telegram_bot/app.py` | `/workspace/telegram_bot/app.py` |
| .env | `~/hermes-devops-ai-environment/.env` | — |

## Setup-Prozess

### 1. Gateway erweitern

Die Datei `gateway/app.py` muss um Folgendes ergänzt werden:

- **Import** hinzufügen:
  ```python
  from run_addon import setup_run_addon, get_run_addon
  ```

- **Addon initialisieren** (in `lifespan()` vor `yield`):
  ```python
  setup_run_addon()
  ```

- **Endpunkt registrieren** (nach dem `app = FastAPI(...)` Block):
  ```python
  run_addon_instance = get_run_addon()

  @app.post("/run")
  async def run_endpoint(request: Request):
      data = await request.json()
      cmd = data.get("cmd", "")
      result = run_addon_instance(cmd)
      return JSONResponse(content=result)
  ```

**Validierung:**
```bash
export PATH=/usr/local/bin:$PATH
docker exec hermes-devops-ai-environment-control-gateway-1 \
  python3 -c "
from run_addon import setup_run_addon, get_run_addon
setup_run_addon()
addon = get_run_addon()
print('Addon OK:', addon is not None)

import urllib.request, json
req = urllib.request.Request(
    'http://127.0.0.1:8092/run',
    data=json.dumps({'cmd':'df -h'}).encode(),
    headers={'Content-Type':'application/json'},
    method='POST'
)
r = urllib.request.urlopen(req, timeout=10)
print('STATUS:', r.status)
print(r.read().decode()[:200])
"
```

### 2. Telegram-Bot erweitern

In `telegram_bot/app.py` ergänzen:

- **Handler** (innerhalb von `main()`):
  ```python
  async def run_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
      if not context.args:
          await update.message.reply_text("❌ Verwendung: /run <befehl>")
          return
      cmd = " ".join(context.args)
      payload = {"cmd": cmd}
      headers = {"Content-Type": "application/json", "Authorization": "Bearer " + api_key}
      try:
          response = requests.post(
              "http://control-gateway:8092/run",
              json=payload,
              headers=headers,
              timeout=120
          )
          if response.status_code == 200:
              data = response.json()
              stdout = data.get("stdout", "")
              stderr = data.get("stderr", "")
              rc = data.get("returncode", -1)
              lines = stdout.strip().splitlines()
              msg = f"📤 stdout ({len(lines)} Zeilen, returncode={rc}):\n```\n{stdout[:3800]}\n```"
              await update.message.reply_text(msg, parse_mode="Markdown")
          else:
              await update.message.reply_text(f"❌ Fehler vom Gateway: HTTP {response.status_code}")
      except Exception as e:
          await update.message.reply_text(f"❌ Exception: {e}")
      finally:
          context.user_data["chat_session_active"] = True

  application.add_handler(CommandHandler("run", run_cmd))
  ```

### 3. run_addon.py bereitstellen

Datei im Projekt-Root (`~/hermes-devops-ai-environment/run_addon.py`) ablegen:

- Timeout: **120 Sekunden**
- Whitelist erlaubt: `df`, `free`, `uptime`, `docker`, `docker-compose`, `ps`, `ls`, `cat`, `head`, `tail`, `du`, `curl`, `ping`, `git`, `mkdir`, `rm`, `cp`, `mv`, `find`, `grep`, `awk`, `sed`, `python3`, `node`, `npm`, `kubectl`, `terraform`, `ansible-playbook`, `vault`, `consul`, `journalctl`, `systemctl`, `top`, `htop`, `nload`, `iftop`, `netstat`, `ss`, `lsof`
- **Verbotene Zeichen:** `$`, `` ` ``, `\n`, `\r`, `\t` (werden abgelehnt mit `{"error":"forbidden chars"}`)

### 4. Container-Deployment

**Wichtig:** Docker Desktop auf macOS cached Host-Volume-Änderungen nicht zuverlässig in laufende Container.

#### Variante A: Hot-Patch via docker cp (schnell)
```bash
export PATH=/usr/local/bin:$PATH

# Gateway patchen
docker cp ~/hermes-devops-ai-environment/gateway/app.py \
  hermes-devops-ai-environment-control-gateway-1:/app/gateway/app.py
docker cp ~/hermes-devops-ai-environment/run_addon.py \
  hermes-devops-ai-environment-control-gateway-1:/app/run_addon.py
docker restart hermes-devops-ai-environment-control-gateway-1

# Bot patchen
docker cp ~/hermes-devops-ai-environment/telegram_bot/app.py \
  hermes-devops-ai-environment-telegram-bot-1:/workspace/telegram_bot/app.py
docker restart hermes-devops-ai-environment-telegram-bot-1
```

#### Variante B: Docker Compose Rebuild (sauber)
```bash
cd ~/hermes-devops-ai-environment
export PATH=/usr/local/bin:$PATH
docker compose -f docker-compose.control.yml -f docker-compose.override.yml up -d --build
```

**Hinweis:** Variante B kann Deadlocks verursachen, wenn mehrere `docker compose up -d` parallel laufen (siehe *Pitfalls*).

## Verwendung in Telegram

| Befehl | Beschreibung | Beispiel-Ausgabe |
|--------|--------------|------------------|
| `/run df -h` | Disk-Usage | Filesystem /dev/disk3s1s1 … |
| `/run docker ps` | Container-Status | 12 Container UP … |
| `/run docker-compose -f docker-compose.control.yml logs --tail 20 control-gateway` | Gateway-Logs | Letzte 20 Zeilen … |
| `/run uptime` | System-Uptime | 14:23 up 3 days … |

## Troubleshooting

### SSH-Escaping-Probleme beim Remote-Patching und Testen

**Symptom:** `python3: can't open file '/tmp/test_run.py': No such file or directory`

**Ursache:** Nested SSH über 3 Hops (lokal → Hostinger → Mac Mini) mit `cat << EOF` oder inline Python schlägt fehl, weil jeder Hop Quotes anders parsed.

**Fix (Testing): Führe Tests auf dem Mac Mini Host durch, nicht über SSH-Schachtelungen.**

```bash
# Auf dem Mac Mini (nicht über verschachtelte SSH-Hops):
export PATH=/usr/local/bin:$PATH

# Direkter Test im Container
docker exec hermes-devops-ai-environment-control-gateway-1 \
  python3 -c "
import urllib.request, json
req = urllib.request.Request(
    'http://127.0.0.1:8092/run',
    data=json.dumps({'cmd':'docker ps'}).encode(),
    headers={'Content-Type':'application/json'},
    method='POST'
)
r = urllib.request.urlopen(req, timeout=10)
print('STATUS:', r.status)
print(r.read().decode()[:200])
"
```

**Fix (Deployment): Datei-basiert statt Inline:**
```bash
# 1. Lokal erstellen
cat > /tmp/test_run.py << 'PYEOF'
import urllib.request, json
req = urllib.request.Request(
    "http://127.0.0.1:8092/run",
    data=json.dumps({"cmd":"df -h"}).encode(),
    headers={"Content-Type":"application/json"},
    method="POST"
)
r = urllib.request.urlopen(req, timeout=10)
print("STATUS:", r.status)
print(r.read().decode()[:500])
PYEOF

# 2. SCP-Kette: Lokal → Hostinger → Mac Mini
scp /tmp/test_run.py hostinger:/tmp/test_run.py
ssh hostinger "scp -i ~/.ssh/id_macmini -o StrictHostKeyChecking=no \
  /tmp/test_run.py klaus@100.93.33.84:/tmp/test_run.py"

# 3. Auf Mac Mini ausführen
ssh hostinger "ssh -i ~/.ssh/id_macmini -o StrictHostKeyChecking=no \
  klaus@100.93.33.84 'export PATH=/usr/local/bin:\$PATH; \
  docker exec hermes-devops-ai-environment-control-gateway-1 \
  python3 /tmp/test_run.py'"
```

> Siehe auch Skill `mac-mini-remote-access` → `references/ssh-quoting-escaping-pitfalls.md` für tiefere Details.

---

### Gateway-Container startet nicht (SyntaxError)

**Symptom:** `docker ps` zeigt `Restarting`, Log zeigt `SyntaxError`.

**Ursache:** Docker Desktop hat alte Datei im Container-Layer gecached.

**Fix:**
```bash
docker cp ~/hermes-devops-ai-environment/gateway/app.py \
  hermes-devops-ai-environment-control-gateway-1:/app/gateway/app.py
docker cp ~/hermes-devops-ai-environment/run_addon.py \
  hermes-devops-ai-environment-control-gateway-1:/app/run_addon.py
docker restart hermes-devops-ai-environment-control-gateway-1
```

Validierung:
```bash
python3 -c "
import py_compile
py_compile.compile('/Users/klaus/hermes-devops-ai-environment/gateway/app.py', doraise=True)
print('APP_OK')
py_compile.compile('/Users/klaus/hermes-devops-ai-environment/run_addon.py', doraise=True)
print('ADDON_OK')
"
```

### Bot antwortet nicht auf `/run`

**Symptom:** Keine Antwort oder „Unbekannter Befehl“.

**Checks:**
1. Handler im Container prüfen:
   ```bash
   docker exec hermes-devops-ai-environment-telegram-bot-1 \
     grep -n "async def run_cmd" /workspace/telegram_bot/app.py
   ```
2. API-URL im `.env` prüfen: `HERMES_API_URL=http://control-gateway:8092`
3. Bot-Container neustarten:
   ```bash
   docker restart hermes-devops-ai-environment-telegram-bot-1
   ```

### Gateway antwortet 404 auf /run

**Symptom:** `{"detail":"Not Found"}`.

**Fix:** Gateway-Container enthält nicht den gepatchten Code. Patch erneut per `docker cp` einspielen und Container neustarten.

### SSH-Escaping-Probleme beim Remote-Patching

**Symptom:** `python3: can't open file '/tmp/test_run.py': No such file or directory`

**Ursache:** Nested SSH über 3 Hops (lokal → Hostinger → Mac Mini) mit `cat << EOF` Quoting scheitert.

**Fix:** Statt here-doc, Datei lokal erstellen und via SCP-Kette übertragen:
```bash
# Lokal
cat > /tmp/test_run.py << 'PYEOF'
import urllib.request, json
req = urllib.request.Request("http://127.0.0.1:8092/run", ...)
...
PYEOF

scp -P 222 /tmp/test_run.py hostinger:/tmp/
ssh hostinger "scp -i ~/.ssh/id_macmini /tmp/test_run.py klaus@100.93.33.84:/tmp/"
ssh hostinger "ssh -i ~/.ssh/id_macmini klaus@100.93.33.84 'docker exec ... python3 /tmp/test_run.py'"
```

### Docker Compose Deadlock

**Symptom:** `docker compose up -d` hängt ewig.

**Ursache:** Mehrere parallele `docker compose up -d` blockieren sich gegenseitig.

**Fix:**
```bash
pkill -9 docker || true
pkill -9 dockerd || true
pkill -9 docker-credential-desktop || true
pkill -9 Docker || true
pkill -9 com.docker.backend || true
pkill -9 com.docker.helper || true
docker ps -aq | xargs docker rm -f 2>/dev/null || true
ls ~/Library/Containers/com.docker.docker/Data/tasks/ 2>/dev/null | xargs kill -9 2>/dev/null || true
rm -rf ~/Library/Containers/com.docker.docker/Data/tasks
rm -rf ~/Library/Containers/com.docker.docker/Data/com.docker.driver.amd64-linux/Docker.raw
```
Danach Docker Desktop App neu starten.

## Monitoring & Health Checks

```bash
# Gateway Health
curl -s http://control-gateway:8092/health

# /run Endpunkt testen
docker exec hermes-devops-ai-environment-control-gateway-1 \
  python3 -c "
import urllib.request, json
req = urllib.request.Request(
    'http://127.0.0.1:8092/run',
    data=json.dumps({'cmd':'docker ps'}).encode(),
    headers={'Content-Type':'application/json'},
    method='POST'
)
r = urllib.request.urlopen(req, timeout=10)
print(r.status, r.read().decode()[:200])
"

# Container-Status
export PATH=/usr/local/bin:$PATH
docker ps --format "table {% raw %}{{.Names}}\t{{.Status}}{% endraw %}"
```

## References

- Skill: `mac-mini-remote-access` — SSH-Zugriff auf Mac Mini über Hostinger
- Skill: `log-protection-fleet` — Fleet-weite Log-/History-Schutzmaßnahmen
- Skill: `fleet-overview` — Status aller Nodes (Hostinger, Mac Mini, AE8)
