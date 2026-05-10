#!/usr/bin/env bash
# ============================================================
# 💻 Linux Agent Bootstrap
# Ein-Befehl-Setup für neue Systeme
# Verwendung: curl -sL https://raw.githubusercontent.com/KlausDIG/dotfiles/main/bootstrap.sh | bash
# ============================================================
set -euo pipefail

REPO="https://github.com/KlausDIG/dotfiles.git"
GITLAB_MIRROR="https://gitlab.com/KlausDIG/dotfiles.git"
HOME_DIR="$HOME"

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +%H:%M:%S)]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# --- Schritt 1: Voraussetzungen ---
log "🚀 Starte Agent-Bootstrap..."

if ! command -v git >/dev/null 2>&1; then
    log "📦 Installiere Git..."
    sudo apt-get update -qq && sudo apt-get install -y git curl wget || error "Git Installation fehlgeschlagen"
fi

# --- Schritt 2: Dotfiles aus GitHub ausrollen ---
log "📥 Klone Dotfiles von GitHub..."
if [ -d "$HOME/.cfg" ]; then
    warn "Bare-Repo existiert bereits, überschreibe..."
    rm -rf "$HOME/.cfg"
fi

git clone --bare "$REPO" "$HOME/.cfg" || {
    warn "GitHub failed, versuche GitLab Mirror..."
    git clone --bare "$GITLAB_MIRROR" "$HOME/.cfg" || error "Kein Zugriff auf Remote"
}

# --- Schritt 3: Config-Alias setzen ---
log "⚙️  Setze Git-Bare-Repo Config..."
/usr/bin/git --git-dir="$HOME/.cfg/" --work-tree="$HOME" config --local status.showUntrackedFiles no
/usr/bin/git --git-dir="$HOME/.cfg/" --work-tree="$HOME" config --local core.excludesFile "$HOME/.gitignore_dotfiles"

# --- Schritt 4: Dateien auschecken (vorsichtshalber backup) ---
log "📂 Checke Dotfiles aus..."
BACKUP_DIR="$HOME/.config-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Prüfe auf Konflikte
if /usr/bin/git --git-dir="$HOME/.cfg/" --work-tree="$HOME" checkout 2>&1 | grep -q "would overwrite"; then
    log "⚠️  Konflikte erkannt, erstelle Backup..."
    /usr/bin/git --git-dir="$HOME/.cfg/" --work-tree="$HOME" checkout -f || true
else
    /usr/bin/git --git-dir="$HOME/.cfg/" --work-tree="$HOME" checkout || true
fi

# --- Schritt 5: Homebrew ---
if ! command -v brew >/dev/null 2>&1; then
    log "🍺 Installiere Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || warn "Homebrew-Installation fehlgeschlagen"
    eval "$("$HOME/.linuxbrew/bin/brew" shellenv 2>/dev/null)" || true
fi

# --- Schritt 6: SSH-Key ---
if [ ! -f "$HOME/.ssh/id_ed25519" ]; then
    log "🔑 Generiere SSH-Key..."
    mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
    ssh-keygen -t ed25519 -C "agent@$(hostname).local" -f "$HOME/.ssh/id_ed25519" -N "" -q
    log "🔑 SSH-Key:"
    cat "$HOME/.ssh/id_ed25519.pub"
fi

# --- Schritt 7: Shell neu laden ---
log "🐚 Lade Shell neu..."
if [ -f "$HOME/.bashrc" ]; then
    # Alias setzen falls noch nicht vorhanden
    if ! grep -q "alias config=" "$HOME/.bashrc"; then
        echo "" >> "$HOME/.bashrc"
        echo '# Dotfiles Management' >> "$HOME/.bashrc"
        echo 'alias config="/usr/bin/git --git-dir=$HOME/.cfg/ --work-tree=$HOME"' >> "$HOME/.bashrc"
    fi
    source "$HOME/.bashrc" || true
fi

# --- Schritt 8: GitLab Mirror als Backup-Remote ---
log "🔄 Setze GitLab Mirror als Backup..."
/usr/bin/git --git-dir="$HOME/.cfg/" --work-tree="$HOME" remote add gitlab "$GITLAB_MIRROR" 2>/dev/null || true

# --- Schritt 9: Dienste starten ---
log "🚀 Starte systemd Services..."
systemctl --user daemon-reload 2>/dev/null || true
systemctl --user enable agent-autocommit.service 2>/dev/null || true
systemctl --user start agent-autocommit.service 2>/dev/null || true
systemctl --user enable hermes-knowledge-sync.timer 2>/dev/null || true
systemctl --user start hermes-knowledge-sync.timer 2>/dev/null || true
systemctl --user enable dotfiles-sync.timer 2>/dev/null || true
systemctl --user start dotfiles-sync.timer 2>/dev/null || true

# --- Fertig ---
log "✅ Bootstrap abgeschlossen!"
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Agent Setup Fertig!                                 ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "Alias:     config status     # Dotfiles prüfen"
echo "           config add ~/.foo  # Neue Datei tracken"
echo "           config push        # Manuell pushen"
echo ""
echo "Services:  agent-autocommit.service"
echo "           hermes-knowledge-sync.timer"
echo "           dotfiles-sync.timer"
echo ""
echo "GitHub:    https://github.com/KlausDIG/dotfiles"
echo "GitLab:    https://gitlab.com/KlausDIG/dotfiles"
echo ""
