#!/usr/bin/env bash
# ============================================================
# 🤖 Telegram Bot Setup für n8n + Hermes
# ============================================================

set -euo pipefail

echo "═══════════════════════════════════════════════════════"
echo "  🤖 Telegram Bot Setup"
echo "═══════════════════════════════════════════════════════"
echo ""

# --- Schritt 1: Bot bei @BotFather erstellen ---
echo "📱 Schritt 1: Bot bei @BotFather erstellen"
echo ""
echo "1. Öffne Telegram und suche nach @BotFather"
echo "2. Sende: /newbot"
echo "3. Gib einen Namen ein (z.B. 'Hermes Agent')"
echo "4. Gib einen Username ein (z.B. 'hermes_agent_bot')"
echo "5. Kopiere den Token (z.B.: 123456789:ABCdef...)"
echo ""
read -p "Token eingeben: " TOKEN

if [ -z "$TOKEN" ]; then
    echo "❌ Kein Token eingegeben"
    exit 1
fi

# --- Schritt 2: Chat ID herausfinden ---
echo ""
echo "📱 Schritt 2: Chat ID finden"
echo ""
echo "1. Sende @hermes_agent_bot eine Nachricht (irgendetwas)"
echo "2. Öffne im Browser:"
echo "   https://api.telegram.org/bot${TOKEN}/getUpdates"
echo "3. Suche nach 'chat': {'id': 123456789}"
echo "   Die Zahl ist deine Chat ID"
echo ""
read -p "Chat ID eingeben: " CHAT_ID

if [ -z "$CHAT_ID" ]; then
    echo "❌ Keine Chat ID eingegeben"
    exit 1
fi

# --- Schritt 3: Speichern ---
ENV_FILE="$HOME/n8n/.env"
mkdir -p "$HOME/n8n"

if [ -f "$ENV_FILE" ]; then
    # Alte Werte entfernen
    sed -i '/TELEGRAM_/d' "$ENV_FILE"
fi

cat >> "$ENV_FILE" <<EOF
TELEGRAM_BOT_TOKEN=$TOKEN
TELEGRAM_CHAT_ID=$CHAT_ID
EOF

echo "✅ Token + Chat ID in $ENV_FILE gespeichert"

# --- Schritt 4: n8n Config aktualisieren ---
echo ""
echo "🔧 Schritt 3: n8n Docker Compose aktualisieren"

COMPOSE="$HOME/n8n/compose.yml"
if [ -f "$COMPOSE" ]; then
    sed -i "s/\${TELEGRAM_BOT_TOKEN}/$TOKEN/g" "$COMPOSE" 2>/dev/null || true
    sed -i "s/\${TELEGRAM_CHAT_ID}/$CHAT_ID/g" "$COMPOSE" 2>/dev/null || true
    echo "✅ compose.yml aktualisiert"
else
    echo "⚠️ compose.yml nicht gefunden, erstelle es..."
fi

# --- Schritt 5: Test ---
echo ""
echo "📡 Schritt 4: Test-Nachricht senden..."
RESPONSE=$(curl -s "https://api.telegram.org/bot${TOKEN}/sendMessage" \
    -d "chat_id=${CHAT_ID}" \
    -d "text=✅ Hermes Agent verbunden!" \
    -d "parse_mode=Markdown" 2>/dev/null)

if echo "$RESPONSE" | grep -q '"ok":true'; then
    echo "✅ Test-Nachricht gesendet!"
else
    echo "⚠️ Test fehlgeschlagen:"
    echo "$RESPONSE" | head -2
fi

# --- Fertig ---
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ✅ Setup abgeschlossen!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Bot:     @$(echo $TOKEN | cut -d: -f1)"
echo "Chat:    $CHAT_ID"
echo ""
echo "Die Workflows können jetzt Telegram nutzen:"
echo "  - hermes-status-monitor"
echo "  - hermes-webhook-receiver"
echo ""
echo "n8n neu starten mit:"
echo "  systemctl --user restart n8n.service"
