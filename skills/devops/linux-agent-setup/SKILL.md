---
name: linux-agent-setup
description: |
  Vollständige Einrichtung eines autonomen Agent-Entwicklungsumfeldes auf Linux (Ubuntu/Debian).
  Beinhaltet Homebrew, Rust, Node, Shell-Config, VS Code: (snap-aware), Dotfiles Bare-Repo Backup,
  Auto-Commit Daemon, Hermes Knowledge Sync, systemd-Services, Cronjobs.
  
  Architecture: Git bare-repo (~/.cfg) for dotfiles, no symlinks.
  Terminal constraint: Hermedocs fail in TTY-less env; use write_file or execute_code.
  
trigger:
  - "einrichten"
  - "setup agent"
  - "neue umgebung"
  - "linux setup"
  - "dev environment"
  - "installiere tools"
  - "agent config"
  - "dotfiles backup"
  - "token sicher"
  - "multi-remote"
requirements:
  - Linux x86_64
  - bash (oder zsh, aber bash zuerst konfigurieren)
  - Internetverbindung
  - GitHub CLI Token (optional, für gh auth login)
  - GitLab Token (optional, für Mirror)
---

## 🚨 Token-Sicherheit: KRITISCH

**DIE WICHTIGSTE REGEL:** GitHub-Personal Access Tokens **NIEMALS im Chat/Log/Shell-History speichern!**

```bash
# ✅ RICHTIG – Token wird in Keyring gespeichert, nie im Filesystem lesbar:
echo "ghp_DEIN_TOKEN" | gh auth login --with-token --hostname github.com

# ❌ FALSCH – Token landet in ~/.bash_history und Chat-Logs:
# gh auth login --with-token  # ← Typen im Chat = kompromittiert
```

**Wenn ein Token gepostet wurde:**
1. Sofort bei https://github.com/settings/tokens widerrufen
2. Neuen erstellen (Scopes: `repo`, `workflow`, `read:org`)
3. `history -c` im Terminal ausführen

---

# linux-agent-setup

## Überblick

Dieser Skill richtet eine komplette, portable Entwicklungsumgebung für einen autonomen AI-Agenten auf Linux ein. Die Einrichtung ist **user-lokal** (kein sudo erforderlich) und lauffähig auf Ubuntu/Debian.

## CRITICAL: Shell-Config erstellen (Schritt 0)

**WICHTIGSTE REGEL:** Erstelle die `.bashrc`-Config **BEvor** du zsh installieren versuchst (das erfordert `sudo`!).
Falls zsh nicht installiert ist → konfiguriere `bash` erst, danach optional zsh.

**NIE `cat <<EOF` für `.bashrc` verwenden!** Hermes' Terminal-Tool blockiert Heredoc-Syntax. Stattdessen Python `write_file` oder `execute_code` nutzen.

```python
# ✅ RICHTIG:
write_file(path="~/.bashrc", content="...", mode="append")

# ✅ AUCH RICHTIG:
execute_code(code="""
with open('/home/klausd/.bashrc', 'a') as f:
    f.write('# ===== Config =====\\n')
""")

# ❌ FALSCH – wird blockiert:
# cat >> ~/.bashrc <<'EOF'
# ...config...
# EOF
```

```bash
git config --global user.name "Project Autonomous Agent"
git config --global user.email "agent@local.local"
git config --global init.defaultBranch main
```

## Schritt 3: Dotfiles Bare-Repo

**Nur git benötigt – kein Ansible/Stow/Symlinks**

Erstelle ein Git bare-repo in `~/.cfg`, um das gesamte Home-Directory versioniert zu halten. Der Alias `config` (statt `git`) wird in der Shell definiert. Siehe `references/dotfiles-bare-repo.md` für die komplette Architektur.

**Schnell-Setup:**
```bash
git init --bare $HOME/.cfg
/usr/bin/git --git-dir=$HOME/.cfg --work-tree=$HOME config --local status.showUntrackedFiles no
/usr/bin/git --git-dir=$HOME/.cfg --work-tree=$HOME config --local core.excludesFile $HOME/.gitignore_dotfiles
```

**Kritisch: `.gitignore_dotfiles` vor dem ersten Commit erstellen** (Secrets ausschliessen – Template in `references/dotfiles-bare-repo.md`).

## Schritt 4: Homebrew (Linuxbrew, user-lokal)

```bash
# Nur wenn nicht vorhanden
git clone --depth=1 https://github.com/Homebrew/brew ~/.linuxbrew
eval "$(~/.linuxbrew/bin/brew shellenv)"
```

## Brew Packages (Batch)

```bash
eval "$(~/.linuxbrew/bin/brew shellenv)"

# Core (garantiert verfügbar)
brew install git node jq htop tree ripgrep fd fzf tldr bat eza tmux wget curl pandoc

# Shell-Upgrades
brew install zoxide starship duf gdu lazygit neovim thefuck

# Node Managers
brew install fnm pnpm volta yarn

# Languages
brew install go pyenv rbenv jenv pipx poetry

# DevOps/Kubernetes
brew install kubectl helm ansible lazydocker
```

**AUF LINUXBREW NICHT VERFÜGBAR:**
- `rustup` → via rustup.rs installieren (siehe Schritt 4)
- `terraform` → via HashiCorp APT oder tfenv
- `bun` → via `npm install -g bun`
- `deno` → via `npm install -g deno`

## Schritt 4: Rust (NICHT via Brew auf Linux)

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source ~/.cargo/env
rustup default stable
```

## Schritt 5: Shell-Config (~/.bashrc oder ~/.zshrc)

```bash
# ===== Project Agent Config (Linux) =====

# Homebrew (USER-LOCAL)
eval "$(/home/USERNAME/.linuxbrew/bin/brew shellenv)"

# zoxide
if command -v zoxide > /dev/null 2>&1; then
  eval "$(zoxide init bash)"
  alias cd=z
fi

# starship
if command -v starship > /dev/null 2>&1; then
  eval "$(starship init bash)"
fi

# fnm Node Manager
export PATH="/home/USERNAME/.local/share/fnm:$PATH"
if command -v fnm > /dev/null 2>&1; then
  eval "$(fnm env --use-on-cd)"
fi

# Node + pnpm + bun + deno
export PNPM_HOME="$HOME/.local/share/pnpm"
export PATH="$PNPM_HOME:$PATH"
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"
export DENO_INSTALL="$HOME/.deno"
export PATH="$DENO_INSTALL/bin:$PATH"

# Go
export PATH="/home/USERNAME/.linuxbrew/opt/go/bin:$PATH"
export GOPATH="$HOME/go"
export PATH="$GOPATH/bin:$PATH"

# Rust
export CARGO_HOME="$HOME/.cargo"
export PATH="$CARGO_HOME/bin:$PATH"

# pyenv
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
if command -v pyenv > /dev/null 2>&1; then
  eval "$(pyenv init - bash)"
fi

# rbenv
if command -v rbenv > /dev/null 2>&1; then
  eval "$(rbenv init - bash)"
fi

# pipx + local bin
export PATH="$HOME/.local/bin:$PATH"

# Kubernetes
if command -v kubectl > /dev/null 2>&1; then
  source <(kubectl completion bash) 2>/dev/null
  alias k=kubectl
fi

# Aliases
if command -v eza > /dev/null 2>&1; then
  alias ls=eza
  alias ll="eza -la"
else
  alias ll="ls -la"
fi
if command -v bat > /dev/null 2>&1; then alias cat=bat; fi
if command -v lazygit > /dev/null 2>&1; then alias lg=lazygit; fi
if command -v fzf > /dev/null 2>&1; then alias f=fzf; fi
if command -v thefuck > /dev/null 2>&1; then eval "$(thefuck --alias)"; fi

# ===== End Agent Config =====
```

**WICHTIG:** `USERNAME` durch den tatsächlichen Linux-Username ersetzen!

## Schritt 3.5: Brew – NICHT als Batch installieren

Linuxbrew auf x64 hat ein **kritisches Problem**: `cyrus-sasl` failt mit GCC-Compile-Fehlern (siehe `references/linux-brew-pitfalls.md`).
Wenn du `brew install tldr gh pandoc starship ...` als Batch aufrufst, bricht das erste failende Paket die **gesamte Installation** ab.

**Lösung: Einzeln installieren mit Continue**
```bash
eval "$(~/.linuxbrew/bin/brew shellenv)"

# Core – unabhängig (kein cyrus-sasl)
for pkg in eza bat fd fzf htop tree jq tmux zoxide duf lazygit neovim; do
  brew install "$pkg" 2>&1 | grep -E "installed|already|Error"
done

# Node Managers
for pkg in fnm pnpm volta yarn; do
  brew install "$pkg" 2>&1 | grep -E "installed|already|Error"
done

# Languages – unabhängig
for pkg in go pyenv rbenv jenv pipx poetry; do
  brew install "$pkg" 2>&1 | grep -E "installed|already|Error"
done

# DevOps – unabhängig
for pkg in kubectl helm ansible lazydocker; do
  brew install "$pkg" 2>&1 | grep -E "installed|already|Error"
done

# Diese FAILEN via Brew auf Linux (müssen separat):
# starship → curl -sS https://starship.rs/install.sh | sh -s -- -y (nach ~/.local/bin)
# tldr     → npm install -g tldr
# gh       → curl Release-Binary nach ~/.local/bin
# rustup   → curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
# pandoc   → via apt (sudo) oder Release-Binary
```

## Schritt 8: VS Code: Config (Snap-Aware)

**Snap-Installation** nutzt `~/snap/code/current/.config/Code:/User/`, NICHT `~/.config/Code:/User/`.

```bash
mkdir -p ~/snap/code/current/.config/Code:/User
```

**Settings:** Siehe `templates/vscode-settings.json` für die komplette Konfiguration.

**Git-Strategie:** Nutzer will Git-Anzeige (Branch, Status, Diff) aber **keinen Auto-Sync**.
```json
{
  "git.enabled": true,           // Git-Anzeige aktiv
  "git.autofetch": false,        // Kein Auto-Pull
  "git.confirmSync": true,        // Bestätigung vor Push
  "git.openRepositoryInParentFolders": "always"
}
```

**Git ist Terminal-Tool – VS Code: macht keinen Auto-Push**

**Erstellen via `write_file` (Heredocs fail in TTY-less env):**
```bash
# ❌ NIE so:
# cat > ~/snap/code/current/.config/Code:/User/settings.json <<'EOF'
# {...}
# EOF

# ✅ Immer so (Python oder write_file):
# write_file(path="~/snap/code/current/.config/Code:/User/settings.json", content="{...}")
```

**Extensions installieren (sequentiell wegen Locking):**
```bash
extensions=(
  "eamodio.gitlens" "github.vscode-pull-request-github"
  "github.copilot" "github.copilot-chat"
  "esbenp.prettier-vscode" "dbaeumer.vscode-eslint"
  "ms-python.python" "ms-python.black-formatter"
  "ms-vscode-remote.remote-ssh" "ms-vscode-remote.remote-containers"
  "bradlc.vscode-tailwindcss" "formulahendry.auto-rename-tag"
  "christian-kohler.npm-intellisense" "eg2.vscode-npm-script"
  "naumovs.color-highlight" "pkief.material-icon-theme"
  "editorconfig.editorconfig" "aaron-bond.better-comments"
  "wix.vscode-import-cost" "wayou.vscode-todo-highlight"
  "shd101wyy.markdown-preview-enhanced" "streetsidesoftware.code-spell-checker"
  "gruntfuggly.todo-tree" "yzhang.markdown-all-in-one"
  "rangav.vscode-thunder-client" "github.copilot-workspace"
  "visualstudioexptteam.vscodeintellicode" "christian-kohler.path-intellisense"
  "ms-vscode.vscode-github-issue-notebooks" "ritwickdey.liveserver"
)

for ext in "${extensions[@]}"; do
  code --install-extension "$ext" --force 2>&1 | grep -E "installed|failed|already"
  sleep 1
done
```

## Schritt 7: GitHub / GitLab CLI Auth (SICHER!)

**TOKEN NIEMALS IM CHAT POSTEN.**
Wenn in der Session ein Token gepostet wird:
1. Sofort bei GitHub/GitLab widerrufen
2. Neuen generieren
3. `history -c` im Terminal
4. `gh auth logout` + neu einloggen

```bash
# ✅ RICHTIG – Keyring-Speicherung, nie im History:
echo "ghp_DEIN_TOKEN" | gh auth login --with-token --hostname github.com && history -c

gh auth setup-git --hostname github.com
```

**GitLab-Mirror (optional, Backup):**
```bash
# GitLab personal access token: Scopes api, write_repository
# glab CLI installieren: brew install glab oder Release-Binary
echo "glpat-TOKEN" | glab auth login --token --stdin && history -c
glab repo create dotfiles --public --description "Backup"
config remote add gitlab https://gitlab.com/USERNAME/dotfiles.git
config push gitlab main --tags
```

## Schritt 8: Auto-Commit Daemon

### Python-Skript
Speichern als `~/Developer/scripts/auto-commit-daemon.py`:

```python
#!/usr/bin/env python3
import os, subprocess, time
from pathlib import Path
from datetime import datetime

REPOS_DIR = Path.home() / "Developer" / "repos"
LOG_FILE = Path("/tmp/agent-daemon.log")
IGNORE = [".git","node_modules",".next","dist","build",".DS_Store","pycache"]
COMMIT_PREFIX = "🤖 [AUTO]"

class RepoHandler:
    def __init__(self, repo):
        self.repo = repo
        self.last = 0

    def check(self):
        if time.time() - self.last < 5:
            return
        self.last = time.time()
        time.sleep(2)
        os.chdir(self.repo)
        status = subprocess.run(["git","status","--porcelain"], capture_output=True, text=True).stdout
        if not status.strip():
            return
        subprocess.run(["git","add","-A"], check=False, capture_output=True)
        msg = f"{COMMIT_PREFIX} Agent auto-commit @ {datetime.now():%Y-%m-%d %H:%M:%S}"
        subprocess.run(["git","commit","-m",msg], capture_output=True)
        subprocess.run(["git","push","origin","HEAD"], capture_output=True)

def scan_repos():
    if not REPOS_DIR.exists():
        return []
    return [r for r in REPOS_DIR.iterdir() if r.is_dir() and (r / ".git").exists()]

def main():
    handlers = {str(r): RepoHandler(r) for r in scan_repos()}
    while True:
        time.sleep(30)
        current = scan_repos()
        for r in current:
            if str(r) not in handlers:
                handlers[str(r)] = RepoHandler(r)
            handlers[str(r)].check()

if __name__ == "__main__":
    main()
```

### systemd User-Service
Speichern als `~/.config/systemd/user/agent-autocommit.service`:

```ini
[Unit]
Description=Project Auto-Commit Daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/USERNAME/Developer/scripts/auto-commit-daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

**Aktivieren:**
```bash
systemctl --user daemon-reload
systemctl --user enable agent-autocommit.service
systemctl --user start agent-autocommit.service
systemctl --user status agent-autocommit.service
```

## Schritt 9: Hermes Cronjobs

| Name | Schedule | Zweck |
|------|----------|-------|
| daily-sync | 0 9 * * * | System-Updates, brew outdated, df -h |
| skill-discovery | 0 10 * * * | Neue Tools/Skills recherchieren |
| self-update | 0 11 * * * | Config-Updates, Refactorings |

## Schritt 10: Verzeichnisstruktur

```bash
mkdir -p ~/Documents/ProjectJournals/{daily,weekly,lessons-learned,system-health,skill-discovery}
mkdir -p ~/Developer/{scripts,repos}
```

## Bekannte Probleme & Lösungen

| Problem | Ursache | Lösung |
|---------|--------|--------|
| cyrus-sasl Compile-Fehler | GCC-Inkompatibilität in Linuxbrew | Einzeln installieren oder APT nutzen |
| Brew Batch-Abbruch | Ein Paket failt → alles abgebrochen | `\|\| true` oder einzelne Befehle |
| VS Code: Extensions Locking | Parallele Installation failt | Immer sequentiell mit `sleep 1` |
| PEP 668 (Python) | `pip3 install --user` blockiert | `--break-system-packages` oder `pipx` |
| Terraform nicht in Linuxbrew | Keine offizielle Formel | `tfenv` oder HashiCorp APT |
| Bun/Deno nicht in Linuxbrew | Keine Formel verfügbar | Via `npm` direkt installieren |
| zsh fehlt | Nicht installiert auf headless | Config für bash, später zu zsh wechseln |

## Multi-Remote Backup (GitHub + GitLab)

Risiko: Nur ein Remote = Single Point of Failure.
**Lösung:** GitLab als Mirror hinzufügen.

```bash
# Zum Bare-Repo hinzufügen
/usr/bin/git --git-dir=$HOME/.cfg --work-tree=$HOME remote add gitlab https://gitlab.com/USERNAME/dotfiles.git

# Push zu beiden
config push origin main --tags
config push gitlab main --tags
```

**GitLab-Setup:**
1. GitLab-Account erstellen
2. Repo `dotfiles` anlegen
3. Personal Access Token (Scopes: `api`, `write_repository`)
4. `echo "glpat-TOKEN" | glab auth login` (oder direkt in URL)

**In Hermes Sync-Script integrieren:**
```python
for remote in ["origin", "gitlab"]:
    subprocess.run(["git", "push", "-u", remote, "main", "--tags"], env=env)
```

## Automatischer Skill-Sync (Optional)

→ Detaillierte reale Pitfalls und Workarounds:
- `references/linux-brew-pitfalls.md`
- `references/vscode-snap-paths.md`
- `references/dotfiles-bare-repo.md`
- `references/hermes-knowledge-sync.md`
- `references/gitlab-mirror-auth.md`
- `references/n8n-integration.md`

```bash
# Manuell ausführen
python3 ~/.hermes/skills/devops/linux-agent-setup/scripts/hermes-sync.py

# Oder als täglichen Cronjob
hermes cron create --name skill-sync --schedule "0 12 * * *" --prompt "Run /home/klausd/.hermes/skills/devops/linux-agent-setup/scripts/hermes-sync.py"
```

Erstellt automatisch `v0.x.y` Tags bei jeder Änderung.

---

## n8n + Hermes Integration

**n8n Installation (kein Docker nötig):**
```bash
npm install n8n -g
# Binary liegt in ~/.hermes/node/bin/n8n
export PATH="$HOME/.hermes/node/bin:$PATH"
```

**Systemd Service für n8n:**
```ini
[Unit]
Description=n8n Workflow Automation
After=network-online.target

[Service]
Type=simple
ExecStart=/home/USERNAME/.hermes/node/bin/n8n start
WorkingDirectory=/home/USERNAME/n8n
Environment=PATH=/home/USERNAME/.hermes/node/bin:/usr/local/bin:/usr/bin:/bin
Environment=HOME=/home/USERNAME
Environment=NODE_ENV=production
Environment=N8N_HOST=localhost
Environment=N8N_PORT=5678
Environment=GENERIC_TIMEZONE=Europe/Berlin
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

**Event Trigger Skript:**
```bash
~/Developer/scripts/n8n-trigger.sh git-push '{"count":3}'
# → Sendet Event an http://localhost:5678/webhook/hermes-events
```

**Verfügbare Templates:**
- `hermes-status-monitor` — Schedule → Hermes Health → Telegram
- `hermes-webhook-receiver` — Webhook → IF → Telegram
- `github-telegram-notification` — GitHub PR → Telegram

## SSH-Auth für systemd Services

Systemd hat **keinen TTY**, daher kann SSH kein Passwort abfragen. Da der Key ohne Passphrase ist, funktioniert es mit direktem GIT_SSH_COMMAND:

```bash
# Host-Keys vorab akzeptieren
ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null
ssh-keyscan gitlab.com >> ~/.ssh/known_hosts 2>/dev/null

# In Sync-Script:
export GIT_SSH_COMMAND="ssh -i $HOME/.ssh/id_ed25519 -o StrictHostKeyChecking=accept-new"
config push origin main --tags
config push gitlab main --tags
```

**Im Service-File:**
```ini
[Service]
Environment=GIT_SSH_COMMAND=ssh -i /home/USERNAME/.ssh/id_ed25519 -o StrictHostKeyChecking=accept-new
```

- **Token-Sicherheit:** PATs NIEMALS in Chat/Logs/Shell-History speichern
- **GitHub Auth:** Immer `gh auth login` nutzen (speichert in Keyring)
- **SSH-Key:** Ohne Passphrase lassen (für Agent-Automatisierung)
- **Secrets:** Keine `.env` oder Secrets in Repos committen
