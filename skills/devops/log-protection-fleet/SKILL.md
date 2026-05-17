---
name: log-protection-fleet
title: Log-Schutzmaßnahmen für Multi-Node-Fleet
version: 1.0.0
author: KlausDIG
description: Präventive Schutzmaßnahmen gegen Log-/History-Explosion auf Linux/macOS Hosts (Hermes Agent, Hostinger VPS, Mac Mini). Enthält Ursachenanalyse, Rotation, Limits, Guards.
tags: [logrotate, journald, docker, history, disk-space, fleet, ops]
---

# Log-Schutzmaßnahmen für Multi-Node Fleet

## Hintergrund / Ursachenanalyse

Die `.bash_history`-Explosion auf dem Mac Mini (285 GB → 4 KB, 97% → 4% Plattenbelegung) hat gezeigt, dass **Runaway-Logs ohne Limits** schnell die gesamte VM/Festplatte blockieren können. Typische Ursachen:

| Ursache | Beispiel | Ergebnis |
|---------|----------|----------|
| Self-Append Loop | `cat ~/.bash_history >> ~/.bash_history` | Geometrische Explosion |
| Fehlendes Logrotate | Custom Agent-Logs | Endloses Wachstum |
| Docker Default Logs | `--log-driver json-file` ohne `--log-opt` | Container-Logs füllen Platte |
| systemd Journal | Kein `SystemMaxUse` | Journal frisst GBs |
| Cron-Deduplizierungsfehler | `awk '!seen[$0]++'` auf 285 GB Datei | Prozess hängt, .tmp wird nicht verschoben |

---

## Schutzmaßnahmen pro System

### 1. Lokaler Host (Hermes Agent)

**Path:** `~/.hermes/logs/hermes-logrotate.conf`

```
/home/klausd/.hermes/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 klausd klausd
    size 50M
}
```

**Cron:**
```bash
30 3 * * * /usr/sbin/logrotate -s ~/.hermes/logs/logrotate.state ~/.hermes/logs/hermes-logrotate.conf
```

**Deploy:**
```bash
cat > ~/.hermes/logs/hermes-logrotate.conf << 'EOF'
/home/klausd/.hermes/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 klausd klausd
    size 50M
}
EOF
(crontab -l 2>/dev/null; echo "30 3 * * * /usr/sbin/logrotate -s /home/klausd/.hermes/logs/logrotate.state /home/klausd/.hermes/logs/hermes-logrotate.conf") | sort -u | crontab -
```

---

### 2. Hostinger VPS (Ubuntu)

**a) System-Logrotate für Hermes-Custom-Logs:**
```bash
cat > /etc/logrotate.d/hermes-vps << 'EOF'
/var/log/clawbot {
    daily
    rotate 5
    compress
    delaycompress
    missingok
    notifempty
    size 20M
}

/var/log/macmini_health.log {
    daily
    rotate 5
    compress
    delaycompress
    missingok
    notifempty
    size 20M
}

/var/log/tailscale-watchdog.log {
    daily
    rotate 5
    compress
    delaycompress
    missingok
    notifempty
    size 20M
}
EOF
```

**b) systemd Journal-Limit:**
```bash
mkdir -p /etc/systemd/journald.conf.d
cat > /etc/systemd/journald.conf.d/size-limit.conf << 'EOF'
[Journal]
SystemMaxUse=500M
MaxRetentionSec=7day
EOF
systemctl restart systemd-journald
```

**c) History Guard (stündlich):**
```bash
cat > /root/.bash_history_guard.sh << 'EOF'
#!/bin/bash
HIST="/root/.bash_history"
MAX_MB=50
if [ -f "$HIST" ]; then
    SIZE=$(du -m "$HIST" | awk '{print $1}')
    if [ "$SIZE" -gt "$MAX_MB" ]; then
        echo "[$(date)] WARNING: .bash_history is ${SIZE}MB (limit ${MAX_MB}MB) — truncating to 500 lines" | tee -a /var/log/bash_history_guard.log
        tail -n 500 "$HIST" > "${HIST}.tmp" && mv "${HIST}.tmp" "$HIST"
    fi
fi
EOF
chmod +x /root/.bash_history_guard.sh
(crontab -l 2>/dev/null; echo "0 * * * * /root/.bash_history_guard.sh") | sort -u | crontab -
```

---

### 3. Mac Mini (macOS / Apple Silicon)

**a) Docker Log-Limits (daemon.json):**
```bash
mkdir -p ~/.docker
cat > ~/.docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3",
    "compress": "true"
  }
}
EOF
# Docker Desktop → Settings → Docker Engine → Apply & Restart
```

**Alternative per docker-compose (für einzelne Services):**
```yaml
services:
  telegram-bot:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        compress: "true"
```

**b) History Guard (zsh/bash):**
```bash
cat > ~/Automation/Scripts/history-guard.sh << 'EOF'
#!/bin/zsh
HIST="$HOME/.bash_history"
MAX_MB=50
if [ -f "$HIST" ]; then
    SIZE=$(du -m "$HIST" | awk '{print $1}')
    if [ "$SIZE" -gt "$MAX_MB" ]; then
        echo "[$(date)] WARNING: .bash_history is ${SIZE}MB (limit ${MAX_MB}MB) — truncating" | tee -a /tmp/history-guard.log
        tail -n 500 "$HIST" > "${HIST}.tmp" && mv "${HIST}.tmp" "$HIST"
    fi
fi
EOF
chmod +x ~/Automation/Scripts/history-guard.sh
# Cron hinzufügen: crontab -e → 0 * * * * /Users/klaus/Automation/Scripts/history-guard.sh
```

**c) Shell-History Limits (nach Cleanup setzen):**
```bash
echo 'export HISTFILESIZE=10000' >> ~/.bashrc
echo 'export HISTSIZE=10000'     >> ~/.bashrc
echo 'export SAVEHIST=10000'      >> ~/.zshrc
echo 'export HISTSIZE=10000'      >> ~/.zshrc
```

---

## Verifikation

| Check | Befehl |
|-------|--------|
| Logrotate Config testen | `logrotate -d /path/to/config` (dry-run) |
| Journal Größe | `journalctl --disk-usage` |
| History Größe | `du -sh ~/.bash_history` |
| Docker Log-Config | `docker info --format '{{ .LoggingDriver }}'` |
| Container Log-Größe | `docker inspect <name> --format='{{.LogPath}}'` dann `du -sh` |
| Logrotate Status | `cat /var/lib/logrotate/status` |

---

## Wichtige Pitfalls

1. **Self-Append verhindern:** Niemals `cat $FILE >> $FILE` in Cronjob/Script ohne Prüfung
2. **Deduplizierung auf großen Dateien:** `awk '!seen[$0]++'` ist O(n²) Memory – bei GB-Dateien crasht es
3. **Docker Default:** `json-file` ohne Limits → unbegrenztes Wachstum
4. **ZSH History Format:** `.zsh_history` enthält Zeitstempel (`: timestamp:0;cmd`) – nicht blind mergen
5. **Journald persistiert:** Standard `/var/log/journal` kann schnell GBs fressen

---

## Schnellreferenz: Wenn Platte voll ist

```bash
# 1. Top-Verdächtige finden
sudo du -sh /var/log/* | sort -rh | head -10
sudo du -sh ~/.bash_history
sudo du -sh ~/.hermes/logs/* | sort -rh | head -10

# 2. Sofort freigeben
> ~/.bash_history          # leeren
sudo journalctl --vacuum-size=100M
sudo logrotate -f /etc/logrotate.conf

# 3. Docker-Container-Logs kürzen
sudo truncate -s 0 $(docker inspect <name> --format='{{.LogPath}}')
# oder:
docker system prune -a --volumes
```

## Tags
- `logrotate` `journald` `docker` `history` `disk-space` `fleet` `ops` `preventive`
