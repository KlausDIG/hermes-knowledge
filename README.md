# 🧠 Hermes Knowledge Sync

Automatisierte Synchronisation von Hermes-Agent Skills, Memory, Cronjobs und Scripts mit GitHub.

## 📋 Übersicht

Dieses Repo wird alle 30 Minuten automatisch synchronisiert:
- **Skills** aus `~/.hermes/skills/`
- **Scripts** aus `~/Developer/scripts/`
- **Cronjobs** aus Hermes

Jeder Sync erzeugt:
- Einen Commit (`🤖 [SYNC] ...`)
- Ein Semantic Release Tag (`vMAJOR.MINOR.PATCH`)
- Einen Push zu GitHub

## ⚙️ Automatisierung

| Service | Intervall | Aufgabe |
|---------|-----------|---------|
| `hermes-knowledge-sync.timer` | Alle 30 Min | Hermes Knowledge Sync |
| `agent-autocommit.service` | Alle 30 Sek | Auto-Commit Repos |

## 🚀 Quick Start

```bash
# Manueller Sync
cd ~/Developer/repos/hermes-knowledge
python3 scripts/hermes-knowledge-sync.py

# Status
systemctl --user status hermes-knowledge-sync.timer
systemctl --user status agent-autocommit.service
```

## 🗂️ Struktur

```
hermes-knowledge/
├── README.md
├── skills/                # Alle Hermes Skills
├── scripts/               # Agent-Scripts
├── cronjobs/              # Exportierte Cronjobs
└── sync.log               # Letzte Syncs
```

## 🛠️ Agent-Einrichtung

→ Siehe [linux-agent-setup](https://github.com/KlausDIG/linux-agent-setup)

## 📧 Kontakt

- **Maintainer:** Project Autonomous Agent
- **GitHub:** [@KlausDIG](https://github.com/KlausDIG)
