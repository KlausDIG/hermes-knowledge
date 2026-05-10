#!/usr/bin/env python3
"""
DIN 5008 Brief → Google Docs
Erstellt professionelle Geschäftsbriefe direkt in Google Docs
"""
import os, sys, json, subprocess
from pathlib import Path
from datetime import datetime

HOME = Path.home()
TOKEN_FILE = HOME / ".config/din5008-oauth/token.json"
CREDS_FILE = HOME / ".config/din5008-oauth/credentials.json"

def get_google_creds():
    """Holt Google OAuth Credentials"""
    
    TOKEN_DIR = HOME / ".config/din5008-oauth"
    TOKEN_FILE = TOKEN_DIR / "token.json"
    
    # 1. OAuth Playground Token (einfachst)
    if TOKEN_FILE.exists():
        try:
            token_text = TOKEN_FILE.read_text().strip()
            # Prüfe ob es ein Bearer Token ist (kein JSON)
            if not token_text.startswith('{'):
                return {'token': token_text, 'type': 'oauth_playground'}
            
            # JSON Token (OAuth2)
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE))
            if creds.valid:
                return {'token': creds.token, 'type': 'oauth2'}
            return None
        except Exception:
            pass
    
    # 2. Service Account
    sa_file = HOME / ".config/gcloud/din5008-service-account.json"
    if sa_file.exists():
        try:
            from google.oauth2 import service_account
            creds = service_account.Credentials.from_service_account_file(
                str(sa_file),
                scopes=['https://www.googleapis.com/auth/documents']
            )
            # Konvertiere zu Dict
            from googleapiclient.discovery import build
            return {'service': build('docs', 'v1', credentials=creds), 'type': 'service'}
        except Exception:
            pass
    
    return None

def create_din5008_brief(**kwargs):
    """Erstellt DIN 5008 Brief in Google Docs"""
    
    # Default Werte
    defaults = {
        'absender_firma': 'KlausDIG Services',
        'absender_name': 'Klaus Dreisbusch',
        'absender_strasse': 'Musterstraße 1',
        'absender_plz': '12345',
        'absender_ort': 'Musterstadt',
        'absender_tel': '+49 123 456789',
        'absender_email': 'kontakt@klausdig.de',
        'empfaenger_firma': 'Muster GmbH',
        'empfaenger_name': 'Frau Maxi Mustermann',
        'empfaenger_strasse': 'Beispielweg 42',
        'empfaenger_plz': '54321',
        'empfaenger_ort': 'Beispielstadt',
        'ihr_zeichen': '',
        'unser_zeichen': f'KH-{datetime.now().year}-001',
        'datum': datetime.now().strftime('%d. %B %Y'),
        'betreff': 'Angebotserstellung für IT-Dienstleistungen',
        'anrede': 'Sehr geehrte Frau Mustermann,',
        'text': "vielen Dank für Ihre Anfrage.\n\nGerne unterbreiten wir Ihnen folgendes Angebot:\n\n1. Konzeption und Beratung\n2. Entwicklung\n3. Support\n\nWir freuen uns auf Ihre Rückmeldung.",
        'gruss': 'Mit freundlichen Grüßen',
        'unterschrift': 'Klaus Dreisbusch',
        'position': 'Geschäftsführer',
        'anlagen': ['Angebot_001.pdf'],
    }
    from googleapiclient.discovery import build
    
    cred_info = get_google_creds()
    if not cred_info:
        print("❌ Keine Google API Credentials gefunden")
        print("\nSetup:")
        print("  a) OAuth2: python3 ~/Developer/scripts/setup-google-workspace.py")
        print("  b) Playground:")
        print("     1. https://developers.google.com/oauthplayground")
        print("     2. Autorisiere Docs API")
        print("     3. Kopiere Access Token")
        print("     4. nano ~/.config/din5008-oauth/token.json")
        print("  c) Service Account: Google Cloud Console → JSON Key")
        return None
    
    # Verbindung aufbauen je nach Type
    if cred_info.get('type') == 'oauth_playground':
        # Eigenes Request mit Bearer Token
        import urllib.request
        token = cred_info['token']
        
        # Direct requests statt Google Client Library
        # Aber wir nutzen trotzdem build() mit dem Token als api_key Ersatz
        # Workaround: Custom HTTP
        from googleapiclient.discovery import build, _auth
        from google.auth.credentials import Credentials as GenericCredentials
        
        class BearerTokenAuth(GenericCredentials):
            def __init__(self, token):
                super().__init__()
                self._token = token
            def refresh(self, request):
                pass
            def apply(self, headers, token=None):
                headers['Authorization'] = f'Bearer {self._token}'
        
        creds = BearerTokenAuth(token)
        docs = build('docs', 'v1', credentials=creds)
        
    elif cred_info.get('type') == 'oauth2':
        from google.oauth2.credentials import Credentials
        creds = Credentials(token=cred_info['token'])
        docs = build('docs', 'v1', credentials=creds)
        
    elif cred_info.get('type') == 'service':
        docs = cred_info['service']
    else:
        print("⚠️ Unbekannter Credential Type")
        return None
    
    # Dokument erstellen
    doc = docs.documents().create(body={
        'title': f'DIN 5008 Brief - {defaults["empfaenger_name"]} - {defaults["datum"]}'
    }).execute()
    
    doc_id = doc['documentId']
    
    # Inhalt mit Formatierung
    requests = []
    
    # Absender (kleine Schrift, oben)
    absender_text = f"{defaults['absender_firma']}\n{defaults['absender_strasse']}\n{defaults['absender_plz']} {defaults['absender_ort']}\n\n"
    
    # Empfänger (8,5cm Einzug → simuliert mit Tab)
    empfaenger_text = f"\n\n\n{defaults['empfaenger_name']}\n{defaults['empfaenger_strasse']}\n{defaults['empfaenger_plz']} {defaults['empfaenger_ort']}\n\n\n\n\n"
    
    # Bezugszeichen (rechts)
    bezugs_text = f"Ihr Zeichen:\t{defaults['ihr_zeichen'] or '---'}\nUnser Zeichen:\t{defaults['unser_zeichen']}\nDatum:\t\t{defaults['datum']}\n\n"
    
    # Betreff
    betreff_text = f"{defaults['betreff']}\n\n"
    
    # Anrede
    anrede_text = f"{defaults['anrede']}\n\n"
    
    # Text
    text_content = defaults['text'].replace('\n', '\n\n') + "\n\n"
    
    # Gruß
    gruss_text = f"{defaults['gruss']}\n\n\n\n"
    
    # Unterschrift
    sign_text = f"{defaults['unterschrift']}\n{defaults['position']}\n\n"
    
    # Anlagen
    anlagen_text = "Anlagen:\n" + '\n'.join(f'- {a}' for a in defaults['anlagen'])
    
    # Kompletten Text zusammensetzen
    full_text = absender_text + empfaenger_text + bezugs_text + betreff_text + anrede_text + text_content + gruss_text + sign_text + anlagen_text
    
    # Text einfügen
    requests.append({
        'insertText': {
            'location': {'index': 1},
            'text': full_text
        }
    })
    
    # Formatierung anwenden
    # Absender: klein (9pt)
    requests.append({
        'updateTextStyle': {
            'range': {
                'startIndex': 1,
                'endIndex': len(absender_text)
            },
            'textStyle': {
                'fontSize': {'magnitude': 9, 'unit': 'PT'},
                'weightedFontFamily': {'fontFamily': 'Arial'}
            },
            'fields': 'fontSize,weightedFontFamily'
        }
    })
    
    # Betreff: Fett
    betreff_start = len(absender_text + empfaenger_text + bezugs_text) + 1
    betreff_end = betreff_start + len(defaults['betreff'])
    requests.append({
        'updateTextStyle': {
            'range': {
                'startIndex': betreff_start,
                'endIndex': betreff_end
            },
            'textStyle': {
                'bold': True,
                'fontSize': {'magnitude': 11, 'unit': 'PT'}
            },
            'fields': 'bold,fontSize'
        }
    })
    
    # Seiteneinstellungen (A4, Ränder)
    requests.append({
        'updateDocumentStyle': {
            'documentStyle': {
                'pageSize': {
                    'width': {'magnitude': 595.276, 'unit': 'POINT'},
                    'height': {'magnitude': 841.89, 'unit': 'POINT'}
                },
                'marginTop': {'magnitude': 56.693, 'unit': 'POINT'},
                'marginBottom': {'magnitude': 56.693, 'unit': 'POINT'},
                'marginLeft': {'magnitude': 70.866, 'unit': 'POINT'},
                'marginRight': {'magnitude': 56.693, 'unit': 'POINT'},
            }
        }
    })
    
    # Anfragen ausführen
    docs.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
    
    # URL erstellen
    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    
    return {
        'id': doc_id,
        'url': doc_url,
        'empfaenger': defaults['empfaenger_name'],
        'datum': defaults['datum']
    }

def main():
    print("══════════════════════════════════════════════════════════")
    print("  📝 DIN 5008 Brief → Google Docs")
    print("══════════════════════════════════════════════════════════\n")
    
    # Prüfe ob Google API verfügbar
    creds = get_google_creds()
    if not creds:
        print("❌ Google API nicht authentifiziert")
        print("\nSetup:")
        print("  python3 ~/Developer/scripts/setup-google-workspace.py")
        print("\nOder erstelle nur lokale Datei:")
        print("  python3 ~/Developer/scripts/brief-generator.py")
        return 1
    
    print("✅ Google API verbunden\n")
    
    # Brief erstellen
    result = create_din5008_brief()
    
    if result:
        print(f"✅ Brief erstellt!")
        print(f"   Empfänger: {result['empfaenger']}")
        print(f"   Datum: {result['datum']}")
        print(f"   URL: {result['url']}")
        print(f"")
        print(f"   Öffne: xdg-open '{result['url']}'")
        
        # Automatisch öffnen
        import webbrowser
        webbrowser.open(result['url'])
        
        return 0
    else:
        print("❌ Fehler bei der Erstellung")
        return 1

if __name__ == '__main__':
    sys.exit(main())
