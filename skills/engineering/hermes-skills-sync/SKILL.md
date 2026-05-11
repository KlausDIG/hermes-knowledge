---
name: hermes-skills-sync
description: |
  Automatischer Skills-Sync-Service für Hermes GitHub-Repo.
  Erkennt Änderungen an allen Skills, versioniert (SemVer), taggt und pusht.
  Bietet Git-Subtree-Extraktion für einzelne Skill-Repos.
  Wiederkehrend via Cronjob oder manuell ausführbar.
toolsets:
  - terminal
  - file
  - skill_manage
version: "5.0.0"
category: engineering
tags:
  - skills
  - sync
  - automation
  - git
  - github
  - cronjob
  - semver
  - subtree
  - maintenance
  - packaging
---

# 🔄 Hermes Skills Sync v4.0.0

## Zweck

Hält alle Hermes Skills automatisch mit GitHub synchron.
Bei jeder Änderung an einem Skill:
1. Erkennt den Hash-Vergleich (`~/.hermes/skills` → Repo)
2. Bumped Version in SKILL.md (patch/minor/major)
3. Committet mit Conventional-Commit-Format
4. Erstellt Git-Tag (`skillname@v1.2.3`)
5. Push + Push-Tags zu GitHub

## Skill vs. Projekt

Dieser Skill bildet eine **zweistufige Struktur** ab:

| Aspekt | **Skill** (`skills/...`) | **Projekt** (`projects/...`) |
|--------|--------------------------|------------------------------|
| **Zweck** | Agent-Workflow, Prompts, Know-how | Eigenständiges Python-Paket |
| **Installation** | `skill_view()` im Agenten | `pip install -e .` auf jedem Rechner |
| **Nutzung** | Hermes-Toolcalls, LLM-Kontext | CLI, Import, CI/CD, andere Rechner |
| **Release** | Git-Tag im Monorepo | Subtree-Push zu eigenem Repo |
| **Struktur** | `SKILL.md` + `scripts/` + `references/` | `pyproject.toml` + `src/` + Tests |
| **Beispiel** | *"So analysierst du ein PDF"* | `import hermes_ecad_pdf_analyzer; ...` |

**Faustregel:**
- Ein **Skill** beschreibt dem Agenten *wie* etwas gemacht wird.
- Ein **Projekt** macht es *eigenständig nutzbar* — auch ohne Hermes.

→ Details: `references/skill-vs-project.md`

## Projekt-Erzeugung (Skill → setuptools)

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

## Projekt-Erzeugung (Skill → setuptools)

### Einzelnes Projekt

```bash
# Interaktiv
python3 tools/package_skill.py skills/engineering/ecad-pdf-analyzer

# Ohne Nachfrage, nur generieren
python3 tools/package_skill.py skills/engineering/ecad-pdf-analyzer --auto

# Generieren + direkt installieren
python3 tools/package_skill.py skills/engineering/ecad-pdf-analyzer --auto --install
```

### Alle Skills auf einmal

```bash
# Generiere 82 Projekte aus allen Skills (keine Nachfragen)
python3 tools/package_skill.py --all --auto
```

### Projekt nach GitHub pushen (Subtree)

**Kritisch:** Projekte müssen zuerst committet sein, sonst `fatal: no new revisions were found`:

```bash
git add projects/
git commit -m "feat(projects): generate all X standalone projects from skills"
git push origin main
```

Dann Subtree-Push:

```bash
# Ein Projekt
git subtree split --prefix projects/ecad_pdf_analyzer -b proj-ecad
git remote add hermes-project-ecad_pdf_analyzer https://github.com/KlausDIG/hermes-project-ecad_pdf_analyzer.git
git push -f hermes-project-ecad_pdf_analyzer proj-ecad:main
git branch -D proj-ecad
```

### Batch: Alle Projekte auf GitHub

Siehe `references/project-batch-push.md` für das vollständige Script mit Retry-Logik.

Generiert in `projects/`:
- `pyproject.toml` — setuptools-fähig
- `src/hermes_<name>/` — Module mit den Skill-Skripten
- `README.md` — Kurzbeschreibung
- `SKILL_REFERENCE.md` — Kopie des Original-SKILL.md
- `.skill_manifest.json` — Mapping Skill ↔ Projekt

## Projekt auschecken (eigenständig)

```bash
# Ein Projekt clonen (kein Hermes nötig)
git clone https://github.com/KlausDIG/hermes-project-hermes-skills-sync.git
cd hermes-project-hermes-skills-sync
pip install -e .
extract-subtrees --help
```

## Subtree-Befehle

```bash
# Nur einen Skill brauchen:
git clone https://github.com/<owner>/hermes-skill-<name>.git

# Updates vom Monorepo holen:
git subtree pull --prefix skills/<cat>/<skill> hermes-skill-<name> main

# Updates ins Monorepo zurückspielen:
git subtree push --prefix skills/<cat>/<skill> hermes-skill-<name> main
```

## Dependencies

- Git mit konfiguriertem GitHub-Remote
- `gh` CLI (optional, für Auth-Checks)
- Python 3.10+
- setuptools >= 61.2 (für Projekte)

## Outputs

- Synchronisierte Skills im Git-Repo
- Git-Tags pro Version
- `CHANGELOG.md` mit History
- JSON-State für Inkrementalsync
- 83 separate Skill-Repos auf GitHub (Subtree)
- `projects/` mit setuptools-fähigen Paketen

## Scripts

| Script | Zweck |
|--------|-------|
| `scripts/skills_sync.py` | Haupt-Sync-Daemon |
| `scripts/extract_subtrees.py` | Subtree-Extraktion + GitHub-Push |
| `tools/package_skill.py` | Skill → Python-Projekt Generator |

## References

- `references/cronjob-setup.md` — Hermes Cronjob-Constraints und Pitfalls
- `references/github-auth-pitfalls.md` — PAT vs SSH, Token-Handling
- `references/subtree-workflow.md` — Subtree-Command-Reference
