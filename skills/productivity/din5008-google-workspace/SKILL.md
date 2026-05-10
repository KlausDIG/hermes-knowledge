---
name: din5008-google-workspace
description: |
  Geschäftsbriefe (DIN 5008), Geschäftsberichte/Projektberichte (Google Docs) 
  und Auswertungstabellen (Google Sheets) professionell erstellen.
  Enthält Templates, Style-Guides und Google API Setup-Anleitung.
category: productivity
version: 1.0.0
---

# DIN 5008 + Google Workspace Skill

## Überblick

Erstelle professionelle Geschäftsunterlagen nach DIN 5008 Norm:
- **Geschäftsbriefe** mit korrektem Layout und Formatierung
- **Geschäftsberichte/Projektberichte** strukturiert in Google Docs
- **Auswertungstabellen** in Google Sheets mit Formeln

---

## 1. DIN 5008 Grundlagen

### Form A (Fensterbrief - empfohlen)

```
+--------------------------------------------------+
| [Firma Logo/Name]                                |
| Straße Hausnr.                                   |
| PLZ Ort                                          |
|                                                  |
|                                                  |
| Max Mustermann              <- 8,5 cm von links   |
| Musterstraße 42                                   |
| 12345 Musterstadt                                 |
|                                                  |
|                                                  |
|                                                  |
| Ihr Zeichen: MM              <- rechtsbündig      |
| Unser Zeichen: KH                                 |
| Datum: 10. Mai 2026                             |
|                                                  |
| Betreff: Angebotserstellung                       |
|                                                  |
| Sehr geehrte Frau Mustermann,                    |
|                                                  |
| Text beginnt nach 8 Zeilen vom Empfänger.       |
|                                                  |
| Mit freundlichen Grüßen                          |
|                                                  |
| (Dokument ohne Unterschrift bei E-Mail)          |
|                                                  |
| Klaus Dreisbusch                                 |
| Position                                         |
|                                                  |
| Anlagen: Angebot.pdf                             |
|                                                  |
| Verteiler: Intern                               |
+--------------------------------------------------+
```

### Regeln nach DIN 5008

| Element | Regel | Position |
|---------|-------|----------|
| Absender | Firmenname, Adresse | Oben links (klein) |
| Empfänger | Name, Straße, PLZ Ort | 8,5 cm von links, 4-5 cm von oben |
| Bezugszeichen | Ihr/Unser Zeichen, Datum | Rechtsbündig unter Empfänger |
| Betreffzeile | Prägnant, ohne "Betreff:" | Nach Bezugszeichen |
| Anrede | "Sehr geehrte Frau/Herr..." | Nach 1 Leerzeile |
| Text | Begründung, Mitteilung, Schluss | 1 Leerzeile nach Anrede |
| Grußformel | "Mit freundlichen Grüßen" | Nach Text |
| Name/Amt | Druckschrift | Nach 4 Leerzeilen |
| Anlagen/VV | Aufzählung | Nach Name |

### Zeilenabstände
- Normschrift: **11pt Arial** oder **12pt Times New Roman**
- Zeilenabstand: **1,15** (proportional)
- Seitenränder: Links 2,5 cm, Rechts 2 cm, Oben 2 cm, Unten 2 cm

---

## 2. Google Docs API Setup

### 2.1 Google Cloud Console

```bash
# 1. Google Cloud Console öffnen
xdg-open https://console.cloud.google.com/

# 2. Neues Projekt erstellen: "din5008-automation"
# 3. Google Docs API aktivieren
# 4. Google Sheets API aktivieren
# 5. Service Account erstellen
# 6. JSON Key herunterladen → ~/credentials/din5008-service-account.json
```

### 2.2 Lokale Einrichtung

```bash
# Python-Umgebung
pip3 install --user google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client gspread

# Credentials
mkdir -p ~/.config/gcloud
cp ~/Downloads/din5008-service-account.json ~/.config/gcloud/
chmod 600 ~/.config/gcloud/din5008-service-account.json

# Test
python3 -c "import gspread; print('gspread OK')"
```

---

## 3. Templates

### 3.1 Geschäftsbrief (Python Script)

```python
#!/usr/bin/env python3
"""DIN 5008 Geschäftsbrief erstellen (Google Docs)"""

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/documents']

def create_brief(
    # Absender
    absender_firma="KlausDIG Services",
    absender_strasse="Musterstraße 1",
    absender_plz="12345",
    absender_ort="Musterstadt",
    # Empfänger
    empfaenger_name="Frau Maxi Mustermann",
    empfaenger_strasse="Beispielweg 42",
    empfaenger_plz="54321",
    empfaenger_ort="Beispielstadt",
    # Bezugszeichen
    ihr_zeichen="",
    unser_zeichen="KH-2026-001",
    datum="10. Mai 2026",
    # Inhalt
    betreff="Angebotserstellung für Webentwicklung",
    anrede="Sehr geehrte Frau Mustermann,",
    text="""
vielen Dank für Ihr Interesse an unseren Dienstleistungen.

Gerne unterbreiten wir Ihnen folgendes Angebot für die Webentwicklung:

1. Konzeption und Planung
2. UI/UX Design
3. Frontend-Entwicklung (React)
4. Backend-Entwicklung (Python/FastAPI)
5. Deployment und Hosting

Wir freuen uns auf Ihre Rückmeldung.
""",
    gruss="Mit freundlichen Grüßen",
    name_unterschrift="Klaus Dreisbusch",
    position="Geschäftsführer",
    anlagen=["Angebot_Webentwicklung.pdf"],
    # Ausgabe
    output_doc_id=None  # None = neues Dokument
):
    """Erstellt DIN-5008-konformen Geschäftsbrief"""
    
    creds = service_account.Credentials.from_service_account_file(
        '/home/klausd/.config/gcloud/din5008-service-account.json',
        scopes=SCOPES
    )
    service = build('docs', 'v1', credentials=creds)
    
    # Neues Dokument erstellen oder bestehendes öffnen
    if output_doc_id:
        document = service.documents().get(documentId=output_doc_id).execute()
        doc_id = output_doc_id
    else:
        document = service.documents().create(body={
            'title': f'Brief_{empfaenger_name.replace(" ", "_")}_{datum}'
        }).execute()
        doc_id = document['documentId']
    
    # Inhalt aufbauen (formatierter Text mit Tabstopps)
    content = {
        'requests': [
            # Seiteneinstellungen (A4, Ränder)
            {'updateDocumentStyle': {
                'documentStyle': {
                    'pageSize': {'width': {'magnitude': 595.276, 'unit': 'POINT'},
                                'height': {'magnitude': 841.89, 'unit': 'POINT'}},
                    'marginTop': {'magnitude': 56.693, 'unit': 'POINT'},
                    'marginBottom': {'magnitude': 56.693, 'unit': 'POINT'},
                    'marginLeft': {'magnitude': 70.866, 'unit': 'POINT'},
                    'marginRight': {'magnitude': 56.693, 'unit': 'POINT'},
                }
            }},
            
            # Absender (klein, oben links)
            {'insertText': {
                'location': {'index': 1},
                'text': f'{absender_firma}\n{absender_strasse}\n{absender_plz} {absender_ort}\n\n\n'
            }},
            
            # Empfänger (8,5 cm Einzug)
            {'insertText': {
                'location': {'index': 1},
                'text': f'{empfaenger_name}\n{empfaenger_strasse}\n{empfaenger_plz} {empfaenger_ort}\n\n\n\n'
            }},
            
            # Bezugszeichen (rechts)
            {'insertText': {
                'location': {'index': 1},
                'text': f'Ihr Zeichen:\t{ihr_zeichen}\nUnser Zeichen:\t{unser_zeichen}\nDatum:\t\t{datum}\n\n'
            }},
            
            # Betreff
            {'insertText': {
                'location': {'index': 1},
                'text': f'{betreff}\n\n'
            }},
            
            # Anrede
            {'insertText': {
                'location': {'index': 1},
                'text': f'{anrede}\n\n'
            }},
            
            # Text
            {'insertText': {
                'location': {'index': 1},
                'text': f'{text}\n\n'
            }},
            
            # Gruß
            {'insertText': {
                'location': {'index': 1},
                'text': f'{gruss}\n\n\n\n'
            }},
            
            # Name
            {'insertText': {
                'location': {'index': 1},
                'text': f'{name_unterschrift}\n{position}\n\n'
            }},
            
            # Anlagen
            {'insertText': {
                'location': {'index': 1},
                'text': f'Anlagen:\n' + '\n'.join(f'- {a}' for a in anlagen)
            }},
        ]
    }
    
    service.documents().batchUpdate(documentId=doc_id, body=content).execute()
    
    print(f"✅ Brief erstellt: https://docs.google.com/document/d/{doc_id}/edit")
    return doc_id

if __name__ == '__main__':
    create_brief()
```

### 3.2 Projektbericht (Google Docs)

```python
"""DIN 5008 Projektbericht - Strukturvorlage"""

BERICHT_STRUKTUR = """
# Projekttitel

## 1. Zusammenfassung (Executive Summary)
- Projektziel
- Ergebnisse
- Kosten/Zeit

## 2. Projektmanagement
### 2.1 Projektauftrag
- Auftraggeber
- Projektleiter
- Zeitraum

### 2.2 Projektorganisation
- Teammitglieder
- Rollen
- Stakeholder

### 2.3 Phasenplan
| Phase | Zeitraum | Status |
|-------|----------|--------|
| Kickoff | Q1 | ✅ |
| Konzeption | Q1-Q2 | ✅ |
| Umsetzung | Q2-Q3 | 🔄 |
| Abnahme | Q4 | ⏳ |

## 3. Ist-Analyse
### 3.1 Ausgangssituation
### 3.2 Stärken/Schwächen
### 3.3 Risikoanalyse

## 4. Zielsetzung
### 4.1 Projektziele (SMART)
### 4.2 Anforderungen
### 4.3 Abgrenzung

## 5. Konzeption
### 5.1 Lösungsansatz
### 5.2 Architektur/Tech-Stack
### 5.3 UI/UX Konzept

## 6. Umsetzung
### 6.1 Entwicklung
### 6.2 Testing
### 6.3 Deployment

## 7. Ergebnisse
### 7.1 Deliverables
### 7.2 Abweichungen
### 7.3 Lessons Learned

## 8. Fazit und Ausblick
### 8.1 Zielerreichung
### 8.2 Kosten-Nutzen
### 8.3 Empfehlungen

---
Anhang A: Technische Dokumentation
Anhang B: Screenshots/Diagramme
Anhang C: Meeting-Protokolle
"""
```

### 3.3 Auswertungstabelle (Google Sheets)

```python
#!/usr/bin/env python3
"""DIN 5008 Auswertungstabelle (Google Sheets)"""

import gspread
from google.oauth2 import service_account

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def create_auswertungtabelle(title="Projektauswertung Q2 2026"):
    """Erstellt professionelle Auswertungstabelle"""
    
    creds = service_account.Credentials.from_service_account_file(
        '/home/klausd/.config/gcloud/din5008-service-account.json',
        scopes=SCOPES
    )
    
    # Google Drive API für Datei-Erstellung
    from googleapiclient.discovery import build
    drive_service = build('drive', 'v3', credentials=creds)
    
    # Spreadsheet erstellen
    spreadsheet = {
        'properties': {'title': title}
    }
    spreadsheet = drive_service.files().create(body=spreadsheet, fields='id').execute()
    spreadsheet_id = spreadsheet['id']
    
    # Google Sheets API für Formatierung
    sheets_service = build('sheets', 'v4', credentials=creds)
    
    # Blätter erstellen
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': [
            {'addSheet': {'properties': {'title': 'Dashboard'}}},
            {'addSheet': {'properties': {'title': 'Daten'}}},
            {'addSheet': {'properties': {'title': 'Diagramme'}}},
            # Titelblatt löschen
            {'deleteSheet': {'sheetId': 0}}
        ]}
    ).execute()
    
    # Dashboard formatieren
    dashboard_format = {
        'requests': [
            # Titel
            {'updateCells': {
                'range': {'sheetId': 1, 'startRowIndex': 0, 'endRowIndex': 1, 'startColumnIndex': 0, 'endColumnIndex': 6},
                'rows': {'values': [{'userEnteredValue': {'stringValue': f'PROJEKTAUSWERTUNG - {title}'},
                                    'userEnteredFormat': {'textFormat': {'bold': True, 'fontSize': 18}}}]} }},
            # Header
            {'updateCells': {
                'range': {'sheetId': 1, 'startRowIndex': 2, 'endRowIndex': 3, 'startColumnIndex': 0, 'endColumnIndex': 6},
                'rows': {'values': [{'userEnteredValue': {'stringValue': h},
                                    'userEnteredFormat': {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.85, 'green': 0.85, 'blue': 0.85}}}
                                   for h in ['Kategorie', 'Plan', 'Ist', 'Abweichung', 'Status', 'Trend']]} }},
            # Beispieldaten
            {'updateCells': {
                'range': {'sheetId': 1, 'startRowIndex': 3, 'endRowIndex': 8, 'startColumnIndex': 0, 'endColumnIndex': 6},
                'rows': {'values': [
                    [{'userEnteredValue': {'stringValue': 'Budget'}},
                     {'userEnteredValue': {'numberValue': 50000}, 'userEnteredFormat': {'numberFormat': {'type': 'CURRENCY', 'pattern': '#,##0.00 €'}}},
                     {'userEnteredValue': {'numberValue': 47500}, 'userEnteredFormat': {'numberFormat': {'type': 'CURRENCY', 'pattern': '#,##0.00 €'}}},
                     {'userEnteredValue': {'formulaValue': '=C4-B4'}, 'userEnteredFormat': {'numberFormat': {'type': 'CURRENCY', 'pattern': '#,##0.00 €'}, 'textFormat': {'foregroundColor': {'red': 0.2, 'green': 0.8, 'blue': 0.2}}}},
                     {'userEnteredValue': {'stringValue': '✅ OK'}},
                     {'userEnteredValue': {'stringValue': '↓'}},
                    ],
                    # Weitere Zeilen...
                ]} }},
            
            # Spaltenbreiten
            {'updateDimensionProperties': {
                'range': {'sheetId': 1, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 6},
                'properties': {'pixelSize': 150}
            }},
        ]
    }
    
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=dashboard_format
    ).execute()
    
    print(f"✅ Tabelle erstellt: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
    return spreadsheet_id

if __name__ == '__main__':
    create_auswertungtabelle()
```

---

## 4. Schnellstart

```bash
# 1. Google Cloud Credentials einrichten
#    (siehe Abschnitt 2.1)

# 2. Pakete installieren
pip3 install --user google-auth google-auth-oauthlib google-auth-httplib2 \
    google-api-python-client gspread

# 3. Brief erstellen
python3 ~/.hermes/skills/productivity/din5008-google-workspace/templates/brief.py

# 4. Tabelle erstellen
python3 ~/.hermes/skills/productivity/din5008-google-workspace/templates/tabelle.py

# 5. Im Browser öffnen
xdg-open "https://docs.google.com/document/d/DOC_ID/edit"
xdg-open "https://docs.google.com/spreadsheets/d/SHEET_ID/edit"
```

## 5. Hinweise

- Dokumente werden im Service Account Drive erstellt
- Empfänger müssen manuell hinzugefügt werden
- Für produktiven Einsatz: OAuth statt Service Account
- Templates können angepasst werden
