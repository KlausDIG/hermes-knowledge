#!/usr/bin/env python3
"""
Hermes Knowledge Sync
Synchronisiert täglich Skills + Config mit GitHub
Erstellt automatisch Semantic Release Tags
"""
import os, subprocess, sys, json, re, shutil
from datetime import datetime
from pathlib import Path

REPO_DIR = Path.home() / "Developer/repos/hermes-knowledge"
HERMES_DIR = Path.home() / ".hermes"
LOG_FILE = Path.home() / "Developer/repos/hermes-knowledge/sync.log"

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
    if level == "major": major += 1; minor = 0; patch = 0
    elif level == "minor": minor += 1; patch = 0
    else: patch += 1
    return f"v{major}.{minor}.{patch}"

def sync_skills():
    """Kopiere alle Skills (custom + builtin)"""
    skills_src = HERMES_DIR / "skills"
    skills_tgt = REPO_DIR / "skills"
    skills_tgt.mkdir(parents=True, exist_ok=True)
    changed = False
    
    for skill_md in skills_src.rglob("SKILL.md"):
        rel = skill_md.relative_to(skills_src)
        dest = skills_tgt / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists() or skill_md.stat().st_mtime > dest.stat().st_mtime:
            shutil.copy2(skill_md, dest)
            log(f"📄 Skill: {rel}")
            changed = True
    return changed

def sync_memory():
    """Exportiere Memory"""
    mem_src = HERMES_DIR / "memory"
    mem_tgt = REPO_DIR / "memory"
    if mem_src.exists():
        mem_tgt.mkdir(parents=True, exist_ok=True)
        shutil.copy2(mem_src, mem_tgt / "memory.json") if mem_src.is_file() else None
        log("🧠 Memory exportiert")
        return True
    return False

def sync_cronjobs():
    """Exportiere Cronjobs"""
    cron_file = REPO_DIR / "cronjobs" / "cronjobs.json"
    cron_file.parent.mkdir(parents=True, exist_ok=True)
    out, err, code = run("hermes cron list")
    if code == 0:
        with open(cron_file, "w") as f:
            json.dump({"raw": out, "updated": datetime.now().isoformat()}, f, indent=2)
        log("⏰ Cronjobs exportiert")
        return True
    return False

def sync_scripts():
    """Kopiere Agent-Scripts"""
    scripts_src = Path.home() / "Developer/scripts"
    scripts_tgt = REPO_DIR / "scripts"
    scripts_tgt.mkdir(parents=True, exist_ok=True)
    changed = False
    if scripts_src.exists():
        for f in scripts_src.iterdir():
            if f.is_file():
                dest = scripts_tgt / f.name
                if not dest.exists() or f.stat().st_mtime > dest.stat().st_mtime:
                    shutil.copy2(f, dest)
                    log(f"📜 Script: {f.name}")
                    changed = True
    return changed

def git_commit_and_tag():
    out, _, _ = run("git status --short")
    if not out.strip():
        log("✅ Keine Änderungen")
        return False
    
    run("git add -A")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run(f'git commit -m "🤖 [SYNC] Hermes knowledge sync @ {timestamp}"')
    log("💾 Commited")
    
    last_tag = get_last_tag()
    new_tag = bump_version(last_tag, "patch")
    run(f'git tag -a "{new_tag}" -m "Release {new_tag} - Automated knowledge sync"')
    log(f"🏷️ Tag: {new_tag}")
    
    out, err, code = run("git push origin main --tags")
    if code == 0:
        log("🚀 Gepusht zu GitHub")
    else:
        log(f"⚠️ Push fehlgeschlagen: {err}")
    return True

def main():
    log("=== 🔄 Hermes Knowledge Sync Start ===")
    REPO_DIR.mkdir(parents=True, exist_ok=True)
    os.chdir(REPO_DIR)
    
    if not (REPO_DIR / ".git").exists():
        run("git init")
        run('git config user.name "Project Autonomous Agent"')
        run('git config user.email "agent@local.local"')
    
    run("git pull origin main 2>/dev/null || true")
    
    sync_skills()
    sync_cronjobs()
    sync_scripts()
    
    git_commit_and_tag()
    log("=== ✅ Sync Abgeschlossen ===\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
