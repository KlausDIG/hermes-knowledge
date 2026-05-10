---
name: linux-agent-setup
description: |
  Vollständige Einrichtung eines autonomen Agent-Entwicklungsumfeldes auf Linux (Ubuntu/Debian). 
  Beinhaltet Homebrew, Rust, Node, Shell-Config, VS Code: Extensions, Auto-Commit Daemon, 
  systemd-Service, Hermes Cronjobs und Dokumentationsstruktur.
trigger:
  - "einrichten"
  - "setup agent"
  - "neue umgebung"
  - "linux setup"
  - "dev environment"
  - "installiere tools"
  - "agent config"
requirements:
  - Linux x86_64
  - bash oder zsh
  - Internetverbindung
  - GitHub CLI Token (optional)
---

# linux-agent-setup

## Überblick

Dieser Skill richtet eine komplette, portable Entwicklungsumgebung für einen autonomen AI-Agenten auf Linux ein. Die Einrichtung ist **user-lokal** (kein sudo erforderlich) und lauffähig auf Ubuntu/Debian.

## Schritt 1: Git Basis-Konfiguration

```bash
git config --global user.name "Project Autonomous Agent"
git config --global user.email "agent@local.local"
git config --global init.defaultBranch main
```

## Schritt 2: SSH-Key

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
ssh-keygen -t ed25519 -C "agent@rechner.local" -f ~/.ssh/id_ed25519 -N "" -q
```

## Schritt 3: Homebrew (Linuxbrew, user-lokal)

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

**WICHTIG:** `USERNAME` durch tatsächlichen Linux-Username ersetzen!

## Schritt 6: VS Code: Extensions

```bash
extensions=(
  "eamodio.gitlens"
  "github.vscode-pull-request-github"
  "github.copilot"
  "github.copilot-chat"
  "esbenp.prettier-vscode"
  "dbaeumer.vscode-eslint"
  "ms-python.python"
  "ms-python.black-formatter"
  "ms-vscode-remote.remote-ssh"
  "ms-vscode-remote.remote-containers"
  "bradlc.vscode-tailwindcss"
  "formulahendry.auto-rename-tag"
  "christian-kohler.npm-intellisense"
  "eg2.vscode-npm-script"
  "naumovs.color-highlight"
  "pkief.material-icon-theme"
  "editorconfig.editorconfig"
  "aaron-bond.better-comments"
  "wix.vscode-import-cost"
  "wayou.vscode-todo-highlight"
  "shd101wyy.markdown-preview-enhanced"
  "streetsidesoftware.code-spell-checker"
  "gruntfuggly.todo-tree"
  "yzhang.markdown-all-in-one"
  "rangav.vscode-thunder-client"
  "github.copilot-workspace"
  "visualstudioexptteam.vscodeintellicode"
  "christian-kohler.path-intellisense"
  "ms-vscode.vscode-github-issue-notebooks"
  "ritwickdey.liveserver"
)

for ext in "${extensions[@]}"; do
  echo "Installing $ext..."
  code --install-extension "$ext" --force 2>&1 | grep -E "installed|failed|already"
  sleep 1
done
```

## Schritt 7: GitHub CLI Auth

```bash
# TOKEN NIEMALS im Chat/Log speichern!
echo "ghp_DEIN_TOKEN_HIER" | gh auth login --with-token --hostname github.com
gh auth setup-git --hostname github.com
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

## Sicherheitshinweise

- **Token-Sicherheit:** PATs NIEMALS in Chat/Logs/Shell-History speichern
- **GitHub Auth:** Immer `gh auth login` nutzen (speichert in Keyring)
- **SSH-Key:** Ohne Passphrase lassen (für Agent-Automatisierung)
- **Secrets:** Keine `.env` oder Secrets in Repos committen
