import re
import markdown
from weasyprint import HTML

def erstelle_karteikarten(input_md, output_pdf):
    # Lese die Markdown-Datei ein
    with open(input_md, 'r', encoding='utf-8') as f:
        content = f.read()

    # Trenne die Folien anhand der horizontalen Linien (---)
    slides = re.split(r'\n---\s*\n', content)

    # HTML-Grundgerüst mit CSS für die exakte Halb-A4-Aufteilung
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        @page {
            size: A4 portrait;
            margin: 0;
        }
        body {
            font-family: Arial, "Noto Color Emoji", sans-serif;
            margin: 0;
            padding: 0;
            background-color: white;
        }
        .slide {
            width: 210mm;
            height: 148.5mm; /* Exakt eine halbe A4-Seite */
            box-sizing: border-box;
            padding: 10mm; /* Rand von 15mm auf 10mm reduziert */
            border-bottom: 1px dashed #ccc;
            overflow: hidden;
        }
        /* Seitenumbruch nach jeder zweiten Folie und Linie entfernen */
        .slide:nth-child(2n) {
            border-bottom: none;
            page-break-after: always;
        }
        h2 {
            font-size: 13pt; /* Von 16pt auf 13pt reduziert */
            color: #000;
            margin-top: 0;
            margin-bottom: 4mm; /* Abstand verkleinert */
        }
        p, li {
            font-size: 10.5pt; /* Von 13pt auf 10.5pt reduziert */
            line-height: 1.3;
            margin-bottom: 2.5mm; /* Abstand verkleinert */
        }
        mark {
            background-color: #ffff00;
            font-weight: bold;
        }
        ul {
            margin-top: 0;
            padding-left: 6mm; /* Einzug der Aufzählungszeichen reduziert */
        }
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