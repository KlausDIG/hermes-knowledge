---
name: n8n-workflows
description: |
  Erstelle, deploye und debugge n8n-Workflows – Node-basierte Automation für Daten, APIs und Benachrichtigungen.
  Unterstützung für Docker-Selfhosting, Webhook-Trigger, API-Integration, Error-Handling und Best Practices.
category: devops
version: 1.0.0
---

# n8n Workflows

## Überblick

n8n ("nodenation") ist ein Open-Source Workflow-Automation-Tool mit Node-basiertem Editor.

### Einsatzgebiete
- **API-Integration**: Daten zwischen Diensten synchronisieren
- **Datentransformation**: JSON-Filter, Mapping, Grouping
- **Benachrichtigungen**: Slack, Telegram, Email
- **Scheduled Tasks**: Cron-basierte Automation
- **Webhook-Empfang**: Externe Events verarbeiten
- **AI-Integration**: LLM-Chains, RAG, Datenbank-Queries

---

## Installation

### Docker (empfohlen)
```bash
# Docker Compose vorbereiten
mkdir -p ~/n8n && cd ~/n8n

# compose.yml
cat > compose.yml <<'EOF'
services:
  n8n:
    image: n8nio/n8n:latest
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - NODE_ENV=production
      - WEBHOOK_URL=http://localhost:5678/
      - GENERIC_TIMEZONE=Europe/Berlin
    volumes:
      - ~/.n8n:/home/node/.n8n
    networks:
      - n8n-network

  # Optional: PostgreSQL für Produktion
  postgres:
    image: postgres:16-alpine
    restart: always
    environment:
      - POSTGRES_USER=n8n
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=n8n
    volumes:
      - n8n-postgres:/var/lib/postgresql/data
    networks:
      - n8n-network

volumes:
  n8n-postgres:

networks:
  n8n-network:
    driver: bridge
EOF

# .env erstellen
echo "N8N_PASSWORD=dein_sicheres_passwort" > .env
echo "DB_PASSWORD=dein_db_passwort" >> .env

# Starten
docker compose up -d
```

### npm (entwicklung)
```bash
# Node.js 18+ benötigt
npm install n8n -g
n8n start
```

---

## Webhook-Trigger

### Aktivierung
```bash
# Webhook-URL von n8n bekommen (im Workflow Editor)
POST http://localhost:5678/webhook/WORKFLOW-ID
```

### n8n → Hermes Integration
```json
{
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "hermes-trigger",
        "responseMode": "responseNode"
      },
      "name": "Hermes Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [250, 300]
    }
  ]
}
```

### Hermes Cronjob → n8n Webhook
```bash
# Cronjob in Hermes, der n8n triggert
curl -X POST http://localhost:5678/webhook/daily-sync \
  -H "Content-Type: application/json" \
  -d '{"source": "hermes", "job": "daily-sync"}'
```

---

## Node-Kategorien

| Kategorie | Beispiel-Nodes | Nutzen |
|-----------|---------------|--------|
| **Trigger** | Webhook, Schedule, Manual | Workflow starten |
| **App** | Slack, Telegram, GitHub, Notion | Dienste ansteuern |
| **Data** | Set, Code, Function, HTTP Request | Daten transformieren |
| **Logic** | IF, Switch, Merge, Wait | Kontrollfluss |
| **AI** | OpenAI, Pinecone, Vector Store | LLM-Integration |
| **Files** | Read Binary, Write Binary, FTP | Datei-Handling |

---

## Best Practices

### 1. Error-Handling
```json
{
  "nodes": [
    {
      "name": "Try API Call",
      "type": "n8n-nodes-base.httpRequest",
      "continueOnFail": true
    },
    {
      "name": "IF Success",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "options": {
            "caseSensitive": true,
            "leftValue": "",
            "typeValidation": "strict"
          },
          "conditions": [
            {
              "id": "check-error",
              "leftValue": "={{ $json.error }}",
              "rightValue": "",
              "operator": {
                "type": "exists",
                "operation": "notExists"
              }
            }
          ]
        }
      }
    }
  ]
}
```

### 2. Secrets/Variablen
```bash
# In Docker Compose
environment:
  - TELEGRAM_BOT_TOKEN=${TELEGRAM_TOKEN}
  - OPENAI_API_KEY=${OPENAI_KEY}

# In n8n: Verwendung
{{ $env.TELEGRAM_BOT_TOKEN }}
```

### 3. Expression Syntax
```javascript
// Daten aus vorheriger Node
{{ $json.data.field }}

// Array-Operationen
{{ $json.items.map(i => i.name).join(", ") }}

// Bedingungen
{{ $json.status === "success" ? "✅" : "❌" }}

// Datum
{{ new Date().toISOString() }}

// String-Manipulation
{{ $json.title.toUpperCase().trim() }}
```

---

## Wartung

### Backup
```bash
# Workflows exportieren (JSON)
docker exec n8n-n8n-1 n8n export:workflow --all --output=/tmp/workflows.json

# Credentials exportieren
docker exec n8n-n8n-1 n8n export:credentials --all --output=/tmp/credentials.json

# Volumes sichern
tar -czf n8n-backup-$(date +%Y%m%d).tar.gz ~/.n8n
```

### Logs
```bash
# Docker Logs
docker logs -f n8n-n8n-1

# N8n CLI Logs
n8n logstream
```

---

## Integration mit Hermes

### 1. n8n startet Hermes Cronjob
```bash
# n8n HTTP Request Node → Hermes Webhook
POST http://hermes:8080/api/webhooks/daily-sync
```

### 2. Hermes startet n8n Workflow
```bash
# Hermes Script
result=$(curl -s -X POST http://localhost:5678/webhook/my-workflow \
  -H "Content-Type: application/json" \
  -d '{"data": "from_hermes"}')
echo "n8n Response: $result"
```

### 3. Bidirektional
- Hermes → n8n: HTTP Request Node
- n8n → Hermes: Webhook Node

---

## Troubleshooting

| Problem | Ursache | Lösung |
|---------|---------|--------|
| Webhook nicht erreichbar | Port forwarding | `-p 5678:5678` prüfen |
| Auth fehlgeschlagen | Basic Auth falsch | `.env` prüfen |
| Credentials nicht gefunden | Scope falsch | "Owner" statt "User" |
| Execution hängt | Timeout | "Options" → "Timeout" setzen |
| Daten nicht verarbeitet | JSON falsch | Expression-Tester nutzen |

---

## Resources

- **n8n Docs**: https://docs.n8n.io/
- **Community**: https://community.n8n.io/
- **Node-Reference**: https://docs.n8n.io/integrations/builtin/
- **Workflow-Templates**: ~/Developer/repos/n8n-templates/
