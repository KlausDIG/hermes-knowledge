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

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| `Permission denied` | Key nicht im Panel hinterlegt oder falsche IP |
| `Connection refused` | VPS noch im Setup / Firewall blockt |
| `Host key verification failed` | `ssh-keygen -R 187.77.65.191` ausführen |

## Tags

- `ssh` `vps` `hostinger` `server` `root`
