---
name: fleet-overview
version: 1.0.0
description: Fleet-Übersicht über alle Hermes Nodes — Status, Ressourcen, Erreichbarkeit.
category: devops
author: Hermes Agent
---

# Fleet-Übersicht

Skill zur Erstellung und Aktualisierung einer Fleet-Übersicht über alle Hermes Nodes.

## Nodes

### 1. Hostinger VPS (srv1482003)
- **Öffentliche IP**: 187.77.65.191
- **Tailscale IP**: 100.125.211.54
- **OS**: Ubuntu 6.8.0-111-generic x86_64
- **SSH**: Erreichbar
- **RAM**: 7.8 Gi total / ~1 Gi used (~12 %)
- **Disk**: 96 G total / 61 G used (64 %)
- **Hermes**: hermes-consumer + ollama-hermes-proxy aktiv
- **Docker**: Nicht installiert
- **Tailscale**: active (direct)

### 2. Mac Mini (Mini-von-Klaus)
- **Tailscale IP**: 100.93.33.84
- **OS**: macOS 25.3.0 Darwin (ARM64)
- **SSH**: Erreichbar via Hostinger Jumphost
- **RAM**: ~31 Gi total / ~19 Gi used
- **Disk**: 460 G APFS / 12 G used (4 %) / 298 G avail
- **Hermes**: ✅ **Hermes Stack aktiv** — 12 Docker Container laufen
  - control-gateway, codex-worker, telegram-bot
  - prometheus, grafana, alertmanager, alert-receiver
  - cadvisor, node-exporter, open-webui, n8n, scheduler
  - Weitere: Discord-Bots (crew_discord_bot.py, code_discord_bot.py, controller_relay.py) + LM Studio
- **Docker**: Docker Desktop, Compose Stack aktiv
- **Tailscale**: active (direct)

## Audit-Befehle

### Hostinger VPS
```bash
ssh root@187.77.65.191 "free -h; df -h; systemctl status hermes-consumer ollama-hermes-proxy; tailscale status"
```

### Mac Mini (via Jumphost)
```bash
ssh -o ConnectTimeout=10 hostinger "ssh -i ~/.ssh/id_macmini -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR klaus@100.93.33.84 'top -l 1 | head -15; df -h /; docker ps 2>/dev/null || true'"
```

### Tailscale-Status
```bash
ssh root@187.77.65.191 "tailscale status"
```

## Erstellt
- 2026-05-17
