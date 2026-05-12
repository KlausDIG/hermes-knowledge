---
name: git-auto-sync
version: 1.0.0
description: Offline-resilientes Git Auto-Push für alle lokalen Repos mit Retry, Timeout und Pending-Queue.
tags: [git, sync, cronjob, offline, automation, bash]
author: KlausDIG
---

# git-auto-sync

Automatisches Git-Commit und Push für alle Repos unter konfigurierbaren Suchpfaden — robust gegen Abbrüche, Netzwerkausfälle und Offline-Zustände.

## Trigger

Nutze diesen Skill, wenn du:
- Alle lokalen Git-Repos automatisch sichern willst
- Commits im Hintergrund erstellen möchtest (auch ohne Internet)
- Pushes automatisch nachholen lassen willst, sobald du wieder online bist
- Einen Cronjob für Git-Sync einrichten möchtest

## Setup

### 1. Skill-Script kopieren

```bash
cp ~/.hermes/skills/git-auto-sync/scripts/auto-push-projects.sh ~/.hermes/scripts/auto-push-projects.sh
chmod +x ~/.hermes/scripts/auto-push-projects.sh
```

### 2. Hermes Cronjob erstellen

```bash
hermes cronjob create \
  --name project-auto-push \
  --schedule "*/30 * * * *" \
  --script ~/.hermes/scripts/auto-push-projects.sh \
  --no-agent
```

Oder via `cronjob` tool:
- `action`: `create`
- `name`: `project-auto-push`
- `no_agent`: `true`
- `schedule`: `*/30 * * * *`
- `script`: `auto-push-projects.sh`

### 3. Suchpfade anpassen (optional)

Im Script, Array `SEARCH_PATHS`, z.B.:

```bash
SEARCH_PATHS=(
    "${HOME}/Developer/repos"
    "${HOME}/projects"
    "${HOME}/dev"
)
```

## Features

| Feature | Beschreibung |
|---|---|
| 🔒 **Lock-File** | Verhindert parallele Ausführung (3 Min Stale-Timeout) |
| 📴 **Offline-Modus** | Commits lokal, Push in Queue verschoben |
| 📦 **Pending-Queue** | `~/.hermes/cache/pending-pushes.txt` — automatisch nachgeholt |
| ⏱️ **Push-Timeout** | `timeout 30` bricht hängende Pushes ab |
| 🔁 **Retry (3×)** | Netzwerkfehler mit exponentiellem Backoff (5s → 10s → 20s) |
| 🔇 **SSH non-interactive** | Keine Passwort-Prompts, 10s Connect-Timeout |
| 🚫 **Rejected-Erkennung** | Stale info / non-fast-forward → manuell markiert, kein Endlos-Retry |

## Konfiguration

### Log-Datei
`~/.hermes/logs/auto-push-projects.log`

### Pending-File-Format

```
/home/user/project|main
/home/user/other|dev|rejected
```
- `rejected`: Übersprungen, erfordert manuelles `git pull` + Merge

### Exkludierte Pfade
Im Script, Array `EXCLUDE_PATTERNS`:

```bash
EXCLUDE_PATTERNS=(
    ".linuxbrew"
    ".pyenv"
    ".rbenv"
    ".jenv"
    ".nvm"
    ".hermes"
    "node_modules"
)
```

## Ablauf

```
Start
  → Lock-File prüfen (oder abbrechen)
  → Alte pending Pushes nachholen
  → Für jedes Repo:
      → Änderungen committen (immer lokal)
      → Online-Check (curl GitHub/Google, 4s Timeout)
      → Falls online:
          → git push (max 30s, 3 Retries)
          → Bei Fehler → pending Queue
      → Falls offline:
          → → pending Queue
  → Neue pending Pushes nachholen
  → Fertig
```

## Troubleshooting

| Symptom | Ursache | Lösung |
|---|---|---|
| `🔒 Anderer Prozess läuft` | Vorheriger Lauf hängt | Lock-File prüfen: `cat ~/.hermes/cache/auto-push.lock` |
| `❌ PUSH nach 3 Versuchen` | Dauerhafter Netzwerkfehler | Manuelle Prüfung: `git push` im Repo |
| `🚫 Push rejected` | Upstream hat neue Commits | `git pull`, Konflikte lösen, neu pushen |
| `📴 OFFLINE` | Kein Internet | Normal — nächster Lauf holt nach |
| Script läuft nicht | Kein execute-Bit | `chmod +x ~/.hermes/scripts/auto-push-projects.sh` |

## Variablen (im Script)

| Variable | Standard | Beschreibung |
|---|---|---|
| `LOCK_TIMEOUT` | `180` | Sekunden bis stale Lock überschrieben wird |
| `max_retries` | `3` | Push-Versuche pro Repo |
| `delay` | `5` | Initiale Retry-Wartezeit (wird verdoppelt) |
| Push-Timeout | `30s` | `timeout 30` um hängende Pushes abzubrechen |
| Online-Check | `4s` | `curl --max-time 4` |
| SSH-Connect | `10s` | `ssh -o ConnectTimeout=10` |

## Abhängigkeiten

- `bash`
- `git`
- `curl`
- `timeout` (GNU coreutils)
- `awk`, `grep`, `sort`
