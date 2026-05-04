import os
from dotenv import load_dotenv
from supabase import create_client


def conectar_supabase():
    load_dotenv()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("Faltan SUPABASE_URL o SUPABASE_KEY en el archivo .env")

    return create_client(url, key)


def obtener_o_crear_fuente_pdf(supabase, nombre_archivo):
    respuesta = (
        supabase.table("fuentes_pdf")
        .select("id")
        .eq("nombre_archivo", nombre_archivo)
        .execute()
    )

    if respuesta.data:
        return respuesta.data[0]["id"]

    nueva_fuente = {
        "nombre_archivo": nombre_archivo,
        "tipo_fuente": "PDF procesado automáticamente",
        "fuente": "Carpeta pdfs",
        "procesado": True,
        "observaciones": "Fuente creada automáticamente desde el extractor de PDFs."
    }

    insercion = supabase.table("fuentes_pdf").insert(nueva_fuente).execute()
    return insercion.data[0]["id"]


def competencia_ya_existe(supabase, fuente_pdf_id, nombre_competencia, evidencia):
    respuesta = (
        supabase.table("competencias_mercado")
        .select("id")
        .eq("fuente_pdf_id", fuente_pdf_id)
        .eq("nombre_competencia", nombre_competencia)
        .eq("evidencia", evidencia)
        .execute()
    )

    return len(respuesta.data) > 0


def transformar_tipo(tipo_original):
    if not tipo_original:
        return "No clasificada"

    tipo = tipo_original.lower()

    if "técnica" in tipo or "tecnica" in tipo:
        return "Técnica"

    if "transversal" in tipo:
        return "Transversal"

    if "tendencia" in tipo:
        return "Tendencia laboral"

    return tipo_original


def estimar_nivel_demanda(porcentajes_texto):
    if not porcentajes_texto:
        return "Media"

    porcentajes = []

    for parte in porcentajes_texto.split(","):
        parte = parte.strip().replace("%", "")

        if parte.isdigit():
            porcentajes.append(int(parte))

    if not porcentajes:
        return "Media"

    maximo = max(porcentajes)

    if maximo >= 50:
        return "Alta"
    elif maximo >= 25:
        return "Media"
    else:
        return "Baja"


def alimentar_competencias_mercado():
    supabase = conectar_supabase()

    respuesta = (
        supabase.table("variables_extraidas_pdf")
        .select("*")
        .execute()
    )

    variables = respuesta.data

    if not variables:
        print("No hay variables extraídas desde PDFs.")
        return

    registros_insertados = 0
    registros_omitidos = 0

    for variable in variables:
        archivo = variable.get("archivo")
        nombre_variable = variable.get("variable_detectada")
        tipo = transformar_tipo(variable.get("tipo"))
        categoria = variable.get("categoria")
        evidencia = variable.get("evidencia")
        porcentajes = variable.get("porcentajes_en_pagina")

        if not archivo or not nombre_variable:
            registros_omitidos += 1
            continue

        fuente_pdf_id = obtener_o_crear_fuente_pdf(supabase, archivo)

        if competencia_ya_existe(supabase, fuente_pdf_id, nombre_variable, evidencia):
            registros_omitidos += 1
            continue

        nuevo_registro = {
            "fuente_pdf_id": fuente_pdf_id,
            "nombre_competencia": nombre_variable,
            "tipo_competencia": tipo,
            "categoria": categoria,
            "sector": "No especificado",
            "cargo_asociado": "No especificado",
            "nivel_demanda": estimar_nivel_demanda(porcentajes),
            "evidencia": evidencia
        }

        supabase.table("competencias_mercado").insert(nuevo_registro).execute()
        registros_insertados += 1

    print("Proceso terminado.")
    print(f"Registros insertados en competencias_mercado: {registros_insertados}")
    print(f"Registros omitidos por duplicado o datos incompletos: {registros_omitidos}")


if __name__ == "__main__":
    alimentar_competencias_mercado()