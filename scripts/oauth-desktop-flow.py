#!/usr/bin/env python3
"""
Google OAuth Desktop Flow
Erstellt einen Token aus dem Desktop Client
"""
import json, os, urllib.request, urllib.parse, webbrowser
from pathlib import Path
from datetime import datetime, timedelta

HOME = Path.home()
CRED_FILE = HOME / ".config/din5008-oauth/service-account.json"
TOKEN_FILE = HOME / ".config/din5008-oauth/token.json"
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
]

def load_client_credentials():
    """Lädt OAuth Desktop Client"""
    with open(CRED_FILE) as f:
        data = json.load(f)
    return data['installed']

def generate_auth_url(client_id):
    """Erstellt Google OAuth URL"""
    params = {
        'client_id': client_id,
        'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
        'response_type': 'code',
        'scope': ' '.join(SCOPES),
        'access_type': 'offline',
        'prompt': 'consent'
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

def exchange_code(client_id, client_secret, code):
    """Tauscht Code gegen Token"""
    data = urllib.parse.urlencode({
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
        'grant_type': 'authorization_code',
    }).encode()
    
    req = urllib.request.Request(
        'https://oauth2.googleapis.com/token',
        data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def main():
    print("══════════════════════════════════════════════════════════")
    print("  🔑 Google OAuth Desktop Flow")
    print("══════════════════════════════════════════════════════════\n")
    
    # Prüfe Client
    if not CRED_FILE.exists():
        print("❌ Keine Client Credentials gefunden!")
        return 1
    
    client = load_client_credentials()
    client_id = client['client_id']
    client_secret = client['client_secret']
    
    print(f"✅ Client geladen: {client_id[:20]}...")
    print()
    
    # Prüfe ob bereits Token existiert
    if TOKEN_FILE.exists():
        print("⚠️ Token existiert bereits!")
        print("   Teste Verbindung...")
        
        try:
            token_data = json.loads(TOKEN_FILE.read_text())
            
            # Test mit einfachem Request
            req = urllib.request.Request(
                'https://docs.googleapis.com/v1/documents?pagesize=1',
                headers={'Authorization': f"Bearer {token_data['access_token']}"}
            )
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                print("✅ Token gültig!")
                print(f"   Ablauf: {token_data.get('expires_in', 'unbekannt')} Sekunden")
                return 0
                
        except Exception as e:
            print(f"⚠️ Token ungültig: {e}")
            print("   Neue Authentifizierung nötig\n")
    
    # Authorization URL
    auth_url = generate_auth_url(client_id)
    
    print("══════════════════════════════════════════════════════════")
    print("  SCHRITTE:")
    print("══════════════════════════════════════════════════════════\n")
    
    print("[1] Öffne diese URL im Browser:")
    print("    (Wenn nicht automatisch geöffnet)")
    print()
    print(f"    {auth_url}")
    print()
    
    # Browser öffnen (nur im Vordergrund)
    try:
        webbrowser.open(auth_url)
        print("🌐 Browser wird geöffnet...")
    except:
        pass
    
    print()
    print("[2] Melde dich mit Google an und klicke 'Weiter'")
    print()
    
    print("[3] Bestätige die Berechtigungen:")
    print("    ☑ Google Docs")
    print("    ☑ Google Sheets")
    print("    ☑ Google Drive")
    print()
    
    print("[4] Du erhältst einen CODE (z.B. '4/xxxx')")
    print("    → Kopiere diesen Code")
    print()
    
    # Code abfragen (nicht im Chat posten!)
    print("══════════════════════════════════════════════════════════")
    print()
    
    # Nutze Datei-basierte Eingabe (sicherer)
    code_file = HOME / ".config/din5008-oauth/code.txt"
    if code_file.exists():
        code_file.unlink()
    
    print(f"Bitte Code in diese Datei einfügen:")
    print(f"  nano {code_file}")
    print(f"  (Einfügen → Strg+O → Enter → Strg+X)")
    print()
    
    # Warte auf Datei
    import time
    timeout = 300  # 5 Minuten
    waited = 0
    
    print("⏳ Warte auf Code-Datei...")
    while not code_file.exists() and waited < timeout:
        time.sleep(2)
        waited += 2
        if waited % 20 == 0:
            print(f"   ... noch warte ({waited}s)")
    
    if not code_file.exists():
        print("❌ Timeout! Kein Code empfangen.")
        return 1
    
    code = code_file.read_text().strip()
    code_file.unlink()  # Datei löschen
    
    if not code:
        print("❌ Code-Datei war leer!")
        return 1
    
    print("✅ Code empfangen!")
    print("   Tausche gegen Token...")
    
    # Token austauschen
    try:
        token_data = exchange_code(client_id, client_secret, code)
        
        # Speichern
        TOKEN_FILE.write_text(json.dumps(token_data, indent=2))
        os.chmod(TOKEN_FILE, 0o600)
        
        print("✅ Token gespeichert!")
        print(f"   Datei: {TOKEN_FILE}")
        print(f"   Ablauf: {token_data.get('expires_in', '?')} Sekunden")
        print()
        
        if 'refresh_token' in token_data:
            print("🔄 Refresh Token vorhanden (Token wird automatisch erneuert)")
        
        # Test
        print("\n🧪 Teste Verbindung...")
        req = urllib.request.Request(
            'https://docs.googleapis.com/v1/documents?pagesize=1',
            headers={'Authorization': f"Bearer {token_data['access_token']}"}
        )
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            print("✅ Google API Verbindung erfolgreich!")
            print()
            print("══════════════════════════════════════════════════════════")
            print("  🎉 Google Workspace ist jetzt aktiv!")
            print("══════════════════════════════════════════════════════════")
            print()
            print("Verwendung:")
            print("  python3 ~/Developer/scripts/ga-brief.py")
            print("  python3 ~/Developer/scripts/ga-sheets.py")
        
        return 0
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
