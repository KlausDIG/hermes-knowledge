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

## 2. Erstellungsmethoden

### 2.1 Präferierte Methode: Lokale HTML (kein Google Account nötig)

> ✅ **Empfohlen** – funktioniert sofort ohne Cloud-Setup, ohne Auth, ohne API-Keys.

```python
#!/usr/bin/env python3
"""DIN 5008 Brief als HTML (A4-konform, druckfertig)"""
from pathlib import Path
from datetime import datetime

OUTPUT = Path.home() / "Documents/DIN5008_Output"
OUTPUT.mkdir(parents=True, exist_ok=True)

def brief_html(absender_firma="KlausDIG Services", absender_strasse="Musterstraße 1",
               absender_plz="12345", absender_ort="Musterstadt", empfaenger_name="",
               empfaenger_strasse="", empfaenger_plz="", empfaenger_ort="",
               betreff="", text="", datum=None, anlagen=None):
    if datum is None:
        datum = datetime.now().strftime("%d. %B %Y")
    anlagen = anlagen or []
    anlagen_html = "\n".join(f"<li>{a}</li>" for a in anlagen)
    h = f"""
<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>DIN 5008 Brief</title>
<style>
@page {{ size: A4; margin: 20mm 25mm; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: Arial, sans-serif; font-size: 11pt; line-height: 1.15;
    color: #333; max-width: 210mm; margin: 0 auto; padding: 20mm 25mm;
}}
.absender {{ font-size: 9pt; line-height: 1.3; margin-bottom: 8mm; height: 27mm; }}
.fenster {{ width: 80mm; margin-bottom: 8mm; line-height: 1.5; min-height: 40mm; }}
.bezugs {{ text-align: left; margin-left: 90mm; margin-bottom: 8mm; font-size: 9pt; }}
.betreff {{ font-size: 11pt; font-weight: bold; margin: 8mm 0 11pt; }}
.anrede {{ font-size: 11pt; margin-bottom: 11pt; }}
.brieftext {{ font-size: 11pt; line-height: 1.15; margin-bottom: 11pt; text-align: justify; }}
.brieftext p {{ margin-bottom: 11pt; }}
.gruss {{ font-size: 11pt; margin-top: 11pt; margin-bottom: 22pt; }}
.unterschrift {{ font-size: 11pt; margin-top: 8mm; }}
.anlagen {{ font-size: 9pt; margin-top: 8mm; border-top: 1px solid #ccc; padding-top: 4mm; }}
.anlagen li {{ margin-left: 15px; margin-bottom: 2pt; }}
.print-btn {{ position: fixed; top: 20px; right: 20px; padding: 12px 24px;
    background: #0066cc; color: white; border: none; border-radius: 4px; font-size: 14pt;
    cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }}
.print-btn:hover {{ background: #0052a3; }}
@media print {{ body {{ padding: 0; max-width: none; }} .no-print {{ display: none; }} }}
</style>
</head>
<body>
<button class="print-btn no-print" onclick="window.print()">🖨️ Drucken / PDF</button>
<div class="absender">{absender_firma}<br>{absender_strasse}<br>{absender_plz} {absender_ort}</div>
<div class="fenster">{empfaenger_name}<br>{empfaenger_strasse}<br>{empfaenger_plz} {empfaenger_ort}</div>
<div style="height:21mm;"></div>
<div class="bezugs">
<table><tr><td>Ihr Zeichen:</td><td>---</td></tr>
<tr><td>Unser Zeichen:</td><td>KH-{datetime.now().year}-001</td></tr>
<tr><td>Datum:</td><td>{datum}</td></tr></table>
</div>
<div style="height:8mm;"></div>
<div class="betreff">{betreff}</div>
<div class="anrede">Sehr geehrte Damen und Herren,</div>
<div class="brieftext">{text.replace(chr(10), "</p><p>")}</div>
<div class="gruss">Mit freundlichen Grüßen</div>
<div style="height:15mm;"></div>
<div class="unterschrift"><strong>Klaus Dreisbusch</strong><br>Geschäftsführer</div>
<div class="anlagen"><strong>Anlagen:</strong><ul>{anlagen_html}</ul></div>
</body>
</html>
"""
    fp = OUTPUT / f"Brief_{datetime.now():%Y%m%d_%H%M}.html"
    fp.write_text(h, encoding="utf-8")
    print(f"✅ {fp}")
    import subprocess
    subprocess.run(["xdg-open", str(fp)], capture_output=True)
    return fp

if __name__ == "__main__":
    brief_html(empfaenger_name="Frau M. Mustermann", empfaenger_strasse="Bsp. 42",
               empfaenger_plz="54321", empfaenger_ort="Bsp-Stadt",
               betreff="Angebot", text="Vielen Dank für Ihre Anfrage.\n\nGerne unterbreiten wir Ihnen folgendes Angebot.")
```

**Nutzung:**
```bash
python3 brief_html.py
# → Öffnet Browser mit Druck-Button → Strg+P → "Als PDF speichern"
```

**Vorteile:** Kein Google-Account, keine API, offline, sofort nutzbar, DIN-5008-A4-Layout mit `@page`.

---

### 2.2 Google Docs API (optional, wenn Cloud nötig)

⚠️ **Pitfall:** Service-Account-Setup und OAuth-Playground können in manchen Umgebungen blockiert sein (Firmen-Firewall, fehlende Browser-Integration). Wenn der Google-Flow nicht klappt, sofort auf Methode 2.1 (HTML) zurückfallen.

```bash
# 1. Google Cloud Console öffnen
xdg-open https://console.cloud.google.com/

# 2. Neues Projekt erstellen: "din5008-automation"
# 3. Google Docs API aktivieren
# 4. Google Sheets API aktivieren
# 5. Service Account erstellen
# 6. JSON Key herunterladen → ~/.config/gcloud/din5008-service-account.json
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
