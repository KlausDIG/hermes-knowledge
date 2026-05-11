---
name: hermes-skills-sync
description: |
  Automatischer Skills-Sync-Service für Hermes GitHub-Repo.
  Erkennt Änderungen an allen Skills, versioniert (SemVer), taggt und pusht.
  Wiederkehrend via Cronjob oder manuell ausführbar.
toolsets:
  - terminal
  - file
version: "1.0.0"
category: devops
tags:
  - skills
  - sync
  - automation
  - git
  - github
  - cronjob
  - semver
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

### Automatisch (Cronjob)

```bash
# Alle 2 Stunden
hermes cronjob create \
  --name skills-sync \
  --schedule "every 2h" \
  --script ~/.hermes/skills/engineering/hermes-klausi-hp/scripts/skills_sync.py

# Oder: Stündlich
hermes cronjob create \
  --name skills-sync-hourly \
  --schedule "0 * * * *" \
  --script ~/.hermes/skills/engineering/hermes-klausi-hp/scripts/skills_sync.py
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

## Dependencies

- Git mit konfiguriertem GitHub-Remote
- `gh` CLI (optional, für Auth-Checks)
- Python 3.10+

## Outputs

- Synchronisierte Skills im Git-Repo
- Git-Tags pro Version
- `CHANGELOG.md` mit History
- JSON-State für Inkrementalsync
