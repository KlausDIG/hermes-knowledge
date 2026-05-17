---
name: cross-system-protection
title: Cross-System Schutzmaßnahmen für die Hermes Mesh-Topologie
version: 1.0.0
author: KlausDIG
description: |
  Gleichzeitiges Deployen von Schutz-Scripts (History-Guard, Logrotate, Docker-Log-Limits, 
  Journal-Limits) auf allen Nodes der Hermes-Mesh: lokaler Host, Hostinger VPS, Mac Mini.
  
  Zentrale Erkenntnis aus Sitzung 2026-05-17: Wenn ein Platz-/Log-Problem auf einem Node 
  auftritt, existiert es wahrscheinlich auch auf den anderen — daher immer alle 3 Nodes 
  gleichzeitig schützen.
tags: [cross-system, protection, mesh, history-guard, logrotate, docker, journal, all-nodes]
---

# Cross-System Protection (Hermes Mesh)

## Topologie

```
┌─────────────────┐      SSH Jump       ┌─────────────────┐
│  Lokaler Host    │ ──────────────────▶│  Hostinger VPS  │
│  (Linux agent)   │                      │  root@187.77.65.191│
│                  │◄────Tailscale VPN────│                  │
│                  │                      │  key: /root/.ssh/  │
└─────────────────┘                      │       id_macmini   │
        │                                │  ────────────────  │
        │ Tailscale                      │  SSH Jump          │
        │                                │  ────────────────  │
        ▼                                │                  │
┌─────────────────┐◄─────────────────────│                  │
│   Mac Mini       │                      └─────────────────┘
│  klaus@100.93.33.84                    
│  /bin/zsh (nicht bash)
└─────────────────┘
```

## Regel: Niemals nur einen Node schützen

Wenn ein Problem (History-Explosion, Log-Überlauf, Docker-VM-Füllung) auf **einem** Node gefunden wird:

- [ ] **Lokaler Host** prüfen und fixen
- [ ] **Hostinger VPS** prüfen und fixen
- [ ] **Mac Mini** prüfen und fixen
- [ ] Optional: **AE8** prüfen (wenn online)

## Deploy-Muster: Alle 3 Nodes gleichzeitig

```bash
# ============================================================
# SCHUTZ-SCRIPT (lokal erstellen)
# ============================================================
cat > /tmp/protect-all.sh << 'DEPLOYEOF'
#!/bin/bash
set -euo pipefail

# === History Guard ===
HIST="${HOME}/.bash_history"
MAX_MB=50
if [ -f "$HIST" ]; then
    SIZE=$(du -m "$HIST" | awk '{print $1}')
    if [ "$SIZE" -gt "$MAX_MB" ]; then
        echo "[$(date)] WARNING: $HIST is ${SIZE}MB (limit ${MAX_MB}MB) — truncating" | tee -a /tmp/history-guard.log
        tail -n 500 "$HIST" > "${HIST}.tmp" && mv "${HIST}.tmp" "$HIST"
    fi
fi

# === Logrotate Config ===
mkdir -p ~/.hermes/logs
cat > ~/.hermes/logs/hermes-logrotate.conf << 'LOGEOF'
${HOME}/.hermes/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    size 50M
}
LOGEOF

# === Docker Log Limits ===
mkdir -p ~/.docker
echo '{"log-driver":"json-file","log-opts":{"max-size":"10m","max-file":"3","compress":"true"}}' > ~/.docker/daemon.json

echo "[$(date)] Protection deployed on $(hostname)"
DEPLOYEOF
chmod +x /tmp/protect-all.sh

# ============================================================
# 1. LOKALER HOST
# ============================================================
cp /tmp/protect-all.sh ~/.hermes/scripts/protect-all.sh
bash ~/.hermes/scripts/protect-all.sh

# Cron: stündlich prüfen
(crontab -l 2>/dev/null || true; echo "0 * * * * bash ${HOME}/.hermes/scripts/protect-all.sh") | sort -u | crontab -

# ============================================================
# 2. HOSTINGER VPS
# ============================================================
scp /tmp/protect-all.sh hostinger:/tmp/protect-all-vps.sh
ssh hostinger "bash /tmp/protect-all-vps.sh"

# VPS spezifisch: systemd Journal-Limit
ssh hostinger "mkdir -p /etc/systemd/journald.conf.d && cat > /etc/systemd/journald.conf.d/size-limit.conf << 'JEOF'
[Journal]
SystemMaxUse=500M
MaxRetentionSec=7day
JEOF
systemctl restart systemd-journald 2>/dev/null || true"

# ============================================================
# 3. MAC MINI (via Hostinger SCP-Kette + zsh)
# ============================================================
scp /tmp/protect-all.sh hostinger:/tmp/protect-macmini.sh
ssh hostinger "scp -i ~/.ssh/id_macmini -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null /tmp/protect-macmini.sh \
  klaus@100.93.33.84:/tmp/protect-macmini.sh"

ssh hostinger "ssh -i ~/.ssh/id_macmini -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null klaus@100.93.33.84 \
  '/bin/zsh /tmp/protect-macmini.sh'"
```

## Node-spezifische Shell-Unterschiede

| Node | Shell | Pitfall | Fix |
|---|---|---|---|
| Lokaler Host | bash | Standard | – |
| Hostinger VPS | bash | `sudo` braucht root/kein PTY | Script erstellen, User führt `sudo bash` |
| Mac Mini | **zsh** | `bash` Inline-Pipes schlagen fehl | Immer `/bin/zsh script.sh` aufrufen |

## Wichtige Schutzmaßnahmen (Checkliste)

| Maßnahme | Lokaler Host | Hostinger VPS | Mac Mini | Zweck |
|---|---|---|---|---|
| History Guard | ✅ | ✅ | ✅ | `.bash_history` >50MB → truncate |
| Hermes Logrotate | ✅ | – | – | `.hermes/logs/*.log` rotieren |
| System Logrotate | – | ✅ | – | `/var/log/clawbot`, `macmini_health` |
| Journal Limit | – | ✅ | – | systemd max 500MB / 7 Tage |
| Docker Log Limits | – | – | ✅ | Container: 10MB/3files/compress |
| Docker VM Limit | – | – | ✅ | VM max 64GB |

## Referenzen

- `references/macmini-bash-history-explosion.md` — Root-Cause Analyse der 285 GB History
- `references/docker-vm-disk.md` — Docker Desktop VM Sparse-File Verhalten
- `references/vps-bash-history-explosion.md` — Linux-Server History-Explosion (38 GB)
- `scripts/protect-all.sh` — Einheitliches Schutz-Script
- `scripts/deploy-cross-system.sh` — Deploy auf alle 3 Nodes

## Tags
- `cross-system` `protection` `mesh` `history-guard` `logrotate` `docker` `journal`
- `all-nodes` `mac-mini` `hostinger` `local-host` `ae8`
