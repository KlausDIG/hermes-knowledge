#!/usr/bin/env python3
"""
Nextcloud rclone Setup - Nicht-interaktiv
Liest Credentials aus ~/.config/nextcloud/.env
"""
import os, subprocess, sys
from pathlib import Path
from urllib.parse import urlparse

HOME = Path.home()
ENV_FILE = HOME / ".config/nextcloud/.env"
RCLONE_CONF = HOME / ".config/rclone/rclone.conf"

def create_env_template():
    """Erstellt .env Template"""
    template = """# Nextcloud Zugangsdaten
# WICHTIG: Diese Datei niemals im Chat teilen!

NEXTCLOUD_URL=https://cloud.dein-server.de
NEXTCLOUD_USER=dein-benutzername
NEXTCLOUD_PASS=dein-app-token
MOUNT_POINT=/home/klausd/Nextcloud

# Optionale Einstellungen
CACHE_MAX_SIZE=100M
CACHE_MAX_AGE=1h
"""
    
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    ENV_FILE.write_text(template)
    os.chmod(ENV_FILE, 0o600)
    
    print("✅ Template erstellt:")
    print(f"   {ENV_FILE}")
    print()
    print("Befehl zum Bearbeiten:")
    print(f"   nano {ENV_FILE}")
    print()
    print("Fülle URL, Benutzername und App-Token ein.")
    print("App-Token erstellen: Nextcloud → Einstellungen → Sicherheit → Geräte & Sitzungen → App-Passwort erstellen")
    return False

def load_env():
    """Lädt .env Datei"""
    if not ENV_FILE.exists():
        print("❌ .env Datei nicht gefunden!")
        return create_env_template()
    
    env = {}
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                env[key] = val
    
    required = ['NEXTCLOUD_URL', 'NEXTCLOUD_USER', 'NEXTCLOUD_PASS']
    missing = [k for k in required if k not in env or not env[k]]
    
    if missing:
        print(f"❌ Fehlende Werte in .env: {', '.join(missing)}")
        print(f"   Bitte bearbeite: {ENV_FILE}")
        return None
    
    return env

def test_nextcloud_url(url):
    """Testet ob URL erreichbar ist"""
    import urllib.request
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status < 400
    except Exception as e:
        print(f"⚠️ URL-Test fehlgeschlagen: {e}")
        return False

def setup_rclone(env):
    """Konfiguriert rclone"""
    url = env['NEXTCLOUD_URL'].rstrip('/')
    user = env['NEXTCLOUD_USER']
    password = env['NEXTCLOUD_PASS']
    mount = env.get('MOUNT_POINT', str(HOME / 'Nextcloud'))
    
    # Passwort verschlüsseln
    r = subprocess.run(
        ['rclone', 'obscure', password],
        capture_output=True, text=True
    )
    
    if r.returncode != 0:
        print(f"❌ Passwort-Verschlüsselung fehlgeschlagen: {r.stderr}")
        return False
    
    obscured_pass = r.stdout.strip()
    
    # rclone.conf erstellen
    rclone_conf_dir = RCLONE_CONF.parent
    rclone_conf_dir.mkdir(parents=True, exist_ok=True)
    
    config = f"""[nextcloud]
type = webdav
url = {url}/remote.php/dav/files/{user}
vendor = nextcloud
user = {user}
pass = {obscured_pass}
"""
    
    # Prüfe ob bereits andere Remotes existieren
    existing = ""
    if RCLONE_CONF.exists():
        with open(RCLONE_CONF) as f:
            existing = f.read()
        if '[nextcloud]' in existing:
            print("⚠️ nextcloud Remote existiert bereits - wird überschrieben")
            # Entferne alten nextcloud Block
            lines = existing.split('\n')
            filtered = []
            skip = False
            for line in lines:
                if line.startswith('[nextcloud]'):
                    skip = True
                elif skip and line.startswith('['):
                    skip = False
                if not skip:
                    filtered.append(line)
            existing = '\n'.join(filtered)
    
    RCLONE_CONF.write_text(existing + config)
    os.chmod(RCLONE_CONF, 0o600)
    
    print(f"✅ rclone config: {RCLONE_CONF}")
    return True

def create_systemd_service(env):
    """Erstellt systemd Service"""
    mount = env.get('MOUNT_POINT', str(HOME / 'Nextcloud'))
    cache_size = env.get('CACHE_MAX_SIZE', '100M')
    cache_age = env.get('CACHE_MAX_AGE', '1h')
    
    service_dir = HOME / ".config/systemd/user"
    service_dir.mkdir(parents=True, exist_ok=True)
    
    service_file = service_dir / "nextcloud-mount.service"
    
    service = f"""[Unit]
Description=Nextcloud rclone mount (Cloud-First)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStartPre=/bin/mkdir -p {mount}
ExecStart=/snap/bin/rclone mount nextcloud: {mount} \\
    --vfs-cache-mode minimal \\
    --vfs-cache-max-size {cache_size} \\
    --vfs-cache-max-age {cache_age} \\
    --buffer-size 0 \\
    --dir-cache-time 5m \\
    --poll-interval 15s \\
    --log-level INFO \\
    --log-file /tmp/rclone-nextcloud.log
ExecStop=/bin/fusermount -u {mount}
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
"""
    
    service_file.write_text(service)
    print(f"✅ Service: {service_file}")
    
    # Neuladen
    subprocess.run(['systemctl', '--user', 'daemon-reload'], capture_output=True)
    subprocess.run(['systemctl', '--user', 'enable', 'nextcloud-mount.service'], capture_output=True)
    print("✅ Service aktiviert")
    
    return True

def create_directory_structure():
    """Erstellt Verzeichnisstruktur in Nextcloud"""
    dirs = [
        "Dokumente/DIN5008",
        "Dokumente/Geschäftsbriefe",
        "Dokumente/Auswertungen",
        "Dokumente/Projekte",
        "Backups/Dotfiles",
        "Backups/Scripts",
        "Entwicklung/Scripts",
        "Entwicklung/Workflows",
    ]
    
    print("\n📁 Erstelle Verzeichnisstruktur in Nextcloud...")
    for d in dirs:
        r = subprocess.run(
            ['rclone', 'mkdir', f'nextcloud:/{d}'],
            capture_output=True
        )
        if r.returncode == 0:
            print(f"   ✅ {d}")
        else:
            print(f"   ⚠️ {d} (möglicherweise bereits vorhanden)")

def test_connection():
    """Testet Nextcloud-Verbindung"""
    print("\n🧪 Teste Verbindung...")
    r = subprocess.run(
        ['rclone', 'ls', 'nextcloud:'],
        capture_output=True, text=True
    )
    
    if r.returncode == 0:
        print("✅ Verbindung erfolgreich!")
        if r.stdout.strip():
            print("   Dateien:")
            for line in r.stdout.strip().split('\n')[:5]:
                print(f"     {line}")
        return True
    else:
        print(f"❌ Verbindung fehlgeschlagen: {r.stderr[:200]}")
        return False

def create_symlinks(mount_point):
    """Erstellt Symlinks für einfacheren Zugriff"""
    print("\n🔗 Erstelle Symlinks...")
    
    # ~/Documents → Nextcloud/Dokumente
    docs_link = HOME / "Documents"
    if docs_link.exists() and docs_link.is_symlink():
        docs_link.unlink()
    
    if not docs_link.exists():
        docs_link.symlink_to(Path(mount_point) / "Dokumente")
        print(f"   ✅ ~/Documents → Nextcloud/Dokumente")
    
    # ~/Backups → Nextcloud/Backups
    backup_link = HOME / "Backups"
    if not backup_link.exists():
        backup_link.symlink_to(Path(mount_point) / "Backups")
        print(f"   ✅ ~/Backups → Nextcloud/Backups")
    
    # ~/Developer → Nextcloud/Entwicklung (optional, falls nicht vorhanden)
    dev_link = HOME / "Developer-Cloud"
    if not dev_link.exists():
        dev_link.symlink_to(Path(mount_point) / "Entwicklung")
        print(f"   ✅ ~/Developer-Cloud → Nextcloud/Entwicklung")

def main():
    print("══════════════════════════════════════════════════════════")
    print("  ☁️  Nextcloud rclone Setup v2.0")
    print("══════════════════════════════════════════════════════════\n")
    
    # 1. .env laden
    env = load_env()
    if not env:
        return 1
    
    print(f"✅ .env geladen: {ENV_FILE}")
    print(f"   URL: {env['NEXTCLOUD_URL']}")
    print(f"   User: {env['NEXTCLOUD_USER']}")
    print()
    
    # 2. rclone konfigurieren
    if not setup_rclone(env):
        return 1
    
    # 3. Verzeichnisstruktur
    create_directory_structure()
    
    # 4. Verbindung testen
    if not test_connection():
        print("\n⚠️ Setup unvollständig - bitte .env prüfen")
        return 1
    
    # 5. systemd Service
    create_systemd_service(env)
    
    # 6. Symlinks
    mount = env.get('MOUNT_POINT', str(HOME / 'Nextcloud'))
    create_symlinks(mount)
    
    # 7. Zusammenfassung
    print("\n══════════════════════════════════════════════════════════")
    print("  🎉 SETUP ABGESCHLOSSEN")
    print("══════════════════════════════════════════════════════════\n")
    
    print("Strategie: Cloud-First (minimale lokale Speichernutzung)")
    print(f"   Mount-Punkt: {mount}")
    print(f"   Cache:       ~/.cache/rclone-nextcloud/ (max {env.get('CACHE_MAX_SIZE', '100M')})")
    print()
    print("Wichtige Befehle:")
    print(f"   systemctl --user start nextcloud-mount     → Mount starten")
    print(f"   systemctl --user status nextcloud-mount    → Status prüfen")
    print(f"   rclone ls nextcloud:                        → Dateien auflisten")
    print(f"   rclone sync nextcloud:/Dokumente ~/Backup   → Backup erstellen")
    print()
    print("Symlinks:")
    print(f"   ~/Documents      → Nextcloud/Dokumente")
    print(f"   ~/Backups        → Nextcloud/Backups")
    print(f"   ~/Developer-Cloud → Nextcloud/Entwicklung")
    print()
    print("⚠️ WICHTIG: Dotfiles bleiben lokal (~/.cfg)")
    print("   Nur Dokumente/Backups werden in Cloud gespeichert")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
