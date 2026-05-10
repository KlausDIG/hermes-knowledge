#!/usr/bin/env python3
"""
eCAD PDF Compare v1.0.0
Vergleicht zwei Schaltungsbücher
"""
import sys, json, argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Import vom Analyzer
sys.path.insert(0, str(Path(__file__).parent))
from ecad_analyze import ECADAnalyzer

OUTPUT_DIR = Path.home() / "Documents/eCAD_Analysis"

class ECADComparator:
    """Vergleicht zwei eCAD-Analysen"""
    
    def __init__(self, old_result: Dict, new_result: Dict):
        self.old = old_result
        self.new = new_result
        self.differences = []
    
    def compare(self) -> Dict[str, Any]:
        """Hauptvergleich"""
        print("══════════════════════════════════════════════════════════")
        print("  📊 eCAD PDF Vergleich v1.0.0")
        print("══════════════════════════════════════════════════════════\n")
        
        # Projektvergleich
        self._compare_projects()
        
        # Gerätevergleich
        self._compare_devices()
        
        # Klemmenvergleich
        self._compare_terminals()
        
        # SPS-Vergleich
        self._compare_plc()
        
        # Kabelvergleich
        self._compare_cables()
        
        # Stücklistenvergleich
        self._compare_bom()
        
        # Seitenvergleich
        self._compare_pages()
        
        return {
            'old_project': self.old['project'],
            'new_project': self.new['project'],
            'differences': self.differences,
            'summary': self._generate_summary(),
        }
    
    def _compare_projects(self):
        """Projektmetadaten vergleichen"""
        old_p = self.old['project']
        new_p = self.new['project']
        
        if old_p.get('revision') != new_p.get('revision'):
            self.differences.append({
                'object_type': 'Projekt',
                'object_id': 'Revision',
                'change_type': 'modified',
                'old_value': old_p.get('revision', ''),
                'new_value': new_p.get('revision', ''),
                'page_old': '',
                'page_new': '',
                'confidence': 1.0,
            })
    
    def _compare_devices(self):
        """Geräte vergleichen"""
        old_devices = {d['bmk']: d for d in self.old['devices']}
        new_devices = {d['bmk']: d for d in self.new['devices']}
        
        # Hinzugefügt
        for bmk in set(new_devices.keys()) - set(old_devices.keys()):
            self.differences.append({
                'object_type': 'Gerät',
                'object_id': bmk,
                'change_type': 'added',
                'old_value': '',
                'new_value': f"Seite {new_devices[bmk]['page']}",
                'page_old': '',
                'page_new': str(new_devices[bmk]['page']),
                'confidence': 0.85,
            })
        
        # Entfernt
        for bmk in set(old_devices.keys()) - set(new_devices.keys()):
            self.differences.append({
                'object_type': 'Gerät',
                'object_id': bmk,
                'change_type': 'removed',
                'old_value': f"Seite {old_devices[bmk]['page']}",
                'new_value': '',
                'page_old': str(old_devices[bmk]['page']),
                'page_new': '',
                'confidence': 0.85,
            })
        
        # Geändert (Seitenwechsel)
        for bmk in set(old_devices.keys()) & set(new_devices.keys()):
            old_page = old_devices[bmk]['page']
            new_page = new_devices[bmk]['page']
            if old_page != new_page:
                self.differences.append({
                    'object_type': 'Gerät',
                    'object_id': bmk,
                    'change_type': 'modified',
                    'old_value': f"Seite {old_page}",
                    'new_value': f"Seite {new_page}",
                    'page_old': str(old_page),
                    'page_new': str(new_page),
                    'confidence': 0.80,
                })
    
    def _compare_terminals(self):
        """Klemmen vergleichen"""
        old_terms = {f"{t['leiste']}:{t['nummer']}": t for t in self.old['terminals']}
        new_terms = {f"{t['leiste']}:{t['nummer']}": t for t in self.new['terminals']}
        
        for key in set(new_terms.keys()) - set(old_terms.keys()):
            self.differences.append({
                'object_type': 'Klemme',
                'object_id': key,
                'change_type': 'added',
                'old_value': '',
                'new_value': f"Seite {new_terms[key]['page']}",
                'confidence': 0.80,
            })
        
        for key in set(old_terms.keys()) - set(new_terms.keys()):
            self.differences.append({
                'object_type': 'Klemme',
                'object_id': key,
                'change_type': 'removed',
                'old_value': f"Seite {old_terms[key]['page']}",
                'new_value': '',
                'confidence': 0.80,
            })
    
    def _compare_plc(self):
        """SPS vergleichen"""
        old_plc = {p['adresse']: p for p in self.old['plc_io']}
        new_plc = {p['adresse']: p for p in self.new['plc_io']}
        
        for addr in set(new_plc.keys()) - set(old_plc.keys()):
            self.differences.append({
                'object_type': 'SPS',
                'object_id': addr,
                'change_type': 'added',
                'old_value': '',
                'new_value': new_plc[addr]['typ'],
                'confidence': 0.90,
            })
        
        for addr in set(old_plc.keys()) - set(new_plc.keys()):
            self.differences.append({
                'object_type': 'SPS',
                'object_id': addr,
                'change_type': 'removed',
                'old_value': old_plc[addr]['typ'],
                'new_value': '',
                'confidence': 0.90,
            })
    
    def _compare_cables(self):
        """Kabel vergleichen"""
        old_cables = {c['nummer']: c for c in self.old['cables']}
        new_cables = {c['nummer']: c for c in self.new['cables']}
        
        for num in set(new_cables.keys()) - set(old_cables.keys()):
            self.differences.append({
                'object_type': 'Kabel',
                'object_id': num,
                'change_type': 'added',
                'confidence': 0.75,
            })
    
    def _compare_bom(self):
        """Stückliste vergleichen"""
        old_bom = {f"{b['hersteller']}_{b['artikelnummer']}": b for b in self.old['bill_of_materials']}
        new_bom = {f"{b['hersteller']}_{b['artikelnummer']}": b for b in self.new['bill_of_materials']}
        
        for key in set(new_bom.keys()) - set(old_bom.keys()):
            self.differences.append({
                'object_type': 'Stückliste',
                'object_id': key,
                'change_type': 'added',
                'confidence': 0.70,
            })
    
    def _compare_pages(self):
        """Seiten vergleichen"""
        old_pages = {p['page_number']: p for p in self.old['pages']}
        new_pages = {p['page_number']: p for p in self.new['pages']}
        
        for num in set(new_pages.keys()) - set(old_pages.keys()):
            self.differences.append({
                'object_type': 'Seite',
                'object_id': f"Seite {num}",
                'change_type': 'added',
                'new_value': new_pages[num]['page_type'],
                'confidence': 0.80,
            })
    
    def _generate_summary(self) -> Dict:
        """Zusammenfassung"""
        added = len([d for d in self.differences if d['change_type'] == 'added'])
        removed = len([d for d in self.differences if d['change_type'] == 'removed'])
        modified = len([d for d in self.differences if d['change_type'] == 'modified'])
        
        return {
            'total_changes': len(self.differences),
            'added': added,
            'removed': removed,
            'modified': modified,
            'unchanged': len(self.old['devices']) - removed,  # Annäherung
        }
    
    def generate_report(self) -> str:
        """Markdown-Vergleichsbericht"""
        s = self._generate_summary()
        
        md = f"""# eCAD Vergleichsbericht

## Zusammenfassung

| Metrik | Wert |
|--------|------|
| Gesamtänderungen | {s['total_changes']} |
| Hinzugefügt | {s['added']} |
| Entfernt | {s['removed']} |
| Geändert | {s['modified']} |

## Detaillierte Änderungen

"""
        
        for change_type in ['added', 'removed', 'modified']:
            changes = [d for d in self.differences if d['change_type'] == change_type]
            if changes:
                emoji = {'added': '➕', 'removed': '➖', 'modified': '✏️'}[change_type]
                md += f"### {emoji} {change_type.upper()} ({len(changes)})\n\n"
                md += "| Typ | ID | Alt | Neu | Confidence |\n"
                md += "|-----|----|-----|-----|------------|\n"
                for c in changes[:50]:  # Max 50
                    md += f"| {c['object_type']} | {c['object_id']} | {c.get('old_value', '-')} | {c.get('new_value', '-')} | {c['confidence']:.0%} |\n"
                md += "\n"
        
        return md


def main():
    parser = argparse.ArgumentParser(description='eCAD PDF Compare v1.0.0')
    parser.add_argument('old_pdf', help='Alte PDF-Version')
    parser.add_argument('new_pdf', help='Neue PDF-Version')
    parser.add_argument('--output', '-o', default=str(OUTPUT_DIR),
                       help='Ausgabeverzeichnis')
    
    args = parser.parse_args()
    
    print("Analysiere alte Version...")
    old_analyzer = ECADAnalyzer(args.old_pdf)
    old_result = old_analyzer.analyze_pdf()
    
    print("\nAnalysiere neue Version...")
    new_analyzer = ECADAnalyzer(args.new_pdf)
    new_result = new_analyzer.analyze_pdf()
    
    print("\nVergleiche...")
    comparator = ECADComparator(old_result, new_result)
    comparison = comparator.compare()
    
    # Speichern
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    
    # JSON
    json_file = output_dir / f"Vergleich_{timestamp}.json"
    json_file.write_text(json.dumps(comparison, indent=2, ensure_ascii=False), encoding='utf-8')
    
    # Markdown
    md_file = output_dir / f"Vergleich_{timestamp}.md"
    md_file.write_text(comparator.generate_report(), encoding='utf-8')
    
    print(f"\n✅ Vergleich abgeschlossen!")
    print(f"   JSON: {json_file}")
    print(f"   MD:   {md_file}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
