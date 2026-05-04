from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
import os
from supabase import create_client


def conectar_supabase():
    load_dotenv()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("Faltan SUPABASE_URL o SUPABASE_KEY en el archivo .env")

    return create_client(url, key)


def limpiar_valor(valor):
    if pd.isna(valor):
        return None
    return str(valor)


def cargar_csv_a_supabase():
    ruta_csv = Path("resultados/variables_extraidas_pdfs.csv")

    if not ruta_csv.exists():
        print("No existe el archivo resultados/variables_extraidas_pdfs.csv")
        return

    df = pd.read_csv(ruta_csv)

    registros = []

    for _, fila in df.iterrows():
        registros.append({
            "archivo": limpiar_valor(fila.get("archivo")),
            "pagina": int(fila.get("pagina")) if not pd.isna(fila.get("pagina")) else None,
            "variable_detectada": limpiar_valor(fila.get("variable_detectada")),
            "tipo": limpiar_valor(fila.get("tipo")),
            "categoria": limpiar_valor(fila.get("categoria")),
            "palabras_clave_encontradas": limpiar_valor(fila.get("palabras_clave_encontradas")),
            "porcentajes_en_pagina": limpiar_valor(fila.get("porcentajes_en_pagina")),
            "evidencia": limpiar_valor(fila.get("evidencia")),
        })

    supabase = conectar_supabase()

    respuesta = supabase.table("variables_extraidas_pdf").insert(registros).execute()

    print("Carga terminada.")
    print(f"Registros enviados: {len(registros)}")
    print(respuesta)


if __name__ == "__main__":
    cargar_csv_a_supabase()