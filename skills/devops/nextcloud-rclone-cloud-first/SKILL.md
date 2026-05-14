---
name: nextcloud-rclone-cloud-first
description: |
  Nextcloud Integration mit rclone im Cloud-First-Modus.
  Daten werden primär in Nextcloud gespeichert, lokal nur 
  minimale Cache-Nutzung (100MB). Automatisches Mounting 
  via systemd Service.
toolsets:
  - terminal
  - file
version: "1.1.0"
category: devops
---

# ☁️ Nextcloud + rclone Setup (Cloud-First)

## Übersicht

Dieser Skill richtet Nextcloud mit rclone ein, wobei Daten **primär in der Cloud** gespeichert werden.

**Strategie:**
- **Cloud = Primärer Speicher**: Alle Dokumente/Backups in Nextcloud
- **Lokal = Nur Cache**: Max 100MB, 1 Stunde Aufbewahrung
- **Symlinks**: `~/Documents` → Nextcloud, `~/Backups` → Nextcloud

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

### 4. Mount starten

```bash
systemctl --user start nextcloud-mount
systemctl --user status nextcloud-mount
```

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
# Mount verwalten
systemctl --user start nextcloud-mount
systemctl --user stop nextcloud-mount
systemctl --user status nextcloud-mount

# Dateien auflisten (Cloud)
rclone ls nextcloud:
rclone lsd nextcloud:/Dokumente

# Sync zu Cloud
rclone sync ~/Dokumente nextcloud:/Dokumente

# Sync von Cloud
rclone sync nextcloud:/Dokumente ~/Backup

# Bidirektional (vorsichtig!)
rclone bisync nextcloud:/Dokumente ~/Documents

# Mount-Optionen (minimaler Cache)
rclone mount nextcloud: ~/Nextcloud \
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

## Dateien

| Datei | Zweck |
|-------|-------|
| `~/.config/nextcloud/.env` | Zugangsdaten (sicher) |
| `~/.config/rclone/rclone.conf` | rclone Config (verschlüsselt) |
| `~/.config/systemd/user/nextcloud-mount.service` | Auto-Mount |
| `~/Developer/scripts/setup-nextcloud.py` | Setup-Skript |
| `~/Developer/scripts/setup-nextcloud.sh` | Alternative (interaktiv) |

---

## Troubleshooting

```bash
# Verbindung testen
rclone ls nextcloud: --verbose

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

## Sicherheit

- ✅ Passwort in rclone.conf **verschlüsselt**
- ✅ .env Datei mit **Berechtigung 600**
- ✅ Keine Credentials im Chat
- ✅ App-Token (nicht Hauptpasswort)
- ✅ Dotfiles bleiben lokal

## Integration mit DIN 5008 Skill

Sobald Nextcloud läuft:
```bash
# DIN 5008 Dokumente direkt in Cloud speichern
din5008 brief
cp ~/Documents/DIN5008_Output/Brief*.html ~/Documents/DIN5008/

# Oder: rclone sync
rclone sync ~/Documents/DIN5008_Output nextcloud:/Dokumente/DIN5008
```

## Snap-Isolation und Workarounds

Siehe `references/snap-isolation-workaround.md` für Details:
- Config muss unter `~/snap/rclone/current/.config/rclone/` liegen
- `--log-file` funktioniert nicht unter Snap → `tee` verwenden
- Symlinks können blockiert werden

## References

- `references/deferred-setup-pattern.md` — "save for later" Workflow
- `references/snap-isolation-workaround.md` — rclone Snap-Constraints
- `monorepo-project-workflow` Skill — Backup-Sync Integration

## Version

- **Skill:** nextcloud-rclone-cloud-first v1.0.0
- **Rclone:** (via Snap)
- **Systemd:** User-Service
- **Rclone:** (via Snap)
- **Systemd:** User-Service
