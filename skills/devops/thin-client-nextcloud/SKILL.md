---
name: thin-client-nextcloud
description: |
  Thin-Client Workflow für Nextcloud über rclone.
  Lokale Dateien werden on-demand von Nextcloud geholt (get) oder
  dorthin geschoben (put). Kein permanenter FUSE-Mount nötig.
  Automatisches Backup des hermes-klausi-hp Monorepo täglich.
  Schutzregeln: Git-Repo und Skills werden nie durch thin-client gelöscht.
toolsets:
  - terminal
  - file
tags:
  - nextcloud
  - thin-client
  - cloud-first
  - rclone
  - backup
  - sync
  - storage
version: "1.0.0"
related_skills:
  - nextcloud-rclone-cloud-first
  - automated-git-sync
  - monorepo-project-workflow
---

# ☁️ Thin-Client Nextcloud

## Zweck

Speicherplatz-Schonung durch Cloud-First-Philosophie:
- **Primärspeicher:** Nextcloud (neytcloud)
- **Sekundär:** GitHub (hermes-klausi-hp)
- **Lokal:** Nur aktive Arbeitskopien + Cache

## Voraussetzungen

- `rclone` (Snap-Version OK, Config via `~/snap/rclone/current/.config/rclone/`)
- Hermes Skill `nextcloud-rclone-cloud-first` für Setup
- lokaler Pfad `~/bin/thin-client.sh`

## Commands

```bash
# Datei von Nextcloud laden
~/bin/thin-client.sh get "Projects/hermes-klausi-hp/README.md"

# Datei zu Nextcloud hochladen
~/bin/thin-client.sh put "~/Downloads/bericht.pdf" "Documents/"

# Cloud-Inhalte auflisten
~/bin/thin-client.sh list "Projects/"

# Lokale Datei löschen (Schutz aktiv)
~/bin/thin-client.sh drop "~/alter-scratchpad.txt"

# Tägliches Backup ausführen
~/bin/thin-client.sh sync

# Status anzeigen
~/bin/thin-client.sh status
```

## Sicherheitsregeln

| Regel | Verhalten |
|-------|-----------|
| `drop` auf `hermes-klausi-hp` | Verweigert — "NICHT löschen — aktives Git-Repo!" |
| `drop` auf `.hermes/skills/` | Verweigert — Skills sind Master |

## Thin-Cache

```
~/.thin-cache/
├── [run-time Dateien von get-Befehlen]
└── (automatisch beim Reboot geleert)
```

## Cronjob

| Job | Schedule | Funktion |
|-----|----------|----------|
| `neytcloud-backup` | 0 2 * * * | Sync `~/hermes-klausi-...` → `neytcloud:Projects/` |

Script: `~/.hermes/scripts/neytcloud-backup.sh`

## Architektur

```
Lokal (nur aktive Projekte)
    ↓
hermes-klausi-hp (GitHub) ←── Auto-Push alle 30 Min
    ↓
Nextcloud (neytcloud) ←── Nightly Backup
    ↑
Thin-Cache (on-demand)
```

## Pitfalls

### rclone Snap-Isolation
Config muss in **beiden** Orten liegen:
```bash
~/.config/rclone/rclone.conf
~/snap/rclone/current/.config/rclone/rclone.conf
```

### FUSE-Mount nicht verfügbar
`rclone mount` via Snap funktioniert nicht wegen Sandboxing.
**Fix:** Thin-Client mit `rclone copy` statt Mount.

### SSH-Key für Git
Wenn `git push` fehlschägt:
```bash
git remote set-url origin https://github.com/KlausDIG/<repo>.git
```
