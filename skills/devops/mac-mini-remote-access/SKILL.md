---
name: mac-mini-remote-access
title: Remote-Zugriff auf Mac Mini via Hostinger Jumphost
version: 1.0.0
author: KlausDIG
description: SSH-Zugriff auf denMac Mini (Tailscale 100.93.33.84) über denHostinger VPS (187.77.65.191) als Proxy/Jumphost.
tags: [ssh, mac-mini, hostinger, jumphost, tailscale, remote-access]
---

# Mac Mini Remote Access via Hostinger VPS

## Topologie

```
[Agent-Linux / Du] --(SSH)--> [Hostinger VPS 187.77.65.191] --(SSH)--> [Mac Mini 100.93.33.84]
```

## Schnellbefehle

### Direkter Login auf Mac Mini

```bash
ssh hostinger "ssh -i ~/.ssh/id_macmini -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null klaus@100.93.33.84"
```

### Einzelner Befehl auf Mac Mini (nicht-interaktiv)

```bash
ssh hostinger "ssh -i ~/.ssh/id_macmini -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null klaus@100.93.33.84 'whoami; uname -a'"
```

### Datei kopieren via Hostinger Kette

```bash
# Lokal → Hostinger → Mac Mini
scp /local/file.txt hostinger:/tmp/file.txt
ssh hostinger "scp -i ~/.ssh/id_macmini -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null /tmp/file.txt klaus@100.93.33.84:~/file.txt"
```

## SSH-Konfiguration (Hostinger VPS)

| Eigenschaft | Wert |
|---|---|
| Host | `hostinger` (SSH-Alias in `~/.ssh/config`) |
| IP | `187.77.65.191` |
| User | `root` |
| Key | `~/.ssh/id_ed25519` |

## Mac Mini SSH-Eigenschaften

| Eigenschaft | Wert |
|---|---|
| Tailscale IP | `100.93.33.84` |
| User | `klaus` |
| Key auf Hostinger | `~/.ssh/id_macmini` (PEM, `chmod 600`) |
| Host-Key Check | `no` (Tailscale/WireGuard Trust) |
| Shell | `/bin/zsh` |

## Wichtige Pfade auf dem Mac Mini

```
~/.zshrc
~/.bashrc
~/Library/Containers/com.docker.docker/Data/vms/   # Docker VM
~/Library/Developer/Xcode/DerivedData              # Xcode Cache
~/Library/Caches                                   # App Caches
~/Pictures/Photos Library.photoslibrary           # Photos
```

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| `Host key verification failed` | `-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null` |
| `Permission denied` | Key `id_macmini` auf Hostinger prüfen, User ist `klaus` |
| `Too many authentication failures` | Kein SSH-Agent, direkt `-i ~/.ssh/id_macmini` |
| Timeout | `-o ConnectTimeout=10` erhöhen oder Tailscale Status prüfen |
| `zsh: unmatched "` bei komplexen remote Befehlen | **NIE** komplexe zsh-Quoting-Ketten per inline `ssh` — stattdessen Datei via SCP-Kette (Local → Hostinger → Mac Mini) und dann als Datei auf Remote ausführen |
| `Permission denied (publickey,keyboard-interactive)` | `-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null` zusammen mit richtigem Key |

## SCP Datei-Transfer Kette (zuverlässig bei zsh/macOS)

**FALSCH:** Inline-Befehle mit komplexen Quotes über mehrere SSH-Hops — zsh zerstört das Quoting.

**RICHTIG:** Datei als Hülle transportieren:

```bash
# 1. Lokal → Hostinger
scp /local/file.sh hostinger:/tmp/file.sh

# 2. Hostinger → Mac Mini
ssh hostinger \
  "scp -i ~/.ssh/id_macmini -o StrictHostKeyChecking=no \
   -o UserKnownHostsFile=/dev/null \
   /tmp/file.sh klaus@100.93.33.84:/tmp/file.sh"

# 3. Auf Mac Mini ausführen
ssh hostinger \
  "ssh -i ~/.ssh/id_macmini -o StrictHostKeyChecking=no \
   -o UserKnownHostsFile=/dev/null klaus@100.93.33.84 \
   'chmod +x /tmp/file.sh && /bin/zsh /tmp/file.sh'"
```

> **Pitfall:** Mac Mini nutzt **zsh** als Default-Shell. Inline-`bash`-Befehle können unterschiedlich expandieren (Brace-Expansion, Globbing). Immer explizit `/bin/zsh script.sh` oder `bash script.sh` aufrufen.

## Sicherheit

- **Host-Key-Check aus**: Tailscale ist vertrauenswürdiges internes Netz; Host-Keys variieren bei Docker-Neustarts
- **Key `id_macmini`**: Nur auf Hostinger, `chmod 600`, niemals exponieren

## Tags
- `ssh` `mac-mini` `hostinger` `tailscale` `jumphost` `remote-access` `ios` `darwin`
