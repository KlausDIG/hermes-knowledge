---
name: ecad-pdf-analyzer
description: |
  Lokaler eCAD-Analyse-Agent für Schaltungsbücher aus unterschiedlichen 
  eCAD-Systemen (EPLAN, WSCAD, SEE Electrical, AutoCAD Electrical, Zuken, PDF).
  Extrahiert technische Informationen, baut neutrales Engineering-Modell 
  auf, liefert prüfbare Ergebnisse mit Confidence-Werten.
toolsets:
  - terminal
  - file
  - python
version: "1.0.0"
category: engineering
---

# 🔧 eCAD PDF Analyzer v1.0.0

## Pipeline-Übersicht

1. PDF-Eingang analysieren (Text/OCR, Seitenklassifikation)
2. Text- und OCR-Extraktion (mit eCAD-Fehlerkorrektur)
3. eCAD-Objekte erkennen (Geräte, Klemmen, Kabel, SPS, etc.)
4. Systemprofil erkennen (optional, nie abhängig)
5. Normalisiertes Zwischenmodell (JSON)
6. Graphmodell ableiten (Beziehungen)
7. Plausibilitätsprüfung (Warnungen, Fehler)
8. Vergleich mehrerer PDFs (optional)
9. Strukturierte Antwort (A-H)
10. Sicherheits- und Qualitätsregeln

## System-Start

```
"Ich analysiere das eCAD-PDF systemneutral nach der lokalen eCAD-Pipeline."
```

## Python-Abhängigkeiten

```bash
pip install --user pymupdf pytesseract pdf2image pillow pandas openpyxl
```

oder

```bash
sudo apt install tesseract-ocr tesseract-ocr-deu poppler-utils
```

## Schnellstart

```bash
# Einzelnes PDF analysieren
python3 ~/Developer/scripts/ecad-analyze.py input.pdf

# Mit Ausgabe-Format
python3 ~/Developer/scripts/ecad-analyze.py input.pdf --format json --output result/

# Mehrere PDFs vergleichen
python3 ~/Developer/scripts/ecad-compare.py old.pdf new.pdf --output diff/
```

## Ausgabe-Formate

| Format | Befehl | Verwendung |
|--------|--------|------------|
| JSON | `--format json` | Weiterverarbeitung |
| CSV | `--format csv` | Excel-Import |
| Excel | `--format xlsx` | Tabellenkalkulation |
| Markdown | `--format md` | Dokumentation |
| Graph | `--format graph` | Netzwerkvisualisierung |

## Hauptkomponenten

| Modul | Funktion |
|-------|----------|
| `pdf_analyzer.py` | PDF-Eingang, OCR, Text-Extraktion |
| `object_extractor.py` | Geräte, Klemmen, Kabel, SPS erkennen |
| `normalizer.py` | Neutrales JSON-Modell erstellen |
| `graph_builder.py` | Beziehungen ableiten |
| `validator.py` | Plausibilitätsprüfung |
| `comparator.py` | PDF-Vergleich |
| `reporter.py` | Formatierte Ausgabe |

## Verzeichnisse

```
~/.hermes/skills/engineering/ecad-pdf-analyzer/
├── SKILL.md                           # Diese Datei
├── scripts/
│   ├── ecad-analyze.py                # Hauptanalyse
│   ├── ecad-compare.py               # PDF-Vergleich
│   ├── ecad-batch.py                 # Batch-Verarbeitung
│   └── lib/
│       ├── pdf_analyzer.py
│       ├── object_extractor.py
│       ├── normalizer.py
│       ├── graph_builder.py
│       ├── validator.py
│       ├── comparator.py
│       └── reporter.py
├── templates/
│   ├── output_template.json          # JSON-Schema
│   ├── excel_template.xlsx           # Excel-Vorlage
│   └── report_template.md            # Markdown-Report
└── references/
    ├── eplan_patterns.json           # EPLAN-Muster
    ├── wscad_patterns.json          # WSCAD-Muster
    └── generic_patterns.json         # Systemunabhängige Muster
```

## Sicherheitsregeln

- ❌ Keine erfundenen Bauteile
- ❌ Keine Annahmen ohne Evidenz
- ❌ Keine automatische Freigabe
- ✅ Niedriger Confidence bei Unsicherheit
- ✅ Immer Review durch Fachpersonal empfehlen
- ✅ Trennung sicherer Erkenntnisse / Vermutungen

## Integration

Mit anderen Skills:
- **din5008-google-workspace**: Reports in Google Docs/Sheets
- **nextcloud-rclone-cloud-first**: PDFs in Nextcloud, Ergebnisse synchron
- **n8n-workflows**: Automatische Analyse bei PDF-Upload

## Version

- **Skill:** ecad-pdf-analyzer v1.0.0
- **Status:** Bereit für PDF-Analyse
