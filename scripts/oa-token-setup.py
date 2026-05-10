#!/usr/bin/env python3
"""
DIN 5008 → Google OAuth Playground
Einfaches Token-Setup ohne Service Account
Usage: python3 oa-token-setup.py
"""
import json, os
from pathlib import Path

HOME = Path.home()
TOKEN_DIR = HOME / ".config/din5008-oauth"
TOKEN_FILE = TOKEN_DIR / "token.json"

def save_token(token_text):
    """Speichert Token sicher"""
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(token_text.strip())
    os.chmod(TOKEN_FILE, 0o600)
    print(f"✅ Token gespeichert: {TOKEN_FILE}")

def test_token():
    """Testet Google API mit Token"""
    if not TOKEN_FILE.exists():
        print("❌ Kein Token gefunden")
        return False
    
    import subprocess, urllib.request
    token = TOKEN_FILE.read_text().strip()
    
    # Teste Google Docs API
    req = urllib.request.Request(
        'https://docs.googleapis.com/v1/documents?pagesize=1',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    try:
        with urllib.request.urlopen(req) as resp:
            print("✅ Google API Verbindung erfolgreich!")
            return True
    except Exception as e:
        print(f"⚠️ Fehler: {e}")
        print("   Token eventuell abgelaufen oder ungültig")
        return False

def main():
    print("══════════════════════════════════════════════════════════")
    print("  🔑 OAuth Playground Token Setup")
    print("═══════════════════════════════════""═══════════════════════")
    print()
    print("HINWEIS: Token niemals im Chat posten!")
    print()
    print("Öffne im Browser:")
    print("  https://developers.google.com/oauthplayground")
    print()
    print("Schritte:")
    print("  1. Rechts: ☑ 'Use your own OAuth credentials'")
    print("     (Oder lass es leer für Demo-Mode)")
    print()
    print("  2. Links bei 'Select & authorize APIs':")
    print("     Tippe ein: 'docs' → wähle 'Docs API v1'")
    print("     Tippe ein: 'sheets' → wähle 'Sheets API v4'")
    print()
    print("  3. Klicke 'Authorize APIs'")
    print("     → Melde dich mit Google an")
    print("     → Klicke 'Select All' → 'Weiter'")
    print()
    print("  4. Klicke 'Exchange authorization code for tokens'")
    print()
    print("  5. Kopiere das 'Access token' (langer String)")
    print()
    print("══════════════════════════════════════════════════════════")
    
    if TOKEN_FILE.exists():
        print()
        print(f"✅ Token existiert bereits: {TOKEN_FILE}")
        print("   Teste Verbindung...")
        if test_token():
            return 0
        print("   Token ungültig → Setup wiederholen")
    
    print()
    print("Nach Kopiervorgang:")
    print(f"  nano {TOKEN_FILE}")
    print()
    print("  Einfügen (Strg+Umschalt+V), speichern (Strg+O), beenden (Ctrl+X)")
    print()
    
    return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
