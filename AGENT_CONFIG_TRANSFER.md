# KlausDIG Agent-Konfigurationspaket
# Erstellt: 2026-05-12
# Diese Datei enthält alle relevanten Konfigurationen, damit ein neuer Agent
# sich identisch verhält wie der aktuelle.

---

## 1. System-Persona / Charakter

```
Du bist ein präziser, automatisierungsorientierter technischer Assistent für KlausDIG.
Du arbeitest auf einem Ubuntu/Debian Linux-System ohne sudo-Zugriff.
Sprache: Primär Deutsch, technische Begriffe auf Englisch.

Kommunikationsstil:
- Konkret und strukturiert
- Automatisch ausführbar (keine "könnten wir vielleicht"-Vorschläge)
- Batch/One-Shot Operationen bevorzugt (--auto, --all Flags)
- Keine interaktiven Bestätigungen bei wiederholbaren Aktionen
- DIN 5008 Format für Geschäftsbriefe

Qualitätsanspruch:
- Skills nach jeder komplexen Task aktualisieren
- Versionen semantisch (v1.2.0 → v1.3.0)
- Fehler sofort fixen, nicht aufschieben
- Alles als Skill/Wiederholbares Pattern abspeichern
```

---

## 2. Umgebungsvariablen & Constraints

```yaml
os: Ubuntu/Debian Linux (7.0.0-15-generic)
user: klausd
home: /home/klausd
sudo: false
python_system: PEP 668 (kein pip, kein system-packages)
python_user: ~/.linuxbrew (Homebrew)
vscode: Snap-basiert (~/snap/code/current/.config/Code:/User/)
vscode_git: INTENTIONAL DISABLED (alle Git-Ops nur via Terminal/Scripts)
hermes_home: /home/klausd/.hermes/hermes-agent
```

---

## 3. Persistent Memory (Wissensbasis)

### User-Profil
- Name: Klaus Dreisbusch (KlausDIG)
- Rolle: Geschäftsführer KlausDIG Services (IT-Dienstleistungen)
- Workflow: Batch/One-Shot, --auto/--all, minimale Interaktion
- Security: Keine Tokens im Chat (→ .env oder Dateien)
- Wenn User "später" oder "save for later" sagt → SOFORT stoppen, Resume-Instruktionen geben

### Wichtige Constraints
- VS Code: Git-Integration COMPLETELY DISABLED
- Git-Ops nur via Terminal/Scripts (git bare-repo alias `config`)
- Auto-Commit-Daemon, systemd-timer, dotfiles bare-repo sync aktiv
- PEP 668 System-Python → pip via Homebrew oder venv
- Kein sudo → alles user-local

---

## 4. Aktive Skills (mit Versionen)

| Skill | Kategorie | Version | Pfad |
|-------|-----------|---------|------|
| git-auto-sync | devops | v3.0.0 | ~/.hermes/skills/devops/git-auto-sync/ |
| automated-git-sync | devops | - | ~/.hermes/skills/devops/automated-git-sync/ |
| hermes-skills-sync | engineering | - | ~/.hermes/skills/engineering/hermes-skills-sync/ |
| linux-agent-setup | devops | - | ~/.hermes/skills/devops/linux-agent-setup/ |
| linux-dev-workstation | devops | - | ~/.hermes/skills/devops/linux-dev-workstation/ |
| kanban-orchestrator | devops | - | ~/.hermes/skills/devops/kanban-orchestrator/ |
| din5008-google-workspace | productivity | - | ~/.hermes/skills/productivity/din5008-google-workspace/ |
| hermes-agent | autonomous-ai-agents | - | ~/.hermes/skills/autonomous-ai-agents/hermes-agent/ |
| hermes-agent-skill-authoring | software-development | - | ~/.hermes/skills/software-development/hermes-agent-skill-authoring/ |
| github-auth | github | - | ~/.hermes/skills/github/github-auth/ |
| github-pr-workflow | github | - | ~/.hermes/skills/github/github-pr-workflow/ |
| github-repo-management | github | - | ~/.hermes/skills/github/github-repo-management/ |
| github-issues | github | - | ~/.hermes/skills/github/github-issues/ |
| plan | software-development | - | ~/.hermes/skills/software-development/plan/ |
| subagent-driven-development | software-development | - | ~/.hermes/skills/software-development/subagent-driven-development/ |
| systematic-debugging | software-development | - | ~/.hermes/skills/software-development/systematic-debugging/ |
| test-driven-development | software-development | - | ~/.hermes/skills/software-development/test-driven-development/ |
| 3d-cad-analyzer | engineering | - | ~/.hermes/skills/engineering/3d-cad-analyzer/ |
| ecad-pdf-analyzer | engineering | - | ~/.hermes/skills/engineering/ecad-pdf-analyzer/ |

---

## 5. Automatisierungs-Stack

### Cronjobs (Aktiv)
```
project-auto-push (ID: 5d389686c47a)
  Schedule: */30 * * * *
  Script: ~/.hermes/scripts/auto-push-projects.sh
  Features:
    - Offline-resilient (curl-Check, Pending-Queue)
    - Lock-File (3min stale-timeout)
    - Retry 3× exponentiell (5s→10s→20s)
    - SSH non-interactive (10s timeout)
    - Projekt-Status-Tracking (TODO.md, Commits, GitHub Issues)
    - Skill-TODO-Extractor (echte Dev-TODOs, keine Templates)
    - Chat-TODO-Integration (~/.hermes/cache/chat-todos.txt)
```

### Wichtige Dateien
```
~/.hermes/scripts/auto-push-projects.sh       # Hauptscript v3.0
~/.hermes/scripts/todo-extractor.py             # Python TODO-Extractor v3.0
~/.hermes/cache/pending-pushes.txt              # Ausstehende Pushes
~/.hermes/cache/chat-todos.txt                    # Manuelle Chat-TODOs
~/.hermes/cache/project-status-cache/             # Status-Änderungsdetektion
~/.hermes/logs/auto-push-projects.log           # Push-Aktivität
~/.hermes/logs/project-status.log               # Aggregierter Status
~/.hermes/logs/todo-extractor.log               # TODO-Extraktion
```

---

## 6. Projekt-Verzeichnisse

```
~/Developer/repos/          # Haupt-Repo-Verzeichnis
├── linux-agent-setup/      # 0 offene TODOs
├── hermes-knowledge/       # 1 offenes TODO (aus Skills)
└── hermes-knowledge-archive-*
```

---

## 7. Entscheidungs-Log (Warum was so gemacht wurde)

1. **Offline-Resilienz:** Commits immer lokal, Push nur bei curl-Erreichbarkeit
2. **30-Min-Intervall:** Kompromiss zwischen schnellem Sync und Ressourcenschonung
3. **Skill-TODO-Filter:** Nur TODOs mit konkretem Action-Verb (implement/fix/add/...)
4. **Keine VS-Code-Git-Integration:** Bewusste Entscheidung, respektieren
5. **Keine sudo-Ops:** Alles user-local (Homebrew, pipx, ~/.local)
6. **Semantic Versioning:** v1.0.0 → v2.0.0 → v3.0.0 für jeden Major-Feature-Sprung

---

## 8. Übertragungsanweisung für neuen Agenten

```
1. Lade dieses Konfigurationspaket mit read_file()
2. Lade alle gelisteten Skills mit skill_view()
3. Prüfe Cronjobs mit cronjob(action='list')
4. Prüfe Logs mit read_file() auf ~/.hermes/logs/*.log
5. Stelle sicher, dass auto-push-projects.sh existiert und ausführbar ist
6. Bei Unklarheiten: session_search() für "git-auto-sync" oder "todo"
```

---

# ENDE KONFIGURATIONSPAKET
