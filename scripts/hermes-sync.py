#!/usr/bin/env python3
"""
Hermes Knowledge Sync Script
Synchronisiert Skills, Memory und Config mit Git
Erstellt automatisch Semantic Release Tags
"""
import os, subprocess, sys, json, re
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
    
    # Nur nicht-builtin Skills (die in Subdirs sind)
    for skill_md in skills_dir.rglob("SKILL.md"):
        rel = skill_md.relative_to(skills_dir)
        # Skip builtins (top-level)
        if len(rel.parts) == 1:
            continue
        dest = target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Nur kopieren wenn geändert
        if not dest.exists() or skill_md.stat().st_mtime > dest.stat().st_mtime:
            import shutil
            shutil.copy2(skill_md, dest)
            log(f"✅ Skill aktualisiert: {rel}")
    
    return True

def sync_cronjobs():
    """Exportiere Cronjobs"""
    cron_file = REPO_DIR / "cronjobs" / "cronjobs.json"
    cron_file.parent.mkdir(parents=True, exist_ok=True)
    
    out, err, code = run("hermes cron list", cwd=None)
    if code == 0:
        # Parse die Textausgabe
        jobs = []
        # Einfacher Parser: suche nach Job-IDs
        for line in out.split("\n"):
            if re.match(r'^[a-f0-9]{12}', line):
                parts = line.split()
                if len(parts) >= 2:
                    jobs.append({"id": parts[0], "name": parts[1] if len(parts) > 1 else "unknown"})
        with open(cron_file, "w") as f:
            json.dump({"jobs": jobs, "updated": datetime.now().isoformat()}, f, indent=2)
        log(f"✅ Cronjobs exportiert ({len(jobs)} jobs)")
        return True
    else:
        log("⚠️ Cronjob-Export fehlgeschlagen")
        return False

def sync_config():
    """Exportiere Hermes Config"""
    config_dir = REPO_DIR / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Kopiere wichtige Config-Dateien
    for cfg in ["config.yml", "config.yaml"]:
        src = HERMES_DIR / cfg
        if src.exists():
            import shutil
            shutil.copy2(src, config_dir / cfg)
            log(f"✅ Config kopiert: {cfg}")
            return True
    
    log("⚠️ Keine Config-Datei gefunden")
    return False

def sync_scripts():
    """Kopiere Agent-Scripts"""
    scripts_src = Path.home() / "Developer/scripts"
    scripts_tgt = REPO_DIR / "scripts"
    scripts_tgt.mkdir(parents=True, exist_ok=True)
    
    if scripts_src.exists():
        import shutil
        for f in scripts_src.iterdir():
            if f.is_file():
                dest = scripts_tgt / f.name
                if not dest.exists() or f.stat().st_mtime > dest.stat().st_mtime:
                    shutil.copy2(f, dest)
                    log(f"✅ Script aktualisiert: {f.name}")
    return True

def git_commit_and_tag():
    """Wenn Änderungen vorhanden: commit + tag"""
    out, _, code = run("git status --short")
    if not out.strip():
        log("🆗 Keine Änderungen – nichts zu commiten")
        return False
    
    # Commit
    run("git add -A")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"🤖 [AUTO] Knowledge sync @ {timestamp}"
    run(f'git commit -m "{msg}"')
    log(f"✅ Commited: {msg}")
    
    # Semantic Version Bump
    last_tag = get_last_tag()
    new_tag = bump_version(last_tag, "patch")
    run(f'git tag -a "{new_tag}" -m "Release {new_tag} - Automated knowledge sync"')
    log(f"🏷️ Neue Version: {new_tag}")
    
    # Push
    out, err, code = run("git push origin main --tags")
    if code == 0:
        log("✅ Gepusht zu GitHub")
    else:
        log(f"⚠️ Push fehlgeschlagen: {err}")
    
    return True

def main():
    log("=== Hermes Knowledge Sync Start ===")
    REPO_DIR.mkdir(parents=True, exist_ok=True)
    
    # cd into repo
    os.chdir(REPO_DIR)
    
    # Init falls nötig
    if not (REPO_DIR / ".git").exists():
        run("git init")
        run('git config user.name "Project Autonomous Agent"')
        run('git config user.email "agent@local.local"')
        log("✅ Git-Repo initialisiert")
    
    # Sync
    sync_skills()
    sync_cronjobs()
    sync_config()
    sync_scripts()
    
    # Git
    changed = git_commit_and_tag()
    
    log("=== Sync Abgeschlossen ===")
    return 0 if changed else 1

if __name__ == "__main__":
    sys.exit(main())
