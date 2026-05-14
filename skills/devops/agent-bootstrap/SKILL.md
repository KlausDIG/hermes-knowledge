---
name: agent-bootstrap
description: |
  Master-Bootstrap-Routine für den Hermes-Agenten auf KlausDIGs System.
  Prüft bei jedem Start alle Automatisierungen, füllt Lücken,
  syncs fehlende Configs, und zeigt Statusübersichten.
  Selbstausführend ohne Benutzerinteraktion — außer bei sudo-Pflicht.
toolsets:
  - terminal
  - file
tags:
  - bootstrap
  - autonomy
  - checkup
  - sync
  - automation
  - agent
version: "1.0.0"
related_skills:
  - monorepo-project-workflow
  - thin-client-nextcloud
  - automated-git-sync
  - hermes-skills-sync
  - hermes-agent
---

# 🚀 Agent Bootstrap

## References

- `references/bootstrap-checklist.md` — Automatische Checks bei Session-Start (autonom + sudo-Limitationen)

## Ausführung

Dieser Skill wird **automatisch** bei jeder Session-Einleitung geprüft.
Kein manueller Aufruf nötig.

## Checks (selbstausführend)

### 1. Git-Config
```bash
if [ "$(git config --global user.name)" != "KlausDIG" ]; then
    git config --global user.name "KlausDIG"
    git config --global user.email "KlausDIG@users.noreply.github.com"
fi
```

### 2. rclone-Config (Snap-Isolation)
```bash
mkdir -p ~/snap/rclone/current/.config/rclone
if [ -f ~/.config/rclone/rclone.conf ]; then
    cp ~/.config/rclone/rclone.conf ~/snap/rclone/current/.config/rclone/
fi
```

### 3. Auto-Push Suchpfad
```bash
if ! grep -q "hermes-klausi-hp" ~/.hermes/scripts/auto-push-projects.sh 2>/dev/null; then
    # Nachricht: "Suchepfad fehlt"
fi
```

### 4. Git-Status Monorepo
```bash
cd ~/hermes-klausi-hp/hermes-klausi-hp
git status --short
# Falls Änderungen: automatisch add + commit + push
```

### 5. Dotfiles-Status
```bash
cd ~
git --git-dir=$HOME/.cfg --work-tree=$HOME status --short
# Falls Änderungen: auto-commit + push
```

### 7. ZRAM-Check
```bash
if ! grep -q "zram" /proc/swaps 2>/dev/null; then
    # WARNUNG: ZRAM nicht aktiv, System langsam
fi
```

### 8. Swap-Datei-Check
```bash
if [ -f /swap.img ]; then
    # HINWEIS: Altes Swap-File noch vorhanden — +4 GB SSD bei Entfernung
fi
```
```bash
PERCENT=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$PERCENT" -gt 90 ]; then
    # WARNUNG an User
fi
```

### 7. Swap-Warnung
```bash
SWAP_USED=$(free | grep Swap | awk '{print $3}')
if [ "$SWAP_USED" -gt 3800000 ]; then
    # WARNUNG: Swap fast voll, Neustart/ZRAM empfohlen
fi
```

## Was ich NICHT allein kann (sudo nötig)

| Task | Status | Befehl für User |
|------|--------|-----------------|
| ZRAM einrichten | ⚠️ Braucht sudo | `sudo bash ~/bin/setup-zram.sh` |
| Swap deaktivieren | ⚠️ Braucht sudo | `sudo swapoff /swap.img` |
| System-Pakete installieren | ⚠️ Braucht sudo | `sudo apt install ...` |

## Automatisierungs-Status

| Service | Schedule | Status |
|---------|----------|--------|
| daily-sync (brew) | 09:00 | ✅ Cronjob |
| skill-discovery | 10:00 | ✅ Cronjob |
| self-update | 11:00 | ✅ Cronjob |
| skills-sync | alle 2h | ✅ Cronjob |
| project-auto-push | alle 30 Min | ✅ Cronjob |
| neytcloud-backup | 02:00 | ✅ Cronjob |

## Manuell noch abzuarbeiten

1. **ZRAM aktivieren:** `sudo bash ~/bin/setup-zram.sh`
2. **Neustart** nach ZRAM-Setup
3. **Browser-Tabs reduzieren** (RAM-Problem)

## Verhalten bei Problemen

| Situation | Reaktion |
|-----------|----------|
| Divergenz auf main | `git pull origin main --rebase` |
| Push rejected | Kein `--force` — User benachrichtigen |
| rclone fehlgeschlagen | Error loggen, nächster Lauf retry |
| Repo neu erstellt | Auto in `projects/<name>/` verschieben |
| Kein Internet | Lokale Commits, später pushen |

## Skills-Status

| Skill | Version | Status |
|-------|---------|--------|
| monorepo-project-workflow | v1.0.0 | ✅ Aktiv |
| thin-client-nextcloud | v1.0.0 | ✅ Aktiv |
| automated-git-sync | v1.0.0 | ✅ Verfügbar |
| hermes-skills-sync | v5.0.0 | ✅ Verfügbar |
| agent-bootstrap | v1.0.0 | ✅ Meta |
