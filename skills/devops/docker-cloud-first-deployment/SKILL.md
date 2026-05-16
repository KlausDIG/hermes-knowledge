---
name: docker-cloud-first-deployment
description: Cloud-First Docker-Compose-Deployment auf macOS mit Zero-Persistence, VM-Disk-Limits und SSH-Remote-Monitoring.
trigger: docker compose auf macOS, Docker Desktop VM-Disk voll, Cloud-First Container-Strategie, Log-Rotation, SSH-Jump-Cronjob-Monitoring.
model: kimi-k2.6
---

# Docker Cloud-First Deployment (macOS)

Cloud-First: Container halten KEINE Daten persistent — alles fließt ins Nächsten oder wird nach GitHub/Nextcloud synchronisiert. Docker Desktop VM auf macOS wird begrenzt, Logs rotieren, Health-Checks via SSH-Jump-Host.

## 1. Voraussetzungen

- macOS mit Docker Desktop
- SSH-Zugang (lokal oder via Jump-Host + Tailscale)
- `docker-compose.control.yml` (Base-Stack) und `docker-compose.override.yml` (Cloud-First-Anpassungen)

## 2. Cloud-First Compose-Regeln

### 2.1 Named Volumes ENTFERNEN (control.yml)

In der `docker-compose.control.yml` dürfen KEINE named volumes definiert sein:

```yaml
# FALSCH — erzeugt persistente Daten:
volumes:
  control_data:
  prometheus_data:
  grafana_data:

services:
  prometheus:
    volumes:
      - prometheus_data:/prometheus   # ❌
```

### 2.2 Override.yml: explizite `volumes: []`

```yaml
# RICHTIG — keine Persistenz:
services:
  n8n:
    volumes: []   # explizit leer
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        compress: "true"
```

> **Pitfall:** Wenn `volumes:` komplett fehlt, erbt der Service ggf. Volumes aus der Base-Compose. Explizit `[]` setzen!

### 2.3 Read-Only Skill/Memory-Mounts (erlaubt)

```yaml
services:
  telegram-bot:
    volumes:
      - /Users/klaus/.hermes/skills:/workspace/hermes-skills:ro
```

Read-only Mounts von lokalem Filesystem sind OK — sie verändern nicht die VM-Disk.

## 3. Docker Desktop VM-Disk begrenzen (macOS)

### 3.1 Settings.json direkt setzen

```bash
mkdir -p "/Users/$USER/Library/Group Containers/group.com.docker"
printf '{\n\t"diskSizeMiB": 65536\n}\n' > \
  "/Users/$USER/Library/Group Containers/group.com.docker/settings.json"
```

> **64 GB** = 65536 MiB. Docker Desktop muss NEU gestartet werden damit das greift.

### 3.2 Notfall-Reset bei voller Platte

Wenn Docker Desktop die VM-Disk aufgebläht hat (Sparse-File zeigt 100–400 GB):

```bash
# Docker beenden
pkill -9 -x "Docker Desktop"
pkill -9 -f "com.docker.backend"
sleep 10

# VM-Disk löschen (bringt sofort 10–15 GB)
rm -rf ~/Library/Containers/com.docker.docker/Data/vms/0/
rm -rf ~/Library/Containers/com.docker.docker/Data/log/*

# Docker mit begrenzter VM neu starten
open -a "Docker Desktop"
```

> **Wichtig:** Nach dem Löschen der VM sind alle Container-Images weg — Docker muss sie neu pullen.

## 4. Log-Rotation in allen Services

Jeder Service in der override.yml bekommt:

```yaml
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        compress: "true"
```

Für sehr gesprächige Services (scheduler, cadvisor, node-exporter): `max-size: "5m"`, `max-file: "2"`.

## 5. SSH-Remote-Monitoring via Cronjob

### 5.1 Health-Check Script (auf Mac Mini)

Pfad: `~/hermes-devops-ai-environment/scripts/ops/macmini-health-check.sh`

Aufgaben:
1. Docker Engine prüfen → `docker version`
2. Speicherplatz checken → `df -h /`
3. Container prüfen → `docker ps`
4. VM-Disk Größe melden
5. Bei Notfall: Docker-Caches löschen (`docker system prune -f`)

### 5.2 Cronjob auf Jump-Host (Hostinger VPS)

SSH-Jump zum Mac Mini alle 30 Min:

```bash
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -i /root/.ssh/id_macmini klaus@100.93.33.84 \
  '~/hermes-devops-ai-environment/scripts/ops/macmini-health-check.sh'
```

## 6. Zuverlässige SSH-Remote-Techniken

### 6.1 Python/sed-Einliner → NICHT über Zsh-SSH

Zsh-Quoting über SSH-Jump zerstört komplexe Einzeiler. Stattdessen:

```bash
# Zuverlässig: Datei lokal schreiben, via cat | ssh pipen
cat /tmp/script.py | ssh hostinger \
  "ssh -i /root/.ssh/id_macmini klaus@100.93.33.84 'python3 -'"
```

### 6.2 Python-Skripte auf Remote ausführen

```bash
# 1. Lokale Datei erstellen
cat > /tmp/check_mounts.py << 'EOF'
import json, subprocess
out = subprocess.check_output(['docker','inspect','container_name'], text=True)
data = json.loads(out)
for m in data[0].get('Mounts',[]):
    print(m['Type'], ':', m.get('Name',m['Source']), '->', m['Destination'])
EOF

# 2. Auf Remote pipen und ausführen
cat /tmp/check_mounts.py | ssh user@host 'python3 -'
```

## 7. Manuelles macOS-Cleanup-Script

Pfad: `~/macmini-cleanup.sh`

Bereinigt interaktiv:
- Time Machine Snapshots
- Docker Caches
- Browser Caches (Safari, Chrome, Firefox)
- System Caches (>7 Tage)
- System Logs (>30 Tage)
- Downloads
- Papierkorb
- Xcode DerivedData

Ausführen: `chmod +x ~/macmini-cleanup.sh && ~/macmini-cleanup.sh`

Mit `--force` läuft ohne Rückfragen.

## 8. Referenzen

- [references/docker-vm-disk.md](references/docker-vm-disk.md) — Docker VM Sparse-File Verhalten
- [references/compose-override-patterns.md](references/compose-override-patterns.md) — Cloud-First Compose-Muster
- [templates/docker-compose.override.yml](templates/docker-compose.override.yml) — Starter-Override ohne named Volumes
- [scripts/macmini-health-check.sh](scripts/macmini-health-check.sh) — Health-Check für Cronjob
- [scripts/macmini-cleanup.sh](scripts/macmini-cleanup.sh) — Interaktives macOS Cleanup
