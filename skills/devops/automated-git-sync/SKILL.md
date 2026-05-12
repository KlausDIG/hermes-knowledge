---
name: automated-git-sync
description: |
  Automatisiertes Git-Repo-Sync über Cronjob: Discovery, Auto-Commit, Auto-Push,
  Offline-Resilienz, Retry mit exponentiellem Backoff, Timeout-Schutz, Locking,
  und Pending-Queue für unterbrochene Übertragungen.
toolsets:
  - terminal
  - file
tags:
  - git
  - automation
  - cronjob
  - sync
  - offline
  - retry
  - backup
version: "1.0.0"
related_skills:
  - github-repo-management
  - linux-dev-workstation
  - hermes-skills-sync
---

# 🔄 Automated Git Sync

Automatisiertes Management multipler lokaler Git-Repositories über einen wiederkehrenden Cronjob. Das System commitet Änderungen lokal (offline-fähig), versucht Push nur bei bestehender Internetverbindung, und wiederholt ausstehende Pushes bei Netzwerk-Wiederkehr.

## Trigger

Lade diesen Skill wenn der User fragt nach:
- Automatisiertes Git-Push für mehrere Projekte
- Auto-Commit / Auto-Push per Cronjob
- Offline-resilientes Git-Sync
- Git-Backup-Strategie ohne manuelle Eingriffe
- Retry bei Netzwerkabbrüchen während `git push`

## Architektur

```
Cronjob (alle 30 Min) → Script lock → Pending-Retries (vorher)
                                         ↓
                        For each repo: Commit (immer lokal)
                                         ↓
                              Online? → Push mit Retry(3×) + Timeout(30s)
                                         ↓
                              Fehler? → Pending-Queue → nächster Lauf
                                         ↓
                        Pending-Retries (nachher)
```

## Schnellstart

### 1. Script installieren

```bash
mkdir -p ~/.hermes/scripts ~/.hermes/logs ~/.hermes/cache
cp scripts/auto-push-projects.sh ~/.hermes/scripts/
chmod +x ~/.hermes/scripts/auto-push-projects.sh
```

### 2. Hermes Cronjob anlegen

```bash
hermes cronjob create \
  --name project-auto-push \
  --schedule "*/30 * * * *" \
  --script auto-push-projects.sh \
  --no-agent \
  --prompt "Auto-push alle Git-Repos: commit lokal, push wenn online, retry bei Fehlern."
```

**Kritisch:** Der `--script` Parameter darf keinen Pfad enthalten — nur den reinen Dateinamen. Hermes sucht automatisch unter `~/.hermes/scripts/`.

```bash
# FALSCH:
--script /home/user/.hermes/scripts/auto-push-projects.sh

# RICHTIG:
--script auto-push-projects.sh
```

### 3. Manueller Test

```bash
bash ~/.hermes/scripts/auto-push-projects.sh
```

Log: `~/.hermes/logs/auto-push-projects.log`

---

## Konfiguration

Im Script direkt editieren (Zeilen 21–41):

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `SEARCH_PATHS` | `~/Developer/repos`, `~/projects`, … | Wo nach `.git` gesucht wird |
| `EXCLUDE_PATTERNS` | `.linuxbrew`, `.pyenv`, `.hermes`, `node_modules` | Ignorierte Substrings |
| `LOCK_TIMEOUT` | `180` | Sekunden bis ein stale Lock überschrieben wird |
| `max_retries` | `3` | Push-Versuche pro Repo |
| `timeout 30` | `30` | Sekunden pro Push-Versuch |
| `curl --max-time 4` | `4` | Sekunden für Online-Check |

---

## Offline-Resilienz

| Zustand | Verhalten |
|---------|-----------|
| **Kein Internet** | Commits lokal, Push in Pending-Queue verschoben |
| **Internet wieder da** | Nächster Lauf holt Pending-Pushes nach (mit Retry) |
| **Push hängt / Timeout** | 30s Kill → Retry mit Backoff → Queue |
| **Push rejected** | Erkannt als nicht retry-fähig, Status `rejected` |

Online-Check (primary → fallback):
```bash
curl -s --max-time 4 https://github.com > /dev/null 2>&1 ||
curl -s --max-time 4 https://google.com > /dev/null 2>&1
```

---

## Retry-Mechanismus

```
Versuch 1 → sofort
Versuch 2 → nach 5s
Versuch 3 → nach 10s
```

Erfolgt via `timeout 30 bash -c "git push origin '$branch'"`.

Erkannte Fehlertypen:
| Fehler | Reaktion |
|--------|----------|
| Timeout (`exit 124`) | Retry |
| Connection reset / broken pipe / refused | Retry |
| Rejected / stale info / non-fast-forward | Nicht retry-fähig → `rejected` |
| Sonstiger Fehler | Retry, dann Queue |

---

## Locking

Verhindert parallele Ausführung bei überlappenden Cronjob-Läufen:

```bash
LOCKFILE="~/.hermes/cache/auto-push.lock"
```

- Bei aktivem Lock (< 180s): sauberer Abbruch
- Bei stale Lock (> 180s): Überschreiben mit Warnung
- EXIT-Trap gibt Lock immer frei

---

## Pending-Queue

Datei: `~/.hermes/cache/pending-pushes.txt`

Format:
```
/home/user/Developer/repos/project-a|main
/home/user/Developer/repos/project-b|develop|rejected
```

- Ohne Status: wird bei jedem Lauf retry-fähig
- Mit `rejected`: übersprungen (manueller Eingriff nötig)

---

## Sicherheitsfeatures

```bash
export GIT_TERMINAL_PROMPT=0              # Keine interaktiven Prompts
export GIT_SSH_COMMAND="ssh -o ConnectTimeout=10 -o BatchMode=yes ..."
```

- SSH-Passwort-Prompts werden blockiert
- Connect-Timeout 10s, Keepalive 5s/2 Versuche
- Kein Hängenbleiben an interaktiven Shells

---

## Pitfalls

### A. `--script` mit Pfad im Cronjob
**Fehler:** `Script not found: /home/.../script.sh`
**Fix:** Nur Dateiname ohne Pfad übergeben.

### B. Push rejected (upstream diverged)
**Fix:** Manuell `git pull --rebase` oder rebase im betroffenen Repo.

### C. Lock bleibt hängen nach Crash
**Fix:** Lock-Timeout von 180s — nächster Lauf erkennt stale Lock.

### D. SSH-Keys ohne Passphrase nötig
Wenn Repos via SSH geklont sind, muss der Key ohne Passphrase oder mit ssh-agent agieren, sonst blockiert `BatchMode=yes`.

---

## References

- `scripts/auto-push-projects.sh` — Vollständige Referenz-Implementierung (copy-ready)
- `references/retry-logic-explained.md` — Detaillierte Erklärung der Retry-Heuristik
