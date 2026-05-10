# 📄 Google Workspace Integration für DIN 5008

Automatische Erstellung von Geschäftsbriefen und Auswertungstabellen in Google Workspace.

## Voraussetzungen

### 1. Google API Credentials

**Option A: OAuth2 (empfohlen)**
```bash
# Einmalig einrichten
python3 ~/Developer/scripts/setup-google-workspace.py
```
Dies öffnet den Browser für Google OAuth.

**Option B: Service Account (für Automation)**
1. https://console.cloud.google.com/ → Neue Projekt
2. APIs aktivieren: Docs, Sheets, Drive
3. Service Account erstellen → JSON Key herunterladen
4. `~/.config/gcloud/din5008-service-account.json` speichern

### 2. Abhängigkeiten
```bash
pip3 install --user google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

## Schnellstart

### Brief erstellen (Google Docs)
```bash
python3 ~/Developer/scripts/ga-brief.py
```
→ Erstellt DIN-5008-konformen Brief in Google Docs

### Tabelle erstellen (Google Sheets)
```bash
python3 ~/Developer/scripts/ga-sheets.py
```
→ Erstellt Auswertungstabelle mit Formeln

## Authentifizierung

### OAuth2 Flow (interaktiv)
```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Nutzer    │────▶│ Google OAuth │────▶│   Token      │
│  (Browser)  │◄────│   Screen    │◄────│  (lokal)     │
└─────────────┘     └──────────────┘     └──────────────┘
```

### Service Account (automatisch)
```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Skript    │────▶│ Service Acc. │────▶│   Docs       │
│  (systemd)  │     │   (JSON)     │     │  (Business)  │
└─────────────┘     └──────────────┘     └──────────────┘
```

## Dateien

| Datei | Zweck |
|-------|-------|
| `setup-google-workspace.py` | OAuth2 Setup (einmalig) |
| `ga-brief.py` | Brief in Google Docs erstellen |
| `ga-sheets.py` | Tabelle in Sheets erstellen |
| `brief-generator.py` | Lokale Text-Version |
| `tabelle-generator.py` | Lokale Markdown-Version |

## Sicherheit

- Token wird nur lokal gespeichert (`~/.config/din5008-oauth/`)
- Berechtigung 600 (nur Nutzer)
- Niemals Token im Chat posten
- Service Account JSON: nur auf lokalem Rechner

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| `credentials.json` nicht gefunden | OAuth Setup erneut ausführen |
| Token abgelaufen | Skript erneut starten, aktualisiert automatisch |
| `ModuleNotFoundError: google` | `pip3 install google-api-python-client` |
| Zugriff verweigert | APIs aktivieren in Google Cloud Console |

## Links

- [Google Cloud Console](https://console.cloud.google.com/)
- [Docs API](https://developers.google.com/docs/api)
- [Sheets API](https://developers.google.com/sheets/api)
