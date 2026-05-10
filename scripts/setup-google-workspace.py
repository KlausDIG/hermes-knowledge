#!/usr/bin/env python3
"""
DIN 5008 Google Workspace OAuth2 Setup
Interaktive Authentifizierung ohne Token im Chat
"""
import os, sys, json, webbrowser, http.server, socketserver, threading
from pathlib import Path
from urllib.parse import urlparse, parse_qs

HOME = Path.home()
OAUTH_DIR = HOME / ".config/din5008-oauth"
TOKEN_FILE = OAUTH_DIR / "token.json"
CREDS_FILE = OAUTH_DIR / "credentials.json"

SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
]

DIN5008_GUIDE = """
╔══════════════════════════════════════════════════════════════╗
║  📋 GOOGLE OAUTH2 SETUP                                       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  SCHNELLE METHODE (empfohlen):                             ║
║                                                              ║
║  1. Browser öffnen:                                        ║
║     https://console.cloud.google.com/                       ║
║                                                              ║
║  2. Neues Projekt: "din5008-editor"                         ║
║                                                              ║
║  3. APIs aktivieren:                                       ║
║     → APIs & Services → Library                             ║
║     → Suche: "Google Docs API" → ENABLE                     ║
║     → Suche: "Google Sheets API" → ENABLE                   ║
║     → Suche: "Google Drive API" → ENABLE                    ║
║                                                              ║
║  4. OAuth-Anmeldedaten erstellen:                          ║
║     → APIs & Services → Credentials                         ║
║     → "OAuth 2.0 Client ID" → "Desktop app"                 ║
║     → Name: "DIN 5008 Desktop"                              ║
║     → CREATE                                               ║
║                                                              ║
║  5. JSON herunterladen → nach ~/.config/din5008-oauth/     ║
║     verschieben als "credentials.json"                      ║
║                                                              ║
║  6. Dieses Skript erneut ausführen                          ║
║                                                              ║
║  ALTERNATIVE (ohne Google Cloud Console):                  ║
║                                                              ║
║  Verwende nur lokale Markdown-Generierung                    ║
║  → Briefe/Tabelle werden als Dateien gespeichert            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

def print_guide():
    print(DIN5008_GUIDE)

class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """Empfängt Google OAuth Redirect"""
    
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        if 'code' in params:
            code = params['code'][0]
            
            # Token austauschen
            self.server.auth_code = code
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html><head><style>
                body { font-family: Arial; text-align: center; padding: 50px; }
                .success { color: green; font-size: 24px; }
                </style></head><body>
                <div class="success">Authentication successful!</div>
                <p>You can close this window and return to the terminal.</p>
                </body></html>
            """)
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Error: No code received")
    
    def log_message(self, format, *args):
        pass  # Silent

def setup_oauth_webserver():
    """Startet lokaler Webserver für OAuth Callback"""
    with socketserver.TCPServer(("127.0.0.1", 8085), OAuthCallbackHandler) as httpd:
        httpd.auth_code = None
        httpd.handle_request()
        return httpd.auth_code

def check_credentials():
    """Prüft ob OAuth Credentials vorhanden"""
    if CREDS_FILE.exists():
        return True
    return False

def check_token():
    """Prüft ob gültiger Token vorhanden"""
    if TOKEN_FILE.exists():
        try:
            data = json.loads(TOKEN_FILE.read_text())
            if data.get('token'):
                return True
        except:
            pass
    return False

def authenticate():
    """Führt OAuth-Flow durch"""
    
    if not CREDS_FILE.exists():
        print("❌ OAuth Credentials nicht gefunden")
        print_guide()
        print(f"\n📌 Erstelle Verzeichnis: {OAUTH_DIR}")
        OAUTH_DIR.mkdir(parents=True, exist_ok=True)
        print(f"   Speichere credentials.json dort ab")
        print(f"   Dann: python3 {__file__}")
        return False
    
    # Credentials laden
    try:
        creds_data = json.loads(CREDS_FILE.read_text())
        if 'installed' in creds_data:
            client_id = creds_data['installed']['client_id']
            client_secret = creds_data['installed']['client_secret']
            redirect_uri = 'http://localhost:8085'
        elif 'web' in creds_data:
            client_id = creds_data['web']['client_id']
            client_secret = creds_data['web']['client_secret']
            redirect_uri = 'http://localhost:8085'
        else:
            print("⚠️ Ungültiges credentials.json Format")
            return False
    except Exception as e:
        print(f"⚠️ Fehler beim Lesen der Credentials: {e}")
        return False
    
    # Auth URL erstellen
    from urllib.parse import urlencode
    
    auth_params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': ' '.join(SCOPES),
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(auth_params)}"
    
    print("🌐 Öffne Browser für Google OAuth...")
    print("   Wenn der Browser nicht öffnet, kopiere diese URL:")
    print(f"   {auth_url[:80]}...")
    print("")
    
    # Browser öffnen
    webbrowser.open(auth_url)
    
    # Webserver starten
    print("⏳ Warte auf Authentifizierung...")
    auth_code = setup_oauth_webserver()
    
    if auth_code:
        print("✅ Auth-Code empfangen, tausche Token...")
        
        # Token austauschen
        import urllib.request
        
        token_data = {
            'code': auth_code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        req = urllib.request.Request(
            'https://oauth2.googleapis.com/token',
            data=json.dumps(token_data).encode(),
            headers={'Content-Type': 'application/json'}
        )
        
        try:
            with urllib.request.urlopen(req) as resp:
                token_response = json.loads(resp.read())
                
                # Token speichern
                TOKEN_FILE.write_text(json.dumps(token_response, indent=2))
                print(f"✅ Token gespeichert: {TOKEN_FILE}")
                
                # Berechtigungen setzen
                os.chmod(TOKEN_FILE, 0o600)
                
                print("\n🎉 Google Workspace Integration aktiv!")
                print("   Du kannst jetzt Briefe direkt in Google Docs erstellen.")
                return True
                
        except Exception as e:
            print(f"❌ Token-Austausch fehlgeschlagen: {e}")
            return False
    else:
        print("❌ Kein Auth-Code empfangen")
        return False

def main():
    print("══════════════════════════════════════════════════════════")
    print("  🤖 DIN 5008 Google Workspace OAuth2 Setup")
    print("══════════════════════════════════════════════════════════\n")
    
    # Verzeichnis erstellen
    OAUTH_DIR.mkdir(parents=True, exist_ok=True)
    
    # Prüfungen
    if check_token():
        print("✅ Google Workspace bereits authentifiziert!")
        print(f"   Token: {TOKEN_FILE}")
        
        # Test: Auf Google zugreifen
        print("\n🧪 Teste Zugriff...")
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
            docs = build('docs', 'v1', credentials=creds)
            
            # Probe: Liste erste 5 Docs
            result = docs.documents().list().execute()
            print(f"✅ Zugriff funktioniert! (keine Fehler)")
            
        except Exception as e:
            print(f"⚠️ Token eventuell abgelaufen: {e}")
            print("   Starte Re-Authentifizierung...")
            authenticate()
        
        return 0
    
    if not check_credentials():
        print("❌ OAuth Credentials nicht gefunden")
        print_guide()
        
        # Verzeichnis erstellen
        OAUTH_DIR.mkdir(parents=True, exist_ok=True)
        print(f"\n📁 Erstellt: {OAUTH_DIR}")
        print("   Bitte credentials.json dort speichern.")
        print("   Danach: python3 ~/Developer/scripts/setup-google-workspace.py")
        return 1
    
    # Authentifizierung starten
    print("✅ Credentials gefunden")
    print("   Starte OAuth-Flow...\n")
    
    if authenticate():
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())
