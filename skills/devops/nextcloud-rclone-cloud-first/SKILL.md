---
name: nextcloud-rclone-cloud-first
description: |
  Nextcloud Integration mit rclone im Cloud-First-Modus.
  Daten werden primär in Nextcloud + GitHub gespeichert, lokal nur 
  minimale Cache-Nutzung (100MB). Monorepo-Sync, Auto-Backup,
  Thin-Client-Strategie für speicherarme Workstations.
  Bevorzugte Methode: rclone copy/sync statt FUSE-Mount (Snap-Limitationen).
toolsets:
  - terminal
  - file
version: "1.3.0"
category: devops
tags:
  - nextcloud
  - rclone
  - cloud-first
  - thin-client
  - backup
  - sync
  - monorepo
related_skills:
  - automated-git-sync
  - monorepo-project-workflow
  - hermes-skills-sync
---

# ☁️ Nextcloud + rclone Setup (Cloud-First)

## Übersicht

Dieser Skill richtet Nextcloud mit rclone ein, wobei Daten **primär in der Cloud** gespeichert werden.

**Strategie:**
- **Cloud = Primärer Speicher**: Alle Dokumente/Backups in Nextcloud
- **Lokal = Nur Cache**: Max 100MB, 1 Stunde Aufbewahrung
- **Symlinks**: `~/Documents` → Nextcloud, `~/Backups` → Nextcloud

**Empfohlene Methode:** Thin-Client via `rclone copy/sync` statt permanentes FUSE-Mount (siehe unten).

---

## Schnellstart

### 1. Voraussetzungen

```bash
# rclone installiert (Snap)
rclone version

# .env Datei erstellt
ls ~/.config/nextcloud/.env
```

### 2. .env Konfiguration

```bash
nano ~/.config/nextcloud/.env
```

**Inhalt:**
```bash
NEXTCLOUD_URL=https://cloud.dein-server.de
NEXTCLOUD_USER=dein-benutzername
NEXTCLOUD_PASS=dein-app-token
MOUNT_POINT=/home/klausd/Nextcloud
```

**App-Token erstellen:**
1. Nextcloud → Einstellungen → Sicherheit
2. "App-Passwort erstellen"
3. Name: "Hermes Agent"
4. Token kopieren

### 3. Setup ausführen

```bash
python3 ~/Developer/scripts/setup-nextcloud.py
```

Das Skript macht automatisch:
- ✅ rclone config (verschlüsselt)
- ✅ Nextcloud-Verzeichnisse anlegen
- ✅ Verbindung testen
- ✅ systemd Service erstellen
- ✅ Symlinks erstellen

### 4. Thin-Client nutzen (empfohlen)

```bash
# Datei on-demand laden
~/bin/thin-client.sh get Projects/hermes-klausi-hp/README.md

# Datei hochladen
~/bin/thin-client.sh put ~/Download/report.pdf Documents/

# Cloud-Inhalte auflisten
~/bin/thin-client.sh list Projects/

# Backup auslösen
~/bin/thin-client.sh sync
```

---

## Thin-Client Strategie (Empfohlen)

Da Snap-rclone **kein zuverlässiges FUSE-Mount** unterstützt (siehe Pitfalls), verwenden wir ein **on-demand Sync** Pattern:

| Pattern | Befehl | Nutzung |
|---------|--------|---------|
| **Get** | `thin-client.sh get <cloud-path>` | Datei kurzfristig lokal laden |
| **Put** | `thin-client.sh put <local> <cloud>` | Datei hochladen |
| **List** | `thin-client.sh list <prefix>` | Cloud-Inhalte browsen |
| **Drop** | `thin-client.sh drop <local-path>` | Lokale Kopie löschen (Schutz aktiv) |
| **Sync** | `thin-client.sh sync` | `neytcloud-backup.sh` ausführen |
| **Status** | `thin-client.sh status` | Cache + lokale Daten anzeigen |

**Vorteile:**
- Kein ständiger FUSE-Prozess nötig
- Keine Snap-Berechtigungsprobleme
- Nur benötigte Dateien liegen lokal
- Automatischer Schutz vor Löschen des Git-Repos

**Cache:** `~/.thin-cache/` — wird bei `get` befüllt, sonst leer.

---

## Verzeichnisstruktur in Nextcloud

```
Nextcloud/
├── Dokumente/
│   ├── DIN5008/
│   ├── Geschäftsbriefe/
│   ├── Auswertungen/
│   └── Projekte/
├── Backups/
│   ├── Dotfiles/
│   └── Scripts/
└── Entwicklung/
    ├── Scripts/
    └── Workflows/
```

---

## Lokale Symlinks

| Lokal | Zeigt auf |
|-------|-----------|
| `~/Documents` | `Nextcloud/Dokumente` |
| `~/Backups` | `Nextcloud/Backups` |
| `~/Developer-Cloud` | `Nextcloud/Entwicklung` |

**Wichtig:** `~/.cfg` (Dotfiles) bleibt **lokal**!

---

## Wichtige Befehle

```bash
# Mount verwalten (nur wenn rclone NICHT via Snap)
rclone mount neytcloud: ~/cloud \
    --vfs-cache-mode writes \
    --vfs-cache-max-size 1G \
    --daemon

# Dateien auflisten (Cloud)
rclone ls neytcloud:
rclone lsd neytcloud:/Dokumente

# Sync zu Cloud
rclone sync ~/Dokumente neytcloud:/Dokumente

# Sync von Cloud
rclone sync neytcloud:/Dokumente ~/Backup

# Bidirektional (vorsichtig!)
rclone bisync neytcloud:/Dokumente ~/Documents

# Mount-Optionen (minimaler Cache)
rclone mount neytcloud: ~/Nextcloud \
    --vfs-cache-mode minimal \
    --vfs-cache-max-size 100M \
    --vfs-cache-max-age 1h \
    --buffer-size 0
```

---

## Cache-Einstellungen (Cloud-First)

| Option | Wert | Bedeutung |
|--------|------|-----------|
| `--vfs-cache-mode` | minimal | Nur aktive Dateien |
| `--vfs-cache-max-size` | 100M | Max 100MB Cache |
| `--vfs-cache-max-age` | 1h | 1 Stunde Aufbewahrung |
| `--buffer-size` | 0 | Kein RAM-Buffer |
| `--dir-cache-time` | 5m | Verzeichnis-Cache 5min |

**Gesamt lokaler Speicher:** ~100MB + kleiner Overhead

---

## Pitfalls

### Snap-rclone kann kein FUSE-Mount

**Symptom:** `CRITICAL: Fatal error: daemon exited with error code 1`

**Ursache:** `--daemon` und `--log-file` funktionieren im Snap-Sandkasten nicht.

**Fix:** Thin-Client verwenden (siehe oben) statt FUSE-Mount.

### Config muss im Snap-Home liegen

**Symptom:** `Config file not found - using defaults`

**Fix:** Config nach `~/snap/rclone/current/.config/rclone/` kopieren.

### `--log-file` blockiert durch Snap

**Symptom:** `Failed to open log file: permission denied`

**Fix:** `2>&1 | tee -a "$LOGFILE"` statt `--log-file`.

### Push rejected (non-fast-forward) bei GitHub-Sync

**Symptom:** `error: failed to push some refs`

**Fix:** Vor jedem Push erst pullen:
```bash
git pull origin main --rebase
```

---

## Dateien

| Datei | Zweck |
|-------|-------|
| `~/.config/nextcloud/.env` | Zugangsdaten (sicher) |
| `~/.config/rclone/rclone.conf` | rclone Config (verschlüsselt) |
| `~/snap/rclone/current/.config/rclone/rclone.conf` | Snap-rclone Config (Kopie) |
| `~/.config/systemd/user/nextcloud-mount.service` | Auto-Mount |
| `~/bin/thin-client.sh` | Thin-Client Manager |
| `~/bin/mount-cloud.sh` | FUSE-Mount Script (experimentell) |
| `~/Developer/scripts/setup-nextcloud.py` | Setup-Skript |

---

## Troubleshooting

```bash
# Verbindung testen
rclone ls neytcloud: --verbose

# Logs ansehen
tail -f /tmp/rclone-nextcloud.log

# Config prüfen (ohne Passwörter)
cat ~/.config/rclone/rclone.conf | grep -v pass

# Cache leeren
rm -rf ~/.cache/rclone-nextcloud/*

# Re-Mount
systemctl --user restart nextcloud-mount
```

---

## Sicherheit

- ✅ Passwort in rclone.conf **verschlüsselt**
- ✅ .env Datei mit **Berechtigung 600**
- ✅ Keine Credentials im Chat
- ✅ App-Token (nicht Hauptpasswort)
- ✅ Dotfiles bleiben lokal
- ✅ `thin-client.sh drop` blockiert Löschen von Git-Repos

## Integration mit DIN 5008 Skill

Sobald Nextcloud läuft:
```bash
# DIN 5008 Dokumente direkt in Cloud speichern
din5008 brief
cp ~/Documents/DIN5008_Output/Brief*.html ~/Documents/DIN5008/

# Oder: rclone sync
rclone sync ~/Documents/DIN5008_Output neytcloud:/Dokumente/DIN5008
```

## Snap-Isolation und Workarounds

Siehe `references/snap-isolation-workaround.md` für Details:
- Config muss unter `~/snap/rclone/current/.config/rclone/` liegen
- `--log-file` funktioniert nicht unter Snap → `tee` verwenden
- `--daemon` funktioniert nicht unter Snap → Thin-Client verwenden
- Symlinks können blockiert werden

## References

- `references/snap-isolation-workaround.md` — rclone Snap-Constraints
- `references/thin-client-strategy.md` — Thin-Client Pattern Details
- `references/deferred-setup-pattern.md` — "save for later" Workflow
- `monorepo-project-workflow` Skill — Backup-Sync Integration

## Version

- **Skill:** nextcloud-rclone-cloud-first v1.3.0
- **Rclone:** (via Snap)
- **Systemd:** User-Service