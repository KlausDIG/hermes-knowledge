---
name: linux-system-maintenance
description: |
  Systempflege auf speicherarmen Ubuntu/Debian-Workstations:
  ZRAM-Einrichtung statt Swap, Speicheranalyse, sicheres Aufräumen,
  Browser-Reduktion, Snap-Reduktion, automatische Cronjob-Cleanup.
  Alle sudo-Aufgaben werden als Scripts bereitgestellt, die der User
  manuell ausführt (Hermes hat kein PTY für sudo).
toolsets:
  - terminal
  - file
tags:
  - linux
  - maintenance
  - zram
  - swap
  - cleanup
  - disk-space
  - snap
version: "1.2.0"
related_skills:
  - linux-agent-setup
  - linux-dev-workstation
  - thin-client-nextcloud
  - agent-bootstrap
version: "1.1.0"
---

# 🛠️ Linux System Maintenance

## Zweck

Speicher- und Performance-Optimierung auf Systemen mit begrenztem Platz
(233 GB SSD, 14 GB RAM, keine sudo-Rechte für Hermes).

## Voraussetzungen

- Ubuntu/Debian Linux (kein sudo für Hermes-Agent)
- Hermes erstellt Scripts, User führt diese manuell mit sudo aus

## ZRAM statt Swap-File

### Warum ZRAM?
- Kein SSD-Verschleiß durch ständiges Swap-Schreiben
- Komprimierter RAM-Swap ist schneller als SSD-Swap
- +4 GB SSD frei nach Entfernen des alten /swap.img

> ⚠️ **Wichtig:** Nach Firefox-Entfernung (`snap remove firefox`) kann das alte **Profil-Dir** `~/snap/firefox/` noch existieren. Manuell prüfen und bei Bedarf entfernen:
> ```bash
> ls -la ~/snap/ | grep firefox
> rm -rf ~/snap/firefox   # nur wenn Daten nicht mehr nötig
> ```

### Einrichten
```bash
# 1. Hermes erstellt Script (bereits in ~/bin/setup-zram.sh)
# 2. User führt aus:
sudo bash ~/bin/setup-zram.sh
# 3. Neustart empfohlen
```

### Altes Swap entfernen
```bash
sudo bash ~/bin/remove-old-swap.sh
# Oder direkt:
sudo swapoff /swap.img
sudo rm -f /swap.img
sudo sed -i '/swap.img/d' /etc/fstab
```

### Verifizierung
```bash
cat /proc/swaps
# Sollte nur /dev/zram0 zeigen, nicht /swap.img
free -h
# Swap-Größe ~50% des RAMs (z.B. 7,2 GB bei 14 GB RAM)
```

## Speicheranalyse

### Schnellübersicht (schnell, nie Timeouts)
```bash
df -h /                    # SSD-Status
cat /proc/swaps            # Swap-Status
free -h                    # RAM + Swap
du -sh ~/* 2>/dev/null | sort -rh | head -10   # Größte Home-Ordner
```

### Systemebene (gezielte Pfade — `du -sh /*` timed out oft!)
> ⚠️ **Pitfall:** Auf langsamen SSDs mit vielen Dateien timed `du -sh /` oder `du -sh /home` nach 60s aus.
> Stattdessen gezielte Pfade scannen — siehe `references/disk-analysis-tools.md`.

```bash
du -sh /usr /var /opt /snap /home 2>/dev/null
du -sh /var/lib/* 2>/dev/null | sort -rh | head -10
du -sh /snap/*/current 2>/dev/null | sort -rh | head -10
```

### Snap-Platz detailliert (oft der größte Block!)
```bash
du -sh /var/lib/snapd/snaps              # Physische .snap-Dateien
ls -lhS /var/lib/snapd/snaps/ | head -10 # Größte einzelne Snaps
snap list --all | grep deaktiviert        # Alte Revisionen
```

### User-Ordner detailliert
```bash
for dir in ~/.hermes ~/snap ~/.local ~/.cache ~/.linuxbrew ~/.config ~/Downloads ~/bin ~/workspace; do
    [ -d "$dir" ] && du -sh "$dir" 2>/dev/null
done | sort -rh | head -15
```

### Werkzeuge für interaktive Analyse
Siehe `references/disk-analysis-tools.md` für `ncdu` (via Homebrew), typische Platzfresser auf diesem System, und wöchentliche Platzverlust-Erwartungswerte.

### Docker Desktop macOS Recovery
Siehe `references/docker-desktop-recovery-mac.md` für den vollständigen Notfall-Recovery-Prozess, wenn Docker Desktop bei knappem Speicher hängt. Inklusive VM-Disk-Löschung, Settings.json für 64 GB VM-Limit, und Cloud-First Docker Override.

## Browser-Reduktion (größter RAM-Verursacher)

### Ergebnisse aus Praxis
Mit Chrome + Brave + Firefox gleichzeitig:
- **56 Renderer-Prozesse**
- **~5-8 GB RAM belegt**
- Swap läuft voll

Nach Schließen aller Browser:
- **~4-5 GB RAM freigegeben**
- Swap entspannt

### Empfohlene Reduktion
| Browser | Typ | Größe | Status |
|---------|-----|-------|--------|
| Google Chrome | DEB | ~415 MB | ✅ **BEHALTEN** (schnell, wenig Overhead) |
| Brave | Snap | ~630 MB | Optional entfernen |
| Firefox | Snap | **~8,3 GB** | ❌ **ENTFERNEN** (größter Platzfresser) |

### Entfernungs-Command
```bash
snap remove firefox --purge
# Optional:
snap remove brave --purge
```

## Snap-Reduktion

### Alte Snap-Revisionen entfernen (AM SICHERSTEN)

Snap behält alte Revisionen als Backup — die können **GBs** belegen.

**Anzeigen:**
```bash
snap list --all | grep deaktiviert
```

**Wo die Daten physikalisch liegen:**
```bash
ls -lhS /var/lib/snapd/snaps/
# -> z.B. code_238.snap (380 MB), thunderbird_1093.snap (228 MB)
```

**Entfernen (nur deaktivierte Revisionen!):**
```bash
snap remove <name> --revision=<rev>
# Beispiel:
snap remove code --revision=238
snap remove thunderbird --revision=1093
```

**Was erwartet wird:**
| Snap | Revision | Größe | Status |
|------|----------|-------|--------|
| code | 238 | ~380 MB | deaktiviert → entfernbar |
| thunderbird | 1093 | ~228 MB | deaktiviert → entfernbar |

> ⚠️ **NIE aktive Revisionen entfernen!** Nur Snapps mit Status `deaktiviert`.
> Aktive Revision hat **kein** "deaktiviert"-Label.

### Gesamte Snaps entfernen
| Snap | Größe | Erklärung |
|------|-------|-----------|
| firefox | ~8,3 GB | Siehe Browser-Reduktion |
| telegram-desktop | ~6,9 GB | Wenn nicht aktiv genutzt |
| rclone-dev | ~16 MB | Nur stable rclone nötig |
| brave | ~630 MB | Wenn nur Chrome genügt |

## Automatischer Snap-Cleanup (Cronjob)

Deaktivierte Snap-Revisionen werden manuell oft vergessen. Ein **wöchentlicher Cronjob** bereinigt automatisch.

### Script erstellen
```bash
mkdir -p ~/.hermes/scripts
cat > ~/.hermes/scripts/snap-cleanup.sh << 'SNAPSCRIPT'
#!/usr/bin/env bash
set -euo pipefail
LOG_FILE="$HOME/.local/state/snap-cleanup.log"
mkdir -p "$(dirname "$LOG_FILE")"
exec >>"$LOG_FILE" 2>&1

echo "=========================================="
echo "Snap-Cleanup gestartet: $(date -Iseconds)"
echo "=========================================="

DISABLED=$(snap list --all | grep 'deaktiviert' || true)

if [ -z "$DISABLED" ]; then
    echo "Keine deaktivierten Snaps gefunden."
    exit 0
fi

echo "Gefundene deaktivierte Snaps:"
echo "$DISABLED"
echo "=========================================="

while IFS= read -r line; do
    NAME=$(echo "$line" | awk '{print $1}')
    REV=$(echo "$line" | awk '{print $3}')
    if [ -n "$NAME" ] && [ -n "$REV" ]; then
        echo "→ Entferne $NAME (Revision $REV)..."
        if sudo snap remove "$NAME" --revision="$REV" 2>&1; then
            echo "  ✓ $NAME Rev $REV entfernt"
        else
            echo "  ⚠️ Fehler bei $NAME Rev $REV (vermutlich sudo erforderlich)"
        fi
    fi
done <<< "$DISABLED"

echo "Snap-Cleanup beendet: $(date -Iseconds)"
echo "=========================================="
SNAPSCRIPT
chmod +x ~/.hermes/scripts/snap-cleanup.sh
```

### Cronjob erstellen
```bash
hermes cronjob create \
  --name snap-cleanup \
  --schedule "0 4 * * 0" \
  --script snap-cleanup.sh \
  --no-agent
```

Oder via `cronjob` tool:
- `action`: `create`
- `name`: `snap-cleanup`
- `no_agent`: `true`
- `schedule`: `0 4 * * 0` (Sonntag 04:00)
- `script`: `snap-cleanup.sh`

### Hinweis: sudo erforderlich
Snap-Revisions-Entfernung braucht `root`. Optionen:
1. **Manuell:** `sudo snap remove <name> --revision=<rev>`
2. **Automation mit visudo:** `klausd ALL=(ALL:ALL) NOPASSWD: /usr/bin/snap`

### Verifizierung
```bash
cat ~/.local/state/snap-cleanup.log          # Letzte Lauf-Logs
snap list --all | grep deaktiviert            # Sollte leer sein
du -sh /var/lib/snapd/snaps                   # Physische Größe
```

### Was NIEMALS entfernt werden darf
| Snap | Grund |
|------|-------|
| core / core20 / core22 / core24 | Snap-Grundsystem |
| snapd | Snap-Engine |
### Werkzeuge für interaktive Analyse
Siehe `references/disk-analysis-tools.md` für `ncdu` (via Homebrew), typische Platzfresser auf diesem System, und wöchentliche Platzverlust-Erwartungswerte.

## `.bash_history` Explosion auf Servern (Root-Cause: 38 GB)

### Problem
Automatisierte Skripte (PM2, Cronjobs, Bots), die als **root** laufen, schreiben jeden Befehl in `.bash_history`. Bei dauerhaftem Betrieb wächst die Datei auf **Zehn-GB-Niveau**.

**Realer Fall:** Hostinger VPS — `/root/.bash_history` = **38,4 GB** bei 96 GB SSD.

### Erkennung
```bash
# Schnell auf VPS:
ssh hostinger "du -sh /root/.bash_history"
# Oder lokal:
du -sh ~/.bash_history
# Alarm wenn > 100 MB
```

### Sofort-Fix (erfordert sudo)
Hermes kann `sudo` nicht interaktiv ausführen (kein PTY). Script erstellen, User führt aus:

```bash
cat > ~/bin/clear-bash-history.sh << 'EOF'
#!/bin/bash
# Bash-History leeren (Server)
for userdir in /home/* /root; do
    histfile="$userdir/.bash_history"
    [ -f "$histfile" ] || continue
    size=$(du -sh "$histfile" 2>/dev/null | cut -f1)
    echo "Vorher: $histfile = $size"
    > "$histfile"
    history -c 2>/dev/null || true
    echo "Nachher: $histfile geleert"
done
EOF
# Dann manuell:
sudo bash ~/bin/clear-bash-history.sh
```

**Ergebnis:** +38 GB frei, Speicher von 99% → 62%.

### Dauerhafte Prävention (Server-Setup)
Bei jeder neuen Server-Einrichtung — Hermes erstellt Script, User führt aus:

```bash
cat > ~/bin/set-history-limits.sh << 'EOF'
#!/bin/bash
for profile in /etc/profile /root/.bashrc; do
    [ -f "$profile" ] || continue
    grep -q "HISTSIZE=" "$profile" && continue
    echo -e "\n# Limitiere Bash-Historie (verhindert GB-Explosionen)" >> "$profile"
    echo "HISTSIZE=1000" >> "$profile"
    echo "HISTFILESIZE=2000" >> "$profile"
    echo "✅ Limits in $profile gesetzt"
done
EOF
sudo bash ~/bin/set-history-limits.sh
```

### Warum passiert das?
| Ursache | Mechanismus |
|---------|-------------|
| PM2-Apps als root | `pm2 start` in root-Cron → jeder Node-Befehl wird geloggt |
| Cronjobs mit `bash -c` | Jeder Cron-Aufruf landet in der Historie |
| Interaktive root-Sessions | Lange manuelle Sessions häufen Einträge an |

## `.bash_history` Explosion auf macOS (Mac Mini: 285 GB)

### Kontext
Das `.bash_history`-Explosionsproblem betrifft nicht nur Linux-Server — bei intensiver Automatisierung auf macOS kann die Datei ebenfalls ins **Hundert-GB-Gebiet** wachsen. Realfall: Mac Mini mit macOS 25.3, `.bash_history` = **285 GB** (~57 % der gesamten 494 GB SSD).

**Wichtig:** macOS nutzt standardmäßig zsh, aber viele Automatisierungs-Scripts starten explizit `bash` — daher existiert `~/.bash_history` parallel zu `~/.zsh_history`.

**🚨 Root-Cause identifiziert (Session 2026-05-17):**
Cronjob `sync-history-macmini.sh` enthielt den Bug:
```bash
cat ~/.bash_history ~/.zsh_history >> ~/.bash_history  # GEOMETRISCHE EXPLOSION
```
Diese Zeile fügt `.bash_history` **an sich selbst** an — jeden Tag. Nach 60 Tagen: 1,8 Mio Zeilen = 285 GB.
`tail -2000` kam danach, aber `awk '!seen[$0]++'` bei 285 GB fror ein → `.bash_history.tmp` wurde nie erstellt.

**Fix:** Self-Append eliminieren, Hard-Limits (10.000 Zeilen / 50 MB), crash-sicheres `set -euo pipefail`. Siehe `references/macmini-bash-history-explosion.md`.

### Schnellerfassung (Remote über SSH)
```bash
ssh <host> "du -sh ~/.bash_history  ~/.zsh_history"
# Alarm: > 1 GB → Sofortmaßnahme
```

### Sofort-Fix (macOS, kein sudo nötig)
```bash
# History sofort leeren
> ~/.bash_history
rm -f ~/.bash_history.tmp

# Limits für beide Shells setzen
for rc in ~/.bashrc ~/.zshrc; do
    [ -f "$rc" ] || continue
    grep -q "HISTSIZE=" "$rc" && continue
    echo -e "\n# Limitiere Shell-Historie (verhindert GB-Explosionen)" >> "$rc"
    echo "export HISTSIZE=10000"      >> "$rc"
    echo "export SAVEHIST=10000"      >> "$rc"
    echo "export HISTFILESIZE=20000"  >> "$rc"
done

# Verifizierung
ls -lh ~/.bash_history ~/.zsh_history
grep HIST ~/.bashrc ~/.zshrc 2>/dev/null
```

**Erwartetes Ergebnis:** +285 GB frei → SSD von 97 % auf ~40 % Belegung.

### Dauerhafte Prävention (macOS + Linux)
Bei jeder neuen Automatisierungs-Session — Hermes erstellt Script, User führt aus:

```bash
cat > ~/bin/set-history-limits.sh << 'EOF'
#!/bin/bash
for rc in ~/.bashrc ~/.zshrc /root/.bashrc /etc/profile; do
    [ -f "$rc" ] || continue
    grep -q "HISTSIZE=" "$rc" && continue
    echo -e "\n# Limitiere Shell-Historie (verhindert GB-Explosionen)" >> "$rc"
    echo "export HISTSIZE=10000"      >> "$rc"
    echo "export SAVEHIST=10000"      >> "$rc"
    echo "export HISTFILESIZE=20000"  >> "$rc"
    echo "✅ Limits in $rc gesetzt"
done
EOF
bash ~/bin/set-history-limits.sh
```

### Verifizierung nach Fix
```bash
ssh hostinger "ls -lh /root/.bash_history"
# Sollte: 0 oder wenige KB
ssh hostinger "grep HISTSIZE /root/.bashrc"
# Sollte: HISTSIZE=1000, HISTFILESIZE=2000
```

Siehe `references/vps-bash-history-explosion.md` für vollständiges Linux-Post-Mortem.
Siehe `references/macmini-bash-history-explosion.md` für vollständiges macOS-Post-Mortem.

## Automatisches Cleanup (Cronjob)
```bash
snap remove <name> --purge          # Ganzen Snap entfernen
snap remove <name> --revision=<rev>  # Nur alte Revision
```

## Automatisches Cleanup (Cronjobs)

### Mehrstufiges Defense-System

| Job | Script | Schedule | Funktion |
|-----|--------|----------|----------|
| `disk-watchdog` | `disk-watchdog.sh` | **Jede Stunde** | Prüft freien Speicher. Bei < 5 GB → Notfall-Cleanup |
| `daily-cleanup` | `daily-cleanup.sh` | **Täglich 02:00** | Chrome/Snap-Caches, Homebrew, npm, Hermes-Logs, /tmp, Downloads |
| `snap-cleanup` | `snap-cleanup.sh` | **Sonntag 04:00** | Deaktivierte Snap-Revisionen entfernen |

### Manuelle Emergency-Scripts

| Script | Funktion | Sudo nötig? | Erwartete Freigabe |
|--------|----------|-------------|-------------------|
| `~/bin/cleanup-now.sh` | Sofort-Cleanup nach intensiver Session | ❌ Nein | ~200 MB - 2 GB |
| `~/bin/cleanup-ollama-gpu.sh` | Ollama ROCm/CUDA/Vulkan entfernen (Intel-iGPU) | ✅ Ja | **~5.9 GB** |
| `~/bin/cleanup-snaps.sh` | Thunderbird/Brave entfernen + alte Revs | ✅ Ja | **~1-2 GB** |
| `~/bin/cleanup-dotfiles.sh` | `~/.cfg` Git-Objects komprimieren | ❌ Nein | **~3-5 GB** |
| `~/bin/cleanup-downloads.sh` | Installationsarchive + alte Downloads | ❌ Nein | ~50-200 MB |
| `~/bin/setup-zram.sh` | ZRAM aktivieren | ✅ Ja | +4 GB (Swap.img entfällt) |
| `~/bin/remove-old-swap.sh` | Altes Swap-File entfernen | ✅ Ja | +4 GB |
| `~/bin/thin-client.sh` | Cloud on-demand | ❌ Nein | — |

### Verifizierung nach Cleanup
```bash
df -h /
free -h
cat ~/.local/state/daily-cleanup.log
cat ~/.local/state/disk-watchdog.log
```

## Docker Desktop VM-Disk explodiert bei knappem Speicher (macOS)

> Siehe `references/docker-desktop-recovery-mac.md` fuer den vollstaendigen Notfall-Recovery-Prozess, inklusive:
> - VM-Disk-Loeschung (bringt sofort ~10-15 GB)
> - Settings.json fuer 64 GB VM-Limit
> - Cloud-First Docker Compose Override (keine named Volumes)
> - SSH-Escaping-Pitfalls mit zsh/macOS
>
> Siehe auch `templates/docker-compose-cloud-first.yml` fuer ein fertiges Cloud-First Compose-File.

Wenn `df -h /` >= 90% zeigt, kann Docker Desktop keine neue VM anlegen oder friert ein.
**Symptom:** `docker info` → Endloses Warten. Letztes VM-Log: "shutdown complete".

**Schnell-Diagnose:**
```bash
df -h /                    # Wenn >= 90% → VM-Disk ist blockiert
ls ~/Downloads/*.dmg       # Installationsarchive oft mehrere GB
# Python-Scan statt du -sh (timeout-sicher):
python3 -c "import os; [print(p, f'{sum(os.path.getsize(os.path.join(d,f)) for d,_,files in os.walk(p) for f in files if os.path.exists(os.path.join(d,f)))/(1024**3):.1f} GB' if os.path.exists(p) else 'MISSING') for p in ['/Users/klaus/Library/Containers/com.docker.docker','/Users/klaus/Documents','/Users/klaus/Library/Application Support/Autodesk','/Users/klaus/Library/Application Support/Google']]"
```

**Notfall-Recovery (4 Schritte):**
```bash
# 1. Docker beenden
pkill -9 -x "Docker Desktop"
pkill -9 -f "com.docker.backend"
sleep 10

# 2. VM-Disk loeschen (Bringt IMMER sofort ~10-15 GB)
rm -rf ~/Library/Containers/com.docker.docker/Data/vms/0/

# 3. Docker Desktop neu starten
open -a "Docker Desktop"
# Warte 60-90s bis Engine antwortet

# 4. Verifizierung
docker version --format "Daemon: {{.Server.Version}}"
df -h /  # Sollte < 60% belegt zeigen
```

**VM-Disk dauerhaft begrenzen:**
```bash
mkdir -p "$HOME/Library/Group Containers/group.com.docker"
printf '{"diskSizeMiB":65536}\n' > \
    "$HOME/Library/Group Containers/group.com.docker/settings.json"
# ODER Docker Desktop GUI: Settings → Resources → Virtual disk limit = 64 GB
```

## Pitfalls

### No PTY for sudo
Hermes kann `sudo` **nicht** interaktiv ausführen (kein TTY).
**Fix:** Script erstellen, User führt `sudo bash script.sh` manuell aus.

### No PTY for sudo
Hermes kann `sudo` **nicht** interaktiv ausführen (kein TTY).
**Fix:** Script erstellen, User führt `sudo bash script.sh` manuell aus.

### `local` in Bash-case-Blöcken
`local PID=$!` in `case`-Blöcken → Fehler.
**Fix:** Entweder Funktion verwenden oder `PID=$!` ohne `local`.

### Swap.img nach ZRAM nicht manuell löschen
Wenn `/swap.img` noch in `/etc/fstab` steht → Boot-Probleme.
**Fix:** Immer `remove-old-swap.sh` verwenden, das fstab bereinigt.

### Snap-Isolation bei rclone
Config muss an beiden Orten liegen:
```bash
~/.config/rclone/rclone.conf
~/snap/rclone/current/.config/rclone/rclone.conf
```

## Docker Desktop VM-Disk explodiert bei knappem Speicher (macOS)

> Siehe `references/docker-desktop-recovery-mac.md` fuer den vollstaendigen Notfall-Recovery-Prozess, inklusive:
> - VM-Disk-Loeschung (bringt sofort ~10-15 GB)
> - Settings.json fuer 64 GB VM-Limit
> - Cloud-First Docker Compose Override (keine named Volumes)
> - SSH-Escaping-Pitfalls mit zsh/macOS

Wenn `df -h /` >= 90% zeigt, kann Docker Desktop keine neue VM anlegen oder friert ein.
**Symptom:** `docker info` → Endloses Warten. Letztes VM-Log: "shutdown complete".

**Schnell-Diagnose:**
```bash
df -h /                    # Wenn >= 90% → VM-Disk ist blockiert
ls ~/Downloads/*.dmg       # Installationsarchive oft mehrere GB
# Python-Scan statt du -sh (timeout-sicher):
python3 -c "import os; [print(p, os.path.exists(p) and f'{sum(os.path.getsize(os.path.join(d,f)) for d,_,files in os.walk(p) for f in files if os.path.exists(os.path.join(d,f)))/(1024\*\*3):.1f} GB') for p in ['/Users/klaus/Library/Containers/com.docker.docker','/Users/klaus/Documents','/Users/klaus/Library/Application Support/Autodesk']]"
```

**Notfall-Recovery (4 Schritte):**
```bash
# 1. Docker beenden
pkill -9 -x "Docker Desktop"
pkill -9 -f "com.docker.backend"
sleep 10

# 2. VM-Disk loeschen (Bringt IMMER sofort ~10-15 GB)
rm -rf ~/Library/Containers/com.docker.docker/Data/vms/0/

# 3. Docker Desktop neu starten
open -a "Docker Desktop"
# Warte 60-90s bis Engine antwortet

# 4. Verifizierung
docker version --format "Daemon: {{.Server.Version}}"
df -h /  # Sollte < 60% belegt zeigen
```

**VM-Disk dauerhaft begrenzen:**
```bash
mkdir -p "$HOME/Library/Group Containers/group.com.docker"
printf '{"diskSizeMiB":65536}\n' > \
    "$HOME/Library/Group Containers/group.com.docker/settings.json"
# ODER Docker Desktop GUI: Settings → Resources → Virtual disk limit = 64 GB
```

Siehe auch `templates/docker-compose-cloud-first.yml` fuer ein vollstaendiges Cloud-First Override.

## Mehrstufiges Defense-System gegen Chrome/Snap-Cache-Explosion

**Kontext:** KlausDIG nutzt intensiv Chrome und Snap-basierte Apps (Code:, etc.). Bei intensiven Sessions kann Chrome-Cache und Snap-Caches innerhalb von Stunden GBs verbrauchen — wöchentliches Cleanup reicht nicht. Entwickelt nach einem realen 99%-Füllungs-Notfall.

### Defense-Ebenen

| Ebene | Job | Frequenz | Trigger |
|-------|-----|----------|---------|
| 1. **Watchdog** | `disk-watchdog` | **Jede Stunde** | Auto — prüft freien Speicher |
| 2. **Daily** | `daily-cleanup` | **Täglich 02:00** | Auto — aggressives Cache-Cleanup |
| 3. **Snap** | `snap-cleanup` | **Sonntag 04:00** | Auto — deaktivierte Revisionen |
| 4. **Manual** | `~/bin/cleanup-now.sh` | **Sofort** | Manuell nach intensiver Session |
| 5. **Deep** | `~/bin/cleanup-*.sh` | **Ad-hoc** | Einmalige Brocken (Ollama, Dotfiles) |

### Watchdog-Logik (stündlich)

```bash
FREE_GB=$(df -BG / | tail -1 | awk '{print $4}' | tr -d 'G')
if [ "$FREE_GB" -lt 5 ]; then
    # Sofort:
    rm -rf ~/.cache/google-chrome/* ~/.cache/chromium/*
    rm -rf ~/snap/*/current/.cache/*
    npm cache clean --force
    brew cleanup -s
    find /tmp -user "$USER" -type f -delete
fi
```

> **Lernen aus Session:** "Wöchentlich ist zu selten — Chrome-Cache explodiert bei intensiver Nutzung innerhalb von Stunden."

### Daily-Cleanup Ziele (aggressiv)

```bash
# Chrome/Chromium + VS Code: Snap-Caches (alle Varianten)
for cache in \
    "$HOME/.cache/google-chrome" \
    "$HOME/.cache/chromium" \
    "$HOME/.config/google-chrome/Default/Cache" \
    "$HOME/.config/chromium/Default/Cache" \
    "$HOME/snap/code/current/.config/Code:/Cache" \
    "$HOME/snap/code/current/.config/Code:/CachedData" \
    "$HOME/snap/code/current/.config/Code:/CachedExtensionVSIXs"; do
    [ -d "$cache" ] && rm -rf "$cache"/* 2>/dev/null || true
done

# Snap-Caches (alle Snaps)
for snap_cache in "$HOME"/snap/*/current/.cache; do
    [ -d "$snap_cache" ] && rm -rf "$snap_cache"/* 2>/dev/null || true
done

# + Homebrew, npm, Hermes-Logs (>7 Tage), /tmp, Downloads (>3 Tage)
```

### Sofort-Cleanup Script (`~/bin/cleanup-now.sh`)

Ein Befehl nach intensiver Chrome-Session:
```bash
bash ~/bin/cleanup-now.sh   # Chrome/Snap-Caches + /tmp + npm + Brew
```

## Incident: Disk-Platz-Notstand bei 99% Füllung (2026-05-15)

**Situation:** `/` bei 99% (217 GB / 233 GB), nur 4 GB frei. `du -sh /` und `du -sh /home` timen aus.

### Neue Platzfresser entdeckt

| # | Pfad | Größe | Ursache |
|---|------|-------|---------|
| 1 | `~/.cfg` (Dotfiles bare-repo Git-Objects) | ~7 GB | Auto-Sync hat Snaps/Caches als Git-Objects eingecheckt |
| 2 | `/usr/local/lib/ollama` | ~6 GB | GPU-Backends (ROCm 2.5G, CUDA 3.5G) — nutzlos bei Intel-iGPU |
| 3 | `~/.vscode/` | ~600 MB | Extensions (Pylance, IntelliCode) |
| 4 | `~/.rustup/` | ~1.4 GB | Rust-Toolchains |
| 5 | `~/.npm/` | ~1.2 GB | Node-Modules-Cache |

### Analyse-Techniken bei Timeouts

Wenn `du -sh /` oder `du -sh /home` timed out (60s):

**1. Python-Scan statt Shell-du (Timeout-sicher)**
```python
paths = ["/usr", "/var", "/opt", "/snap", "/home", "/tmp"]
for p in paths:
    r = terminal(f'du -sh {p} 2>/dev/null')
    print(r['output'].strip())
```

**2. Bare-Repo mit GIT_DIR statt `--git-dir`**
```bash
# FALSCH (Git-Version auf Ubuntu 24.04):
git --git-dir=~/.cfg count-objects -vH   # → "Kein Git-Repository"

# RICHTIG:
GIT_DIR=/home/klausd/.cfg git count-objects -vH
GIT_DIR=/home/klausd/.cfg git log --oneline | head -20
GIT_DIR=/home/klausd/.cfg git rev-list --all --objects | wc -l
```

**3. Finden des Timeout-Verursachers**
```bash
ls -d ~/.* 2>/dev/null              # versteckte Verzeichnisse auflisten
for dir in ~/.ollama ~/.n8n ~/.dotnet ~/.cfg ~/.vscode ~/.cargo; do
    timeout 15 du -sh "$dir" 2>/dev/null || echo "TIMEOUT: $dir"
done
```

### Bereinigung: Ollama GPU-Backends (Sudo nötig)

Bei Intel-iGPU sind ROCm und CUDA-Backends **komplett nutzlos**:
```bash
# Nur behalten: libggml-cpu-*.so + libggml-base.so*
# Löschen (Root erforderlich):
sudo rm -rf /usr/local/lib/ollama/rocm      # ~2.5 GB
sudo rm -rf /usr/local/lib/ollama/cuda_v12  # ~2.5 GB
sudo rm -rf /usr/local/lib/ollama/cuda_v13  # ~1 GB
# Vulkan (~55 MB) optional
```

### Bereinigung: Dotfiles bare-repo

**Analyse großer Git-Objects:**
```bash
GIT_DIR=/home/klausd/.cfg git rev-list --all --objects | \
    awk '{print $1}' | xargs -I{} sh -c 'GIT_DIR=/home/klausd/.cfg git cat-file -s {}' 2>/dev/null | \
    sort -rh | head -20
```

**Typisch:** Alte Snap-Revisions, Download-Caches, oder Modelle wurden per `config add` eingecheckt. `git-filter-repo` oder `git gc --aggressive` nach Identifikation.

Siehe `references/disk-fresser-klausdig.md` für vollständige Session-Dokumentation.
