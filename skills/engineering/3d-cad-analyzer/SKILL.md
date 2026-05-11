---
name: 3d-cad-analyzer
description: |
  Lokaler 3D-CAD-Analyse-Agent für technische CAD-Modelle und 2D→3D-Rekonstruktion.
  Unterstützt: STEP, IGES, BREP, STL, OBJ, PDF, DXF, DWG.
  Features: Teile-/Baugruppen-Erkennung, Fertigungsanalyse, Plausibilitätsprüfung,
  Modellvergleich, und Reverse-Engineering aus 2D-Zeichnungen (mehrere Ansichten).
toolsets:
  - terminal
  - file
  - python
version: "1.2.0"
category: engineering
tags:
  - cad
  - ecad
  - step
  - iges
  - brep
  - stl
  - obj
  - 3d-analysis
  - feature-extraction
  - manufacturing
  - 2d-to-3d
  - reverse-engineering
  - pdf
  - dxf
  - dwg
  - reconstruction
---

# 🔧 3D CAD Analyzer & Reconstructor v1.2.0

## Pipeline-Übersicht

### Analyse-Modus (3D → Daten)
1. Dateieingang analysieren (Format, Metadaten, Einzelteil/Baugruppe)
2. Vorverarbeitung und Normalisierung (Einheiten, Modellintegrität)
3. Bauteile und Baugruppen erkennen
4. Systemprofil erkennen (optional, nie abhängig)
5. Normalisiertes Zwischenmodell (JSON)
6. Graphmodell ableiten (Beziehungen)
7. Plausibilitätsprüfung
8. Vergleich mehrerer 3D-CAD-Dateien
9. Fertigungsanalyse
10. Strukturierte Antwort (A-J)

### Rekonstruktions-Modus (2D → 3D)
11. 2D-Zeichnung einlesen (PDF, DXF)
12. Maßstabserkennung aus Anmerkungen/Text (z.B. "M 1:10", "Scale 1:5")
13. Ansichten erkennen (Top, Front, Right, Section)
14. Geometrie extrahieren (Linien, Kreise, Bögen)
15. Symmetrieerkennung (vertikal/horizontal) → Halbmodell → Vollmodell-Spiegelung
16. Features identifizieren und korrelieren
17. 3D-Solid generieren und als STEP/STL/DWG/DXF exportieren
18. Geometrie mit erkanntem Maßstab skalieren

## System-Start

```
"Ich analysiere das 3D-CAD-Modell systemneutral nach der lokalen CAD-Pipeline."
```

## Python-Abhängigkeiten

```bash
pip install --user numpy scipy meshio trimesh pyvista cadquery-ocp
```

Zusätzlich (optional, für native Formate):
```bash
pip install --user pythonocc-core freecad-python pycollada
```

Systemabhängigkeiten:
```bash
sudo apt install python3-openbabel libocct-*
```

## Schnellstart

```bash
# ═══ 3D-Analyse-Modus ═══

# Einzelnes CAD-Modell analysieren
python3 ~/Developer/scripts/cad_analyze.py model.step

# JSON für ERP/PLM
python3 ~/Developer/scripts/cad_analyze.py model.step --format json --output result/

# Zwei Modelle vergleichen
python3 ~/Developer/scripts/cad_compare.py v1.step v2.step --output diff/


# ═══ 2D→3D Rekonstruktions-Modus ═══

# Aus PDF-Zeichnung (mehrere Ansichten) STEP generieren
python3 ~/Developer/scripts/reconstruct_3d.py drawing.pdf --format step --output models/

# Aus DXF-Zeichnung STL generieren
python3 ~/Developer/scripts/reconstruct_3d.py drawing.dxf --format stl

# Nur JSON-Bericht (ohne OCC = ohne 3D-Export)
python3 ~/Developer/scripts/reconstruct_3d.py drawing.pdf --format json

# 2D-Rekonstruktion als DXF (kein pythonocc nötig)
python3 ~/Developer/scripts/reconstruct_3d.py drawing.pdf --format dxf
```

## Ausgabe-Formate

| Format | Befehl | Verwendung |
|--------|--------|------------|
| JSON | `--format json` | Weiterverarbeitung, ERP/PLM |
| CSV | `--format csv` | Excel-Import, Stücklisten |
| Excel | `--format xlsx` | Tabellenkalkulation |
| Markdown | `--format md` | Dokumentation, Reviews |
| Graph | `--format graph` | Netzwerkvisualisierung |
| STEP | `--format step` | Neutrales Export-Modell |
| STL | `--format stl` | 3D-Druck, Simulation |
| DXF | `--format dxf` | AutoCAD-kompatibel |

## Hauptkomponenten

### Analyse
| Modul | Funktion |
|-------|----------|
| `cad_analyze.py` | Eingang, Format-Erkennung, Metadaten, Analyse-Steuerung |
| `geometry_processor.py` | BREP-, Mesh- und Baugruppen-Verarbeitung |
| `feature_extractor.py` | Bohrungen, Gewinde, Taschen, Nuten, Radien, Fasen |
| `normalizer.py` | Neutrales JSON-Modell erstellen |
| `graph_builder.py` | Beziehungen ableiten (CONTAINS, HAS_FEATURE, CONNECTED_TO) |
| `manufacturing_analyzer.py` | CNC, 3D-Druck, Guss, Blechbewertung |
| `validator.py` | Plausibilitätsprüfung, Interferenzen, offene Kanten |
| `cad_compare.py` | Modellvergleich, Revisions-Diff |

### Rekonstruktion (2D → 3D)
| Modul | Funktion | Referenz |
|-------|----------|----------|
| `reconstruct_3d.py` | PDF/DXF → Ansichten → Features → STEP/STL/DXF/JSON | `references/2d-to-3d-reconstruction.md` |

## JSON-Zwischenmodell (kurz)

```json
{
  "project": { "name", "source_system", "file_format", "unit", "confidence" },
  "assembly": { "name", "is_assembly", "component_count", "subassemblies", "confidence" },
  "parts": [ { "part_id", "name", "material", "mass", "volume", "surface_area", "bounding_box", "features", "confidence" } ],
  "features": [],
  "mates_constraints": [],
  "connections": [],
  "bill_of_materials": [],
  "manufacturing_analysis": [],
  "warnings": [],
  "open_questions": []
}
```

Vollständiges Schema: siehe `templates/output_schema.json`

## Unterstützte Dateiformate

| Format | Typ | Lesen | Feature-Extraktion |
|--------|-----|-------|--------------------|
| STEP / STP | BREP/Volumen | ✅ Vollständig | ✅ Hoch |
| IGES / IGS | BREP/Volumen | ✅ Vollständig | ✅ Hoch |
| STL | Mesh (Triangulierung) | ✅ Vollständig | ⚠️ Begrenzt |
| OBJ | Mesh | ✅ Vollständig | ⚠️ Begrenzt |
| 3MF | Mesh + Metadaten | ✅ Vollständig | ⚠️ Begrenzt |
| glTF / GLB | Mesh + Szene | ✅ Vollständig | ⚠️ Begrenzt |
| FCStd | FreeCAD nativ | ✅ Vollständig | ✅ Hoch |
| PDF | 2D-Zeichnung (Vektor) | ✅ Vollständig | ✅ Mittel (Rekonstruktion) |
| DXF | 2D-Zeichnung (Vektor) | ✅ Vollständig | ✅ Mittel (Rekonstruktion) |
| DWG | 2D/3D nativ | ⚠️ Indirekt (als DXF/PDF) | ⚠️ Über Umweg |
| SLDPRT / SLDASM | SolidWorks | ⚠️ Über STEP/IFC | ✅ Mittel |
| IPT / IAM | Inventor | ⚠️ Über STEP/IFC | ✅ Mittel |
| CATPart / CATProduct | CATIA | ⚠️ Über STEP/IFC | ✅ Mittel |
| PRT (NX/Creo) | NX / Creo | ⚠️ Über STEP/IFC | ✅ Mittel |

## Confidence-Skala

| Wert | Bedeutung |
|------|-----------|
| 0.90–1.00 | Sicher (direkt aus Datei gelesen) |
| 0.70–0.89 | Wahrscheinlich (Heuristik, konsistente Daten) |
| 0.50–0.69 | Unsicher (Annahme, fehlende Bestätigung) |
| 0.30–0.49 | Spekulativ (mehrere Möglichkeiten) |
| <0.30 | Nicht bestimmbar (explizit markieren) |

## 2D → 3D Rekonstruktion

**Detaillierte Pipeline-Doku:** `references/2d-to-3d-reconstruction.md`

**ODA Installations-Helper:** `scripts/install_odafc.sh` — automatisiert ODAFileConverter-Setup

### Ansichten-Erkennung
- Vertikale Separierung (große Y-Lücken = separate Ansichten)
- Klassifizierung: Top (horizontal), Front (vertikal), Right (gemischt)
- Standard-Anordnung (3 Ansichten: Top→Front→Right)

### Feature-Korrelation
- Extrusion aus geschlossenem Profil (Top-View)
- Tiefe aus Front-View (höchste Linie in gleicher X-Position)
- Bohrungen aus Kreisen (Durchmesser aus Top, Tiefe aus Front)
- Schnitte (Section-View) erkennen durch Schraffur/Abbruchkanten

### Export-Formate
| Format | Anwendung | Braucht pythonocc |
|--------|-----------|-------------------|
| STEP (.step/.stp) | Alle CAD-Systeme | ✅ Ja |
| STL (.stl) | 3D-Druck, Simulation | ✅ Ja |
| DXF (.dxf) | AutoCAD-kompatibel | ❌ Nein (nur ezdxf) |
| JSON (.json) | Feature-Report | ❌ Nein |

### Beispiele
```bash
# Multi-Ansicht-Zeichnung → STEP-Modell
python3 ~/Developer/scripts/reconstruct_3d.py drawing.pdf --format step

# 2D-Rekonstruktion als DXF (kein OCC nötig)
python3 ~/Developer/scripts/reconstruct_3d.py drawing.pdf --format dxf

# Nur JSON-Bericht
python3 ~/Developer/scripts/reconstruct_3d.py drawing.pdf --format json

# Mit Skalierung (1:10 Zeichnung)
python3 ~/Developer/scripts/reconstruct_3d.py drawing.pdf --scale 10 --format step

# STL für 3D-Druck
python3 ~/Developer/scripts/reconstruct_3d.py drawing.dxf --format stl --output print/
```

### DWG-Konvertierung (auto-detection)
Das Skript erzeugt bei `--format dwg` automatisch eine DXF-Datei und konvertiert diese
sofern ein Tool verfügbar ist:

**Priorität:**
1. `ODAFileConverter` (beste Qualität, AutoCAD-kompatibel)
2. `dxf2dwg` / `libreDWG` (Open Source)
3. **Fallback:** DXF wird als Ersatz behalten (AutoCAD, LibreCAD, FreeCAD lesen DXF)

**Tool installieren:**
```bash
# ODA File Converter herunterladen
https://www.opendesign.com/guestfiles/oda_file_converter
# → DEB Installieren oder AppImage nach ~/.local/bin/oda/ extrahieren

# Alternative: libreDWG (Ubuntu/Debian)
sudo apt install libredwg-bin

# Verfügbarkeit prüfen
python3 ~/Developer/scripts/oda_wrapper.py
```

**Beispiel DWG-Export:**
```bash
python3 ~/Developer/scripts/reconstruct_3d.py drawing.pdf --format dwg --output cad/
# → cad/drawing.dwg  (oder cad/drawing.dxf als Fallback)
```

### Limitierungen
- Kein Gewinde-Recognition (nur Zylinderbohrung)
- Nur einfache Extrusionen (keine Sweeps/Lofts)
- Freiformflächen nicht unterstützt
- Gewinde- und Toleranz-Informationen werden nicht aus Text extrahiert

### Neu in v1.2.0
- **Automatische Maßstabserkennung** — Erkennt "1:10", "M 1:5", "Scale 1:20" aus PDF/DXF-Text
- **Automatische Symmetrieerkennung** — Erkennt vertikale/horizontale Symmetrieachsen, vervollständigt das 3D-Modell automatisch per Spiegelung

### Pitfalls
1. **PDF mit Rasterbildern** — `get_drawings()` liefert nur Vektoren; gescannte Pläne müssen vorher vektorisiert werden
2. **Falsche Ansichtenzuordnung** — Bei abweichender Anordnung (z.B. Front über Top) manuell prüfen
3. **OCC-Abhängigkeit vergessen** — STEP/STL brauchen `pythonocc-core`; ohne geht nur DXF/JSON
4. **Skalierung falsch** — Erkannte Maßstäbe werden automatisch angewendet; bei Fehler `--scale` überschreiben

## Wichtige Hinweise

- **STL/OBJ** enthalten meist keine exakten Feature- oder Materialinformationen.
- **STEP/IGES** sind für technische Analyse deutlich besser geeignet als STL.
- Bei sicherheitsrelevanten Bauteilen immer Review durch Fachpersonal empfehlen.
- Keine automatische Freigabe von Konstruktionsänderungen.
- Bei defekter Geometrie explizit "nicht sicher auswertbar" ausgeben.
- Maß-, Toleranz- und Festigkeitsbewertungen nur durchführen, wenn entsprechende Daten vorhanden sind.

## Versionierung

- v1.2.0 — Maßstabserkennung aus Anmerkungen, automatische Symmetrieerkennung (Halbmodell-Spiegelung), Confidence-Boost für erkannte Maßstäbe/Symmetrien
- v1.1.0 — 2D→3D Rekonstruktion (PDF/DXF → STEP/STL/DXF), Multi-Ansichten-Erkennung, DWG-Bridge-Doku
- v1.0.0 — Initiale Pipeline mit STEP, IGES, STL, OBJ, 3MF, glTF/GLB, FCStd
