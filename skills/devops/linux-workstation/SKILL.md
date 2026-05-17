---
name: linux-workstation
description: |
  Bootstrap, operate, and maintain a complete Linux development workstation from scratch.
  Covers package managers (Homebrew, apt, snap), shell configuration, runtime installation,
  background daemons (systemd), disk-space and memory management, ZRAM, automated Git
  sync across multiple repositories, offline-resilient cronjobs, Snap/browser cleanup,
  history explosion prevention, and incident response for 99 % disk-full emergencies.
toolsets:
  - terminal
  - file
tags:
  - linux
  - workstation
  - homebrew
  - git
  - automation
  - cronjob
  - maintenance
  - cleanup
  - zram
  - snap
version: "2.0.0"
related_skills:
  - hermes-mesh-operations
  - github-repo-management
  - hermes-skills-sync
---

# Linux Workstation

## Trigger

Load this skill when the user asks about:
- Setting up a fresh Linux dev machine or VM
- Porting a macOS dotfiles / setup script to Linux
- Installing Homebrew (Linuxbrew), runtimes, or dev tools in batches
- Creating systemd user services or background auto-commit daemons
- Disk space running low, SSD cleanup, or Snap cache explosion
- Replacing swap with ZRAM on a memory-constrained system
- Automating Git commits and pushes across multiple local repositories
- Browser reduction, history guard, or log rotation on Linux

---

## 1. Core Principles

- **Never assume macOS paths on Linux.** Replace `/Users/NAME` with `/home/NAME`, `~/Library/LaunchAgents` with `~/.config/systemd/user`.
- **Use `bash` as fallback shell.** If `zsh` is not installed and `sudo` has no TTY, proceed with `bash`.
- **Run long brew installs in background.** They take 10–45 minutes. Use `background=true` with `notify_on_complete`.
- **Check formulas before batch-install.** A single missing formula aborts an entire `brew install` batch.
- **No PTY for sudo.** Hermes cannot run `sudo` interactively. Write scripts; let the user run `sudo bash script.sh` manually.
- **Prevent history explosions.** Limit `HISTSIZE` and truncate `.bash_history` proactively.

---

## 2. Homebrew (Linuxbrew) Setup

```bash
# Install user-local Homebrew
git clone --depth=1 https://github.com/Homebrew/brew ~/.linuxbrew

# Activate in current session
eval "$(~/.linuxbrew/bin/brew shellenv)"

# Add to shell RC
echo 'eval "$(/home/USER/.linuxbrew/bin/brew shellenv)"' >> ~/.bashrc
```

**Critical:** On Linux the brew prefix is `~/.linuxbrew`, not `/opt/homebrew` or `/usr/local`.

---

## 3. Shell Configuration

If the user is on `bash` (check with `echo $SHELL`):
- Append Homebrew env, completions, and aliases to `~/.bashrc`.
- Use `command -v` guards for every optional tool so the RC never breaks if a tool is missing.
- **DO NOT overwrite `~/.bashrc`.** Append only. Deduplicate before writing.

If `zsh` is requested but not installed and `sudo` has no TTY:
- Skip zsh install; document manual command for later: `sudo apt-get install -y zsh`
- Create bash config now; copy to `.zshrc` later with `bash` → `zsh` substitutions.

---

## 4. Batch Tool Installation

Run in **background** because source builds or bottle fetches take 10–45 min.

```bash
eval "$(~/.linuxbrew/bin/brew shellenv)"
brew install git gh node jq htop tree ripgrep fd fzf tldr bat eza tmux wget curl pandoc
brew install zoxide starship duf gdu lazygit neovim thefuck
brew install go rustup pyenv rbenv jenv pipx poetry
brew install kubectl helm terraform ansible lazydocker
```

### Formula Pitfalls on Linuxbrew

| macOS name | Linuxbrew name | Note |
|---|---|---|
| `rustup-init` | `rustup` | On Linuxbrew the formula is `rustup` |
| `bun` | **missing** | Install via `curl -fsSL https://bun.sh/install \| bash` |
| `terraform` | **missing / needs tap** | Not in core; use `hashicorp/tap` or binary |
| `volta` | `volta` | Verify with `brew search` first |
| `gdu` | `gdu-go` | Installs as `gdu-go` to avoid conflict with `coreutils` |

**`cyrus-sasl` build failure (GCC 15+):** Blocks `gh`, `pandoc`, `tldr`, `ansible`, `helm`, `lazydocker`. Workarounds:
- `gh` → GitHub releases binary
- `tldr` → `npm install -g tldr`
- `pandoc` → static binary
- `ansible`, `lazydocker` → `pip install ansible`, `go install github.com/jesseduffield/lazydocker@latest`

**Always run `brew search` preflight** for any uncertain formula before including it in a batch command.

---

## 5. VS Code: Extensions

- CLI path on Snap installs: `/snap/bin/code` usually works.
- Install **sequentially**, never parallel. Parallel installs corrupt VS Code:'s extension directory.

```bash
for ext in eamodio.gitlens github.vscode-pull-request-github esbenp.prettier-vscode; do
  code --install-extension "$ext" --force 2>&1 | grep -E "installed|failed|already"
  sleep 1
done
```

---

## 6. Background Daemons (systemd User Services)

On macOS you would use `~/Library/LaunchAgents/*.plist`. On Linux use **systemd user units**:

```ini
# ~/.config/systemd/user/my-daemon.service
[Unit]
Description=My Daemon
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/USER/Developer/scripts/my-daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

Enable & start:
```bash
systemctl --user daemon-reload
systemctl --user enable my-daemon.service
systemctl --user start my-daemon.service
systemctl --user status my-daemon.service --no-pager
```

**Advantage:** No root, no sudo, survives logout if `linger` is enabled (`loginctl enable-linger $USER`).

---

## 7. Auto-Commit Daemon

### Polling Approach (most robust)
Scan every 30s with `git status --porcelain`. No external Python dependencies.

Key logic:
1. Discover repos under `~/Developer/repos/*/.git`
2. Every 30s, `chdir` → `git status --porcelain`
3. If dirty: `git add -A` → `git commit -m "🤖 [AUTO] ..."` → `git push origin HEAD`

See `scripts/auto-commit-poll.py` for the full reference implementation.

---

## 8. Automated Git Sync (multi-repo)

### What it does

A cronjob-driven script discovers all `.git` repos under configured search paths, auto-commits local changes (offline-safe), pushes only when online, and retries failed pushes with exponential backoff.

### Schnellstart

```bash
mkdir -p ~/.hermes/scripts ~/.hermes/logs ~/.hermes/cache
cp scripts/auto-push-projects.sh ~/.hermes/scripts/
chmod +x ~/.hermes/scripts/auto-push-projects.sh

hermes cronjob create \
  --name project-auto-push \
  --schedule "*/30 * * * *" \
  --script auto-push-projects.sh \
  --no-agent \
  --prompt "Auto-push alle Git-Repos: commit lokal, push wenn online, retry bei Fehlern."
```

**Critical:** The `--script` parameter must be a bare filename, not a path.

```bash
# WRONG:
--script /home/user/.hermes/scripts/auto-push-projects.sh

# CORRECT:
--script auto-push-projects.sh
```

Test manually:
```bash
bash ~/.hermes/scripts/auto-push-projects.sh
# Log: ~/.hermes/logs/auto-push-projects.log
```

### Configuration (inside the script, lines ~21–41)

| Variable | Default | Description |
|---|---|---|
| `SEARCH_PATHS` | `~/Developer/repos`, `~/projects`, … | Where to look for `.git` |
| `EXCLUDE_PATTERNS` | `.linuxbrew`, `.pyenv`, `.hermes`, `node_modules` | Substrings to ignore |
| `LOCK_TIMEOUT` | `180` | Seconds until a stale lock is overwritten |
| `max_retries` | `3` | Push attempts per repo |
| `timeout 30` | `30` | Seconds per push attempt |
| `curl --max-time 4` | `4` | Seconds for online check |

### Offline Resilience

| State | Behaviour |
|---|---|
| No internet | Commits locally; push deferred to pending queue |
| Internet returns | Next run processes pending pushes with retry |
| Push hangs / timeout | 30s kill → retry with backoff → queue |
| Push rejected | Marked as non-retryable, status `rejected` |

### Retry Logic

```
Attempt 1 → immediately
Attempt 2 → after 5s
Attempt 3 → after 10s
```

Recognized error types:
| Error | Reaction |
|---|---|
| Timeout (`exit 124`) | Retry |
| Connection reset / broken pipe / refused | Retry |
| Rejected / stale info / non-fast-forward | Non-retryable → `rejected` |
| Other | Retry, then queue |

### Pending Queue

File: `~/.hermes/cache/pending-pushes.txt`

Format:
```
/home/user/Developer/repos/project-a|main
/home/user/Developer/repos/project-b|develop|rejected
```

### Security

```bash
export GIT_TERMINAL_PROMPT=0              # Block interactive prompts
export GIT_SSH_COMMAND="ssh -o ConnectTimeout=10 -o BatchMode=yes ..."
```

### Pitfalls

- **Push rejected (diverged upstream):** Script cannot rebase — manual `git pull --rebase && git push` required.
- **SSH keys must be passphrase-free or ssh-agent running:** `BatchMode=yes` blocks password prompts.
- **Monorepo (hermes-klausi-hp):** New projects go under `projects/<name>/` inside the monorepo, NOT as separate repos.
- **Thin-client / cloud-first:** Only keep active projects locally. Use Ollama + llama-cpp-python (GGUF) for local AI; avoid large ML packages (PyTorch, Transformers, Sentence-Transformers).

---

## 9. Memory & Disk Management

### 9.1 ZRAM Instead of Swap

Why ZRAM:
- No SSD wear from constant swap writes
- Compressed RAM swap is faster than SSD swap
- +4 GB SSD free after removing old `/swap.img`

Setup script (`~/bin/setup-zram.sh`):
```bash
#!/usr/bin/env bash
set -euo pipefail

# Remove old swap
if [ -f /swap.img ]; then
    sudo swapoff /swap.img || true
    sudo rm -f /swap.img
    sudo sed -i '/swap.img/d' /etc/fstab
fi

# Enable zram
debian-zram-config start || true
systemctl enable zramswap 2>/dev/null || true

echo "ZRAM configured. Reboot recommended."
```

Verify:
```bash
cat /proc/swaps    # should show only /dev/zram0, not /swap.img
free -h            # swap size ~50 % of RAM
```

### 9.2 Disk Analysis (Timeout-Safe)

**Quick overview (never times out):**
```bash
df -h /                    # SSD status
cat /proc/swaps            # swap status
free -h                    # RAM + swap
du -sh ~/* 2>/dev/null | sort -rh | head -10   # largest home folders
```

**Targeted system paths (avoid `du -sh /` which times out):**
```bash
du -sh /usr /var /opt /snap /home 2>/dev/null
du -sh /var/lib/* 2>/dev/null | sort -rh | head -10
```

**Snap space breakdown (often the largest block):**
```bash
du -sh /var/lib/snapd/snaps              # physical .snap files
ls -lhS /var/lib/snapd/snaps/ | head -10 # largest individual snaps
snap list --all | grep deaktiviert      # old revisions
```

**User folder scan:**
```bash
for dir in ~/.hermes ~/snap ~/.local ~/.cache ~/.linuxbrew ~/.config ~/Downloads ~/bin ~/workspace; do
    [ -d "$dir" ] && du -sh "$dir" 2>/dev/null
done | sort -rh | head -15
```

**Interactive tooling:** Use `ncdu` (via Homebrew) for a navigable disk-use tree. See `references/disk-analysis-tools.md`.

### 9.3 Browser Reduction (biggest RAM consumer)

Real data from this system with Chrome + Brave + Firefox simultaneously:
- **56 renderer processes**
- **~5–8 GB RAM consumed**
- Swap fills up

After closing all browsers:
- **~4–5 GB RAM freed**
- Swap pressure relieved

| Browser | Type | Size | Status |
|---|---|---|---|
| Google Chrome | DEB | ~415 MB | ✅ **KEEP** (fast, low overhead) |
| Brave | Snap | ~630 MB | Optional remove |
| Firefox | Snap | **~8.3 GB** | ❌ **REMOVE** (largest space consumer) |

Remove:
```bash
snap remove firefox --purge
# Optional: snap remove brave --purge
```

> ⚠️ After removing Firefox snap, the old profile dir `~/snap/firefox/` may still exist. Check and remove manually if no longer needed.

---

## 10. Snap Management

### 10.1 Remove Old Snap Revisions (safest)

Snap keeps old revisions as backups — they can consume **GBs**.

**Show disabled revisions:**
```bash
snap list --all | grep deaktiviert
```

**Where the data physically lives:**
```bash
ls -lhS /var/lib/snapd/snaps/
```

**Remove (disabled only — never active):**
```bash
snap remove <name> --revision=<rev>
# Example:
snap remove code --revision=238
```

> ⚠️ **NEVER remove active revisions.** Active has no `deaktiviert` label.

### 10.2 Automated Snap Cleanup (Cronjob)

```bash
mkdir -p ~/.hermes/scripts
cat > ~/.hermes/scripts/snap-cleanup.sh << 'SNAPSCRIPT'
#!/usr/bin/env bash
set -euo pipefail
LOG_FILE="$HOME/.local/state/snap-cleanup.log"
mkdir -p "$(dirname "$LOG_FILE")"
exec >> "$LOG_FILE" 2>&1

echo "Snap-Cleanup started: $(date -Iseconds)"
DISABLED=$(snap list --all | grep 'deaktiviert' || true)

if [ -z "$DISABLED" ]; then
    echo "No disabled snaps found."
    exit 0
fi

echo "$DISABLED"
while IFS= read -r line; do
    NAME=$(echo "$line" | awk '{print $1}')
    REV=$(echo "$line" | awk '{print $3}')
    if [ -n "$NAME" ] && [ -n "$REV" ]; then
        echo "→ Removing $name revision $REV..."
        if sudo snap remove "$NAME" --revision="$REV" 2>&1; then
            echo "  ✓ $NAME Rev $REV removed"
        else
            echo "  ⚠ Error on $NAME Rev $REV (sudo may be needed)"
        fi
    fi
done <<< "$DISABLED"

echo "Snap-Cleanup done: $(date -Iseconds)"
SNAPSCRIPT
chmod +x ~/.hermes/scripts/snap-cleanup.sh
```

Create cronjob:
```bash
hermes cronjob create \
  --name snap-cleanup \
  --schedule "0 4 * * 0" \
  --script snap-cleanup.sh \
  --no-agent
```

**Note:** Removing snap revisions requires root. Options:
1. Run manually: `sudo bash ~/.hermes/scripts/snap-cleanup.sh`
2. Add to `visudo`: `klausd ALL=(ALL:ALL) NOPASSWD: /usr/bin/snap`

### 10.3 Snaps to Never Remove

| Snap | Reason |
|---|---|
| core / core20 / core22 / core24 | Snap base system |
| snapd | Snap engine |

---

## 11. Defense System Against Disk Emergencies

Developed after a real 99 % full incident (2026-05-15, 217 GB / 233 GB, only 4 GB free).

### Defense Layers

| Layer | Job | Frequency | Trigger |
|---|---|---|---|
| 1. Watchdog | `disk-watchdog` | **Hourly** | Auto — checks free space |
| 2. Daily | `daily-cleanup` | **Daily 02:00** | Auto — aggressive cache cleanup |
| 3. Snap | `snap-cleanup` | **Sunday 04:00** | Auto — disabled revisions |
| 4. Manual | `~/bin/cleanup-now.sh` | **Ad-hoc** | After intensive sessions |
| 5. Deep | `~/bin/cleanup-*.sh` | **Ad-hoc** | One-off bulk (Ollama, dotfiles) |

### Watchdog Logic (hourly)

```bash
FREE_GB=$(df -BG / | tail -1 | awk '{print $4}' | tr -d 'G')
if [ "$FREE_GB" -lt 5 ]; then
    rm -rf ~/.cache/google-chrome/* ~/.cache/chromium/*
    rm -rf ~/snap/*/current/.cache/*
    npm cache clean --force
    brew cleanup -s
    find /tmp -user "$USER" -type f -delete
fi
```

### Daily Cleanup Targets (aggressive)

```bash
# Chrome/Chromium / VS Code: Snap caches (all variants)
for cache in \
    "$HOME/.cache/google-chrome" \
    "$HOME/.cache/chromium" \
    "$HOME/.config/google-chrome/Default/Cache" \
    "$HOME/.config/chromium/Default/Cache" \
    "$HOME/snap/code/current/.config/Code:/Cache" \
    "$HOME/snap/code/current/.config/Code:/CachedData" \
    "$HOME/snap/code/current/.config/Code:/CachedExtensionVSIXs"; do
    [ -d "$cache" ] && rm -rf "$cache"/* 2>/dev/null || true
done

# Snap caches (all snaps)
for snap_cache in "$HOME"/snap/*/current/.cache; do
    [ -d "$snap_cache" ] && rm -rf "$snap_cache"/* 2>/dev/null || true
done

# + Homebrew, npm, Hermes logs (>7 days), /tmp, Downloads (>3 days)
```

### Emergency Cleanup Scripts

| Script | Function | Sudo needed? | Expected Recovery |
|---|---|---|---|
| `~/bin/cleanup-now.sh` | Immediate post-session cleanup | ❌ No | ~200 MB – 2 GB |
| `~/bin/cleanup-ollama-gpu.sh` | Remove ROCm/CUDA (useless on Intel iGPU) | ✅ Yes | **~5.9 GB** |
| `~/bin/cleanup-snaps.sh` | Thunderbird/Brave + old revs | ✅ Yes | **~1–2 GB** |
| `~/bin/cleanup-dotfiles.sh` | Compress `~/.cfg` Git objects | ❌ No | **~3–5 GB** |
| `~/bin/cleanup-downloads.sh` | Installers + old downloads | ❌ No | ~50–200 MB |
| `~/bin/setup-zram.sh` | Activate ZRAM | ✅ Yes | +4 GB (old swap removed) |
| `~/bin/thin-client.sh` | Cloud-on-demand switch | ❌ No | — |

### Incident Post-Mortem (99 % Full, 2026-05-15)

**Newly discovered space consumers:**

| # | Path | Size | Cause |
|---|------|------|-------|
| 1 | `~/.cfg` (dotfiles bare-repo Git objects) | ~7 GB | Auto-sync checked in snaps/caches as Git objects |
| 2 | `/usr/local/lib/ollama` | ~6 GB | GPU backends (ROCm 2.5G, CUDA 3.5G) — useless on Intel iGPU |
| 3 | `~/.vscode/` | ~600 MB | Extensions |
| 4 | `~/.rustup/` | ~1.4 GB | Toolchains |
| 5 | `~/.npm/` | ~1.2 GB | Node modules cache |

**Analysis techniques when `du` times out:**

1. **Python scan instead of shell `du`:**
   ```python
   import os; [print(p, f'{sum(os.path.getsize(os.path.join(d,f)) for d,_,files in os.walk(p) for f in files if os.path.exists(os.path.join(d,f)))/(1024**3):.1f} GB') for p in ['/home/klausd/.hermes','/home/klausd/.vscode','/usr/local/lib/ollama']]
   ```

2. **Bare repo with `GIT_DIR` (not `--git-dir`):**
   ```bash
   # WRONG on Ubuntu 24.04:
   git --git-dir=~/.cfg count-objects -vH
   # RIGHT:
   GIT_DIR=/home/klausd/.cfg git count-objects -vH
   ```

3. **Find timeout culprits:**
   ```bash
   for dir in ~/.ollama ~/.n8n ~/.dotnet ~/.cfg ~/.vscode ~/.cargo; do
       timeout 15 du -sh "$dir" 2>/dev/null || echo "TIMEOUT: $dir"
   done
   ```

**Ollama GPU cleanup (requires sudo, Intel iGPU only):**
```bash
sudo rm -rf /usr/local/lib/ollama/rocm      # ~2.5 GB
sudo rm -rf /usr/local/lib/ollama/cuda_v12  # ~2.5 GB
sudo rm -rf /usr/local/lib/ollama/cuda_v13  # ~1 GB
# Keep: libggml-cpu-*.so + libggml-base.so*
```

See `references/disk-fresser-klausdig.md` for full session documentation.

---

## 12. Shell History Explosion Prevention

### Linux Server

Automated scripts as root wrote every command to `.bash_history`. A Hostinger VPS reached **38 GB**.

Immediate fix (script then `sudo bash`):
```bash
cat > ~/bin/clear-bash-history.sh << 'EOF'
#!/bin/bash
for userdir in /home/* /root; do
    histfile="$userdir/.bash_history"
    [ -f "$histfile" ] || continue
    size=$(du -sh "$histfile" 2>/dev/null | cut -f1)
    echo "Before: $histfile = $size"
    > "$histfile"
    history -c 2>/dev/null || true
    echo "After: cleared"
done
EOF
# Then: sudo bash ~/bin/clear-bash-history.sh
```

Permanent prevention:
```bash
# Set HISTSIZE=1000, HISTFILESIZE=2000 in /etc/profile and /root/.bashrc
```

### macOS

A buggy cron (`cat ~/.bash_history ~/.zsh_history >> ~/.bash_history`) caused a **285 GB** history. Fix:
```bash
> ~/.bash_history
rm -f ~/.bash_history.tmp
for rc in ~/.bashrc ~/.zshrc; do
    [ -f "$rc" ] || continue
    grep -q "HISTSIZE=" "$rc" && continue
    echo -e "\nexport HISTSIZE=10000\nexport SAVEHIST=10000\nexport HISTFILESIZE=20000" >> "$rc"
done
```

See `references/vps-bash-history-explosion.md` and `references/macmini-bash-history-explosion.md` for full post-mortems.

---

## 13. Skill Discovery Workflow (automated)

See `references/skill-discovery-workflow.md` for the full runnable recipe. Summary:

1. Query local tool versions via `which --version` / `<tool> --version`
2. Query latest upstream via GitHub API:
   ```bash
   curl -s https://api.github.com/repos/OWNER/REPO/releases/latest | jq -r '.tag_name'
   ```
3. Query VS Code: updates via:
   ```bash
   curl -s https://update.code.visualstudio.com/api/update/linux-x64/stable/<CURRENT_COMMIT> | jq -r '.productVersion'
   ```
4. Compare and flag anything where local ≠ latest
5. Inventory missing high-value tools from baseline set
6. Check VS Code: extensions with `code --list-extensions`
7. Deliver a compact table and actionable `brew install` / `gh upgrade` / `uv self update` commands

---

## 14. Pitfalls & Workarounds

| Pitfall | Fix |
|---|---|
| `sudo` requires TTY, terminal tool has none | Skip system-wide installs; use user-local alternatives (Homebrew, pip `--user`, cargo, npm `--global`) |
| `write_file` rejects `~/.bashrc` as "protected" | Use `terminal` with `echo ... >> ~/.bashrc` or Python `Path(...).write_text()` |
| Heredoc (`cat <<EOF`) times out in terminal | Use Python `execute_code` with `read_file`/`write_file`, or line-by-line `echo >>` |
| Background brew install aborts on missing formula | Split into batches after `brew search` preflight |
| `bun` missing from Linuxbrew | Install via `curl -fsSL https://bun.sh/install \| bash` |
| Swap.img still referenced in `/etc/fstab` after ZRAM | Always use `remove-old-swap.sh` which cleans fstab |
| Snap isolation — rclone config at two paths | Write to both `~/.config/rclone/rclone.conf` and `~/snap/rclone/current/.config/rclone/rclone.conf` |
| `local PID=$!` in bash `case` blocks | Use a function, or `PID=$!` without `local` |

---

## Scripts

| File | Purpose |
|---|---|
| `scripts/auto-commit-poll.py` | Polling-based auto-commit daemon (no watchdog dependency) |
| `scripts/auto-push-projects.sh` | Multi-repo auto-commit + auto-push with offline resilience |
| `scripts/snap-cleanup.sh` | Snap disabled-revision cleanup |
| `scripts/disk-watchdog.sh` | Hourly free-space watchdog |
| `scripts/daily-cleanup.sh` | Aggressive daily cache/browser/tmp cleanup |

## Templates

| File | Purpose |
|---|---|
| `templates/systemd-user-service.ini` | Starter template for a systemd user daemon |
| `templates/shell-rc-fragment.sh` | Bash RC fragment with PATHs, completions, and aliases |

## References

| File | Purpose |
|---|---|
| `references/skill-discovery-workflow.md` | Full daily tool-audit recipe |
| `references/disk-fresser-klausdig.md` | Full 99 %-full incident documentation |
| `references/disk-analysis-tools.md` | `ncdu`, timeout-safe analysis, weekly loss expectations |
| `references/vps-bash-history-explosion.md` | Linux server 38 GB history post-mortem |
| `references/macmini-bash-history-explosion.md` | macOS 285 GB history post-mortem |
| `references/docker-desktop-recovery-mac.md` | Docker Desktop recovery when VM disk is full |
