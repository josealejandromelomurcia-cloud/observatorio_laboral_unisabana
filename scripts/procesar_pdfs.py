from pathlib import Path
from pypdf import PdfReader


def extraer_texto_pdf(ruta_pdf):
    lector = PdfReader(ruta_pdf)
    texto_paginas = []

    for numero_pagina, pagina in enumerate(lector.pages, start=1):
        texto = pagina.extract_text() or ""
        texto_paginas.append({
            "pagina": numero_pagina,
            "texto": texto.strip()
        })

    return texto_paginas


def procesar_carpeta_pdfs():
    carpeta_pdfs = Path("pdfs")
    archivos_pdf = list(carpeta_pdfs.glob("*.pdf"))

    if not archivos_pdf:
        print("No se encontraron PDFs en la carpeta pdfs.")
        return

    for archivo_pdf in archivos_pdf:
        print("=" * 80)
        print(f"Procesando archivo: {archivo_pdf.name}")
        print("=" * 80)

        paginas = extraer_texto_pdf(archivo_pdf)

        for pagina in paginas:
            print(f"\n--- Página {pagina['pagina']} ---")
            texto = pagina["texto"]

            if texto:
                print(texto[:1000])
            else:
                print("No se pudo extraer texto de esta página.")


if __name__ == "__main__":
    procesar_carpeta_pdfs()