#!/usr/bin/env python3
"""
Dotfiles Sync Manager
Nutzt Git-Bare-Repo in ~/.cfg zur Verwaltung aller Dotfiles
"""
import os, subprocess, sys, shutil
from pathlib import Path
from datetime import datetime

HOME = Path.home()
CFG_DIR = HOME / ".cfg"
CONFIG_CMD = ["/usr/bin/git", f"--git-dir={CFG_DIR}", f"--work-tree={HOME}"]

def run_git(args):
    cmd = CONFIG_CMD + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and "showUntrackedFiles" not in " ".join(args):
        pass
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def ensure_config():
    """Stelle sicher, dass das Bare-Repo existiert"""
    if not CFG_DIR.exists():
        subprocess.run(["/usr/bin/git", "init", "--bare", str(CFG_DIR)], check=True)
        run_git(["config", "--local", "status.showUntrackedFiles", "no"])
        run_git(["config", "--local", "core.excludesFile", str(HOME / ".gitignore_dotfiles")])
        print("✅ Bare-Repo initialisiert")
    else:
        print("✅ Bare-Repo existiert")

def stage_default_files():
    """Tracke alle wichtigen Dotfiles"""
    files = [
        # Shell
        "~/.bashrc",
        "~/.profile",
        "~/.bash_aliases",
        # Git
        "~/.gitconfig",
        "~/.gitignore_dotfiles",
        # Systemd
        "~/.config/systemd/user/",
        # VS Code:
        "~/snap/code/current/.config/Code:/User/settings.json",
        # SSH
        "~/.ssh/config",
        # Python
        "~/.pythonrc",
        # Node
        "~/.npmrc",
    ]
    
    for f in files:
        fp = Path(f).expanduser()
        if fp.exists() or fp.is_dir():
            out, err, code = run_git(["add", str(fp)])
            if code == 0:
                print(f"✅ Getrackt: {f}")
            elif "already tracking" in err:
                print(f"⚡ Bereits getrackt: {f}")
            else:
                print(f"⚠️ Fehler bei {f}: {err}")
        else:
            # Wenn .ssh/config fehlt, erstelle es
            if "ssh/config" in f:
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text("# SSH Config - Agent Managed\n\nHost github.com\n  HostName github.com\n  User git\n  IdentityFile ~/.ssh/id_ed25519\n  AddKeysToAgent yes\n")
                run_git(["add", str(fp)])
                print(f"✅ Erstellt + getrackt: {f}")
            else:
                print(f"⏭️ Nicht vorhanden: {f}")

def commit_and_tag():
    """Commit + Semantic Release Tag - NUR explizit getrackte Dateien"""
    out, _, _ = run_git(["status", "--short"])
    if not out.strip():
        print("🆗 Keine Änderungen")
        return False
    
    # NIE git add -A - nur explizit getrackte/modifizierte Dateien stagen
    # Das verhindert, dass riesige Dateien (Downloads, Snaps, etc.) eingecheckt werden
    run_git(["add", "--update"])  # Nur bereits getrackte Dateien updaten
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"🤖 [SYNC] Dotfiles sync @ {timestamp}"
    run_git(["commit", "-m", msg])
    print(f"💾 Commited: {msg}")
    
    # Tag
    last_tag, _, code = run_git(["describe", "--tags", "--abbrev=0"])
    if code != 0 or not last_tag:
        new_tag = "v1.0.0"
    else:
        parts = last_tag.lstrip("v").split(".")
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        patch += 1
        new_tag = f"v{major}.{minor}.{patch}"
    
    run_git(["tag", "-a", new_tag, "-m", f"Release {new_tag}"])
    print(f"🏷️ Tag: {new_tag}")
    return True

def github_sync():
    """Push zu GitHub und GitLab via SSH"""
    env_push = os.environ.copy()
    env_push["GIT_DIR"] = str(CFG_DIR)
    env_push["GIT_WORK_TREE"] = str(HOME)
    # SSH Key direkt angeben (kein Agent nötig für Passphrase-less keys)
    env_push["GIT_SSH_COMMAND"] = f"ssh -i {HOME}/.ssh/id_ed25519 -o StrictHostKeyChecking=accept-new"
    
    for remote in ["origin", "gitlab"]:
        r = subprocess.run(
            ["git", "push", "-u", remote, "main", "--tags"],
            capture_output=True, text=True, env=env_push
        )
        if r.returncode == 0:
            print(f"🚀 Gepusht zu {remote}")
        else:
            print(f"⚠️ {remote}: {r.stderr[:120]}")

def main():
    print("=== 🔄 Dotfiles Sync Start ===")
    ensure_config()
    stage_default_files()
    
    changed = commit_and_tag()
    if changed:
        github_sync()
    
    print("=== ✅ Dotfiles Sync Abgeschlossen ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
