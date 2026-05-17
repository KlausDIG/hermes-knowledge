---
name: mac-mini-bootstrap
description: |
  Bootstrap für Mac Mini (mac-mini-von-klaus) im Hermes Mesh.
  Deckt: Tailscale-Status, SSH-Zugriff, Projekt-Stack (Ollama, LM Studio, AI Bots),
  PM2, und Backup-Infrastruktur.
version: "1.0.0"
category: devops
requires:
  - tailscale-hermes-mesh
  - ssh-hostinger-vps
author: KlausDIG
---

# 🖥️ Mac Mini Bootstrap

**Node:** mac-mini-von-klaus  
**Tailscale IP:** `100.93.33.84`  
**OS:** macOS (Apple Silicon)  
**Erreichbarkeit:** Hostinger Jumphost → `ssh -i /root/.ssh/id_macmini klaus@100.93.33.84`

---

## 1. Architektur

```
┌─────────────────────────────────────────┐
│  Mac Mini (mac-mini-von-klaus)           │
│  100.93.33.84                            │
├─────────────────────────────────────────┤
│  🤖 AI Stack                             │
│  ├── Ollama Serve (PID 1705)             │
│  │   ├── qwen2.5-coder:14b (8.9 GB)      │
│  │   └── hermes3:8b (4.6 GB)             │
│  └── LM Studio (Apple Metal/MLX)         │
├─────────────────────────────────────────┤
│  🐍 Python Apps                          │
│  ├── AI Operator Dashboard (PID 1381)    │
│  └── Multi-Agent System                  │
│      ├── controller_relay.py             │
│      ├── code_discord_bot.py             │
│      └── crew_discord_bot.py             │
├─────────────────────────────────────────┤
│  🔄 PM2 v6.0.14 God Daemon               │
├─────────────────────────────────────────┤
│  📦 Backup-Scripts                       │
│  ├── setup-hermes-restic-backup.sh       │
│  ├── hermes_backup_sync.sh               │
│  └── backup_hermes_to_nextcloud.sh       │
└─────────────────────────────────────────┘
```

---

## 2. SSH-Zugriff (von Hostinger Jumphost)

### 2.1 Voraussetzung auf Hostinger

Key muss existieren:
```bash
ls -la /root/.ssh/id_macmini
```

Falls nicht vorhanden — neu generieren und auf Mac Mini deployen:
```bash
ssh-keygen -t ed25519 -C "hostinger-macmini" -f /root/.ssh/id_macmini -N ""
# Dann auf Mac Mini:
cat /root/.ssh/id_macmini.pub | ssh klaus@100.93.33.84 'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys'
```

### 2.2 Verbindung herstellen

```bash
# Von Hostinger:
ssh -i /root/.ssh/id_macmini klaus@100.93.33.84

# Oder direkt:
ssh -o StrictHostKeyChecking=no -i /root/.ssh/id_macmini klaus@100.93.33.84
```

---

## 3. Tailscale auf Mac Mini

### 3.1 Status prüfen
```bash
tailscale status
```
→ Sollte `mac-mini-von-klaus` als **online** zeigen.

### 3.2 Falls offline
```bash
# Tailscale App neustarten (macOS GUI) oder:
sudo tailscale up --ssh --accept-routes
```

> **Hinweis:** Tailscale auf macOS läuft als **System Extension** (nicht als systemd-Daemon).

---

## 4. Projekt-Details

### 4.1 Ollama
```bash
# Status
curl http://localhost:11434/api/tags

# Modelle
# - qwen2.5-coder:14b
# - hermes3:8b
```

### 4.2 LM Studio
```bash
# Läuft als macOS App (PID 1425+)
# Backend: MLX (Apple Metal)
# Worker-Prozesse: mehrere Node.js Prozesse
```

### 4.3 Python Apps
```bash
# AI Operator Dashboard
cd ~/Projects/ai-operator-dashboard
ps -p 1381 -o command

# Multi-Agent Discord Bots
cd ~/Projects/multi-agent-migrated
# - controller_relay.py
# - code_discord_bot.py
# - crew_discord_bot.py
```

### 4.4 PM2
```bash
pm2 list
pm2 status
pm2 logs
```

---

## 5. Backup-Infrastruktur

### 5.1 Restic Setup (noch nicht vollständig)

**Status:** Script existiert, aber `restic` ist **nicht installiert** (`restic not found`).

**Installieren:**
```bash
brew install restic
```

**Dann ausführen:**
```bash
cd ~/hermes-devops-ai-environment
bash setup-hermes-restic-backup.sh
```

### 5.2 Hermes Backup Sync

**Script:** `~/hermes_backup_sync.sh`

```bash
#!/bin/bash
# Syncs critical data between primary and backup Hermes

PRIMARY_HOST="100.64.108.109"  # ae8 (WSL) — ACHTUNG: IP veraltet!
BACKUP_HOST="100.93.33.84"     # mac-mini-von-klaus
```

> **⚠️ Warnung:** Die IP `100.64.108.109` für AE8 ist **veraltet**.
> Aktuelle AE8 IP: `100.95.25.46`

**Fix:**
```bash
sed -i '' 's/100.64.108.109/100.95.25.46/g' ~/hermes_backup_sync.sh
```

### 5.3 Nextcloud Backup

**Script:** `~/backup_hermes_to_nextcloud.sh`

**Status:** Konfiguration unvollständig (Platzhalter: `BITTE_AENDERN`).

---

## 6. Wartung

### 6.1 Speicher prüfen
```bash
df -h
```
→ Aktuell: 153 GB von 460 GB genutzt (35%)

### 6.2 Docker (falls installiert)
```bash
docker ps -a
docker system df
```

### 6.3 Homebrew Updates
```bash
brew update
brew outdated
brew upgrade
```

---

## 7. Fehlerbehebung

| Problem | Lösung |
|---------|--------|
| `ssh: connect to host ... port 22: Connection refused` | System-Einstellungen → Freigaben → "Entfernte Anmeldung" aktivieren |
| `Permission denied (publickey)` | SSH-Key in `~/.ssh/authorized_keys` prüfen |
| `tailscale: command not found` | Tailscale App neu installieren |
| `restic not found` | `brew install restic` |
| `pm2: command not found` | `npm install -g pm2` |

---

## 8. Mesh-Integration

Der Mac Mini ist über **Hostinger Jumphost** erreichbar:

```
[Lokaler Host] → [Hostinger 100.125.211.54] → [Mac Mini 100.93.33.84]
```

**Von Hostinger:**
```bash
ssh -i /root/.ssh/id_macmini klaus@100.93.33.84
```

**Vom lokalen Host (noch nicht direkt):**
→ Tailscale Routing-Problem (lokaler Host sieht Mac Mini als `Destination Net Unreachable`).

**Fix für lokalen Host:**
```bash
sudo tailscale up --accept-routes --force-reauth
```