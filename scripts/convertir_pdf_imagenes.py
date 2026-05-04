from pathlib import Path
import fitz  # PyMuPDF


def convertir_pdf_a_imagenes(ruta_pdf, carpeta_salida):
    documento = fitz.open(ruta_pdf)
    nombre_pdf = ruta_pdf.stem.replace(" ", "_").replace("(", "").replace(")", "")

    carpeta_pdf = carpeta_salida / nombre_pdf
    carpeta_pdf.mkdir(parents=True, exist_ok=True)

    for numero_pagina in range(len(documento)):
        pagina = documento[numero_pagina]

        zoom = 2
        matriz = fitz.Matrix(zoom, zoom)
        imagen = pagina.get_pixmap(matrix=matriz)

        ruta_imagen = carpeta_pdf / f"pagina_{numero_pagina + 1}.png"
        imagen.save(ruta_imagen)

        print(f"Imagen creada: {ruta_imagen}")

    documento.close()


def procesar_pdfs():
    carpeta_pdfs = Path("pdfs")
    carpeta_salida = Path("imagenes_pdf")

    archivos_pdf = list(carpeta_pdfs.glob("*.pdf"))

    if not archivos_pdf:
        print("No se encontraron PDFs en la carpeta pdfs.")
        return

    for archivo_pdf in archivos_pdf:
        print("=" * 80)
        print(f"Convirtiendo PDF: {archivo_pdf.name}")
        print("=" * 80)

        convertir_pdf_a_imagenes(archivo_pdf, carpeta_salida)


if __name__ == "__main__":
    procesar_pdfs()