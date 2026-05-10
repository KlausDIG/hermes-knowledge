#!/usr/bin/env python3
"""
Einfacher Google Service Account Setup
Braucht kein OAuth im Browser!
"""
import os, json
from pathlib import Path

HOME = Path.home()

print("══════════════════════════════════════════════════════════")
print("  🔑 GOOGLE SERVICE ACCOUNT SETUP")
print("══════════════════════════════════════════════════════════\n")

print("Diese Methode braucht keinen Browser-Login!")
print()
print("SCHRITTE:")
print()
print("[1] Browser: https://console.cloud.google.com/")
print("[2] Projekt wählen oder erstellen: 'din5008-editor'")
print("[3] APIs aktivieren:")
print("    ☰ → APIs & Dienste → Bibliothek")
print("    → 'Google Docs API' → AKTIVIEREN")
print("    → 'Google Sheets API' → AKTIVIEREN")
print()
print("[4] Service Account erstellen:")
print("    ☰ → IAM & Admin → Service Accounts")
print("    → 'Service Account erstellen'")
print("    Name: 'din5008-sa'")
print("    Beschreibung: 'DIN 5008 Automation Account'")
print("    → ERSTELLEN UND FORTFAHREN")
print()
print("[5] Rolle zuweisen:")
print("    → Rolle: 'Editor' (unter 'Basic')")
print("    → FORTFAHREN")
print("    → FERTIG")
print()
print("[6] KEY GENERIEREN! (Wichtigste Schritt)")
print("    → Klicke auf den erstellten Service Account")
print("    → Reiter: 'Schlüssel'")
print("    → 'Schlüssel hinzufügen' → 'Neuen Schlüssel erstellen'")
print("    → Typ: JSON")
print("    → 'ERSTELLEN'")
print("    → Datei wird AUTOMATISCH heruntergeladen!")
print()
print("[7] Datei verschieben:")
print(f"    Im Terminal:")
print(f"    mv ~/Downloads/*.json ~/.config/din5008-oauth/service-account.json")
print()
print("══════════════════════════════════════════════════════════\n")

# Prüfe ob bereits vorhanden
sa_file = HOME / ".config/din5008-oauth/service-account.json"
if sa_file.exists():
    print("✅ Service Account bereits vorhanden!")
    print(f"   {sa_file}")
    print("\nTeste Verbindung...")
    
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        creds = service_account.Credentials.from_service_account_file(
            str(sa_file),
            scopes=['https://www.googleapis.com/auth/documents']
        )
        
        docs = build('docs', 'v1', credentials=creds)
        result = docs.documents().list().execute()
        
        print(f"✅ Verbindung erfolgreich!")
        print(f"   Gefundene Docs: {len(result.get('documents', []))}")
        
    except Exception as e:
        print(f"⚠️ Fehler: {e}")
