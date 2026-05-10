#!/usr/bin/env bash
# ============================================================
# n8n Event Trigger
# Sendet Events von Hermes an n8n Webhooks
# ============================================================

set -euo pipefail

N8N_URL="${N8N_URL:-http://localhost:5678}"
WEBHOOK_PATH="${WEBHOOK_PATH:-hermes-events}"

# Hilfe
if [ ${#@} -eq 0 ]; then
    echo "Usage: $(basename $0) <event> [data]"
    echo ""
    echo "Events:"
    echo "  git-push    Git-Commit gepusht"
    echo "  sync-done   Hermes Sync abgeschlossen"
    echo "  error       Fehler aufgetreten"
    echo ""
    echo "Beispiele:"
    echo "  $(basename $0) git-push '{\"repo\":\"dotfiles\",\"count\":3}'"
    echo "  $(basename $0) sync-done"
    exit 0
fi

EVENT="$1"
DATA="${2:-{}}"
AUTHOR=$(git config user.name 2>/dev/null || echo "$(whoami)")
REPO=$(git -C $(pwd) remote get-url origin 2>/dev/null | sed 's/.*\///;s/\.git$//' || echo "unknown")
BRANCH=$(git -C $(pwd) branch --show-current 2>/dev/null || echo "main")

# Payload erstagen
PAYLOAD=$(cat <<EOF
{
  "event": "$EVENT",
  "timestamp": "$(date -Iseconds)",
  "author": "$AUTHOR",
  "repo": "$REPO",
  "branch": "$BRANCH",
  "data": $DATA
}
EOF
)

# An n8n senden
echo "📡 Sende '$EVENT' an n8n..."
RESPONSE=$(curl -s -X POST "$N8N_URL/webhook/$WEBHOOK_PATH" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  -w "\n%{http_code}" \
  --max-time 10 2>/dev/null || echo -e "\n000")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Event empfangen"
else
    echo "⚠️ HTTP $HTTP_CODE - n8n nicht erreichbar oder falsch konfiguriert"
    echo "   Prüfe: $N8N_URL/webhook/$WEBHOOK_PATH"
fi
