#!/usr/bin/env bash
# ============================================================
# Nextcloud + rclone Setup
# Minimale lokale Speichernutzung durch Cloud-First
# ============================================================

set -euo pipefail

HOME="$HOME"
NEXTCLOUD_DIR="$HOME/Nextcloud"
RCLONE_CONF="$HOME/.config/rclone/rclone.conf"
CACHE_DIR="$HOME/.cache/rclone-nextcloud"

clear
echo "══════════════════════════════════════════════════════════"
echo "  ☁️  Nextcloud + rclone Setup"
echo "══════════════════════════════════════════════════════════"
echo ""
echo "Strategie: Cloud-First (Daten primär in Nextcloud)"
echo "Lokaler Cache: Nur für aktive Dateien (minimal)"
echo ""

# Prüfe rclone
if ! command -v rclone >/dev/null 2>&1; then
    echo "❌ rclone nicht installiert"
    echo "   Installiere: sudo snap install rclone"
    exit 1
fi

echo "✅ rclone gefunden: $(which rclone)"
echo ""

# Konfiguration
mkdir -p "$HOME/.config/rclone"
mkdir -p "$CACHE_DIR"

# Konfiguration abfragen (NICHT im Chat!)
echo "══════════════════════════════════════════════════════════"
echo "  NEXTCLOUD ZUGANGSDATEN"
echo "══════════════════════════════════════════════════════════"
echo ""
echo "Bitte gib folgende Daten ein (werden verschlüsselt gespeichert):"
echo ""

read -rp "Nextcloud URL (z.B. https://cloud.klausdig.de): " NEXTCLOUD_URL
read -rp "Benutzername: " NEXTCLOUD_USER
read -rsp "Passwort/App-Token: " NEXTCLOUD_PASS
echo ""
read -rp "Mount-Punkt [$NEXTCLOUD_DIR]: " MOUNT_POINT
MOUNT_POINT="${MOUNT_POINT:-$NEXTCLOUD_DIR}"

echo ""
echo "Konfiguriere rclone..."

# rclone config erstellen
cat > "$RCLONE_CONF" <<EOF
[nextcloud]
type = webdav
url = ${NEXTCLOUD_URL}/remote.php/dav/files/${NEXTCLOUD_USER}
vendor = nextcloud
user = ${NEXTCLOUD_USER}
pass = $(rclone obscure "$NEXTCLOUD_PASS")
EOF

chmod 600 "$RCLONE_CONF"
echo "✅ rclone config erstellt: $RCLONE_CONF"
echo "   (Passwort verschlüsselt gespeichert)"
echo ""

# Teste Verbindung
echo "🧪 Teste Verbindung..."
if rclone ls nextcloud: >/dev/null 2>&1; then
    echo "✅ Verbindung erfolgreich!"
    echo ""
    echo "Dateien in Nextcloud:"
    rclone lsd nextcloud: 2>/dev/null | head -5 || echo "   (Verzeichnis leer oder Root)"
else
    echo "⚠️ Verbindung fehlgeschlagen!"
    echo "   Prüfe URL, Benutzername und Passwort"
    exit 1
fi

echo ""
echo "══════════════════════════════════════════════════════════"
echo "  SYSTEMD SERVICE ERSTELLEN"
echo "══════════════════════════════════════════════════════════"
echo ""

mkdir -p "$HOME/.config/systemd/user"

cat > "$HOME/.config/systemd/user/nextcloud-mount.service" <<EOF
[Unit]
Description=Nextcloud rclone mount
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/snap/bin/rclone mount nextcloud: "$MOUNT_POINT" \\
    --vfs-cache-mode minimal \\
    --vfs-cache-max-size 100M \\
    --vfs-cache-max-age 1h \\
    --buffer-size 0 \\
    --dir-cache-time 5m \\
    --poll-interval 15s \\
    --log-level INFO \\
    --log-file /tmp/rclone-nextcloud.log
ExecStop=/bin/fusermount -u "$MOUNT_POINT"
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
EOF

echo "✅ Systemd Service erstellt"
echo ""

# Verzeichnisstruktur in Nextcloud anlegen
echo "══════════════════════════════════════════════════════════"
echo "  VERZEICHNISSTRUKTUR ANLEGEN"
echo "══════════════════════════════════════════════════════════"
echo ""

echo "Erstelle Verzeichnisse in Nextcloud..."
rclone mkdir "nextcloud:/Dokumente/DIN5008" 2>/dev/null || true
rclone mkdir "nextcloud:/Dokumente/Geschäftsbriefe" 2>/dev/null || true
rclone mkdir "nextcloud:/Dokumente/Auswertungen" 2>/dev/null || true
rclone mkdir "nextcloud:/Dokumente/Projekte" 2>/dev/null || true
rclone mkdir "nextcloud:/Backups/Dotfiles" 2>/dev/null || true
rclone mkdir "nextcloud:/Backups/Scripts" 2>/dev/null || true
rclone mkdir "nextcloud:/Entwicklung/Scripts" 2>/dev/null || true
rclone mkdir "nextcloud:/Entwicklung/Workflows" 2>/dev/null || true

echo "✅ Verzeichnisse angelegt"
echo ""

# Systemd aktivieren
echo "══════════════════════════════════════════════════════════"
echo "  AKTIVIERUNG"
echo "══════════════════════════════════════════════════════════"
echo ""

systemctl --user daemon-reload
systemctl --user enable nextcloud-mount.service

echo "✅ Service aktiviert"
echo ""
echo "══════════════════════════════════════════════════════════"
echo "  🎉 SETUP ABGESCHLOSSEN"
echo "══════════════════════════════════════════════════════════"
echo ""
echo "Nutzung:"
echo "  1. Mount starten:  systemctl --user start nextcloud-mount"
echo "  2. Mount prüfen:   ls $MOUNT_POINT"
echo "  3. Auto-Start:     systemctl --user enable nextcloud-mount"
echo ""
echo "Daten-Strategie (Cloud-First):"
echo "  • ~/Nextcloud/      → Gemountete Cloud (primärer Speicher)"
echo "  • ~/Documents/      → Symlink zu Nextcloud (optional)"
echo "  • Cache:            ~/.cache/rclone-nextcloud/ (max 100MB)"
echo ""
echo "Wichtige Befehle:"
echo "  rclone ls nextcloud:              → Dateien auflisten"
echo "  rclone sync lokaler/ nextcloud:/  → Sync zu Cloud"
echo "  rclone sync nextcloud:/ lokaler/  → Sync von Cloud"
echo "  rclone bisync nextcloud:/ ~/Nextcloud/  → Bidirektional"
echo ""
echo "Mount-Optionen (minimaler lokaler Speicher):"
echo "  --vfs-cache-mode minimal   → Nur aktuelle Dateien"
echo "  --vfs-cache-max-size 100M → Max 100MB Cache"
echo "  --vfs-cache-max-age 1h    → 1 Stunde Cache"
echo "  --buffer-size 0           → Kein RAM-Buffer"
echo ""
