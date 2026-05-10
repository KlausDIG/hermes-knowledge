#!/usr/bin/env bash
# ============================================================
# DIN 5008 Google Workspace Setup
# Einrichtung der Google API Credentials
# ============================================================

set -euo pipefail

echo "═══════════════════════════════════════════════════════"
echo "  📋 DIN 5008 Google Workspace Setup"
echo "══════════════════════════════════════════════════════="
echo ""

# 1. Prüfen ob Credentials existieren
CRED_DIR="$HOME/.config/gcloud"
mkdir -p "$CRED_DIR"

if [ -f "$CRED_DIR/din5008-service-account.json" ]; then
    echo "✅ Credentials bereits vorhanden"
else
    echo "⚠️ Credentials fehlen!"
    echo ""
    echo "Schritte zum Einrichten:"
    echo ""
    echo "1. Öffne: https://console.cloud.google.com/"
    echo "2. Erstelle neues Projekt: 'din5008-automation'"
    echo "3. Aktiviere APIs: "
    echo "   - Google Docs API"
    echo "   - Google Sheets API"
    echo "   - Google Drive API"
    echo "4. Erstelle Service Account"
    echo "5. Generiere JSON Key"
    echo "6. Lade Key herunter"
    echo "7. Verschiebe nach: $CRED_DIR/din5008-service-account.json"
    echo ""
    echo "Alternativ: Teile mir den heruntergeladenen Key zu"
    echo "   (kopiere Inhalt in eine Datei auf dem Desktop)"
    echo ""
    exit 1
fi

# 2. Python-Pakete prüfen
echo "📦 Prüfe Python-Pakete..."
python3 -c "import googleapiclient" 2>/dev/null && echo "✅ google-api-python-client" || {
    echo "📦 Installiere Google API Client..."
    pip3 install --user google-auth google-auth-oauthlib \
        google-auth-httplib2 google-api-python-client gspread
}

# 3. Verzeichnisse erstellen
echo "📁 Erstelle Ausgabeverzeichnisse..."
mkdir -p "$HOME/Documents/Geschäftsbriefe"
mkdir -p "$HOME/Documents/Projektberichte"
mkdir -p "$HOME/Documents/Auswertungen"
mkdir -p "$HOME/Documents/Projektauswertungen"

# 4. Berechtigungen
echo "🔒 Setze Berechtigungen..."
chmod 600 "$CRED_DIR/din5008-service-account.json"
chmod +x "$HOME/.hermes/skills/productivity/din5008-google-workspace/scripts/"*.py

# 5. Test
echo ""
echo "🧪 Teste Setup..."
python3 "$HOME/.hermes/skills/productivity/din5008-google-workspace/scripts/brief-generator.py" > /tmp/din5008-test 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Brief-Generator funktioniert"
else
    echo "⚠️ Brief-Generator hat Fehler"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ✅ Setup abgeschlossen!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Schnellstart:"
echo "  Brief:    python3 ~/.hermes/skills/productivity/din5008-google-workspace/scripts/brief-generator.py"
echo "  Tabelle:  python3 ~/.hermes/skills/productivity/din5008-google-workspace/scripts/tabelle-generator.py"
echo ""
echo "Templates:"
echo "  $HOME/.hermes/skills/productivity/din5008-google-workspace/templates/"
echo ""
echo "Ausgabe:"
echo "  $HOME/Documents/Geschäftsbriefe/"
echo "  $HOME/Documents/Auswertungen/"
