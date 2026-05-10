#!/usr/bin/env python3
"""
DIN 5008 Auswertungstabelle → Google Sheets
Erstellt professionelle Tabellen mit Formeln
"""
import os, sys
from pathlib import Path
from datetime import datetime, timedelta

HOME = Path.home()
TOKEN_FILE = HOME / ".config/din5008-oauth/token.json"

def get_sheets_service():
    """Verbindet zu Google Sheets API"""
    
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(
                str(TOKEN_FILE),
                ['https://www.googleapis.com/auth/spreadsheets']
            )
            return build('sheets', 'v4', credentials=creds)
        
        # Service Account
        sa = HOME / ".config/gcloud/din5008-service-account.json"
        if sa.exists():
            from google.oauth2 import service_account
            creds = service_account.Credentials.from_service_account_file(
                str(sa),
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            return build('sheets', 'v4', credentials=creds)
            
    except ImportError:
        print("⚠️ Google API nicht installiert")
    except Exception as e:
        print(f"⚠️ Auth-Fehler: {e}")
    
    return None

def create_auswertung(title="Projektauswertung", daten=None):
    """Erstellt Auswertungstabelle in Sheets"""
    
    service = get_sheets_service()
    if not service:
        print("❌ Google Sheets API nicht verfügbar")
        print("   Setup: python3 ~/Developer/scripts/setup-google-workspace.py")
        return None
    
    # Neue Tabelle erstellen
    spreadsheet = {
        'properties': {
            'title': f'DIN 5008 {title} - {datetime.now().strftime("%Y-%m-%d")}'
        }
    }
    
    result = service.spreadsheets().create(body=spreadsheet).execute()
    sheet_id = result['spreadsheetId']
    
    # Standarddaten
    if not daten:
        daten = {
            'headers': ['Phase', 'Geplant [h]', 'Ist [h]', 'Abweichung', 'Status', 'Trend'],
            'rows': [
                ['Konzeption', 40, 35, '=C2-B2', '✅', '↓'],
                ['Entwicklung', 120, 110, '=C3-B3', '🔄', '↓'],
                ['Testing', 30, 25, '=C4-B4', '🔄', '↓'],
                ['Dokumentation', 20, 30, '=C5-B5', '⚠️', '↑'],
                ['Deployment', 15, 12, '=C6-B6', '✅', '↓'],
                ['Gesamt', '=SUM(B2:B6)', '=SUM(C2:C6)', '=SUM(D2:D6)', '✅', '-'],
            ]
        }
    
    # Werte schreiben
    values = [daten['headers']] + daten['rows']
    
    body = {
        'values': values
    }
    
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range='A1',
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()
    
    # Formatierung
    requests = [
        # Header formatieren
        {
            'repeatCell': {
                'range': {
                    'sheetId': 0,
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                    'startColumnIndex': 0,
                    'endColumnIndex': 6
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {'red': 0.85, 'green': 0.85, 'blue': 0.85},
                        'horizontalAlignment': 'CENTER',
                        'textFormat': {
                            'bold': True,
                            'fontSize': 11,
                            'fontFamily': 'Arial'
                        }
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
            }
        },
        # Spaltenbreiten
        {
            'updateDimensionProperties': {
                'range': {
                    'sheetId': 0,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': 6
                },
                'properties': {
                    'pixelSize': 150
                },
                'fields': 'pixelSize'
            }
        },
        # Zahlenformat
        {
            'repeatCell': {
                'range': {
                    'sheetId': 0,
                    'startRowIndex': 1,
                    'endRowIndex': 6,
                    'startColumnIndex': 1,
                    'endColumnIndex': 3
                },
                'cell': {
                    'userEnteredFormat': {
                        'numberFormat': {
                            'type': 'NUMBER',
                            'pattern': '#,##0'
                        }
                    }
                },
                'fields': 'userEnteredFormat(numberFormat)'
            }
        },
        # Formeln: Abweichung rot/grün
        {
            'addConditionalFormatRule': {
                'rule': {
                    'ranges': [{
                        'sheetId': 0,
                        'startRowIndex': 1,
                        'endRowIndex': 6,
                        'startColumnIndex': 3,
                        'endColumnIndex': 4
                    }],
                    'booleanRule': {
                        'condition': {
                            'type': 'LESS_THAN',
                            'values': [{'userEnteredValue': '0'}]
                        },
                        'format': {
                            'textFormat': {
                                'foregroundColor': {'red': 0, 'green': 0.5, 'blue': 0}
                            }
                        }
                    }
                }
            }
        },
        # Summenzeile fett
        {
            'repeatCell': {
                'range': {
                    'sheetId': 0,
                    'startRowIndex': 6,
                    'endRowIndex': 7,
                    'startColumnIndex': 0,
                    'endColumnIndex': 6
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'bold': True
                        },
                        'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
                    }
                },
                'fields': 'userEnteredFormat(textFormat,backgroundColor)'
            }
        }
    ]
    
    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={'requests': requests}
    ).execute()
    
    url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/edit'
    
    print(f"✅ Tabelle erstellt: {url}")
    
    # Öffnen
    import webbrowser
    webbrowser.open(url)
    
    return {'id': sheet_id, 'url': url}

def main():
    print("══════════════════════════════════════════════════════════")
    print("  📊 DIN 5008 Tabelle → Google Sheets")
    print("══════════════════════════════════════════════════════════\n")
    
    result = create_auswertung()
    
    if result:
        print(f"\n✅ Erfolgreich!")
        print(f"   Öffne: {result['url']}")
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())
