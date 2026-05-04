from pathlib import Path
import re
import pandas as pd
from pypdf import PdfReader


DICCIONARIO_VARIABLES = {
    "Liderazgo": {
        "tipo": "Competencia transversal",
        "categoria": "Liderazgo y gestión",
        "palabras_clave": ["liderazgo", "líder", "lideres", "líderes", "ceo"]
    },
    "Comunicación efectiva": {
        "tipo": "Competencia transversal",
        "categoria": "Comunicación",
        "palabras_clave": ["comunicación efectiva", "comunicacion efectiva", "feedback", "transparencia"]
    },
    "Pensamiento estratégico": {
        "tipo": "Competencia transversal",
        "categoria": "Pensamiento estratégico",
        "palabras_clave": ["pensamiento estratégico", "pensamiento estrategico", "estratégico", "estrategico"]
    },
    "Conocimiento técnico": {
        "tipo": "Competencia técnica",
        "categoria": "Conocimiento técnico",
        "palabras_clave": ["conocimiento técnico", "conocimiento tecnico", "habilidad técnica", "habilidad tecnica"]
    },
    "Digitalización y tecnología": {
        "tipo": "Tendencia laboral",
        "categoria": "Transformación digital",
        "palabras_clave": ["digitalization", "digitalización", "digitalizacion", "technology", "tecnología", "tecnologia"]
    },
    "Atracción y retención de talento": {
        "tipo": "Tendencia laboral",
        "categoria": "Talento humano",
        "palabras_clave": ["hiring", "retention", "retención", "retencion", "atracción", "atraccion", "talento"]
    },
    "Upskilling y reskilling": {
        "tipo": "Tendencia laboral",
        "categoria": "Formación y actualización",
        "palabras_clave": ["upskilling", "reskilling", "capacitación", "capacitacion", "development"]
    },
    "Trabajo flexible y remoto": {
        "tipo": "Tendencia laboral",
        "categoria": "Modelos de trabajo",
        "palabras_clave": ["flexible", "remote", "remoto", "work from anywhere", "modelos de trabajo"]
    },
    "Bienestar y balance vida-trabajo": {
        "tipo": "Tendencia laboral",
        "categoria": "Bienestar laboral",
        "palabras_clave": ["wellbeing", "work-life balance", "bienestar", "balance"]
    },
    "ESG y sostenibilidad": {
        "tipo": "Tendencia laboral",
        "categoria": "Sostenibilidad",
        "palabras_clave": ["esg", "sustentabilidad", "sostenibilidad", "responsabilidad social"]
    },
    "DE&I y diversidad": {
        "tipo": "Tendencia laboral",
        "categoria": "Diversidad e inclusión",
        "palabras_clave": ["de&i", "diversidad", "inclusión", "inclusion", "equidad"]
    }
}


def extraer_texto_pdf(ruta_pdf):
    lector = PdfReader(ruta_pdf)
    paginas = []

    for numero_pagina, pagina in enumerate(lector.pages, start=1):
        texto = pagina.extract_text() or ""
        paginas.append({
            "pagina": numero_pagina,
            "texto": texto
        })

    return paginas


def extraer_porcentajes(texto):
    patron = r"\d{1,3}%"
    return re.findall(patron, texto)


def buscar_variables_en_texto(nombre_archivo, paginas):
    resultados = []

    for pagina in paginas:
        numero_pagina = pagina["pagina"]
        texto_original = pagina["texto"]
        texto = texto_original.lower()
        porcentajes = extraer_porcentajes(texto_original)

        for nombre_variable, datos_variable in DICCIONARIO_VARIABLES.items():
            palabras_encontradas = []

            for palabra in datos_variable["palabras_clave"]:
                if palabra.lower() in texto:
                    palabras_encontradas.append(palabra)

            if palabras_encontradas:
                evidencia = texto_original[:700].replace("\n", " ").strip()

                resultados.append({
                    "archivo": nombre_archivo,
                    "pagina": numero_pagina,
                    "variable_detectada": nombre_variable,
                    "tipo": datos_variable["tipo"],
                    "categoria": datos_variable["categoria"],
                    "palabras_clave_encontradas": ", ".join(palabras_encontradas),
                    "porcentajes_en_pagina": ", ".join(porcentajes),
                    "evidencia": evidencia
                })

    return resultados


def procesar_pdfs():
    carpeta_pdfs = Path("pdfs")
    carpeta_resultados = Path("resultados")
    carpeta_resultados.mkdir(exist_ok=True)

    archivos_pdf = list(carpeta_pdfs.glob("*.pdf"))

    if not archivos_pdf:
        print("No se encontraron PDFs en la carpeta pdfs.")
        return

    todos_resultados = []

    for archivo_pdf in archivos_pdf:
        print("=" * 80)
        print(f"Analizando PDF: {archivo_pdf.name}")
        print("=" * 80)

        paginas = extraer_texto_pdf(archivo_pdf)
        resultados_pdf = buscar_variables_en_texto(archivo_pdf.name, paginas)

        todos_resultados.extend(resultados_pdf)

        print(f"Variables detectadas en {archivo_pdf.name}: {len(resultados_pdf)}")

    if not todos_resultados:
        print("No se detectaron variables en los PDFs.")
        return

    df = pd.DataFrame(todos_resultados)

    ruta_csv = carpeta_resultados / "variables_extraidas_pdfs.csv"
    df.to_csv(ruta_csv, index=False, encoding="utf-8-sig")

    print("\nProceso terminado.")
    print(f"Archivo generado: {ruta_csv}")
    print("\nVista previa:")
    print(df[["archivo", "pagina", "variable_detectada", "tipo", "categoria", "porcentajes_en_pagina"]])


if __name__ == "__main__":
    procesar_pdfs()