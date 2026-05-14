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
  - browser-memory
related_skills:
  - linux-agent-setup
  - linux-dev-workstation
  - thin-client-nextcloud
  - agent-bootstrap
version: "1.0.0"
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

### Was NIEMALS entfernt werden darf
| Snap | Grund |
|------|-------|
| core / core20 / core22 / core24 | Snap-Grundsystem |
| snapd | Snap-Engine |
| rclone (stable) | Backup-Sync |
| code | VS Code: Editor |

### Commands
```bash
snap remove <name> --purge          # Ganzen Snap entfernen
snap remove <name> --revision=<rev>  # Nur alte Revision
```

## Automatisches Cleanup (Cronjob)

### Script: `~/bin/cleanup-safe.sh`
**Was es macht:**
1. Alte Hermes-Logs (>30 Tage)
2. Browser-/App-Caches (keine Configs!)
3. Alte Snap-Revisionen
4. Homebrew cleanup + autoremove
5. Papierkorb leeren
6. /tmp User-Dateien (>1 Tag)

**Schedule:** Sonntag 03:00 Uhr
**Ergebnis:** ~500 MB - 2 GB pro Woche

### Verifizierung nach Cleanup
```bash
df -h /
free -h
```

## Scripts-Referenz

| Script | Funktion | Sudo nötig? |
|--------|----------|-------------|
| `~/bin/setup-zram.sh` | ZRAM aktivieren | ✅ Ja |
| `~/bin/remove-old-swap.sh` | Altes Swap-File entfernen | ✅ Ja |
| `~/bin/cleanup-safe.sh` | Sicheres Aufräumen | ❌ Nein |
| `~/bin/thin-client.sh` | Cloud on-demand | ❌ Nein |

## Pitfalls

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
