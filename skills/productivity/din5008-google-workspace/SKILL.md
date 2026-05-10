---
name: din5008-google-workspace
description: |
  Geschäftsbriefe (DIN 5008), Geschäftsberichte/Projektberichte und
  Auswertungstabellen professionell erstellen. Lokal als HTML/PDF
  (sofort nutzbar) oder optional in Google Workspace (API vorbereitet).
category: productivity
version: 2.1.0
---

# DIN 5008 + Google Workspace Skill

## Überblick

Erstelle professionelle Geschäftsunterlagen nach DIN 5008 Norm:

- **Geschäftsbriefe** (Form A Fensterbrief) – HTML oder Text
- **Auswertungstabellen** – HTML mit farbigen Status-Icons oder Markdown
- **Projektberichte** – Strukturvorlage
- Optional: Google Docs / Sheets (API vorbereitet, Auth pending)

---

## 1. Schnellstart (Empfohlen: Lokal)

> ✅ **Empfohlen** – funktioniert sofort ohne Cloud-Setup, ohne Auth, ohne API-Keys.
>
> ⚠️ **Pitfall – Cloud Auth Frustration:** Mehrere Sessions haben gezeigt, dass
> Google Cloud Console / OAuth / Service Accounts in dekorativen Umgebungen
> (Snap, headless, Firmen-Firewall) oft blockieren oder zu komplex sind.
> **Regel:** Starte IMMER mit lokaler HTML/PDF. Cloud-Integration ist ein
> **zusätzlicher Schritt**, nie ein Blocker.
> Siehe: `references/google-auth-frustration.md`

```bash
# Ein-Kommando Generator – sofort nutzbar
din5008 brief      # Geschäftsbrief (HTML + Text)
din5008 tabelle    # Auswertungstabelle (HTML + Markdown)
din5008 all        # Beides (default)
din5008 help       # Hilfe
```

**Oder direkt:**
```bash
python3 ~/Developer/scripts/din5008-generator.py brief
python3 ~/Developer/scripts/din5008-generator.py tabelle
python3 ~/Developer/scripts/din5008-generator.py all
```

**Ausgabe:** `~/Documents/DIN5008_Output/`
- `Brief_*.html` → Im Browser öffnen → `Strg+P` → "Als PDF speichern"
- `Tabelle_*.html` → Farbige Status-Icons, Hover-Effekte
- `Tabelle_*.md` → Für GitHub/GitLab

---

## 2. DIN 5008 Grundlagen

### Form A (Fensterbrief)

```
+--------------------------------------------------+
| KlausDIG Services GmbH                           |
| Musterstraße 1, 12345 Musterstadt                |
|                                                  |
|                                                  |
| Frau Maxi Mustermann          <- Fensterbereich  |
| Beispielweg 42                                  |
| 54321 Beispielstadt                              |
|                                                  |
|                                                  |
|                                                  |
| Ihr Zeichen:  ---           <- rechtsbündig      |
| Unser Zeichen: KH-2026-001                       |
| Datum: 10. Mai 2026                             |
|                                                  |
| Angebotserstellung für IT-Dienstleistungen       |
|                                                  |
| Sehr geehrte Frau Mustermann,                    |
|                                                  |
| vielen Dank für Ihre Anfrage...                 |
|                                                  |
| Mit freundlichen Grüßen                          |
|                                                  |
|                                                  |
|                                                  |
| Klaus Dreisbusch                                 |
| Geschäftsführer                                  |
|                                                  |
| Anlagen: Angebot_2026_001.xlsx                   |
|                                                  |
+--------------------------------------------------+
```

### Regeln nach DIN 5008

| Element | Regel | Position |
|---------|-------|----------|
| Absender | Firmenname, Adresse | Oben links, **9pt** |
| Empfänger | Name, Straße, PLZ Ort | **80mm Breite**, 8,5cm von oben |
| Bezugszeichen | Ihr/Unser Zeichen, Datum | Rechtsbündig unter Empfänger, **9pt** |
| Betreffzeile | Prägnant | Fett, nach Bezugszeichen |
| Anrede | "Sehr geehrte Frau/Herr..." | Nach 1 Leerzeile |
| Text | Blocksatz | **11pt**, Zeilenabstand **1,15** |
| Grußformel | "Mit freundlichen Grüßen" | Nach Text |
| Name/Amt | Druckschrift | Nach 4 Leerzeilen |
| Anlagen | Aufzählung | **9pt**, Trennlinie oben |

### Seitenformat
- **Schrift:** Arial 11pt (Text), 9pt (Absender/Bezugszeichen/Anlagen)
- **Zeilenabstand:** 1,15 (proportional)
- **Ränder:** Links 25mm, Rechts 20mm, Oben 20mm, Unten 20mm
- **Seite:** A4 (210mm × 297mm)

---

## 3. Lokale Generierung (Kein Google nötig)

### 3.1 Geschäftsbrief als HTML

```python
from pathlib import Path
from datetime import datetime

OUTPUT = Path.home() / "Documents/DIN5008_Output"
OUTPUT.mkdir(parents=True, exist_ok=True)

def brief_html(
    absender_firma="KlausDIG Services GmbH",
    absender_strasse="Musterstraße 1",
    absender_plz="12345",
    absender_ort="Musterstadt",
    empfaenger_name="Frau Maxi Mustermann",
    empfaenger_strasse="Beispielweg 42",
    empfaenger_plz="54321",
    empfaenger_ort="Beispielstadt",
    betreff="Angebotserstellung für IT-Dienstleistungen",
    anrede="Sehr geehrte Frau Mustermann,",
    text="vielen Dank für Ihre Anfrage...",
    gruss="Mit freundlichen Grüßen",
    unterschrift_name="Klaus Dreisbusch",
    unterschrift_position="Geschäftsführer",
    anlagen=["Angebot_2026_001.xlsx"],
):
    """Erstellt DIN-5008-Form-A-Fensterbrief als druckbare HTML-Datei."""
    ...
    # Siehe: templates/brief-html.py (vollständiges Template)
```

**Features des HTML-Briefs:**
- ✅ DIN 5008 Form A (Fensterbrief) korrekt
- ✅ A4 `@page` CSS-Regeln für korrektes Drucken
- ✅ Ränder 20/25/20/25 mm
- ✅ Absender 9pt, Text 11pt, Zeilenabstand 1.15
- ✅ Fensteranschrift mit blauem Rand (Sichtfenster-Markierung)
- ✅ Bezugszeichen als Tabelle rechtsbündig
- ✅ Betreff fett + blaue Unterstreichung
- ✅ Druck-Button (fixiert oben rechts) mit Hover-Effekt
- ✅ Print-Stylesheet: Button ausblenden, Ränder entfernen
- ✅ Footer mit Seitenangabe und Zeitstempel
- ✅ Responsiv: Im Browser A4-Layout, beim Drucken sauber

**Nutzung:**
```bash
python3 brief_html.py
# → Browser öffnet sich automatisch
# → Strg+P → "Als PDF speichern"
```

**Vorteile:** Kein Google-Account, keine API, offline, sofort nutzbar.

---

### 3.2 Auswertungstabelle als HTML

**Features:**
- ✅ Farbige Header-Zeile (blau, weiße Schrift)
- ✅ Status-Icons groß + farbig:
  - 🟢 ✅ = Im Plan
  - 🔵 🔄 = In Arbeit
  - 🟡 ⚠️ = Abweichung
  - 🔴 ❌ = Kritisch
- ✅ Gesamtzeile grau hervorgehoben + fett
- ✅ Hover-Effekt auf Zeilen
- ✅ Trend-Pfeile (↑ Abweichung, ↓ gut, - neutral)
- ✅ Print-Button
- ✅ Legende am Ende

**Nutzung:**
```bash
python3 tabelle_html.py
# → Browser öffnet sich automatisch
```

---

### 3.3 Ein-Kommando Generator

```bash
# Alias (nach source ~/.bashrc verfügbar)
din5005 brief      # Nur Brief
din5008 tabelle    # Nur Tabelle
din5008 all        # Beides (default)
din5008 help       # Hilfe
```

**Alias-Definition:** `~/bin/din5008`
- Ruft `~/Developer/scripts/din5008-generator.py` auf
- Erstellt beide Varianten (HTML + Text/Markdown)
- Öffnet Browser automatisch

---

## 4. Google Workspace Integration (Optional – nur wenn lokal funktioniert)

> ⚠️ **Pitfall aus mehreren Sessions:** Google Cloud Console / OAuth kann
> blockieren wenn: Browser-Integration fehlt, Firmen-Firewall aktiv, oder
> der OAuth-Flow im Terminal nicht interaktiv durchführbar ist.>
> **Wenn der Flow nicht klappt:** Nutze SOFORT Abschnitt 3 (Lokale HTML).> Die visuelle Qualität ist identisch – Google Docs bringt keinen Vorteil> für statische DIN 5008 Briefe.>
> **NUR fortfahren wenn:** Der Nutzer explizit "Google Setup" fordert UND> Credentials bereits vorhanden sind (z.B. Service Account JSON auf dem System).
**Option A: OAuth Desktop Client (empfohlen für Einzelnutzer)**
1. https://console.cloud.google.com/ → Projekt "din5008-editor"
2. APIs aktivieren: Docs API, Sheets API, Drive API
3. OAuth Client ID erstellen (Desktop App)
4. JSON herunterladen → `~/.config/din5008-oauth/credentials.json`
5. Token holen via OAuth Playground oder Desktop Flow

**Option B: Service Account (für Automation)**
1. Google Cloud Console → Service Account "din5008-sa"
2. Rolle: Editor
3. JSON Key erstellen → `~/.config/gcloud/din5008-service-account.json`

### 4.2 Setup-Skripte

| Skript | Zweck |
|--------|-------|
| `scripts/setup-google-workspace.py` | OAuth2 Setup-Assistent |
| `scripts/oauth-desktop-flow.py` | Desktop OAuth Flow mit Browser |
| `scripts/oa-token-setup.py` | OAuth Playground Anleitung |
| `scripts/setup-din5008.sh` | All-in-One Setup |

### 4.3 Google API Skripte (pending Auth)

| Skript | Zweck | Status |
|--------|-------|--------|
| `scripts/ga-brief.py` | Brief in Google Docs erstellen | ⏳ Auth pending |
| `scripts/ga-sheets.py` | Tabelle in Sheets erstellen | ⏳ Auth pending |

**Wenn Auth vorhanden:**
```bash
python3 ~/Developer/scripts/ga-brief.py
# → Erstellt DIN 5008 Brief direkt in Google Docs

python3 ~/Developer/scripts/ga-sheets.py
# → Erstellt Auswertungstabelle in Google Sheets
```

---

## 5. Templates

### 5.1 Projektbericht Struktur

```
1. Zusammenfassung (Executive Summary)
2. Projektmanagement
   2.1 Projektauftrag
   2.2 Projektorganisation
   2.3 Phasenplan
3. Ist-Analyse
4. Zielsetzung (SMART)
5. Konzeption
6. Umsetzung
7. Ergebnisse
8. Fazit und Ausblick
Anhang A-C
```

**Datei:** `templates/projektbericht.json`

---

## 6. GitHub Actions Auto-Renderer

**Workflow:** `.github/workflows/din5008-render.yml`

**Triggert bei:**
- Push auf `main` (Änderungen an DIN 5008 Dateien)
- Jeden Montag 09:00 Uhr (Schedule)
- Manuell (`workflow_dispatch`)

**Was es tut:**
1. Brief generieren → `_site/brief.txt`
2. Tabelle generieren → `_site/tabelle.md`
3. HTML Index mit Links erstellen
4. GitHub Pages deployen

**URL nach Deploy:** `https://klausdig.github.io/dotfiles/`

---

## 7. Dateistruktur

```
~/.hermes/skills/productivity/din5008-google-workspace/
├── SKILL.md                              # Diese Datei
├── templates/
│   ├── brief-html.py                     # HTML Brief Generator
│   └── projektbericht.json               # Bericht-Struktur
└── scripts/
    ├── din5008-generator.py              # Unified Generator (v2.1)
    ├── brief-generator.py                # Legacy Text-Generator
    ├── tabelle-generator.py              # Legacy Markdown-Generator
    ├── render-html.py                    # HTML Renderer
    ├── ga-brief.py                       # Google Docs API (pending)
    ├── ga-sheets.py                      # Google Sheets API (pending)
    ├── oauth-desktop-flow.py             # OAuth Desktop Flow
    ├── oa-token-setup.py                 # OAuth Playground Helper
    ├── setup-google-workspace.py         # Google API Setup
    └── setup-din5008.sh                  # All-in-One Setup

~/bin/din5008                             # Bash Alias
~/.github/workflows/din5008-render.yml    # GitHub Actions
~/Documents/DIN5008_Output/               # Ausgabeverzeichnis
```

---

## 8. Troubleshooting

| Problem | Lösung |
|---------|--------|
| Google OAuth funktioniert nicht | **Lokale HTML nutzen** (Abschnitt 3) – visuell identisch |
| `din5008` Alias nicht gefunden | `source ~/.bashrc` oder direkt `python3 ~/Developer/scripts/din5008-generator.py` |
| Browser öffnet nicht | `xdg-open ~/Documents/DIN5008_Output/Brief_*.html` |
| PDF erstellen | Im Browser: `Strg+P` → "Als PDF speichern" |
| Keine Farben im PDF | Browser-Druckdialog: "Hintergrundgrafiken" aktivieren |

---

## 9. Version History

| Version | Änderung |
|---------|----------|
| 1.0.0 | Erste Version (Google API only) |
| 2.0.0 | Lokale HTML-Generierung hinzugefügt |
| 2.1.0 | Unified `din5008-generator.py`, `din5008` Alias, verbessertes CSS |
