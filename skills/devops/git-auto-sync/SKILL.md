---
name: git-auto-sync
version: "3.2.1"
description: Auto-Push + Projekt-Status Tracker + Trend-Tracking + Recovery bei rejected Push. Committet, pusht, trackt offene/vollendete Punkte, Trend-Entwicklung, und repariert Divergenzen automatisch.
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
- **Offene und vollendete Punkte aller Projekte tracken willst**
- Automatische Status-Reports über Projektfortschritt haben willst

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

### Notfall-Workarounds

**Pending-Queue leeren (sofort):**
```bash
> ~/.hermes/cache/pending-pushes.txt
```

**Manueller Merge:**
```bash
cd ~/hermes-klausi-hp/hermes-klausi-hp  # oder entsprechendes Repo
git fetch origin
git merge origin/main --no-edit
git push
```

## Recovery bei rejected Push (v3.2.1+)

Siehe `references/rejected-recovery-incident-2026-05-14.md` für vollständige Post-Mortem, Root-Cause, Verifikations-Logs und Code-Details.

### Problem bis v3.1: Stale rejected-Entries
Nach erfolgreichem Push wurden alte `rejected`-Einträge in `~/.hermes/cache/pending-pushes.txt` **nicht** entfernt. Das führte zu dauerhaftem „übersprungen (rejected)“.

**Fix ab v3.1.1 — Sofort-Cleanup** (nach jedem erfolgreichem Push):
```bash
if [ -f "$PENDING_FILE" ]; then
    grep -vFx "$repo|$br" "$PENDING_FILE" > "${PENDING_FILE}.tmp" 2>/dev/null || true
    grep -vFx "$repo|$br|rejected" "${PENDING_FILE}.tmp" > "${PENDING_FILE}.tmp2" 2>/dev/null || true
    mv "${PENDING_FILE}.tmp2" "$PENDING_FILE" 2>/dev/null || true
fi
```

### Problem bis v3.1.1: Divergenz nach Skills-Sync
Wenn der Skills-Sync (`skills_sync.py`) während eines anderen Laufes pusht, entsteht Divergenz (local → remote). Der Auto-Push wird rejected und blockiert **für immer**.

**Fix ab v3.2.1 — Auto-Merge Recovery**
Bei `rejected`-Status in der Pending-Queue:
1. `git fetch origin <branch>`
2. `git merge origin/<branch> -m "Auto-merge: Recovery von rejected push"`
3. Neuen Push versuchen
4. Bei Erfolg → Eintrag aus Pending-Queue entfernen
5. Bei Merge-Konflikt → Log-Meldung „manueller Eingriff nötig“, bleibt rejected

### Schnelle Rezepte
**Pending-Queue leeren (Notfall):**
```bash
> ~/.hermes/cache/pending-pushes.txt
```

**Status checken:**
```bash
hermes cronjob list   # Zeigt letzte Lauf-Ergebnisse
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
| 📊 **Projekt-Status-Tracker** | Scant TODO.md, ROADMAP.md, GitHub Issues, Commit-TODOs |
| 🔍 **Skill-TODO-Extraktor** | Echte Entwickler-TODOs aus Skills (keine Template-Checklisten) |
| 💬 **Chat-TODO-Integration** | Manuelle Punkte aus `~/.hermes/cache/chat-todos.txt` |
| 🔄 **Status-Änderungsdetektion** | Cache-basiert, meldet nur bei echten Änderungen |
| 📝 **Status-Log** | Zentraler Report unter `~/.hermes/logs/project-status.log` |

## Konfiguration

### Status-Dateien (automatisch gescannt)

Folgende Dateien im Repo-Wurzelverzeichnis werden geprüft:

- `TODO.md`
- `ROADMAP.md`
- `STATUS.md`
- `CHECKLIST.md`
- `PLAN.md`
- `TASKS.md`

Erkannt werden:
- **Offen:** `[ ]`, `- [ ]`, `□`, `☐`, `TODO:`, `OFFEN:`, `OPEN:`
- **Vollendet:** `[x]`, `[X]`, `☑`, `☒`, `✅`, `DONE:`, `ERLEDIGT:`, `COMPLETE:`

### Log-Dateien
- **Push-Log:** `~/.hermes/logs/auto-push-projects.log`
- **Status-Report:** `~/.hermes/logs/project-status.log`
- **Status-Cache:** `~/.hermes/cache/project-status-cache/status-entries.txt`

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
  → 🔄 TODO-Extractor ausführen (optional)
      → Skills nach echten TODOs scannen (keine Templates)
      → Chat-TODOs aus ~/.hermes/cache/chat-todos.txt lesen
      → In Projekt-TODO.md eintragen (clean-rewrite)
  → Alte pending Pushes nachholen
  → Für jedes Repo:
      → 📊 Status scan (TODO.md, ROADMAP.md, GitHub Issues, Commit-TODOs)
      → Cache prüfen (bei Änderung → melden)
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

## FAQ

### Wie verhindere ich, dass Template-Checklisten als offene Punkte gezählt werden?

Der TODO-Extractor filtert automatisch:
- Markdown-Tabellen (`^\s*\|`)
- YAML-Frontmatter (`tags:`, `---`)
- HTML-Kommentare (`<!--`)
- Reine Code-Zeilen (nur Symbole)
- Checklisten ohne konkretes Action-Verb

Nur Zeilen mit **TODO:/FIXME:/BUG:** **+ Action-Verb** (implement/fix/add/...) werden als echt gezählt.

### Wie trage ich manuell ein TODO ein?

Schreibe in `~/.hermes/cache/chat-todos.txt`:

```bash
echo "Mein neues TODO: Web-Dashboard bauen" >> ~/.hermes/cache/chat-todos.txt
```

Beim nächsten Lauf wird es automatisch in das passende Projekt-TODO.md eingetragen und die Datei geleert.

### Wo finde ich die extrahierten TODOs?

- **Projekt-TODOs:** `~/Developer/repos/<projekt>/TODO.md`
- **Chat-TODOs-Quelle:** `~/.hermes/cache/chat-todos.txt`
- **Extraktor-Log:** `~/.hermes/logs/todo-extractor.log`

## Abhängigkeiten

- `bash`
- `git`
- `curl`
- `timeout` (GNU coreutils)
- `awk`, `grep`, `sort`
- `python3` (für TODO-Extractor)

## Referenzen

- `references/todo-filtering.md` — Filter-Heuristiken des TODO-Extractors (False-Positive vs. echte TODOs)
- `references/rejected-recovery-incident-2026-05-14.md` — Post-Mortem: Divergenz durch Skills-Sync-Parallelität, Recovery-Strategie
