---
name: monorepo-project-workflow
description: |
  Prozedur für neue Projekte im hermes-klausi-hp Monorepo.
  Jedes neue Projekt kommt unter projects/<name>/, wird sofort nach
  GitHub gepusht, und der Auto-Push-Cronjob übernimmt zukünftige Änderungen.
toolsets:
  - terminal
  - file
tags:
  - git
  - github
  - monorepo
  - projects
  - workflow
  - automation
version: "1.3.0"
related_skills:
  - automated-git-sync
  - github-repo-management
  - hermes-skills-sync
  - nextcloud-rclone-cloud-first
---

# 📁 Monorepo Project Workflow

## Kontext

Alle Projekte landen zentral in **einem** Repo:

- **Repo:** `https://github.com/KlausDIG/hermes-klausi-hp`
- **Lokal:** `~/hermes-klausi-hp/hermes-klausi-hp/`
- **Pfad für neue Projekte:** `projects/<projektname>/`
- **Auto-Push:** Cronjob `project-auto-push` alle 30 Minuten
- **Nextcloud-Backup:** Cronjob `neytcloud-backup` täglich 02:00 Uhr

Keine separaten Repos mehr für Einzelprojekte.

## Workflow: Neues Projekt anlegen

### 1. Verzeichnis erstellen

```bash
cd ~/hermes-klausi-hp/hermes-klausi-hp
mkdir -p projects/<projektname>
```

### 2. Dateien hineinkopieren

```bash
cp ~/neues-projekt/* projects/<projektname>/
```

### 3. README anlegen (minimal)

```bash
cat > projects/<projektname>/README.md << 'EOF'
# <Projektname>

Kurzbeschreibung...

## Versionen

| Version | Datum | Status |
|---------|-------|--------|
| v1.0    | ...   | ✅     |
EOF
```

### 4. Committen und sofort pushen

```bash
git add projects/<projektname>/
git commit -m "feat(projects): add <projektname> v1.0"
git pull origin main --rebase  # falls Divergenz
git push origin main
```

### 5. Auto-Push übernimmt den Rest

Ab jetzt prüft der Cronjob alle 30 Min:
- Committet lokale Änderungen
- Pushed nach `origin main`

## Beispiel: DC Power Calculator (durchgeführt)

```bash
cd ~/hermes-klausi-hp/hermes-klausi-hp
mkdir -p projects/dc-power-calculator
cp ~/dc-power-calculator/*.xlsx projects/dc-power-calculator/
cp ~/dc-power-calculator/README.md projects/dc-power-calculator/
git add projects/dc-power-calculator/
git commit -m "feat: Add DC Power Calculator v2.0–v2.3 to projects/"
git pull origin main --rebase
git push origin main
```

## Regel: Keine separaten Repos

| Früher | Jetzt |
|--------|-------|
| `gh repo create <projekt>` | `mkdir projects/<projekt>/` |
| Eigenes `.git/` | Zentrales `.git/` im Monorepo |
| Remote `origin` pro Projekt | Eines: `KlausDIG/hermes-klausi-hp` |
| `auto-push-projects.sh` sucht viele Pfade | `~/hermes-klausi-hp/hermes-klausi-hp/` als Suchpfad |

## Auto-Push-Script: Suchpfad

Im `auto-push-projects.sh` muss der Pfad enthalten sein:

```bash
SEARCH_PATHS=( ... "${HOME}/hermes-klausi-hp" )
```

→ Nicht `~/hermes-klausi-hp/hermes-klausi-hp` (weil `find` dort `.git` findet und `hermes-klausi-hp/hermes-klausi-hp/` als Repo-Root identifiziert).

## Git-Config

```bash
git config --global user.name "KlausDIG"
git config --global user.email "KlausDIG@users.noreply.github.com"
```

## Cronjobs

| Job | Schedule | Status |
|-----|----------|--------|
| `project-auto-push` | Alle 30 Min | ✅ GitHub-Sync |
| `neytcloud-backup` | Täglich 02:00 | ✅ Nextcloud-Backup |

## Pitfalls

### a) Push rejected (non-fast-forward)

**Fix:** Vor jedem Push erst pullen:
```bash
git pull origin main --rebase
```

### b) Git-Config mit falscher E-Mail

**Fix:** Nicht `gridtrace` oder andere Domains verwenden:
```bash
git config --global user.email "KlausDIG@users.noreply.github.com"
```

### c) Ordner-Struktur: nicht `~/hermes-klausi-hp/` direkt

Das Repo liegt unter `~/hermes-klausi-hp/hermes-klausi-hp/` (verschachtelt). Im `auto-push-projects.sh` den äußeren Pfad referenzieren — `find` findet `.git` automatisch darin.

### d) Snap-Isolation bei rclone

rclone via Snap sieht NUR `~/snap/rclone/current/.config/rclone/`, NICHT `~/.config/rclone/`.
**Fix:** Config unter `~/snap/rclone/current/.config/rclone/rclone.conf` anlegen.

### e) rclone `--log-file` funktioniert nicht unter Snap

**Fix:** Stattdessen `2>&1 | tee -a "$LOGFILE"` verwenden.

### f) rclone `--daemon` funktioniert nicht unter Snap

**Fix:** FUSE-Mount funktioniert nicht zuverlässig. Thin-Client-Pattern verwenden (siehe `nextcloud-rclone-cloud-first` Skill).

### g) Automatischer Nextcloud-Backup-Cronjob

Der `neytcloud-backup`-Cronjob läuft täglich um 02:00 Uhr und sichert das gesamte Monorepo zu Nextcloud. Kein manuelles Eingreifen nötig — aber langsamer Upload muss beachtet werden (typisch ~40 Min für 7 MB).

## References

- `references/backup-sync.md` — Nextcloud-Backup via rclone (Sekundär-Backup)
- `references/thin-client-strategy.md` — On-demand Sync statt FUSE-Mount
- `automated-git-sync` Skill — Auto-Push zu GitHub (Primär-Backup)
- `github-repo-management` Skill — Repo-Setup und Remotes
- `nextcloud-rclone-cloud-first` Skill — Thin-Client + Snap-Workarounds