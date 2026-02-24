import re
import markdown
from weasyprint import HTML

# --- KONFIGURATION (HIER ANPASSEN) ---
SCHRIFTGROESSE_TITEL = "10pt"  # Größe der Überschriften (h2)
SCHRIFTGROESSE_TEXT = "9pt"    # Größe des normalen Textes (p, li)
KARTEN_INNENABSTAND = "10mm"   # Rand innerhalb der Karteikarte
# -------------------------------------

def erstelle_karteikarten(input_md, output_pdf):
    # Lese die Markdown-Datei ein
    with open(input_md, 'r', encoding='utf-8') as f:
        content = f.read()

    # Trenne die Folien anhand der horizontalen Linien (---)
    slides = re.split(r'\n---\s*\n', content)

    # HTML-Grundgerüst mit CSS für die exakte Halb-A4-Aufteilung
    # Die Variablen aus der Konfiguration werden hier per f-string eingefügt
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        @page {{
            size: A4 portrait;
            margin: 0;
        }}
        body {{
            font-family: Arial, "Noto Color Emoji", sans-serif;
            margin: 0;
            padding: 0;
            background-color: white;
        }}
        .slide {{
            width: 210mm;
            height: 148.5mm; /* Exakt eine halbe A4-Seite */
            box-sizing: border-box;
            padding: {KARTEN_INNENABSTAND}; 
            border-bottom: 1px dashed #ccc;
            overflow: hidden;
        }}
        /* Seitenumbruch nach jeder zweiten Folie und Linie entfernen */
        .slide:nth-child(2n) {{
            border-bottom: none;
            page-break-after: always;
        }}
        h2 {{
            font-size: {SCHRIFTGROESSE_TITEL};
            color: #000;
            margin-top: 0;
            margin-bottom: 3mm;
        }}
        p, li {{
            font-size: {SCHRIFTGROESSE_TEXT};
            line-height: 1.3;
            margin-bottom: 2mm;
        }}
        mark {{
            background-color: #ffff00;
            font-weight: bold;
        }}
        ul {{
            margin-top: 0;
            padding-left: 5mm;
        }}
    </style>
    </head>
    <body>
    """

    for slide_text in slides:
        if not slide_text.strip():
            continue

        # Markierungen (==text==) in HTML-Tags umwandeln
        slide_text = re.sub(r'==(.*?)==', r'<mark>\1</mark>', slide_text)

        # Markdown zu HTML konvertieren
        slide_html = markdown.markdown(slide_text.strip())

        # HTML in den Container für die halbe Seite einfügen
        html_content += f'<div class="slide">\n{slide_html}\n</div>\n'

    html_content += """
    </body>
    </html>
    """

    # Generiere das PDF
    HTML(string=html_content).write_pdf(output_pdf)

if __name__ == "__main__":
    # Trage hier den Dateinamen deiner Markdown-Datei ein
    input_datei = "lansamsprechen.md" 
    output_datei = "karteikarten.pdf"
    
    erstelle_karteikarten(input_datei, output_datei)
    print(f"Fertig! Die Datei wurde als {output_datei} im selben Ordner gespeichert.")