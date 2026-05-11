---
name: hermes-skills-sync
description: |
  Automatischer Skills-Sync-Service für Hermes GitHub-Repo.
  Erkennt Änderungen an allen Skills, versioniert (SemVer), taggt und pusht.
  Wiederkehrend via Cronjob oder manuell ausführbar.
toolsets:
  - terminal
  - file
  - skill_manage
version: "1.0.0"
category: engineering
tags:
  - skills
  - sync
  - automation
  - git
  - github
  - cronjob
  - semver
  - maintenance
---

# 🔄 Hermes Skills Sync v1.0.0

## Zweck

Hält alle Hermes Skills automatisch mit GitHub synchron.
Bei jeder Änderung an einem Skill:
1. Erkennt den Hash-Vergleich (`~/.hermes/skills` → Repo)
2. Bumped Version in SKILL.md (patch/minor/major)
3. Committet mit Conventional-Commit-Format
4. Erstellt Git-Tag (`skillname@v1.2.3`)
5. Push + Push-Tags zu GitHub

## Anwendung

### Manueller Sync

```bash
# Live-Sync
python3 scripts/skills_sync.py

# Nur prüfen
python3 scripts/skills_sync.py --dry-run

# Mit Details
python3 scripts/skills_sync.py --verbose
```

### Automatisch (Hermes Cronjob)

Skripte für Cronjobs müssen unter `~/.hermes/scripts/` liegen und als reiner Dateiname referenziert werden:

```bash
# Skript installieren
mkdir -p ~/.hermes/scripts
cp scripts/skills_sync.py ~/.hermes/scripts/

# Cronjob anlegen
hermes cronjob create \
  --name skills-sync \
  --schedule "every 2h" \
  --script skills_sync.py \
  --no-agent
```

Pitfall: Der `script`-Parameter darf keinen Pfad enthalten — nur den Dateinamen. Der Pfad wird intern auf `~/.hermes/scripts/` aufgelöst.

### Automatisch (Systemd Timer / Cron)

Alternativ als klassischer Cronjob:

```bash
# Stündlich
0 * * * * cd /path/to/repo && python3 /home/user/.hermes/scripts/skills_sync.py >> /tmp/skills-sync.log 2>&1
```

## Pipeline

1. `ensure_repo()` — Prüft Git-Remote
2. `compute_hash()` — Vergleicht `~/.hermes/skills` mit Repo
3. `detect_change_type()` — Heuristik für patch/minor/major
4. `bump_version()` — SemVer-Bump
5. Commit: `type(skills): name vOld → vNew`
6. Tag: `name@vNew`
7. `git push origin main --tags`

## State

`.sync_state.json` im Repo speichert:
- Hash pro Skill
- Letzte Version
- Zeitstempel des Syncs

## SemVer-Heuristik

| Signal | Bump |
|--------|------|
| `BREAKING` / `Überarbeitung` in SKILL.md | major |
| `neu` / `new feature` / `hinzugefügt` | minor |
| Alles andere | patch |

## Dependencies

- Git mit konfiguriertem GitHub-Remote
- `gh` CLI (optional, für Auth-Checks)
- Python 3.10+

## Outputs

- Synchronisierte Skills im Git-Repo
- Git-Tags pro Version
- `CHANGELOG.md` mit History
- JSON-State für Inkrementalsync

## References

- `references/cronjob-setup.md` — Hermes Cronjob-Constraints und Pitfalls
- `references/github-auth-pitfalls.md` — PAT vs SSH, Token-Handling

## Scripts

- `scripts/skills_sync.py` — Haupt-Sync-Daemon
