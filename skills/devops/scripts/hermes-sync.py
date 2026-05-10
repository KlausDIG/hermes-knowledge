#!/usr/bin/env python3
"""
Hermes Knowledge Sync Script
Synchronisiert Skills, Config und Scripts mit Git

github-token muss via `gh auth login` oder Keyring gespeichert sein
NEVER hardcode tokens in this file!
"""
import os, subprocess, sys, json, re, shutil
from datetime import datetime
from pathlib import Path

REPO_DIR = Path.home() / "Developer/repos/hermes-knowledge"
HERMES_DIR = Path.home() / ".hermes"
LOG_FILE = Path("/tmp/hermes-sync.log")

def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def run(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd or REPO_DIR)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def get_last_tag():
    out, _, code = run("git describe --tags --abbrev=0")
    return out if code == 0 else "v0.0.0"

def bump_version(tag, level="patch"):
    m = re.match(r'v(\d+)\.(\d+)\.(\d+)', tag)
    if not m:
        return "v0.1.0"
    major, minor, patch = map(int, m.groups())
    if level == "major":
        major += 1; minor = 0; patch = 0
    elif level == "minor":
        minor += 1; patch = 0
    else:
        patch += 1
    return f"v{major}.{minor}.{patch}"

def sync_skills():
    """Kopiere alle custom Skills (nicht builtin)"""
    skills_dir = HERMES_DIR / "skills"
    target = REPO_DIR / "skills"
    target.mkdir(parents=True, exist_ok=True)
    
    for skill_md in skills_dir.rglob("SKILL.md"):
        rel = skill_md.relative_to(skills_dir)
        # Skip builtins (top-level)
        if len(rel.parts) == 1:
            continue
        dest = target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists() or skill_md.stat().st_mtime > dest.stat().st_mtime:
            shutil.copy2(skill_md, dest)
            log(f"✅ Skill sync: {rel}")
    return True

def sync_scripts():
    """Kopiere Agent-Scripts"""
    scripts_src = Path.home() / "Developer/scripts"
    scripts_tgt = REPO_DIR / "scripts"
    scripts_tgt.mkdir(parents=True, exist_ok=True)
    
    if scripts_src.exists():
        for f in scripts_src.iterdir():
            if f.is_file():
                dest = scripts_tgt / f.name
                if not dest.exists() or f.stat().st_mtime > dest.stat().st_mtime:
                    shutil.copy2(f, dest)
                    log(f"✅ Script sync: {f.name}")
    return True

def git_commit_and_tag():
    """Commit + Semantic Release Tag"""
    out, _, _ = run("git status --short")
    if not out.strip():
        log("🆗 Keine Änderungen")
        return False
    
    run("git add -A")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"🤖 [AUTO] Knowledge sync @ {timestamp}"
    run(f'git commit -m "{msg}"')
    
    last_tag = get_last_tag()
    new_tag = bump_version(last_tag, "patch")
    run(f'git tag -a "{new_tag}" -m "Release {new_tag}"')
    
    out, err, code = run("git push origin main --tags")
    if code == 0:
        log(f"✅ Gepusht: {new_tag}")
    else:
        log(f"⚠️ Push fail: {err}")
    return True

def main():
    log("=== Hermes Knowledge Sync Start ===")
    REPO_DIR.mkdir(parents=True, exist_ok=True)
    os.chdir(REPO_DIR)
    
    if not (REPO_DIR / ".git").exists():
        run("git init")
        run('git config user.name "Project Autonomous Agent"')
        run('git config user.email "agent@local.local"')
        log("✅ Git init")
    
    sync_skills()
    sync_scripts()
    changed = git_commit_and_tag()
    
    log("=== Sync Abgeschlossen ===")
    return 0 if changed else 1

if __name__ == "__main__":
    sys.exit(main())
