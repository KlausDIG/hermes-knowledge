#!/usr/bin/env python3
"""
eCAD PDF Analyzer v1.0.0
Systemneutrale Schaltungsbuch-Analyse
"""
import os, sys, json, re, argparse, subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

HOME = Path.home()
OUTPUT_DIR = HOME / "Documents/eCAD_Analysis"

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    print("⚠️ PyMuPDF nicht installiert. Nutze pdftotext.")

try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

class ECADAnalyzer:
    """Hauptanalyse-Klasse"""
    
    # eCAD-typische OCR-Fehlerkorrektur
    OCR_CORRECTIONS = {
        'O/0': [(r'(?<=[A-Z])O(?=\d)', '0'), (r'(?<=\d)O(?=\d)', '0')],
        'I/1/l': [(r'\bI(?=\d{3,})\b', '1'), (r'\bl(?=\d)\b', '1')],
        'S/5': [(r'(?<![A-Z])S(?=\d{2})', '5')],
        'B/8': [(r'\bB(?=\d{3,})\b', '8')],
    }
    
    # BMK-Muster (systemunabhängig)
    BMK_PATTERNS = [
        r'-?([A-Z]{1,3}\d{1,4})(?:\.(\d+))?\b',           # K1, Q2, M3.1
        r'\+([A-Z\d]+)',                                   # +KM, +24V
        r'-([A-Z\d]+)',                                    # -KM, -0V
    ]
    
    # Klemmen-Muster
    TERMINAL_PATTERNS = [
        r'([A-Z]{1,3}\d{1,3}):(\d{1,2})',                 # X1:1, XT2:5
        r'([A-Z]{1,3}\d{1,3})\.(\d{1,2})',                # X1.1, XT2.5
    ]
    
    # Kabel-Muster
    CABLE_PATTERNS = [
        r'(W\d{1,4})',                                     # W1, W123
        r'(K\d{1,4})',                                     # K1, K123
    ]
    
    # SPS-Adressen
    PLC_PATTERNS = [
        r'(I\d+\.\d+)',                                    # I0.0, I1.5
        r'(Q\d+\.\d+)',                                    # Q0.0, Q1.2
        r'(AI\d+)',                                        # AI0, AI1
        r'(AQ\d+)',                                        # AQ0, AQ1
        r'(DB\d+\.DB[WXD]\d+)',                            # DB1.DBW2
        r'(E\d+\.\d+)',                                    # E0.0 (Siemens)
        r'(A\d+\.\d+)',                                    # A0.0 (Siemens)
    ]
    
    # Seitentypen
    PAGE_TYPES = {
        'stromlaufplan': [
            r'Stromlaufplan', r'Schaltplan', r'Circuit', r'Wiring',
            r'EL-Sch', r'HL-Sch', r'SL-Sch', r'Potenzial'
        ],
        'klemmenplan': [
            r'Klemmenplan', r'Klemmen', r'Terminal', r'X-Plan',
            r'Anschlussplan', r'Potentialverteilung'
        ],
        'kabelplan': [
            r'Kabelplan', r'Kabel', r'Cable', r'Wire List',
            r'Leitungsverzeichnis'
        ],
        'sps_liste': [
            r'SPS', r'PLC', r'I/O', r'I/O-Liste', r'Peripherie',
            r'E/A-Liste', r'Signalliste', r'IO-Liste'
        ],
        'stueckliste': [
            r'Stückliste', r'BOM', r'Bill of Material', r'Teileliste',
            r'Artikelliste', r'Material'
        ],
        'deckblatt': [
            r'Deckblatt', r'Title', r'Titelseite', r'Projekt',
            r'Projektname', r'Dokument'
        ],
        'inhaltsverzeichnis': [
            r'Inhalt', r'Contents', r'Verzeichnis', r'TOC',
            r'Seitenverzeichnis'
        ],
        'revision': [
            r'Revision', r'Änderung', r'Historie', r'Change',
            r'Abnahme'
        ],
    }
    
    def __init__(self, pdf_path: str, verbose: bool = False):
        self.pdf_path = Path(pdf_path)
        self.verbose = verbose
        self.pages = []
        self.devices = []
        self.terminals = []
        self.cables = []
        self.signals = []
        self.plc_io = []
        self.cross_refs = []
        self.bom = []
        self.warnings = []
        self.project_info = {}
        
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF nicht gefunden: {pdf_path}")
    
    def log(self, msg: str):
        if self.verbose:
            print(f"[eCAD] {msg}")
    
    def analyze_pdf(self) -> Dict[str, Any]:
        """Hauptanalyse-Pipeline"""
        print("══════════════════════════════════════════════════════════")
        print("  🔧 eCAD PDF Analyzer v1.0.0")
        print("══════════════════════════════════════════════════════════")
        print(f"\nDatei: {self.pdf_path.name}")
        print(f"Pfad: {self.pdf_path}")
        print()
        
        # 1. PDF-Eingang analysieren
        self._analyze_pdf_structure()
        
        # 2. Text-Extraktion
        self._extract_text()
        
        # 3. Seiten klassifizieren
        self._classify_pages()
        
        # 4. Objekte erkennen
        self._extract_objects()
        
        # 5. Normalisiertes Modell
        result = self._build_model()
        
        # 6. Graph-Beziehungen
        result['graph'] = self._build_graph()
        
        # 7. Plausibilitätsprüfung
        result['warnings'] = self._validate()
        
        return result
    
    def _analyze_pdf_structure(self):
        """PDF-Struktur analysieren"""
        if HAS_PYMUPDF:
            doc = fitz.open(str(self.pdf_path))
            self.page_count = len(doc)
            self.metadata = doc.metadata
            
            self.log(f"Seiten: {self.page_count}")
            self.log(f"PDF-Version: {doc.metadata.get('format', 'unbekannt')}")
            
            for i in range(min(self.page_count, 3)):
                page = doc[i]
                self.log(f"Seite {i+1}: {page.rect.width:.0f} x {page.rect.height:.0f} pt")
            
            doc.close()
        else:
            # Fallback: pdftotext
            r = subprocess.run(['pdftotext', '-layout', str(self.pdf_path), '-'],
                             capture_output=True, text=True)
            if r.returncode == 0:
                lines = r.stdout.split('\n')
                self.page_count = r.stdout.count('\f') + 1
                self.log(f"Seiten (geschätzt): {self.page_count}")
            else:
                self.page_count = 0
                self.log("⚠️ Konnte PDF nicht analysieren")
    
    def _extract_text(self):
        """Text aus PDF extrahieren"""
        self.pages_data = []
        
        if HAS_PYMUPDF:
            doc = fitz.open(str(self.pdf_path))
            
            for i in range(len(doc)):
                page = doc[i]
                text = page.get_text()
                
                # OCR-Fallback wenn wenig Text
                if len(text.strip()) < 50 and HAS_OCR:
                    self.log(f"Seite {i+1}: Wenig Text, OCR wird versucht...")
                    pix = page.get_pixmap(dpi=300)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    text = pytesseract.image_to_string(img, lang='deu+eng')
                
                # OCR-Fehler korrigieren
                text = self._correct_ocr(text)
                
                self.pages_data.append({
                    'number': i + 1,
                    'text': text,
                    'has_text': len(text.strip()) > 0,
                    'text_length': len(text),
                })
            
            doc.close()
        else:
            # Fallback
            r = subprocess.run(['pdftotext', '-layout', str(self.pdf_path), '-'],
                             capture_output=True, text=True)
            if r.returncode == 0:
                # Seiten trennen (Formfeed)
                page_texts = r.stdout.split('\f')
                for i, text in enumerate(page_texts):
                    if text.strip():
                        text = self._correct_ocr(text)
                        self.pages_data.append({
                            'number': i + 1,
                            'text': text,
                            'has_text': True,
                            'text_length': len(text),
                        })
    
    def _correct_ocr(self, text: str) -> str:
        """OCR-Fehler korrigieren"""
        # Typische eCAD-Fehler
        corrections = [
            (r'(?<![A-Z])O(?=\d{2,})', '0'),      # O → 0
            (r'\bI(?=\d{3,})\b', '1'),             # I → 1
            (r'\bl(?=\d)\b', '1'),                  # l → 1
            (r'(?<![A-Z])S(?=\d{2})', '5'),        # S → 5
            (r'\bB(?=\d{3,})\b', '8'),             # B → 8
        ]
        
        for pattern, replacement in corrections:
            text = re.sub(pattern, replacement, text)
        
        return text
    
    def _classify_pages(self):
        """Seiten nach Typ klassifizieren"""
        for page in self.pages_data:
            text_upper = page['text'].upper()
            page['type'] = 'unbekannt'
            page['type_confidence'] = 0.0
            
            scores = {}
            for page_type, patterns in self.PAGE_TYPES.items():
                score = 0
                for pattern in patterns:
                    if re.search(pattern, text_upper, re.IGNORECASE):
                        score += 1
                scores[page_type] = score / len(patterns)
            
            # Besten Typ wählen
            if scores:
                best_type = max(scores, key=scores.get)
                best_score = scores[best_type]
                
                if best_score > 0.2:  # Mindest-Threshold
                    page['type'] = best_type
                    page['type_confidence'] = min(best_score, 1.0)
            
            self.log(f"Seite {page['number']}: {page['type']} ({page['type_confidence']:.0%})")
    
    def _extract_objects(self):
        """eCAD-Objekte aus allen Seiten extrahieren"""
        for page in self.pages_data:
            text = page['text']
            page_num = page['number']
            
            # Geräte (BMK)
            self._extract_devices(text, page_num)
            
            # Klemmen
            self._extract_terminals(text, page_num)
            
            # Kabel
            self._extract_cables(text, page_num)
            
            # SPS
            self._extract_plc(text, page_num)
            
            # Querverweise
            self._extract_cross_refs(text, page_num)
            
            # Stückliste
            self._extract_bom(text, page_num)
    
    def _extract_devices(self, text: str, page: int):
        """Geräte (BMK) extrahieren"""
        for pattern in self.BMK_PATTERNS:
            matches = re.finditer(pattern, text)
            for m in matches:
                bmk = m.group(1)
                # Plausibilität prüfen
                if self._is_valid_bmk(bmk):
                    device = {
                        'bmk': bmk,
                        'page': page,
                        'position': m.start(),
                        'confidence': 0.85,
                        'context': text[max(0, m.start()-20):min(len(text), m.end()+20)]
                    }
                    # Duplikate vermeiden
                    if not any(d['bmk'] == bmk and d['page'] == page for d in self.devices):
                        self.devices.append(device)
    
    def _is_valid_bmk(self, bmk: str) -> bool:
        """Prüft ob BMK plausibel ist"""
        if len(bmk) < 2 or len(bmk) > 10:
            return False
        if not re.match(r'[A-Z]', bmk):
            return False
        return True
    
    def _extract_terminals(self, text: str, page: int):
        """Klemmen extrahieren"""
        for pattern in self.TERMINAL_PATTERNS:
            matches = re.finditer(pattern, text)
            for m in matches:
                terminal = {
                    'leiste': m.group(1),
                    'nummer': m.group(2),
                    'page': page,
                    'position': m.start(),
                    'confidence': 0.80,
                    'context': text[max(0, m.start()-15):min(len(text), m.end()+15)]
                }
                if not any(t['leiste'] == terminal['leiste'] and 
                          t['nummer'] == terminal['nummer'] and 
                          t['page'] == page for t in self.terminals):
                    self.terminals.append(terminal)
    
    def _extract_cables(self, text: str, page: int):
        """Kabel extrahieren"""
        for pattern in self.CABLE_PATTERNS:
            matches = re.finditer(pattern, text)
            for m in matches:
                cable = {
                    'nummer': m.group(1),
                    'page': page,
                    'position': m.start(),
                    'confidence': 0.75,
                    'context': text[max(0, m.start()-15):min(len(text), m.end()+15)]
                }
                if not any(c['nummer'] == cable['nummer'] and c['page'] == page 
                          for c in self.cables):
                    self.cables.append(cable)
    
    def _extract_plc(self, text: str, page: int):
        """SPS-Adressen extrahieren"""
        for pattern in self.PLC_PATTERNS:
            matches = re.finditer(pattern, text)
            for m in matches:
                plc = {
                    'adresse': m.group(1),
                    'typ': self._get_plc_type(m.group(1)),
                    'page': page,
                    'position': m.start(),
                    'confidence': 0.90,
                    'context': text[max(0, m.start()-20):min(len(text), m.end()+20)]
                }
                if not any(p['adresse'] == plc['adresse'] and p['page'] == page 
                          for p in self.plc_io):
                    self.plc_io.append(plc)
    
    def _get_plc_type(self, address: str) -> str:
        """Bestimmt SPS-Adresstyp"""
        if address.startswith(('I', 'E')):
            return 'Eingang'
        elif address.startswith(('Q', 'A')):
            return 'Ausgang'
        elif address.startswith('AI'):
            return 'Analog-Eingang'
        elif address.startswith('AQ'):
            return 'Analog-Ausgang'
        elif address.startswith('DB'):
            return 'Datenbaustein'
        return 'unbekannt'
    
    def _extract_cross_refs(self, text: str, page: int):
        """Querverweise extrahieren"""
        # Muster: /3 (Seite 3), →5, /Seite 3
        xref_patterns = [
            r'/(\d+)',           # /3
            r'→(\d+)',          # →5
            r'Seite\s+(\d+)',    # Seite 3
            r'Blatt\s+(\d+)',    # Blatt 3
        ]
        
        for pattern in xref_patterns:
            matches = re.finditer(pattern, text)
            for m in matches:
                xref = {
                    'von_seite': page,
                    'nach_seite': int(m.group(1)),
                    'position': m.start(),
                    'confidence': 0.70,
                    'context': text[max(0, m.start()-10):min(len(text), m.end()+10)]
                }
                self.cross_refs.append(xref)
    
    def _extract_bom(self, text: str, page: int):
        """Stückliste extrahieren"""
        # Artikelnummern: typisch 8-12 stellig
        # Hersteller: Siemens, Phoenix, Wago, etc.
        
        # Suche nach Herstellern
        hersteller = ['SIEMENS', 'PHOENIX', 'WAGO', 'RITTAL', 'SCHNEIDER', 
                     'ALLEN-BRADLEY', 'BECKHOFF', 'BOSCH', 'FESTO']
        
        text_upper = text.upper()
        for h in hersteller:
            if h in text_upper:
                # Suche Artikelnummern in der Nähe
                idx = text_upper.index(h)
                nearby = text[max(0, idx-50):min(len(text), idx+100)]
                
                # Artikelnummern-Muster
                artnr_matches = re.finditer(r'\b(\d{6,12})\b', nearby)
                for m in artnr_matches:
                    bom_item = {
                        'hersteller': h,
                        'artikelnummer': m.group(1),
                        'page': page,
                        'confidence': 0.65,
                        'context': nearby[max(0, m.start()-20):m.end()+20]
                    }
                    self.bom.append(bom_item)
    
    def _build_model(self) -> Dict[str, Any]:
        """Normalisiertes JSON-Modell erstellen"""
        # Projektinfo aus erster Seite oder Metadaten
        self.project_info = {
            'name': self._extract_project_name(),
            'source_system': self._detect_system(),
            'document_type': 'ecad_pdf',
            'revision': self._extract_revision(),
            'date': self._extract_date(),
            'language': 'de',
            'confidence': 0.75,
        }
        
        # Seiten
        pages = []
        for p in self.pages_data:
            page_obj = {
                'page_number': p['number'],
                'page_label': f'{p["number"]}',
                'page_type': p['type'],
                'title': self._extract_page_title(p['text']),
                'objects': [],
                'confidence': p.get('type_confidence', 0.5),
            }
            
            # Objekte dieser Seite zuordnen
            for d in self.devices:
                if d['page'] == p['number']:
                    page_obj['objects'].append({'type': 'device', 'id': d['bmk']})
            
            for t in self.terminals:
                if t['page'] == p['number']:
                    page_obj['objects'].append({'type': 'terminal', 
                                               'id': f"{t['leiste']}:{t['nummer']}"})
            
            pages.append(page_obj)
        
        return {
            'project': self.project_info,
            'pages': pages,
            'devices': self.devices,
            'terminals': self.terminals,
            'cables': self.cables,
            'signals': self.signals,
            'plc_io': self.plc_io,
            'cross_references': self.cross_refs,
            'bill_of_materials': self.bom,
            'warnings': [],
            'open_questions': [],
        }
    
    def _extract_project_name(self) -> str:
        """Projektname aus erster Seite extrahieren"""
        if self.pages_data:
            first_page = self.pages_data[0]['text']
            # Suche nach "Projekt" oder "Project"
            m = re.search(r'(?:Projekt|Project)[\s:]+(.+?)(?:\n|$)', first_page, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return 'unbekannt'
    
    def _detect_system(self) -> str:
        """Versucht das Ursprungssystem zu erkennen (optional)"""
        all_text = ' '.join(p['text'] for p in self.pages_data[:3])
        all_text_upper = all_text.upper()
        
        indicators = {
            'EPLAN': ['EPLAN', 'EPLAN Electric', '.Z13', '.Z11', 'Funktionsdefinition'],
            'WSCAD': ['WSCAD', 'WSCAD SUITE', 'WSCAD-Design'],
            'SEE Electrical': ['IGE+XAO', 'SEE Electrical', 'SEE ELECTRICAL'],
            'AutoCAD Electrical': ['AUTOCAD ELECTRICAL', 'ACE', 'WD.ISO'],
            'Zuken': ['ZUKEN', 'E3.SERIES', 'E3 CABLE'],
        }
        
        scores = {}
        for system, patterns in indicators.items():
            score = sum(1 for p in patterns if p in all_text_upper)
            scores[system] = score
        
        if scores and max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return 'unbekannt'
    
    def _extract_revision(self) -> str:
        """Revision extrahieren"""
        all_text = ' '.join(p['text'] for p in self.pages_data[:2])
        m = re.search(r'(?:Rev|Revision|Stand)[\s.:]+([A-Z0-9.]+)', all_text, re.IGNORECASE)
        if m:
            return m.group(1)
        return ''
    
    def _extract_date(self) -> str:
        """Datum extrahieren"""
        all_text = ' '.join(p['text'] for p in self.pages_data[:2])
        # DD.MM.YYYY oder YYYY-MM-DD
        m = re.search(r'(\d{2}\.\d{2}\.\d{4}|\d{4}-\d{2}-\d{2})', all_text)
        if m:
            return m.group(1)
        return ''
    
    def _extract_page_title(self, text: str) -> str:
        """Seitentitel extrahieren"""
        lines = text.split('\n')[:5]  # Erste 5 Zeilen
        for line in lines:
            if len(line.strip()) > 3 and len(line.strip()) < 80:
                return line.strip()
        return ''
    
    def _build_graph(self) -> List[Dict]:
        """Graph-Beziehungen ableiten"""
        relations = []
        
        # Geräte → Seiten
        for d in self.devices:
            relations.append({
                'source': d['bmk'],
                'relation': 'LOCATED_ON',
                'target': f"Seite_{d['page']}",
                'evidence': {
                    'page': d['page'],
                    'text': d['context'][:50],
                    'confidence': d['confidence'],
                }
            })
        
        # Querverweise
        for xref in self.cross_refs:
            relations.append({
                'source': f"Seite_{xref['von_seite']}",
                'relation': 'REFERENCES',
                'target': f"Seite_{xref['nach_seite']}",
                'evidence': {
                    'page': xref['von_seite'],
                    'text': xref['context'][:50],
                    'confidence': xref['confidence'],
                }
            })
        
        # Klemmen → Geräte (heuristisch)
        for t in self.terminals:
            # Suche Geräte auf gleicher Seite
            for d in self.devices:
                if d['page'] == t['page']:
                    relations.append({
                        'source': f"{t['leiste']}:{t['nummer']}",
                        'relation': 'CONNECTED_TO',
                        'target': d['bmk'],
                        'evidence': {
                            'page': t['page'],
                            'text': f"{t['leiste']}:{t['nummer']} auf Seite {t['page']}",
                            'confidence': 0.60,
                        }
                    })
        
        return relations
    
    def _validate(self) -> List[Dict]:
        """Plausibilitätsprüfung"""
        warnings = []
        
        # Doppelte BMKs
        bmk_counts = {}
        for d in self.devices:
            bmk = d['bmk']
            bmk_counts[bmk] = bmk_counts.get(bmk, 0) + 1
        
        for bmk, count in bmk_counts.items():
            if count > 1:
                warnings.append({
                    'severity': 'warning',
                    'category': 'doppelte_BMK',
                    'message': f'BMK "{bmk}" kommt {count}x vor',
                    'affected_objects': [bmk],
                    'confidence': 0.85,
                    'recommended_action': 'Prüfe ob BMK korrekt vergeben ist',
                })
        
        # Doppelte SPS-Adressen
        plc_counts = {}
        for p in self.plc_io:
            addr = p['adresse']
            plc_counts[addr] = plc_counts.get(addr, 0) + 1
        
        for addr, count in plc_counts.items():
            if count > 1:
                warnings.append({
                    'severity': 'critical',
                    'category': 'doppelte_SPS_Adresse',
                    'message': f'SPS-Adresse "{addr}" kommt {count}x vor',
                    'affected_objects': [addr],
                    'confidence': 0.90,
                    'recommended_action': 'KRITISCH: SPS-Adressen müssen eindeutig sein!',
                })
        
        # Kabel ohne Quelle/Ziel (heuristisch)
        if self.cables:
            for c in self.cables:
                # Suche Quelle/Ziel im Kontext
                if len(c['context']) < 20:
                    warnings.append({
                        'severity': 'info',
                        'category': 'Kabel_unvollstaendig',
                        'message': f'Kabel {c["nummer"]} hat wenig Kontext',
                        'affected_objects': [c['nummer']],
                        'confidence': 0.50,
                        'recommended_action': 'Kabelverbindung manuell prüfen',
                    })
        
        # Seitenreferenzen auf nicht existierende Seiten
        max_page = max((p['number'] for p in self.pages_data), default=0)
        for xref in self.cross_refs:
            if xref['nach_seite'] > max_page:
                warnings.append({
                    'severity': 'warning',
                    'category': 'ungueltige_Referenz',
                    'message': f'Referenz zu Seite {xref["nach_seite"]}, aber PDF hat nur {max_page} Seiten',
                    'affected_objects': [f'Seite_{xref["von_seite"]}'],
                    'confidence': 0.80,
                    'recommended_action': 'Prüfe ob PDF vollständig ist',
                })
        
        return warnings
    
    def generate_report(self, result: Dict, format_type: str = 'md') -> str:
        """Generiert formatierten Bericht"""
        
        if format_type == 'json':
            return json.dumps(result, indent=2, ensure_ascii=False)
        
        elif format_type == 'md':
            return self._generate_markdown(result)
        
        elif format_type == 'csv':
            return self._generate_csv(result)
        
        else:
            return self._generate_text(result)
    
    def _generate_markdown(self, result: Dict) -> str:
        """Markdown-Bericht"""
        p = result['project']
        
        md = f"""# eCAD Analysebericht

## A. Kurzfazit

Ich analysiere das eCAD-PDF systemneutral nach der lokalen eCAD-Pipeline.

**Projekt:** {p['name']}
**System:** {p['source_system']} (Heuristik, nicht verbindlich)
**Revision:** {p['revision']}
**Datum:** {p['date']}
**Seiten:** {len(result['pages'])}
**Confidence:** {p['confidence']:.0%}

---

## B. Erkannte Dokumentstruktur

| Seite | Typ | Confidence | Objekte |
|-------|-----|------------|---------|
"""
        
        for page in result['pages']:
            obj_count = len(page.get('objects', []))
            md += f"| {page['page_number']} | {page['page_type']} | {page['confidence']:.0%} | {obj_count} |\n"
        
        md += """
---

## C. Extrahierte Hauptobjekte

### Geräte (BMK)
"""
        
        if result['devices']:
            md += "| BMK | Seite | Confidence | Kontext |\n"
            md += "|-----|-------|------------|---------|\n"
            for d in result['devices'][:20]:  # Max 20
                ctx = d['context'][:40].replace('\n', ' ')
                md += f"| {d['bmk']} | {d['page']} | {d['confidence']:.0%} | {ctx}... |\n"
            if len(result['devices']) > 20:
                md += f"\n... und {len(result['devices']) - 20} weitere\n"
        else:
            md += "*Keine Geräte erkannt*\n"
        
        md += "\n### Klemmen\n"
        if result['terminals']:
            md += "| Leiste | Nr | Seite | Confidence |\n"
            md += "|--------|----|-------|------------|\n"
            for t in result['terminals'][:20]:
                md += f"| {t['leiste']} | {t['nummer']} | {t['page']} | {t['confidence']:.0%} |\n"
        else:
            md += "*Keine Klemmen erkannt*\n"
        
        md += "\n### SPS I/O\n"
        if result['plc_io']:
            md += "| Adresse | Typ | Seite | Confidence |\n"
            md += "|---------|-----|-------|------------|\n"
            for p in result['plc_io'][:20]:
                md += f"| {p['adresse']} | {p['typ']} | {p['page']} | {p['confidence']:.0%} |\n"
        else:
            md += "*Keine SPS-Adressen erkannt*\n"
        
        md += """
---

## D. Kritische Auffälligkeiten

"""
        
        critical = [w for w in result['warnings'] if w['severity'] == 'critical']
        warnings = [w for w in result['warnings'] if w['severity'] == 'warning']
        
        if critical:
            md += "### 🔴 Kritisch\n\n"
            for w in critical:
                md += f"- **{w['category']}:** {w['message']}\n"
                md += f"  → {w['recommended_action']}\n\n"
        
        if warnings:
            md += "### 🟡 Warnungen\n\n"
            for w in warnings:
                md += f"- **{w['category']}:** {w['message']}\n"
                md += f"  → {w['recommended_action']}\n\n"
        
        if not critical and not warnings:
            md += "*Keine kritischen Auffälligkeiten erkannt*\n"
        
        md += """
---

## E. Offene Unsicherheiten

"""
        
        # Objekte mit niedrigem Confidence
        uncertain = [d for d in result['devices'] if d['confidence'] < 0.6]
        if uncertain:
            md += f"- {len(uncertain)} Geräte mit niedrigem Confidence (< 60%)\n"
        
        md += "- Systemerkennung ist Heuristik, nicht verbindlich\n"
        md += "- Manuelle Überprüfung empfohlen\n"
        
        md += """
---

## F. Empfohlene nächste Schritte

1. **Manuelle Überprüfung** der kritischen Warnungen
2. **SPS-Adressen** mit Steuerung abgleichen
3. **Querverweise** auf Vollständigkeit prüfen
4. **Stückliste** mit Bestellung abgleichen
5. **Review durch Fachpersonal** durchführen

---

*Analysiert mit eCAD PDF Analyzer v1.0.0*
*Datum: {datetime.now().strftime('%d.%m.%Y %H:%M')}*
"""
        
        return md
    
    def _generate_csv(self, result: Dict) -> str:
        """CSV-Ausgabe für Excel"""
        import io, csv
        
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        # Header
        writer.writerow(['Typ', 'ID', 'Seite', 'Attribut', 'Wert', 'Confidence'])
        
        # Geräte
        for d in result['devices']:
            writer.writerow(['Gerät', d['bmk'], d['page'], 'Kontext', 
                           d['context'][:50], f"{d['confidence']:.0%}"])
        
        # Klemmen
        for t in result['terminals']:
            writer.writerow(['Klemme', f"{t['leiste']}:{t['nummer']}", 
                           t['page'], 'Position', t.get('position', ''), 
                           f"{t['confidence']:.0%}"])
        
        # SPS
        for p in result['plc_io']:
            writer.writerow(['SPS', p['adresse'], p['page'], 
                           'Typ', p['typ'], f"{p['confidence']:.0%}"])
        
        # Warnungen
        for w in result['warnings']:
            writer.writerow(['WARNUNG', w['category'], '', 
                           w['severity'], w['message'], ''])
        
        return output.getvalue()
    
    def _generate_text(self, result: Dict) -> str:
        """Text-Ausgabe"""
        lines = [
            "══════════════════════════════════════════════════════════",
            "  eCAD Analyseergebnis",
            "══════════════════════════════════════════════════════════",
            "",
            f"Projekt: {result['project']['name']}",
            f"System: {result['project']['source_system']}",
            f"Seiten: {len(result['pages'])}",
            f"Geräte: {len(result['devices'])}",
            f"Klemmen: {len(result['terminals'])}",
            f"SPS I/O: {len(result['plc_io'])}",
            f"Kabel: {len(result['cables'])}",
            f"Querverweise: {len(result['cross_references'])}",
            f"Stücklisten: {len(result['bill_of_materials'])}",
            f"Warnungen: {len(result['warnings'])}",
            "",
            "══════════════════════════════════════════════════════════",
        ]
        return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='eCAD PDF Analyzer v1.0.0')
    parser.add_argument('pdf', help='PDF-Datei zu analysieren')
    parser.add_argument('--format', '-f', choices=['json', 'md', 'csv', 'txt'],
                       default='md', help='Ausgabeformat')
    parser.add_argument('--output', '-o', default=str(OUTPUT_DIR),
                       help='Ausgabeverzeichnis')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Detaillierte Ausgabe')
    
    args = parser.parse_args()
    
    try:
        # Analyse
        analyzer = ECADAnalyzer(args.pdf, verbose=args.verbose)
        result = analyzer.analyze_pdf()
        
        # Bericht generieren
        report = analyzer.generate_report(result, args.format)
        
        # Speichern
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        base_name = Path(args.pdf).stem
        
        if args.format == 'json':
            ext = 'json'
        elif args.format == 'md':
            ext = 'md'
        elif args.format == 'csv':
            ext = 'csv'
        else:
            ext = 'txt'
        
        output_file = output_dir / f"{base_name}_Analyse_{timestamp}.{ext}"
        output_file.write_text(report, encoding='utf-8')
        
        # Auch JSON immer speichern
        json_file = output_dir / f"{base_name}_Analyse_{timestamp}.json"
        json_file.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        
        print(f"\n✅ Analyse abgeschlossen!")
        print(f"   Bericht: {output_file}")
        print(f"   JSON:    {json_file}")
        
        # Kurzübersicht anzeigen
        print("\n" + analyzer._generate_text(result))
        
        return 0
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
