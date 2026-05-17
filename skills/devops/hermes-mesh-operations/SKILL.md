---
name: hermes-mesh-operations
description: |
  Operate, protect, and deploy across a Hermes mesh of heterogenous nodes:
  local Linux workstations, cloud VPS (Hostinger), macOS nodes (Mac Mini via Tailscale),
  and remote thin clients. Covers SSH jump chains, cross-system protection scripts,
  Docker cloud-first deployment on macOS, shell-history explosion prevention, and
  node-specific cleanup regimes.
toolsets:
  - terminal
  - file
tags:
  - mesh
  - cross-system
  - ssh
  - docker
  - macos
  - protection
  - history-guard
  - cleanup
version: "1.0.0"
related_skills:
  - linux-workstation
  - github-repo-management
---

# Hermes Mesh Operations

## Trigger

Load this skill when the user asks about:
- Multi-node operations across local host, VPS, and macOS nodes
- SSH jump chains or Tailscale-based remote access
- Deploying protection/cleanup scripts to all mesh nodes at once
- Docker Desktop VM disk limits or cloud-first container strategy on macOS
- Shell history explosion on servers or macOS
- Log rotation, journal limits, or Docker log limits across multiple systems

---

## 1. Mesh Topology

```
┌─────────────────┐      SSH Jump       ┌─────────────────┐
│  Local Host      │ ──────────────────▶│  Hostinger VPS  │
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
│  /bin/zsh (not bash)
└─────────────────┘
```

**Golden rule:** If a space/log/History problem appears on one node, it almost certainly exists on the others. Always protect/deploy to **all active nodes** simultaneously.

---

## 2. SSH Patterns & Node-Specific Shells

| Node | Shell | Pitfall | Fix |
|---|---|---|---|
| Local Host | bash | Standard | – |
| Hostinger VPS | bash | `sudo` needs root / no PTY | Script file + `sudo bash script.sh` |
| Mac Mini | **zsh** | `bash` inline pipes fail over SSH | Always invoke `/bin/zsh script.sh` |

**Reliable remote-script execution over zsh jumps:**

```bash
# File-based (avoids heredoc/quoting hell)
cat /tmp/script.py | ssh hostinger \
  "ssh -i /root/.ssh/id_macmini klaus@100.93.33.84 'python3 -'"
```

---

## 3. Cross-System Protection (all nodes)

Deploy a unified protection script to every node. See `scripts/protect-all.sh` for the reference implementation.

### What it covers

| Measure | Local Host | VPS | Mac Mini | Purpose |
|---|---|---|---|---|
| History Guard | ✅ | ✅ | ✅ | Truncate `.bash_history` > 50 MB |
| Hermes Logrotate | ✅ | – | – | Rotate `~/.hermes/logs/*.log` |
| System Logrotate | – | ✅ | – | Rotate `/var/log/*` |
| Journal Limit | – | ✅ | – | systemd journal max 500 MB / 7 days |
| Docker Log Limits | – | – | ✅ | Container: 10 MB / 3 files / compress |
| Docker VM Limit | – | – | ✅ | Desktop VM max 64 GB |

### Deploy chain (local → VPS → Mac Mini)

```bash
# 1. Write script locally
cat > /tmp/protect-all.sh << 'DEPLOYEOF'
#!/bin/bash
set -euo pipefail

# --- History Guard ---
HIST="${HOME}/.bash_history"
MAX_MB=50
if [ -f "$HIST" ]; then
    SIZE=$(du -m "$HIST" | awk '{print $1}')
    if [ "$SIZE" -gt "$MAX_MB" ]; then
        echo "[$(date)] WARNING: $HIST is ${SIZE}MB — truncating" | tee -a /tmp/history-guard.log
        tail -n 500 "$HIST" > "${HIST}.tmp" && mv "${HIST}.tmp" "$HIST"
    fi
fi

# --- Logrotate Config ---
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

# --- Docker Log Limits ---
mkdir -p ~/.docker
echo '{"log-driver":"json-file","log-opts":{"max-size":"10m","max-file":"3","compress":"true"}}' > ~/.docker/daemon.json

echo "[$(date)] Protection deployed on $(hostname)"
DEPLOYEOF
chmod +x /tmp/protect-all.sh

# 2. Local
cp /tmp/protect-all.sh ~/.hermes/scripts/protect-all.sh
bash ~/.hermes/scripts/protect-all.sh

# 3. VPS
scp /tmp/protect-all.sh hostinger:/tmp/protect-all-vps.sh
ssh hostinger "bash /tmp/protect-all-vps.sh"
# VPS: systemd journal limit
ssh hostinger "mkdir -p /etc/systemd/journald.conf.d && \
  cat > /etc/systemd/journald.conf.d/size-limit.conf << 'JEOF'
[Journal]
SystemMaxUse=500M
MaxRetentionSec=7day
JEOF
systemctl restart systemd-journald 2>/dev/null || true"

# 4. Mac Mini (via VPS SCP chain + zsh)
scp /tmp/protect-all.sh hostinger:/tmp/protect-macmini.sh
ssh hostinger "scp -i ~/.ssh/id_macmini -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null /tmp/protect-macmini.sh \
  klaus@100.93.33.84:/tmp/protect-macmini.sh"
ssh hostinger "ssh -i ~/.ssh/id_macmini -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null klaus@100.93.33.84 \
  '/bin/zsh /tmp/protect-macmini.sh'"
```

---

## 4. Docker Cloud-First Deployment (macOS)

On macOS with Docker Desktop, adopt a **zero-persistence** container strategy to prevent the VM disk from growing unbounded.

### 4.1 Cloud-First Compose Rules

- **No named volumes** in base compose — they persist inside the VM disk.
- **Explicit empty volumes** in override so base volumes are not inherited:

```yaml
services:
  n8n:
    volumes: []   # explicit empty
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        compress: "true"
```

- Read-only host mounts (skills, configs) are fine — they do not grow the VM disk.

### 4.2 VM Disk Limits

Limit Docker Desktop VM to 64 GB:

```bash
mkdir -p "$HOME/Library/Group Containers/group.com.docker"
printf '{"diskSizeMiB":65536}\n' > \
  "$HOME/Library/Group Containers/group.com.docker/settings.json"
```

**Emergency reset** if VM disk has already blown up:

```bash
pkill -9 -x "Docker Desktop"
pkill -9 -f "com.docker.backend"
sleep 10
rm -rf ~/Library/Containers/com.docker.docker/Data/vms/0/
rm -rf ~/Library/Containers/com.docker.docker/Data/log/*
open -a "Docker Desktop"
```

> All container images will need to be re-pulled after a VM reset.

### 4.3 Log Rotation in Every Service

Every service in the override should declare:

```yaml
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        compress: "true"
```

For very chatty services (scheduler, cadvisor): use `max-size: "5m"`, `max-file: "2"`.

### 4.4 macOS Cleanup Script

See `scripts/macmini-cleanup.sh` — an interactive script that cleans:
- Time Machine snapshots
- Docker caches
- Browser caches (Safari, Chrome, Firefox)
- System caches (> 7 days)
- System logs (> 30 days)
- Downloads and Trash
- Xcode DerivedData

Run with `--force` for non-interactive mode.

---

## 5. Shell History Explosion Prevention (all nodes)

### Linux VPS

 automated scripts running as root write every command to `.bash_history`. A Hostinger VPS once reached **38 GB** of history on a 96 GB SSD.

Immediate fix (script then `sudo bash`):

```bash
cat > ~/bin/clear-bash-history.sh << 'EOF'
#!/bin/bash
for userdir in /home/* /root; do
    histfile="$userdir/.bash_history"
    [ -f "$histfile" ] || continue
    size=$(du -sh "$histfile" 2>/dev/null | cut -f1)
    echo "Before: $histfile = $size"
    > "$histfile"
    history -c 2>/dev/null || true
    echo "After: cleared"
done
EOF
# Then: sudo bash ~/bin/clear-bash-history.sh
```

Permanent prevention — set limits in `/etc/profile` and `/root/.bashrc`:

```bash
HISTSIZE=1000
HISTFILESIZE=2000
```

### macOS (Mac Mini)

A buggy cronjob (`cat ~/.bash_history ~/.zsh_history >> ~/.bash_history`) caused a **285 GB** `.bash_history`. Fix:

```bash
> ~/.bash_history
rm -f ~/.bash_history.tmp
for rc in ~/.bashrc ~/.zshrc; do
    [ -f "$rc" ] || continue
    grep -q "HISTSIZE=" "$rc" && continue
    echo -e "\nexport HISTSIZE=10000\nexport SAVEHIST=10000\nexport HISTFILESIZE=20000" >> "$rc"
done
```

**Never append a history file to itself.** Always use `set -euo pipefail` in automation scripts.

---

## 6. Remote Health Monitoring

Cronjob-based health checks from a jump host (e.g., VPS polling Mac Mini):

```bash
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -i /root/.ssh/id_macmini klaus@100.93.33.84 \
  '~/hermes-devops-ai-environment/scripts/ops/macmini-health-check.sh'
```

The check script should verify: Docker engine, disk space, running containers, VM disk size, and trigger `docker system prune -f` if needed.

---

## Scripts

| File | Purpose |
|---|---|
| `scripts/protect-all.sh` | Unified protection script (history guard + logrotate + Docker limits) |
| `scripts/macmini-cleanup.sh` | Interactive macOS deep-cleanup |
| `scripts/macmini-health-check.sh` | Remote Docker/health check for cronjobs |
| `scripts/deploy-cross-system.sh` | Deploy protect-all.sh to all 3 nodes in one go |

## Templates

| File | Purpose |
|---|---|
| `templates/docker-compose.override.yml` | Cloud-First override starter (no named volumes, log limits) |

## References

| File | Purpose |
|---|---|
| `references/docker-vm-disk.md` | Docker Desktop VM sparse-file behaviour |
| `references/compose-override-patterns.md` | Cloud-First compose patterns |
| `references/macmini-bash-history-explosion.md` | Root-cause of 285 GB macOS history |
| `references/vps-bash-history-explosion.md` | Root-cause of 38 GB Linux history |
| `references/disk-analysis-tools.md` | `ncdu`, timeout-safe disk analysis |
