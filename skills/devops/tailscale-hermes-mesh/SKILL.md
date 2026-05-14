---
name: tailscale-hermes-mesh
title: Tailscale Hermes Mesh Network
version: 1.0.0
author: KlausDIG
description: Verwaltung der Tailscale-basierten Hermes-Mesh-Netzwerktopologie (Hostinger, AE8, Mac Mini, lokale Instanzen)
tags: [tailscale, mesh, vps, ae8, mac-mini, sync, network]
---

# Tailscale Hermes Mesh Network

## Netzwerktopologie

```
                    ┌─────────────────┐
                    │   INTERNET      │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐        ┌────▼────┐        ┌────▼────┐
    │Hostinger│◄──────►│  AE8    │◄──────►│Mac Mini │
    │  (VPS)  │  ❌    │(Desktop)│  ❌    │  (M1)   │
    │100.125.│(12d off)│100.64. │(offline)│100.93.  │
    │  211.54 │        │ 108.109 │        │  33.84  │
    └────┬────┘        └────┬────┘        └────┬────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                    ┌────────▼────────┐
                    │   LOCAL         │
                    │ (klaus-gk50)    │
                    │ 100.69.151.91   │
                    └─────────────────┘
```

## Geräte-Status

| Gerät | Tailscale Name | IP | Status | Letzter Kontakt |
|-------|---------------|-----|--------|----------------|
| **Hostinger VPS** | srv1482003 | 100.125.211.54 | ✅ Online | Aktiv |
| **AE8** | ae8 | 100.64.108.109 | ❌ **Offline** | 12 Tage |
| **Mac Mini** | mac-mini-von-klaus | 100.93.33.84 | ✅ Online | Direkt |
| **Lokal** | klaus-gk50 | 100.69.151.91 | ✅ Online | Direkt |
| **iPad** | ipad-pro-11-gen-3 | 100.104.106.119 | ⚠️ Unbekannt | - |
| **linux-clawbot** | linux-clawbot-agent | 100.105.214.86 | ❌ Offline | 16 Tage |
| **Anne M1** | anne-m1 | 100.118.194.66 | ❌ Offline | 14 Tage |

## Mac Mini — Docker-basierte Hermes/AI-Umgebung

> ⚠️ **Wichtig:** Der Mac Mini nutzt eine **eigenständige Docker-Compose-Umgebung** (`hermes-devops-ai-environment`), die NICHT das Standard-`~/.hermes/`-Layout verwendet. Für Cloud-First-Sync muss ein `docker-compose.override.yml` die Skills/Memory in die Container mounten.

### Architektur
| Aspekt | Standard-Hermes | Mac Mini Docker |
|--------|----------------|-----------------|
| Hermes-Agent | `~/.hermes/` nativ | ❌ Kein nativer Agent |
| Skills | `~/.hermes/skills/` | ✅ Via Override gemountet |
| Memory | `~/.hermes/memory/` | ✅ Via Override gemountet |
| Docker-Container | — | ✅ **12 Services** |
| Telegram-Bot | — | ✅ **Funktioniert** |
| Cloud-Sync | Hostinger + Nextcloud | ✅ Git pull + rclone + rsync |

### Docker-Compose Override für Hermes-Skills/Memory

Erstelle `~/hermes-devops-ai-environment/docker-compose.override.yml`:

```yaml
services:
  control-gateway:
    volumes:
      - /Users/klaus/.hermes/skills:/workspace/hermes-skills:ro
      - /Users/klaus/.hermes/memory:/workspace/hermes-memory:ro

  telegram-bot:
    volumes:
      - /Users/klaus/.hermes/skills:/workspace/hermes-skills:ro
```

Anwenden:
```bash
cd ~/hermes-devops-ai-environment
docker compose -f docker-compose.control.yml -f docker-compose.override.yml up -d
```

### rclone auf macOS installieren (ohne Homebrew)

```bash
# Download + Installieren nach ~/bin/ (kein sudo nötig)
cd /tmp
curl -sLO https://downloads.rclone.org/rclone-current-osx-arm64.zip
unzip -q rclone-current-osx-arm64.zip
cp rclone-*-osx-arm64/rclone ~/bin/rclone
chmod +x ~/bin/rclone

# PATH in ~/.zshrc ergänzen:
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc

# Nextcloud-Config korrigieren (wichtig: /dav/files/USER/ statt WebDAV-URL):
cat > ~/.config/rclone/rclone.conf <<EOF
[nextcloud]
type = webdav
url = https://nx95358.your-storageshare.de/remote.php/dav/files/klausi/
vendor = nextcloud
user = klausi
pass = <DEIN_PASS>
EOF
```

### Container-Stack (`docker-compose.control.yml`)
| # | Container | Status | Port | Zweck |
|---|-----------|--------|------|-------|
| 1 | `control-gateway` | Up (healthy) | **8092** | API Gateway |
| 2 | `telegram-bot` | Up | — | Telegram Bot |
| 3 | `codex-worker` | Up | — | OpenAI Codex Worker |
| 4 | `alert-receiver` | Up | **9094** | Alert Handler |
| 5 | `scheduler` | Up | — | Task Scheduler |
| 6 | `open-webui` | Up (healthy) | **3001** | LLM Chat Interface |
| 7 | `n8n` | Up | **5678** | Workflow Automation |
| 8 | `grafana` | Up | **3000** | Dashboards |
| 9 | `prometheus` | Up | **9090** | Monitoring |
| 10 | `cadvisor` | Up (healthy) | **8081** | Container Metrics |
| 11 | `alertmanager` | Up | **9093** | Alert Manager |
| 12 | `node-exporter` | Up | **9100** | System Metrics |
## Docker-Desktop macOS Troubleshooting

### Symptom: `docker ps` timeout, GUI läuft aber Engine nicht

**Diagnose:** Docker Desktop ist in einem "Not Responding" Zustand — die GUI startet, aber die Docker-Engine antwortet nicht. Das passiert oft nach macOS-Updates oder wenn die Docker-VM nicht sauber startet.

**Hinweis:** Wenn der Container-Stack vorher lief und Docker Desktop hängt, ist die **einfachste Lösung** oft ein Neustart der App (nicht des ganzen Systems).

```bash
# Schritt 1: Docker Desktop beenden
osascript -e 'quit app "Docker Desktop"'
sleep 10
killall "Docker Desktop" 2>/dev/null
killall com.docker.backend 2>/dev/null
sleep 10

# Schritt 2: Neustarten
open -a "Docker Desktop"
sleep 60

# Schritt 3: Prüfen
export PATH="/usr/local/bin:$PATH"
docker ps
docker compose -f ~/hermes-devops-ai-environment/docker-compose.control.yml ps
```

### Container-Stack nach Docker-Neustart wiederherstellen

Sobald Docker Desktop läuft, startet es Container **NICHT automatisch** (nur wenn `restart: unless-stopped` konfiguriert ist). Prüfe:

```bash
cd ~/hermes-devops-ai-environment
docker compose -f docker-compose.control.yml -f docker-compose.override.yml up -d
```

**Wichtig:** Die `override.yml` mit den Hermes-Skills/Memory-Mounts muss beim Start mit angegeben werden!

### Sync-Kompatibilität
| Sync-Richtung | Funktioniert | Bemerkung |
|---------------|-------------|-----------|
| Hostinger → Mac Mini (Skills) | ✅ | rsync zu `~/.hermes/skills/` auf macOS |
| Hostinger → Mac Mini (Memory) | ⚠️ | Nur falls vorhanden |
| Mac Mini → Hostinger (Memory) | ✅ | Bidirektional |
| **Docker-Umgebung → ~/.hermes** | ❌ | Nicht automatisch; Container mounten nur Projekt-Ordner |

Für Docker-interne Git-Sync: `cd ~/hermes-devops-ai-environment && git push`
Für Docker-interne Nextcloud-Sync: rclone muss im Container oder Host installiert sein (nicht vorhanden).

## Wakeup-Prozedur für AE8

### Schritt 1: Wake-on-LAN (falls unterstützt)
```bash
# Von Hostinger oder lokaler Maschine:
ssh hostinger "wakeonlan <AE8_MAC_ADRESSE>"  # MAC aus Tailscale Admin Panel
```

### Schritt 2: Tailscale reaktivieren (auf AE8 lokal)
```bash
# Auf AE8 ausführen (physische Tastatur nötig):
sudo tailscale up
# Oder falls bereits angemeldet:
tailscale status
```

### Schritt 3: Hermes auf AE8 starten
```bash
# Auf AE8:
systemctl start hermes-agent
# oder
hermes gateway --start
```

### Schritt 4: Mesh-Sync prüfen
```bash
# Auf Hostinger:
/root/hermes-sync-mesh.sh
# Ergebnis in /var/log/hermes-mesh-$(date +%Y%m%d).log prüfen
```

## Automatische Sync-Skripte

### 1. Voll-Mesh-Sync (alle 4 Stunden)

**Skript:** `/root/hermes-sync-mesh.sh` (Hostinger) — v1.1, korrigiert

| Richtung | Status | Details |
|---------|--------|---------|
| Hostinger → Mac Mini (Skills) | ✅ | rsync über SSH-Alias `mac-mini` |
| Hostinger → Mac Mini (Memory) | ⚠️ | Nur falls vorhanden (Hostinger hat leeres Memory) |
| Mac Mini → Hostinger (Memory) | ✅ | Bidirektionaler Austausch, macOS `~/.hermes` |
| Nextcloud (Skills + Memory) | ✅ | rclone Fallback |

**macOS-Home:** `~/.hermes` (nicht `/root/.hermes`)  
**SSH-Alias:** definiert in `~/.ssh/config` als `Host mac-mini` mit Key `id_macmini`

### 2. Mac Mini Health Check (alle 5 Min)

**Skript:** `/root/clawbot_macmini_check.sh`

```bash
# Prüft:
# 1. SSH-Erreichbarkeit (Port 22)
# 2. Ollama-Status (Port 11434)
# 3. Hermes-Prozesse
# 4. Speicherplatz
```

**Cron:**
```
*/5 * * * * /root/clawbot_macmini_check.sh >> /var/log/macmini_health.log 2>&1
```

## Manuelle Mesh-Operationen

### Sync von Hostinger zu Mac Mini
```bash
ssh hostinger
rsync -avz /root/.hermes/skills/ klaus@100.93.33.84:/root/.hermes/skills/
rsync -avz /root/.hermes/memory/ klaus@100.93.33.84:/root/.hermes/memory/
```

### Sync von Mac Mini zu Hostinger
```bash
ssh hostinger
rsync -avz klaus@100.93.33.84:/root/.hermes/memory/ /root/.hermes/memory/
```

### Direkter Zugriff auf Geräte
```bash
# Mac Mini
ssh klaus@100.93.33.84

# AE8 (wenn online)
ssh klausi@100.64.108.109

# Hostinger (dieser Server)
ssh hostinger  # oder ssh root@187.77.65.191
```

## Nextcloud als Fallback-Sync

| Quelle | Ziel | Methode | Intervall |
|--------|------|---------|-----------|
| Hostinger Skills | Nextcloud | `rclone sync` | alle 4h |
| Hostinger Memories | Nextcloud | `rclone sync` | alle 4h |
| Alle Geräte | Nextcloud | manuell | bei Bedarf |

## Troubleshooting

### "AE8 offline seit X Tage"
1. **Wake-on-LAN** senden (falls MAC bekannt)
2. **Physischen Zugriff** herstellen, `tailscale up` ausführen
3. **Hermes Agent** starten: `systemctl start hermes-agent`
4. **Mesh-Sync** triggern: `/root/hermes-sync-mesh.sh`

### Codex-Worker in Restart-Loop

**Symptom:** `docker logs` zeigt endlos:
```
[ollama-coder-worker] processing ...
python3: can't open file '/worker/run_ollama.py': [Errno 2] No such file or directory
```

**Ursache:** Die Datei `run_ollama.py` fehlt im `workers/codex/`-Verzeichnis oder wurde nicht ins Docker-Image kopiert.

**Fix:**

```bash
cd ~/hermes-devops-ai-environment

# 1. Datei erstellen
cat > workers/codex/run_ollama.py <>'PY'
#!/usr/bin/env python3
import sys, json, urllib.request, os

def main(task_file, result_file, ollama_url, model):
    with open(task_file, 'r') as f:
        task_content = f.read()
    # Umgebungsvariable prüfen (Docker host.docker.internal)
    ollama_url = os.environ.get('OLLAMA_URL', ollama_url)
    model = os.environ.get('OLLAMA_CODER_MODEL', model)
    url = f"{ollama_url}/api/generate"
    payload = json.dumps({"model": model, "prompt": task_content, "stream": False}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            result = data.get('response', 'No response')
    except Exception as e:
        result = f"ERROR: {str(e)}"
    with open(result_file, 'w') as f:
        f.write(result)
    print(f"[ollama-coder-worker] Result written ({len(result)} chars)")

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: run_ollama.py <task_file> <result_file> <ollama_url> <model>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
PY
chmod +x workers/codex/run_ollama.py

# 2. Image neu bauen + Container neu starten
docker compose -f docker-compose.control.yml build codex-worker
docker compose -f docker-compose.control.yml up -d codex-worker

# 3. Prüfen
docker logs --tail=5 hermes-devops-ai-environment-codex-worker-1
docker exec hermes-devops-ai-environment-codex-worker-1 ls /worker/
```

### "Sync fehlgeschlagen"
1. **Log prüfen:** `tail /var/log/hermes-mesh-$(date +%Y%m%d).log`
2. **Tailscale-Verbindung** prüfen: `tailscale ping <IP>`
3. **SSH-Key** prüfen: `ssh -v <IP>` für verbose Output

## Tags

- `tailscale` `mesh` `network` `vps` `ae8` `mac-mini` `sync` `rsync` `rclone`
