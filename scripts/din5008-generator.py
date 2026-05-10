#!/usr/bin/env python3
"""
DIN 5008 Generator v2.1
Erstellt professionelle Geschäftsbriefe, Tabellen und Berichte
Usage: python3 din5008-generator.py [brief|tabelle|bericht|all]
"""
import os, sys, json, argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

HOME = Path.home()
OUTPUT_DIR = HOME / "Documents/DIN5008_Output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class DIN5008Brief:
    """DIN 5008 Form A (Fensterbrief) Generator"""
    
    def __init__(self, **kwargs):
        self.data = {
            'absender_firma': 'KlausDIG Services GmbH',
            'absender_strasse': 'Musterstraße 1',
            'absender_plz': '12345',
            'absender_ort': 'Musterstadt',
            'absender_tel': '+49 123 456789',
            'absender_email': 'kontakt@klausdig.de',
            'empfaenger_name': 'Frau Maxi Mustermann',
            'empfaenger_strasse': 'Beispielweg 42',
            'empfaenger_plz': '54321',
            'empfaenger_ort': 'Beispielstadt',
            'datum': datetime.now().strftime('%d. %B %Y'),
            'unser_zeichen': f'KH-{datetime.now().year}-001',
            'betreff': 'Angebotserstellung für IT-Dienstleistungen',
            'anrede': 'Sehr geehrte Frau Mustermann,',
            'text': """vielen Dank für Ihre Anfrage vom 01. Mai 2026.

Gerne unterbreiten wir Ihnen folgendes Angebot:

1. Konzeption und Beratung (40 Std.)
2. Entwicklung und Implementierung (120 Std.)
3. Schulung und Support (30 Std.)

Die detaillierte Kalkulation finden Sie in der beigefügten Excel-Datei.

Wir stehen Ihnen für Rückfragen jederzeit zur Verfügung und freuen uns auf Ihre Rückmeldung.""",
            'gruss': 'Mit freundlichen Grüßen',
            'unterschrift': 'Klaus Dreisbusch',
            'position': 'Geschäftsführer',
            'anlagen': ['Angebot_2026_001.xlsx', 'Referenzen.pdf'],
        }
        self.data.update(kwargs)
    
    def render_text(self) -> str:
        """Als Text-Version"""
        d = self.data
        text = f"""
╔══════════════════════════════════════════════════════════════╗
║ DIN 5008 GESCHÄFTSBRIEF (Form A - Fensterbrief)             ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  {d['absender_firma']}
║  {d['absender_strasse']}
║  {d['absender_plz']} {d['absender_ort']}
║                                                              ║
║  ──────────────────────────────────────────────────         ║
║  8,5cm Einzug →                                              ║
║                                                              ║
║  {d['empfaenger_name']}
║  {d['empfaenger_strasse']}
║  {d['empfaenger_plz']} {d['empfaenger_ort']}
║                                                              ║
║                              Ihr Zeichen:  ---               ║
║                              Unser Zeichen: {d['unser_zeichen']}
║                              Datum:        {d['datum']}
║                                                              ║
║  {d['betreff']}
║                                                              ║
║  {d['anrede']}
║                                                              ║
║  {d['text']}
║                                                              ║
║  {d['gruss']}
║                                                              ║
║                                                              ║
║                                                              ║
║                                                              ║
║  {d['unterschrift']}
║  {d['position']}
║                                                              ║
║  Anlagen:
║  {chr(10).join(['  • ' + a for a in d['anlagen']])}
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

Erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
DIN 5008 konform | Zeilenabstand 1,15 | Schrift Arial 11pt
"""
        return text
    
    def render_html(self) -> str:
        """Als HTML-Version (DIN 5008 konform, druckbar)"""
        d = self.data
        
        abs_text = f"{d['absender_firma']} / {d['absender_strasse']} / {d['absender_plz']} {d['absender_ort']}"
        
        # Text in Paragraphen aufteilen
        paragraphs = ''.join(f'<p>{p}</p>' for p in d['text'].split('\n\n') if p.strip())
        
        anlagen_list = ''.join(f'<li>{a}</li>' for a in d['anlagen'])
        
        html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DIN 5008 Brief - {d['empfaenger_name']}</title>
<style>
@page {{ size: A4; margin: 20mm 25mm 20mm 25mm; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
    font-family: Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.15;
    color: #333;
    max-width: 210mm;
    margin: 0 auto;
    padding: 20mm 25mm;
    background: white;
}}

.absender-block {{
    font-size: 9pt;
    line-height: 1.3;
    margin-bottom: 8mm;
    height: 27mm;
    color: #444;
}}

.fenster-anschrift {{
    width: 80mm;
    margin-left: 0mm;
    margin-top: 0mm;
    margin-bottom: 8mm;
    font-size: 11pt;
    line-height: 1.5;
    min-height: 40mm;
    border-left: 3px solid #0066cc;
    padding-left: 10px;
}}

.bezugszeichen {{
    text-align: left;
    margin-left: 90mm;
    margin-bottom: 8mm;
    font-size: 9pt;
}}

.bezugszeichen table {{
    border-collapse: collapse;
}}

.bezugszeichen td {{
    padding: 2px 8px;
    vertical-align: top;
}}

.betreff {{
    font-size: 11pt;
    font-weight: bold;
    margin-bottom: 11pt;
    margin-top: 8mm;
    color: #222;
    border-bottom: 1px solid #0066cc;
    padding-bottom: 4pt;
}}

.anrede {{ font-size: 11pt; margin-bottom: 11pt; }}

.brieftext {{
    font-size: 11pt;
    line-height: 1.15;
    margin-bottom: 11pt;
    text-align: justify;
}}

.brieftext p {{ margin-bottom: 11pt; text-indent: 0; }}

.brieftext ol {{
    margin: 8pt 0;
    padding-left: 20px;
}}

.brieftext li {{
    margin-bottom: 4pt;
}}

.gruss {{
    font-size: 11pt;
    margin-top: 11pt;
    margin-bottom: 22pt;
}}

.unterschrift-block {{
    font-size: 11pt;
    margin-top: 8mm;
}}

.anlagen {{
    font-size: 9pt;
    margin-top: 8mm;
    border-top: 1px solid #ccc;
    padding-top: 4mm;
    color: #555;
}}

.anlagen ul {{
    list-style: none;
    padding-left: 0;
    margin-top: 4pt;
}}

.anlagen li::before {{
    content: "📎 ";
}}

.print-btn {{
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 24px;
    background: #0066cc;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14pt;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    z-index: 1000;
}}

.print-btn:hover {{ background: #0052a3; transform: translateY(-1px); }}

.footer {{
    margin-top: 30pt;
    font-size: 8pt;
    color: #888;
    text-align: center;
    border-top: 1px solid #eee;
    padding-top: 8pt;
}}

@media print {{
    body {{ padding: 0; max-width: none; background: white; }}
    .no-print {{ display: none; }}
    .print-btn {{ display: none; }}
}}

@media screen {{
    body {{
        background: #f5f5f5;
        box-shadow: 0 0 20px rgba(0,0,0,0.1);
        min-height: 297mm;
    }}
}}
</style>
</head>
<body>

<button class="print-btn no-print" onclick="window.print();">🖨️ Drucken / PDF</button>

<!-- DIN 5008 Form A: Absender klein oben -->
<div class="absender-block">
{abs_text}
</div>

<!-- Fensteranschrift (8,5cm von oben, Sichtfenster) -->
<div class="fenster-anschrift">
<strong>{d['empfaenger_name']}</strong><br>
{d['empfaenger_strasse']}<br>
{d['empfaenger_plz']} {d['empfaenger_ort']}
</div>

<div style="height: 21mm;"></div>

<!-- Bezugszeichen rechtsbündig -->
<div class="bezugszeichen">
<table>
<tr><td>Ihr Zeichen:</td><td>---</td></tr>
<tr><td>Unser Zeichen:</td><td><strong>{d['unser_zeichen']}</strong></td></tr>
<tr><td>Datum:</td><td>{d['datum']}</td></tr>
</table>
</div>

<div style="height: 8mm;"></div>

<!-- Betreff -->
<div class="betreff">{d['betreff']}</div>

<!-- Anrede -->
<div class="anrede">{d['anrede']}</div>

<!-- Text -->
<div class="brieftext">
{paragraphs}
</div>

<!-- Gruß -->
<div class="gruss">{d['gruss']}</div>

<div style="height: 15mm;"></div>

<!-- Unterschrift -->
<div class="unterschrift-block">
<strong>{d['unterschrift']}</strong><br>
{d['position']}
</div>

<!-- Anlagen -->
<div class="anlagen">
<strong>Anlagen:</strong>
<ul>
{anlagen_list}
</ul>
</div>

<div class="footer">
DIN 5008 konform erstellt | {datetime.now().strftime('%d.%m.%Y %H:%M')} | Seite 1/1
</div>

</body>
</html>"""
        return html
    
    def save(self):
        """Speichert beide Varianten"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        # Text
        text_file = OUTPUT_DIR / f"Brief_{timestamp}.txt"
        text_file.write_text(self.render_text(), encoding='utf-8')
        print(f"✅ Text: {text_file}")
        
        # HTML
        html_file = OUTPUT_DIR / f"Brief_{timestamp}.html"
        html_file.write_text(self.render_html(), encoding='utf-8')
        print(f"✅ HTML: {html_file}")
        
        # Öffnen
        try:
            import webbrowser
            webbrowser.open(f"file://{html_file}")
            print(f"🌐 Browser geöffnet")
        except:
            pass
        
        return {'text': text_file, 'html': html_file}


class DIN5008Tabelle:
    """Auswertungstabelle nach DIN 5008"""
    
    def __init__(self, title="Projektauswertung", daten=None):
        self.title = title
        self.headers = ['Phase', 'Geplant [h]', 'Ist [h]', 'Abweichung', 'Status', 'Trend']
        self.rows = daten or [
            ['Konzeption', 40, 35, -5, '✅', '↓'],
            ['Entwicklung', 120, 110, -10, '🔄', '↓'],
            ['Testing', 30, 25, -5, '🔄', '↓'],
            ['Dokumentation', 20, 30, 10, '⚠️', '↑'],
            ['Deployment', 15, 12, -3, '✅', '↓'],
            ['Gesamt', 225, 212, -13, '✅', '-'],
        ]
    
    def render_markdown(self) -> str:
        """Als Markdown"""
        lines = [
            f"# {self.title}",
            "",
            f"\u003e Auswertung erstellt: {datetime.now().strftime('%d. %B %Y, %H:%M Uhr')}",
            "",
            "| Phase | Geplant [h] | Ist [h] | Abweichung | Status | Trend |",
            "|-------|-------------|---------|------------|--------|-------|",
        ]
        for row in self.rows:
            lines.append(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} |")
        
        lines += [
            "",
            "## Legende",
            "",
            "| Symbol | Bedeutung |",
            "|--------|-----------|",
            "| ✅ | Im Plan |",
            "| 🔄 | In Arbeit |",
            "| ⚠️ | Abweichung |",
            "| ❌ | Kritisch |",
            "",
            "## Formeln (für Sheets)",
            "",
            "```",
            "Abweichung = IST - PLAN",
            'Status:   =WENN(Abweichung<=0; "✅"; WENN(Abweichung<5; "⚠️"; "❌"))',
            'Trend:    =SVERWEIS(Abweichung; {-999;""; -10;"↓"; 0;"-"; 10;"↑"}; 2)',
            "```",
        ]
        return '\n'.join(lines)
    
    def render_html(self) -> str:
        """Als HTML-Tabelle"""
        rows_html = ''
        for i, row in enumerate(self.rows):
            is_total = row[0] == 'Gesamt'
            style = ' style="font-weight:bold;background:#f0f0f0;"' if is_total else ''
            
            status_color = {'✅': '#27ae60', '🔄': '#3498db', '⚠️': '#f39c12', '❌': '#e74c3c'}
            status_bg = status_color.get(row[4], '#666')
            
            rows_html += f'<tr{style}>'
            for j, cell in enumerate(row):
                if j == 4:  # Status-Spalte
                    rows_html += f'<td style="text-align:center;color:{status_bg};font-size:14pt;">{cell}</td>'
                else:
                    rows_html += f'<td>{cell}</td>'
            rows_html += '</tr>'
        
        headers_html = ''.join(f'<th>{h}</th>' for h in self.headers)
        
        html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>{self.title}</title>
<style>
body {{
    font-family: Arial, sans-serif;
    font-size: 11pt;
    max-width: 900px;
    margin: 40px auto;
    padding: 20px;
    background: #f5f5f5;
}}
.container {{
    background: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}}
h1 {{
    font-size: 18pt;
    color: #333;
    border-bottom: 3px solid #0066cc;
    padding-bottom: 10px;
    margin-bottom: 20px;
}}
.meta {{
    color: #888;
    font-style: italic;
    margin-bottom: 20px;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    font-size: 10pt;
}}
th {{
    background: #0066cc;
    color: white;
    font-weight: bold;
    padding: 12px;
    text-align: left;
}}
td {{
    padding: 10px 12px;
    border-bottom: 1px solid #eee;
}}
tr:hover {{
    background: #f8f8f8;
}}
.legend {{
    margin-top: 30px;
    padding-top: 20px;
    border-top: 1px solid #eee;
}}
.legend h2 {{
    font-size: 14pt;
    color: #444;
}}
.legend-table {{
    width: auto;
    margin-top: 10px;
}}
.legend-table td {{
    padding: 6px 12px;
    border: none;
}}
.print-btn {{
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 10px 20px;
    background: #0066cc;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}}
@media print {{
    body {{ background: white; }}
    .container {{ box-shadow: none; }}
    .print-btn {{ display: none; }}
}}
</style>
</head>
<body>
<button class="print-btn" onclick="window.print();">🖨️ Drucken / PDF</button>
<div class="container">
<h1>📊 {self.title}</h1>
<div class="meta">Erstellt: {datetime.now().strftime('%d. %B %Y, %H:%M Uhr')} | DIN 5008 konform</div>

<table>
<thead>
<tr>{headers_html}</tr>
</thead>
<tbody>
{rows_html}
</tbody>
</table>

<div class="legend">
<h2>Legende</h2>
<table class="legend-table">
<tr><td style="font-size:16pt;">✅</td><td>Im Plan (keine Abweichung)</td></tr>
<tr><td style="font-size:16pt;">🔄</td><td>In Arbeit (leichte Abweichung)</td></tr>
<tr><td style="font-size:16pt;">⚠️</td><td>Abweichung (Achtung)</td></tr>
<tr><td style="font-size:16pt;">❌</td><td>Kritisch (sofort handeln)</td></tr>
</table>
</div>
</div>
</body>
</html>"""
        return html
    
    def save(self):
        """Speichert beide Varianten"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        # Markdown
        md_file = OUTPUT_DIR / f"Tabelle_{timestamp}.md"
        md_file.write_text(self.render_markdown(), encoding='utf-8')
        print(f"✅ Markdown: {md_file}")
        
        # HTML
        html_file = OUTPUT_DIR / f"Tabelle_{timestamp}.html"
        html_file.write_text(self.render_html(), encoding='utf-8')
        print(f"✅ HTML: {html_file}")
        
        # Öffnen
        try:
            import webbrowser
            webbrowser.open(f"file://{html_file}")
            print(f"🌐 Browser geöffnet")
        except:
            pass
        
        return {'markdown': md_file, 'html': html_file}


def main():
    parser = argparse.ArgumentParser(description='DIN 5008 Generator v2.1')
    parser.add_argument('type', choices=['brief', 'tabelle', 'bericht', 'all'], 
                       default='all', nargs='?',
                       help='Was generiert werden soll')
    parser.add_argument('--output', '-o', default=str(OUTPUT_DIR),
                       help='Ausgabeverzeichnis')
    
    args = parser.parse_args()
    
    print("══════════════════════════════════════════════════════════")
    print("  📄 DIN 5008 Generator v2.1")
    print("══════════════════════════════════════════════════════════\n")
    
    results = []
    
    if args.type in ['brief', 'all']:
        print("📝 Erstelle Geschäftsbrief...")
        brief = DIN5008Brief()
        r = brief.save()
        results.append(r)
        print()
    
    if args.type in ['tabelle', 'all']:
        print("📊 Erstelle Auswertungstabelle...")
        tabelle = DIN5008Tabelle()
        r = tabelle.save()
        results.append(r)
        print()
    
    if args.type == 'bericht':
        print("📋 Projektbericht wird noch implementiert...")
        print("   Nutze: python3 brief-generator.py + tabelle-generator.py")
    
    print("══════════════════════════════════════════════════════════")
    print(f"✅ Fertig! Dateien in: {OUTPUT_DIR}")
    print("══════════════════════════════════════════════════════════")
    print()
    print("Nächste Schritte:")
    print("  1. Im Browser: Strg+P → 'Als PDF speichern'")
    print("  2. Oder: wkhtmltopdf Brief.html Brief.pdf")
    print()
    print(f"Ausgabe: {OUTPUT_DIR}")
    for f in OUTPUT_DIR.glob('*'):
        if f.is_file():
            print(f"  📄 {f.name} ({f.stat().st_size:,} Bytes)")

if __name__ == '__main__':
    main()