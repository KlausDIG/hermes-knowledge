---
name: ssh-hostinger-vps
title: Hostinger VPS SSH Setup
version: 1.0.0
author: KlausDIG
description: SSH-Key-basierter Zugriff auf Hostinger VPS (187.77.65.191)
tags: [ssh, vps, hostinger, server-admin]
---

# Hostinger VPS — SSH Setup

## Schnellzugriff

```bash
# Kurzform (Alias)
ssh hostinger

# Langform (falls Alias nicht definiert)
ssh root@187.77.65.191
```

## SSH-Config

Datei: `~/.ssh/config`

```
Host hostinger
  HostName 187.77.65.191
  User root
  IdentityFile ~/.ssh/id_ed25519
  AddKeysToAgent yes
```

## SSH-Key Setup (Ersteinrichtung)

### 1. Key generieren (falls noch keiner existiert)

```bash
ssh-keygen -t ed25519 -C "KlausDIG@users.noreply.github.com" -f ~/.ssh/id_ed25519
```

- **Privater Key** (`~/.ssh/id_ed25519`) → niemals teilen
- **Öffentlicher Key** (`~/.ssh/id_ed25519.pub`) → ins VPS-Panel einfügen

### 2. Public Key anzeigen

```bash
cat ~/.ssh/id_ed25519.pub
```

Ausgabe kopieren und in Hostinger Panel → VPS → SSH Keys einfügen.

### 3. Verbindung testen

```bash
ssh hostinger
```

## Sicherheit nach Einrichtung

**Passwort-Login deaktivieren** (nach erfolgreichem Key-Test):

```bash
ssh hostinger
sed -i 's/#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd
```

## Wartung

| Befehl | Zweck |
|--------|-------|
| `ssh hostinger` | Login |
| `ssh hostinger "uptime"` | Befehl ausführen ohne Login |
| `scp datei.txt hostinger:/root/` | Datei hochladen |
| `scp hostinger:/var/log/syslog ./` | Datei herunterladen |

## Hermes Update auf VPS

Hermes auf dem VPS manuell aktualisieren (manuelle Installation unter `/opt/hermes/hermes-agent/`, nicht via pip):

```bash
# 1. Backup
tar -czf /root/hermes-backup-$(date +%Y%m%d-%H%M%S).tar.gz -C /opt/hermes .

# 2. Services stoppen
systemctl stop clawbot-bridge hermes-consumer ollama-hermes-proxy

# 3. Neue Version downloaden
cd /tmp
curl -L -o hermes-v0.13.0.tar.gz https://github.com/NousResearch/hermes-agent/archive/refs/tags/v2026.5.7.tar.gz
tar -xzf hermes-v0.13.0.tar.gz

# 4. Neue Version installieren (neben alter)
mv /opt/hermes/hermes-agent /opt/hermes/hermes-agent-v0.10.0-backup
mv /tmp/hermes-agent-v2026.5.7 /opt/hermes/hermes-agent-new

# 5. Config übertragen
cp /root/.hermes/config.yaml /opt/hermes/hermes-agent-new/
cp /root/.hermes/SOUL.md /opt/hermes/hermes-agent-new/ 2>/dev/null || true
cp -r /root/.hermes/skills/* /opt/hermes/hermes-agent-new/skills/ 2>/dev/null || true

# 6. Venv installieren
cd /opt/hermes/hermes-agent-new
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e ".[all]"

# 7. Symlink aktualisieren
ln -sf /opt/hermes/hermes-agent-new/venv/bin/hermes /usr/local/bin/hermes
ln -sf /opt/hermes/hermes-agent-new /opt/hermes/hermes-agent

# 8. Systemd reload
systemctl daemon-reload

# 9. Services starten
systemctl start hermes-consumer ollama-hermes-proxy clawbot-bridge
```

### Inventar des VPS (nützlich für Diagnose)
```bash
ssh hostinger '
echo "=== SYSTEM ==="
uname -a; cat /etc/os-release | grep -E "^(NAME|VERSION)="
echo "CPU: $(nproc)"; free -h | grep Mem; df -h / | tail -1
echo "=== HERMES ==="
hermes --version 2>/dev/null
echo "Prozesse: $(ps aux | grep -i hermes | grep -v grep | wc -l)"
echo "=== SERVICES ==="
for svc in hermes-consumer ollama-hermes-proxy clawbot-bridge; do
    echo "  $svc: $(systemctl is-active $svc.service 2>/dev/null)"
done
'
```

| Eigenschaft | Normalwert |
|-------------|------------|
| CPU | 2 Kerne |
| RAM | 7.8 GB |
| Speicher | 96 GB SSD |
| OS | Ubuntu 24.04.4 LTS |
| Hermes (alt) | v0.10.0 (April) |
| Hermes (neu) | v0.13.0 (Mai) |
| Docker | 29.4.2 (keine Container) |
| Speicher nach .bash_history-Fix | ~60/96 GB (vorher 99%) |

### Dienste auf dem VPS
| Dienst | Status | Zweck |
|--------|--------|-------|
| `hermes-consumer.service` | systemd | Event-Verarbeitung |
| `ollama-hermes-proxy.service` | systemd | Ollama localhost:11434 |
| `clawbot-bridge.service` | systemd | Adaptive Clawbot Bridge |
| `sshd` | Port 22 | SSH-Zugriff |
| `pm2-logrotate` | PM2 Modul | Log-Rotation |

### Cronjobs auf dem VPS
| Zeit | Script | Zweck |
|------|--------|-------|
| Stündlich | `clawbot-hermes-sync.sh` | Nextcloud-Sync |
| Alle 4h | `hermes-sync-mesh.sh` | Mesh-Sync |
| Täglich 02:00 | `clawbot-hermes-sync.sh` | Backup |
| Täglich 06:00 | `hermes_failover_test.sh` | Failover-Test |
| Täglich 17:00 | `ai_battery_digest.sh` | AI Digest |
| 4× täglich | `hermes_discord_all_channels.sh` | Discord |

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| `Permission denied` | Key nicht im Panel hinterlegt oder falsche IP |
| `Connection refused` | VPS noch im Setup / Firewall blockt |
| `Host key verification failed` | `ssh-keygen -R 187.77.65.191` |
| **Speicher 99% voll** | `.bash_history` prüfen → leeren → Limits setzen (siehe `linux-system-maintenance` Skill) |
| Hermes nicht erreichbar | `systemctl status hermes-consumer` prüfen |
| Ollama nicht erreichbar | `systemctl status ollama-hermes-proxy` |

## Tags

- `ssh` `vps` `hostinger` `server` `root` `hermes` `ubuntu-2404`
