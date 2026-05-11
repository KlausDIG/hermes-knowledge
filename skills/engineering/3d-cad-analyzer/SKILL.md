---
name: 3d-cad-analyzer
description: |
  Lokaler 3D-CAD-Analyse-Agent für technische CAD-Modelle aus unterschiedlichen
  CAD-Systemen (SolidWorks, Inventor, Fusion 360, CATIA, Siemens NX, Creo, FreeCAD,
  Onshape, STEP, IGES, STL, OBJ). Extrahiert technische Informationen, erkennt
  Bauteile/Baugruppen/Geometrien, prüft Plausibilität, leitet neutrales
  Engineering-Modell ab und liefert prüfbare Ergebnisse mit Confidence-Werten.
toolsets:
  - terminal
  - file
  - python
version: "1.0.0"
category: engineering
---

# 🔧 3D CAD Analyzer v1.0.0

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
12. Ansichten erkennen (Top, Front, Right, Section)
13. Geometrie extrahieren (Linien, Kreise, Bögen)
14. Features identifizieren und korrelieren
15. 3D-Solid generieren und als STEP/STL exportieren

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
| Modul | Funktion |
|-------|----------|
| `reconstruct_3d.py` | PDF/DXF einlesen, Ansichten erkennen, Features korrelieren, 3D-Solid generieren, STEP/STL exportieren |

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

## Wichtige Hinweise

- **STL/OBJ** enthalten meist keine exakten Feature- oder Materialinformationen.
- **STEP/IGES** sind für technische Analyse deutlich besser geeignet als STL.
- Bei sicherheitsrelevanten Bauteilen immer Review durch Fachpersonal empfehlen.
- Keine automatische Freigabe von Konstruktionsänderungen.
- Bei defekter Geometrie explizit "nicht sicher auswertbar" ausgeben.
- Maß-, Toleranz- und Festigkeitsbewertungen nur durchführen, wenn entsprechende Daten vorhanden sind.

## Versionierung

- v1.0.0 — Initiale Pipeline mit STEP, IGES, STL, OBJ, 3MF, glTF/GLB, FCStd
