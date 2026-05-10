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
