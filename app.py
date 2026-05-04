from io import BytesIO
import re
import time

import pandas as pd
import plotly.express as px
import streamlit as st
from pypdf import PdfReader
from supabase import create_client

st.set_page_config(
    page_title="Observatorio Laboral UniSabana",
    page_icon="📊",
    layout="wide"
)

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
    },
    "Analítica de datos": {
        "tipo": "Competencia técnica",
        "categoria": "Analítica de datos",
        "palabras_clave": ["data analytics", "analítica de datos", "analitica de datos", "data analysis", "análisis de datos", "analisis de datos"]
    },
    "Inteligencia artificial": {
        "tipo": "Competencia técnica",
        "categoria": "Transformación digital",
        "palabras_clave": ["artificial intelligence", "inteligencia artificial", "machine learning", "ai", "ia", "modelos predictivos"]
    },
    "Automatización": {
        "tipo": "Competencia técnica",
        "categoria": "Transformación digital",
        "palabras_clave": ["automation", "automatización", "automatizacion", "robotización", "robotizacion", "rpa"]
    },
    "Ciberseguridad": {
        "tipo": "Competencia técnica",
        "categoria": "Tecnología y seguridad",
        "palabras_clave": ["cybersecurity", "ciberseguridad", "seguridad informática", "seguridad informatica", "information security"]
    },
    "Programación y desarrollo de software": {
        "tipo": "Competencia técnica",
        "categoria": "Desarrollo de software",
        "palabras_clave": ["software development", "programación", "programacion", "developer", "desarrollador", "python", "java", "javascript"]
    },
    "Cloud computing": {
        "tipo": "Competencia técnica",
        "categoria": "Infraestructura digital",
        "palabras_clave": ["cloud", "cloud computing", "aws", "azure", "google cloud", "nube"]
    },
    "Business intelligence": {
        "tipo": "Competencia técnica",
        "categoria": "Analítica de datos",
        "palabras_clave": ["business intelligence", "bi", "power bi", "tableau", "dashboards", "visualización de datos", "visualizacion de datos"]
    },
    "Gestión de proyectos": {
        "tipo": "Competencia transversal",
        "categoria": "Gestión de proyectos",
        "palabras_clave": ["project management", "gestión de proyectos", "gestion de proyectos", "scrum", "agile", "metodologías ágiles", "metodologias agiles"]
    },
    "Innovación y emprendimiento": {
        "tipo": "Competencia transversal",
        "categoria": "Innovación",
        "palabras_clave": ["innovation", "innovación", "innovacion", "entrepreneurship", "emprendimiento", "intraemprendimiento"]
    },
    "Finanzas digitales": {
        "tipo": "Competencia técnica",
        "categoria": "Finanzas digitales",
        "palabras_clave": ["fintech", "finanzas digitales", "digital finance", "blockchain", "banca digital"]
    },
    "Salud digital": {
        "tipo": "Competencia técnica",
        "categoria": "Salud digital",
        "palabras_clave": ["healthtech", "salud digital", "telemedicina", "digital health", "tecnología médica", "tecnologia medica"]
    },
    "Logística y cadena de suministro": {
        "tipo": "Competencia técnica",
        "categoria": "Operaciones y logística",
        "palabras_clave": ["logistics", "logística", "logistica", "supply chain", "cadena de suministro", "operaciones"]
    }
}


@st.cache_resource
def conectar_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


@st.cache_data(ttl=600)
def cargar_resumen_brechas():
    supabase = conectar_supabase()
    respuesta = supabase.table("resumen_brechas_por_programa_pdf").select("*").execute()
    return pd.DataFrame(respuesta.data)


@st.cache_data(ttl=600)
def cargar_competencias_criticas():
    supabase = conectar_supabase()
    respuesta = supabase.table("vista_competencias_criticas_pdf").select("*").execute()
    return pd.DataFrame(respuesta.data)


@st.cache_data(ttl=600)
def cargar_brecha_completa():
    supabase = conectar_supabase()
    respuesta = supabase.table("vista_brecha_oferta_demanda_pdf").select("*").execute()
    return pd.DataFrame(respuesta.data)

@st.cache_data(ttl=600)
def cargar_programas_en_riesgo():
    supabase = conectar_supabase()
    respuesta = supabase.table("programas_en_riesgo").select("*").execute()
    return pd.DataFrame(respuesta.data)

@st.cache_data(ttl=600)
def cargar_nuevas_oportunidades():
    supabase = conectar_supabase()
    respuesta = supabase.table("nuevas_oportunidades").select("*").execute()
    return pd.DataFrame(respuesta.data)

@st.cache_data(ttl=600)
def cargar_competencias_emergentes():
    supabase = conectar_supabase()
    respuesta = supabase.table("competencias_emergentes").select("*").execute()
    return pd.DataFrame(respuesta.data)

@st.cache_data(ttl=600)
def cargar_sectores_crecimiento():
    supabase = conectar_supabase()
    respuesta = supabase.table("sectores_crecimiento").select("*").execute()
    return pd.DataFrame(respuesta.data)

@st.cache_data(ttl=600)
def cargar_brechas_automaticas():
    supabase = conectar_supabase()
    respuesta = supabase.table("vista_comparacion_automatica_brechas").select("*").execute()
    return pd.DataFrame(respuesta.data)


def extraer_porcentajes(texto):
    patron = r"\d{1,3}%"
    return re.findall(patron, texto)


def extraer_texto_pdf_subido(archivo_subido):
    contenido = archivo_subido.read()
    lector = PdfReader(BytesIO(contenido))
    paginas = []

    for numero_pagina, pagina in enumerate(lector.pages, start=1):
        texto = pagina.extract_text() or ""
        paginas.append({
            "pagina": numero_pagina,
            "texto": texto
        })

    return paginas



def buscar_variables_en_paginas(nombre_archivo, paginas):
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


# Nueva función: inferir_sector_desde_texto
def inferir_sector_desde_texto(texto):
    texto = str(texto).lower()

    sectores = {
        "Tecnología": [
            "technology", "tecnología", "tecnologia", "software", "cloud", "cybersecurity",
            "ciberseguridad", "data", "inteligencia artificial", "artificial intelligence",
            "machine learning", "programación", "programacion"
        ],
        "Financiero": [
            "finance", "financial", "finanzas", "banca", "banking", "fintech", "seguros",
            "insurance", "inversión", "inversion"
        ],
        "Salud": [
            "health", "salud", "hospital", "clínica", "clinica", "medicina", "enfermería",
            "enfermeria", "telemedicina", "healthtech"
        ],
        "Educación": [
            "education", "educación", "educacion", "universidad", "colegio", "aprendizaje",
            "formación", "formacion", "training"
        ],
        "Manufactura": [
            "manufacturing", "manufactura", "producción", "produccion", "planta", "industrial",
            "operaciones", "maintenance", "mantenimiento"
        ],
        "Energía": [
            "energy", "energía", "energia", "oil", "gas", "renovable", "renewable", "electricidad",
            "minería", "mineria"
        ],
        "Construcción": [
            "construction", "construcción", "construccion", "infraestructura", "civil", "obra",
            "real estate"
        ],
        "Consultoría": [
            "consulting", "consultoría", "consultoria", "advisory", "asesoría", "asesoria"
        ],
        "Comercio y servicios": [
            "retail", "commerce", "comercio", "servicios", "customer", "cliente", "ventas", "sales"
        ],
        "Talento humano": [
            "human resources", "recursos humanos", "talento", "hiring", "retention", "recruitment",
            "reclutamiento"
        ],
        "Logística": [
            "logistics", "logística", "logistica", "supply chain", "cadena de suministro", "transporte"
        ]
    }

    for sector, palabras in sectores.items():
        for palabra in palabras:
            if palabra in texto:
                return sector

    return "No especificado"


def limpiar_valor(valor):
    if pd.isna(valor):
        return None
    return str(valor)

def normalizar_texto_columna(texto):
    texto = str(texto).strip().lower()
    texto = texto.replace("á", "a")
    texto = texto.replace("é", "e")
    texto = texto.replace("í", "i")
    texto = texto.replace("ó", "o")
    texto = texto.replace("ú", "u")
    texto = texto.replace("ñ", "n")
    texto = texto.replace(" ", "_")
    texto = texto.replace("-", "_")
    texto = texto.replace("/", "_")
    return texto


def leer_excel_subido(archivo_subido):
    hojas = pd.read_excel(archivo_subido, sheet_name=None)
    hojas_limpias = {}

    for nombre_hoja, df in hojas.items():
        df = df.copy()
        df.columns = [normalizar_texto_columna(columna) for columna in df.columns]
        df = df.dropna(how="all")
        hojas_limpias[nombre_hoja] = df

    return hojas_limpias


def obtener_valor_flexible(fila, posibles_columnas):
    for columna in posibles_columnas:
        columna_normalizada = normalizar_texto_columna(columna)
        if columna_normalizada in fila.index and not pd.isna(fila[columna_normalizada]):
            return fila[columna_normalizada]
    return None


# ------------------ FUNCIONES DE CARGA DE EXCELS A SUPABASE ------------------
def guardar_excel_competencias_mercado(nombre_archivo, df):
    supabase = conectar_supabase()
    fuente_pdf_id = obtener_o_crear_fuente_pdf(supabase, nombre_archivo)
    registros_insertados = 0
    registros_omitidos = 0

    for _, fila in df.iterrows():
        nombre_competencia = obtener_valor_flexible(
            fila,
            ["nombre_competencia", "competencia", "variable_detectada", "habilidad", "skill"]
        )

        if pd.isna(nombre_competencia) or not nombre_competencia:
            registros_omitidos += 1
            continue

        tipo_competencia = obtener_valor_flexible(
            fila,
            ["tipo_competencia", "tipo", "clasificacion"]
        ) or "No clasificada"

        categoria = obtener_valor_flexible(
            fila,
            ["categoria", "area", "grupo"]
        ) or "No especificada"

        sector = obtener_valor_flexible(
            fila,
            ["sector", "industria"]
        ) or "No especificado"

        cargo_asociado = obtener_valor_flexible(
            fila,
            ["cargo_asociado", "cargo", "perfil", "rol"]
        ) or "No especificado"

        nivel_demanda = obtener_valor_flexible(
            fila,
            ["nivel_demanda", "demanda", "prioridad"]
        ) or "Media"

        evidencia = obtener_valor_flexible(
            fila,
            ["evidencia", "descripcion", "detalle", "observacion", "observaciones"]
        ) or f"Registro cargado desde el Excel {nombre_archivo}."

        if competencia_ya_existe(supabase, fuente_pdf_id, str(nombre_competencia), str(evidencia)):
            registros_omitidos += 1
            continue

        supabase.table("competencias_mercado").insert({
            "fuente_pdf_id": fuente_pdf_id,
            "nombre_competencia": limpiar_valor(nombre_competencia),
            "tipo_competencia": transformar_tipo(limpiar_valor(tipo_competencia)),
            "categoria": limpiar_valor(categoria),
            "sector": limpiar_valor(sector),
            "cargo_asociado": limpiar_valor(cargo_asociado),
            "nivel_demanda": limpiar_valor(nivel_demanda),
            "evidencia": limpiar_valor(evidencia)
        }).execute()
        registros_insertados += 1

    return {
        "registros_insertados": registros_insertados,
        "registros_omitidos": registros_omitidos
    }


def guardar_excel_programas_academicos(df):
    supabase = conectar_supabase()
    registros_insertados = 0
    registros_omitidos = 0

    for _, fila in df.iterrows():
        nombre_programa = obtener_valor_flexible(
            fila,
            ["nombre_programa", "programa", "carrera"]
        )

        if pd.isna(nombre_programa) or not nombre_programa:
            registros_omitidos += 1
            continue

        respuesta = (
            supabase.table("programas_academicos")
            .select("id")
            .eq("nombre_programa", str(nombre_programa))
            .execute()
        )

        if respuesta.data:
            registros_omitidos += 1
            continue

        supabase.table("programas_academicos").insert({
            "nombre_programa": limpiar_valor(nombre_programa),
            "facultad": limpiar_valor(obtener_valor_flexible(fila, ["facultad", "escuela"])),
            "nivel_formacion": limpiar_valor(obtener_valor_flexible(fila, ["nivel_formacion", "nivel"])),
            "descripcion": limpiar_valor(obtener_valor_flexible(fila, ["descripcion", "detalle", "observacion"]))
        }).execute()
        registros_insertados += 1

    return {
        "registros_insertados": registros_insertados,
        "registros_omitidos": registros_omitidos
    }


def obtener_id_programa_por_nombre(supabase, nombre_programa):
    respuesta = (
        supabase.table("programas_academicos")
        .select("id")
        .eq("nombre_programa", str(nombre_programa))
        .execute()
    )

    if respuesta.data:
        return respuesta.data[0]["id"]

    return None


def guardar_excel_competencias_programa(df):
    supabase = conectar_supabase()
    registros_insertados = 0
    registros_omitidos = 0

    for _, fila in df.iterrows():
        nombre_programa = obtener_valor_flexible(
            fila,
            ["nombre_programa", "programa", "carrera"]
        )
        nombre_competencia = obtener_valor_flexible(
            fila,
            ["nombre_competencia", "competencia", "habilidad", "skill"]
        )

        if pd.isna(nombre_programa) or pd.isna(nombre_competencia) or not nombre_programa or not nombre_competencia:
            registros_omitidos += 1
            continue

        programa_id = obtener_id_programa_por_nombre(supabase, nombre_programa)

        if not programa_id:
            registros_omitidos += 1
            continue

        respuesta = (
            supabase.table("competencias_programa")
            .select("id")
            .eq("programa_id", programa_id)
            .eq("nombre_competencia", str(nombre_competencia))
            .execute()
        )

        if respuesta.data:
            registros_omitidos += 1
            continue

        supabase.table("competencias_programa").insert({
            "programa_id": programa_id,
            "nombre_competencia": limpiar_valor(nombre_competencia),
            "tipo_competencia": limpiar_valor(obtener_valor_flexible(fila, ["tipo_competencia", "tipo"])),
            "categoria": limpiar_valor(obtener_valor_flexible(fila, ["categoria", "area", "grupo"])),
            "nivel_formacion": limpiar_valor(obtener_valor_flexible(fila, ["nivel_formacion", "nivel"])),
            "evidencia_curricular": limpiar_valor(obtener_valor_flexible(fila, ["evidencia_curricular", "evidencia", "descripcion", "detalle"]))
        }).execute()
        registros_insertados += 1

    return {
        "registros_insertados": registros_insertados,
        "registros_omitidos": registros_omitidos
    }

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
    if maximo >= 25:
        return "Media"
    return "Baja"


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
        "tipo_fuente": "PDF cargado desde Streamlit",
        "fuente": "Cargador web del observatorio",
        "procesado": True,
        "observaciones": "Fuente creada automáticamente desde el cargador de PDFs de Streamlit."
    }

    insercion = supabase.table("fuentes_pdf").insert(nueva_fuente).execute()
    return insercion.data[0]["id"]


def variable_ya_existe(supabase, archivo, pagina, variable_detectada):
    respuesta = (
        supabase.table("variables_extraidas_pdf")
        .select("id")
        .eq("archivo", archivo)
        .eq("pagina", pagina)
        .eq("variable_detectada", variable_detectada)
        .execute()
    )

    return len(respuesta.data) > 0


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

def dividir_en_lotes(lista, tamano_lote=100):
    for inicio in range(0, len(lista), tamano_lote):
        yield lista[inicio:inicio + tamano_lote]

def guardar_resultados_pdf_en_supabase(resultados):
    supabase = conectar_supabase()
    variables_insertadas = 0
    competencias_insertadas = 0
    registros_omitidos = 0

    if not resultados:
        return {
            "variables_insertadas": 0,
            "competencias_insertadas": 0,
            "registros_omitidos": 0
        }

    fuentes_por_archivo = {}
    archivos_unicos = sorted({
        resultado.get("archivo")
        for resultado in resultados
        if resultado.get("archivo")
    })

    for archivo in archivos_unicos:
        fuentes_por_archivo[archivo] = obtener_o_crear_fuente_pdf(supabase, archivo)

    variables_nuevas = []
    competencias_nuevas = []

    claves_variables_en_lote = set()
    claves_competencias_en_lote = set()

    for resultado in resultados:
        archivo = resultado.get("archivo")
        pagina = resultado.get("pagina")
        variable_detectada = resultado.get("variable_detectada")
        evidencia = resultado.get("evidencia")

        if not archivo or not pagina or not variable_detectada:
            registros_omitidos += 1
            continue

        clave_variable = (
            str(archivo),
            int(pagina),
            str(variable_detectada)
        )

        if clave_variable not in claves_variables_en_lote:
            variables_nuevas.append({
                "archivo": limpiar_valor(resultado.get("archivo")),
                "pagina": int(resultado.get("pagina")),
                "variable_detectada": limpiar_valor(resultado.get("variable_detectada")),
                "tipo": limpiar_valor(resultado.get("tipo")),
                "categoria": limpiar_valor(resultado.get("categoria")),
                "palabras_clave_encontradas": limpiar_valor(resultado.get("palabras_clave_encontradas")),
                "porcentajes_en_pagina": limpiar_valor(resultado.get("porcentajes_en_pagina")),
                "evidencia": limpiar_valor(resultado.get("evidencia"))
            })
            claves_variables_en_lote.add(clave_variable)
        else:
            registros_omitidos += 1

        fuente_pdf_id = fuentes_por_archivo.get(archivo)

        clave_competencia = (
            fuente_pdf_id,
            str(variable_detectada),
            str(evidencia)
        )

        if fuente_pdf_id and clave_competencia not in claves_competencias_en_lote:
            competencias_nuevas.append({
                "fuente_pdf_id": fuente_pdf_id,
                "nombre_competencia": limpiar_valor(variable_detectada),
                "tipo_competencia": transformar_tipo(resultado.get("tipo")),
                "categoria": limpiar_valor(resultado.get("categoria")),
                "sector": inferir_sector_desde_texto(evidencia),
                "cargo_asociado": "No especificado",
                "nivel_demanda": estimar_nivel_demanda(resultado.get("porcentajes_en_pagina")),
                "evidencia": limpiar_valor(evidencia)
            })
            claves_competencias_en_lote.add(clave_competencia)
        else:
            registros_omitidos += 1

    if variables_nuevas:
        for lote_variables in dividir_en_lotes(variables_nuevas, tamano_lote=100):
            respuesta_variables = (
                supabase.table("variables_extraidas_pdf")
                .upsert(
                    lote_variables,
                    on_conflict="archivo,pagina,variable_detectada",
                    ignore_duplicates=True
                )
                .execute()
            )

            variables_insertadas += len(respuesta_variables.data or [])

    if competencias_nuevas:
        for lote_competencias in dividir_en_lotes(competencias_nuevas, tamano_lote=100):
            respuesta_competencias = (
                supabase.table("competencias_mercado")
                .upsert(
                    lote_competencias,
                    on_conflict="fuente_pdf_id,nombre_competencia,evidencia",
                    ignore_duplicates=True
                )
                .execute()
            )

            competencias_insertadas += len(respuesta_competencias.data or [])

    return {
        "variables_insertadas": variables_insertadas,
        "competencias_insertadas": competencias_insertadas,
        "registros_omitidos": registros_omitidos
    }

def recalcular_modulos_analiticos():
    supabase = conectar_supabase()

    funciones_recalculo = [
        "recalcular_programas_en_riesgo",
        "recalcular_nuevas_oportunidades",
        "recalcular_competencias_emergentes",
        "recalcular_sectores_crecimiento"
    ]

    resultados = []

    for nombre_funcion in funciones_recalculo:
        try:
            respuesta = supabase.rpc(nombre_funcion).execute()
            resultados.append({
                "modulo": nombre_funcion,
                "estado": "ok",
                "respuesta": respuesta.data
            })
        except Exception as error:
            resultados.append({
                "modulo": nombre_funcion,
                "estado": "error",
                "error": str(error)
            })

    return resultados


def mostrar_kpis(resumen, criticas, brecha_completa):
    total_programas = resumen["nombre_programa"].nunique()
    total_competencias = brecha_completa["nombre_competencia"].nunique()
    total_brechas_altas = resumen["brechas_altas"].sum()
    total_no_cubiertas = resumen["competencias_no_cubiertas"].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Programas evaluados", total_programas)
    col2.metric("Competencias analizadas", total_competencias)
    col3.metric("Brechas altas", int(total_brechas_altas))
    col4.metric("Competencias no cubiertas", int(total_no_cubiertas))

def obtener_opciones_filtro(df, columna):
    if columna not in df.columns:
        return ["Todos"]

    valores = df[columna].dropna().astype(str).unique().tolist()
    valores = sorted(valores)

    return ["Todos"] + valores


def aplicar_filtros_base(df, prefijo=""):
    datos = df.copy()

    st.markdown("### Filtros principales")

    col1, col2, col3 = st.columns(3)

    programa = col1.selectbox(
        "Programa académico",
        obtener_opciones_filtro(datos, "nombre_programa"),
        key=f"{prefijo}_programa"
    )

    cobertura = col2.selectbox(
        "Cobertura geográfica",
        obtener_opciones_filtro(datos, "cobertura_geografica"),
        key=f"{prefijo}_cobertura"
    )

    fuente = col3.selectbox(
        "Fuente",
        obtener_opciones_filtro(datos, "fuente"),
        key=f"{prefijo}_fuente"
    )

    if programa != "Todos" and "nombre_programa" in datos.columns:
        datos = datos[datos["nombre_programa"].astype(str) == programa]

    if cobertura != "Todos" and "cobertura_geografica" in datos.columns:
        datos = datos[datos["cobertura_geografica"].astype(str) == cobertura]

    if fuente != "Todos" and "fuente" in datos.columns:
        datos = datos[datos["fuente"].astype(str) == fuente]

    st.divider()

    return datos

def calcular_resumen_filtrado(datos):
    if datos.empty:
        return pd.DataFrame()

    resumen = (
        datos.groupby("nombre_programa")
        .agg(
            competencias_mercado=("nombre_competencia", "nunique"),
            competencias_cubiertas=("estado_brecha", lambda x: (x == "Cubierta").sum()),
            competencias_no_cubiertas=("estado_brecha", lambda x: (x == "No cubierta").sum()),
            brechas_altas=("nivel_brecha", lambda x: (x == "Alta").sum()),
            brechas_medias=("nivel_brecha", lambda x: (x == "Media").sum()),
            brechas_bajas=("nivel_brecha", lambda x: (x == "Baja").sum())
        )
        .reset_index()
    )

    resumen["total_evaluaciones"] = (
        resumen["competencias_cubiertas"] + resumen["competencias_no_cubiertas"]
    )

    resumen["porcentaje_cobertura"] = (
        100 * resumen["competencias_cubiertas"] / resumen["total_evaluaciones"].replace(0, pd.NA)
    ).fillna(0).round(1)

    resumen["porcentaje_brecha"] = (
        100 * resumen["competencias_no_cubiertas"] / resumen["total_evaluaciones"].replace(0, pd.NA)
    ).fillna(0).round(1)

    def clasificar_alerta(fila):
        if fila["porcentaje_brecha"] >= 70 or fila["brechas_altas"] >= 10:
            return "Alta"
        if fila["porcentaje_brecha"] >= 40 or fila["brechas_altas"] >= 5:
            return "Media"
        return "Baja"

    resumen["nivel_alerta"] = resumen.apply(clasificar_alerta, axis=1)

    resumen["diagnostico"] = resumen.apply(
        lambda fila: (
            f"El programa presenta {fila['porcentaje_brecha']}% de brecha frente a las competencias detectadas en el mercado. "
            f"Se identifican {int(fila['brechas_altas'])} brechas altas."
        ),
        axis=1
    )

    resumen["recomendacion"] = resumen["nivel_alerta"].map({
        "Alta": "Priorizar revisión curricular, actualización de competencias y rutas complementarias de formación.",
        "Media": "Revisar electivas, certificaciones y resultados de aprendizaje asociados a competencias no cubiertas.",
        "Baja": "Mantener seguimiento periódico y actualizar evidencia con nuevas fuentes de mercado."
    })

    columnas = [
        "nombre_programa",
        "competencias_mercado",
        "competencias_cubiertas",
        "competencias_no_cubiertas",
        "porcentaje_cobertura",
        "porcentaje_brecha",
        "brechas_altas",
        "nivel_alerta",
        "diagnostico",
        "recomendacion"
    ]

    return resumen[columnas]


def calcular_brechas_por_tipo(datos):
    if datos.empty or "tipo_competencia" not in datos.columns:
        return pd.DataFrame()

    resumen_tipo = (
        datos.groupby(["nombre_programa", "tipo_competencia"])
        .agg(
            competencias_mercado=("nombre_competencia", "nunique"),
            competencias_cubiertas=("estado_brecha", lambda x: (x == "Cubierta").sum()),
            competencias_no_cubiertas=("estado_brecha", lambda x: (x == "No cubierta").sum()),
            brechas_altas=("nivel_brecha", lambda x: (x == "Alta").sum()),
            brechas_medias=("nivel_brecha", lambda x: (x == "Media").sum()),
            brechas_bajas=("nivel_brecha", lambda x: (x == "Baja").sum())
        )
        .reset_index()
    )

    resumen_tipo["total_evaluaciones"] = (
        resumen_tipo["competencias_cubiertas"] + resumen_tipo["competencias_no_cubiertas"]
    )

    resumen_tipo["porcentaje_brecha"] = (
        100 * resumen_tipo["competencias_no_cubiertas"] / resumen_tipo["total_evaluaciones"].replace(0, pd.NA)
    ).fillna(0).round(1)

    return resumen_tipo


def preparar_top_brechas_no_cubiertas(datos, max_filas=50):
    if datos.empty:
        return pd.DataFrame()

    datos_no_cubiertos = datos.copy()

    if "estado_brecha" in datos_no_cubiertos.columns:
        datos_no_cubiertos = datos_no_cubiertos[
            datos_no_cubiertos["estado_brecha"].astype(str) == "No cubierta"
        ]

    if datos_no_cubiertos.empty:
        return pd.DataFrame()

    columnas_base = [
        "nombre_programa",
        "nombre_competencia",
        "tipo_competencia",
        "categoria",
        "nivel_demanda",
        "nivel_brecha",
        "fuente",
        "recomendacion"
    ]

    columnas_existentes = [col for col in columnas_base if col in datos_no_cubiertos.columns]

    orden_nivel = {
        "Alta": 1,
        "Media": 2,
        "Baja": 3
    }

    datos_no_cubiertos = datos_no_cubiertos[columnas_existentes].drop_duplicates()

    if "nivel_brecha" in datos_no_cubiertos.columns:
        datos_no_cubiertos["orden_brecha"] = datos_no_cubiertos["nivel_brecha"].map(orden_nivel).fillna(4)
        datos_no_cubiertos = datos_no_cubiertos.sort_values(["orden_brecha", "nombre_programa"])
        datos_no_cubiertos = datos_no_cubiertos.drop(columns=["orden_brecha"])

    return datos_no_cubiertos.head(max_filas)

def mostrar_inicio(resumen, criticas, brecha_completa):
    st.title("Observatorio Laboral UniSabana")
    st.subheader("Monitoreo estratégico del mercado laboral")

    st.write(
        "Esta plataforma integra fuentes del mercado laboral en PDF y Excel para apoyar "
        "la toma de decisiones sobre pertinencia académica, empleabilidad, actualización "
        "curricular y relación con el sector productivo."
    )

    st.success("Conexión exitosa con Supabase.")
    mostrar_kpis(resumen, criticas, brecha_completa)

    st.divider()

    st.markdown("### Módulos principales del observatorio")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**1. Brechas oferta-demanda**")
        st.write(
            "Compara competencias demandadas por el mercado frente a competencias "
            "registradas en los programas académicos."
        )

        st.markdown("**2. Programas en riesgo**")
        st.write(
            "Identifica programas con señales de riesgo por demanda decreciente, baja "
            "cobertura, brechas altas o transformación acelerada del perfil profesional."
        )

        st.markdown("**3. Nuevas oportunidades**")
        st.write(
            "Resume tendencias de empleo, competencias asociadas y rangos salariales "
            "detectados en las fuentes cargadas."
        )

    with col2:
        st.markdown("**4. Competencias emergentes**")
        st.write(
            "Mapea competencias técnicas y transversales con mayor proyección para el "
            "mercado laboral."
        )

        st.markdown("**5. Sectores con mayor crecimiento**")
        st.write(
            "Identifica sectores con señales de expansión para orientar empleabilidad, "
            "orientación profesional y alianzas estratégicas."
        )

        st.markdown("**Administrador de fuentes**")
        st.write(
            "Permite cargar PDFs y Excels para alimentar automáticamente la base de datos "
            "y recalcular los módulos analíticos."
        )

    st.divider()

    st.markdown("### Lectura ejecutiva")
    st.write(
        "El observatorio transforma información dispersa en indicadores comparables. "
        "Cada módulo usa tablas propias en Supabase y se actualiza a partir de las fuentes "
        "procesadas desde el Administrador de fuentes."
    )


def mostrar_resumen_programas(brecha_completa):
    st.title("Resumen ejecutivo por programa")
    st.write(
        "Esta sección resume la brecha entre las competencias exigidas por el mercado "
        "y las competencias registradas en la oferta académica de cada programa."
    )

    datos_filtrados = aplicar_filtros_base(brecha_completa, prefijo="resumen")

    st.caption(f"Registros cargados para el análisis: {len(brecha_completa):,}")

    resumen = calcular_resumen_filtrado(datos_filtrados)

    if resumen.empty:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Programas filtrados", resumen["nombre_programa"].nunique())
    kpi2.metric("Competencias de mercado", int(resumen["competencias_mercado"].sum()))
    kpi3.metric("Brecha promedio", f"{resumen['porcentaje_brecha'].mean():.1f}%")
    kpi4.metric("Programas en alerta alta", int((resumen["nivel_alerta"] == "Alta").sum()))

    st.subheader("Tabla ejecutiva de brecha por programa")

    tabla_resumen = resumen.rename(columns={
        "nombre_programa": "Programa",
        "competencias_mercado": "Competencias exigidas por el mercado",
        "competencias_cubiertas": "Competencias cubiertas",
        "competencias_no_cubiertas": "Competencias no cubiertas",
        "porcentaje_cobertura": "% cobertura académica",
        "porcentaje_brecha": "% brecha",
        "brechas_altas": "Brechas altas",
        "nivel_alerta": "Nivel de alerta",
        "diagnostico": "Diagnóstico",
        "recomendacion": "Recomendación"
    })

    st.dataframe(tabla_resumen, use_container_width=True)

    fig = px.bar(
        resumen,
        x="nombre_programa",
        y=["porcentaje_cobertura", "porcentaje_brecha"],
        title="Cobertura académica vs brecha por programa",
        barmode="group",
        labels={
            "nombre_programa": "Programa académico",
            "value": "Porcentaje",
            "variable": "Indicador"
        }
    )
    st.plotly_chart(fig, use_container_width=True)


def mostrar_brechas_por_tipo(brecha_completa):
    st.title("Brechas por tipo de competencia")
    st.write(
        "Esta sección separa la brecha entre competencias técnicas y competencias "
        "transversales/blandas, tal como lo exige el análisis de pertinencia académica."
    )

    datos = aplicar_filtros_base(brecha_completa, prefijo="tipo_brecha")
    resumen_tipo = calcular_brechas_por_tipo(datos)

    if resumen_tipo.empty:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    st.subheader("Tabla de brechas por tipo de competencia")

    tabla_tipo = resumen_tipo.rename(columns={
        "nombre_programa": "Programa",
        "tipo_competencia": "Tipo de competencia",
        "competencias_mercado": "Competencias de mercado",
        "competencias_cubiertas": "Cubiertas",
        "competencias_no_cubiertas": "No cubiertas",
        "brechas_altas": "Brechas altas",
        "brechas_medias": "Brechas medias",
        "brechas_bajas": "Brechas bajas",
        "porcentaje_brecha": "% brecha"
    })

    st.dataframe(tabla_tipo, use_container_width=True)

    fig = px.bar(
        resumen_tipo,
        x="nombre_programa",
        y="porcentaje_brecha",
        color="tipo_competencia",
        barmode="group",
        title="Porcentaje de brecha por tipo de competencia",
        labels={
            "nombre_programa": "Programa académico",
            "porcentaje_brecha": "% brecha",
            "tipo_competencia": "Tipo de competencia"
        }
    )
    st.plotly_chart(fig, use_container_width=True)


def mostrar_top_brechas_no_cubiertas(brecha_completa):
    st.title("Top competencias no cubiertas")
    st.write(
        "Esta sección identifica las competencias exigidas por el mercado que no aparecen "
        "cubiertas en la oferta académica de los programas filtrados."
    )

    datos = aplicar_filtros_base(brecha_completa, prefijo="top_brechas")

    col1, col2, col3 = st.columns(3)

    tipo_competencia = col1.selectbox(
        "Tipo de competencia",
        obtener_opciones_filtro(datos, "tipo_competencia"),
        key="top_tipo_competencia"
    )

    nivel_demanda = col2.selectbox(
        "Nivel de demanda",
        obtener_opciones_filtro(datos, "nivel_demanda"),
        key="top_nivel_demanda"
    )

    nivel_brecha = col3.selectbox(
        "Nivel de brecha",
        obtener_opciones_filtro(datos, "nivel_brecha"),
        key="top_nivel_brecha"
    )

    filtros = {
        "tipo_competencia": tipo_competencia,
        "nivel_demanda": nivel_demanda,
        "nivel_brecha": nivel_brecha
    }

    for columna, valor in filtros.items():
        if valor != "Todos" and columna in datos.columns:
            datos = datos[datos[columna].astype(str) == valor]

    top_brechas = preparar_top_brechas_no_cubiertas(datos)

    if top_brechas.empty:
        st.warning("No hay competencias no cubiertas para los filtros seleccionados.")
        return

    tabla_top = top_brechas.rename(columns={
        "nombre_programa": "Programa",
        "nombre_competencia": "Competencia no cubierta",
        "tipo_competencia": "Tipo",
        "categoria": "Categoría",
        "nivel_demanda": "Nivel de demanda",
        "nivel_brecha": "Nivel de brecha",
        "fuente": "Fuente",
        "recomendacion": "Recomendación"
    })

    st.subheader("Competencias prioritarias no cubiertas")
    st.dataframe(tabla_top, use_container_width=True)
def mostrar_competencias_criticas(criticas):
    st.title("Competencias críticas")
    st.write(
        "Aquí se muestran las competencias con brecha alta o media. "
        "Los filtros permiten priorizar análisis por programa, facultad, fuente, sector, "
        "cobertura geográfica y nivel de demanda."
    )

    datos = aplicar_filtros_base(criticas, prefijo="criticas")

    if datos.empty:
        st.warning("No hay competencias críticas para los filtros seleccionados.")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Registros críticos", len(datos))
    col2.metric("Competencias únicas", datos["nombre_competencia"].nunique())
    col3.metric("Brechas altas", int((datos["nivel_brecha"] == "Alta").sum()))
    col4.metric("Fuentes", datos["fuente"].nunique() if "fuente" in datos.columns else 0)

    col_graf1, col_graf2 = st.columns(2)

    conteo_nivel = datos["nivel_brecha"].value_counts().reset_index()
    conteo_nivel.columns = ["nivel_brecha", "cantidad"]

    fig_nivel = px.pie(
        conteo_nivel,
        names="nivel_brecha",
        values="cantidad",
        title="Distribución por nivel de brecha"
    )
    col_graf1.plotly_chart(fig_nivel, use_container_width=True)

    conteo_tipo = datos["tipo_competencia"].value_counts().reset_index()
    conteo_tipo.columns = ["tipo_competencia", "cantidad"]

    fig_tipo = px.bar(
        conteo_tipo,
        x="tipo_competencia",
        y="cantidad",
        title="Competencias críticas por tipo",
        labels={
            "tipo_competencia": "Tipo de competencia",
            "cantidad": "Cantidad"
        }
    )
    col_graf2.plotly_chart(fig_tipo, use_container_width=True)

    st.subheader("Tabla de competencias críticas")
    st.dataframe(datos, use_container_width=True)

def mostrar_brecha_detallada(brecha_completa):
    st.title("Detalle de brecha oferta-demanda")
    st.write(
        "Esta tabla integra programa académico, competencia de mercado, fuente, cobertura, "
        "estado de brecha, justificación y recomendación."
    )

    datos = aplicar_filtros_base(brecha_completa, prefijo="detalle")

    st.markdown("### Filtros específicos de brecha")

    col1, col2, col3 = st.columns(3)

    tipo_competencia = col1.selectbox(
        "Tipo de competencia",
        obtener_opciones_filtro(datos, "tipo_competencia"),
        key="detalle_tipo_competencia"
    )

    nivel_demanda = col2.selectbox(
        "Nivel de demanda",
        obtener_opciones_filtro(datos, "nivel_demanda"),
        key="detalle_nivel_demanda"
    )

    nivel_brecha = col3.selectbox(
        "Nivel de brecha",
        obtener_opciones_filtro(datos, "nivel_brecha"),
        key="detalle_nivel_brecha"
    )

    col4, col5, col6 = st.columns(3)

    estado_brecha = col4.selectbox(
        "Estado de brecha",
        obtener_opciones_filtro(datos, "estado_brecha"),
        key="detalle_estado_brecha"
    )

    sector = col5.selectbox(
        "Sector económico",
        obtener_opciones_filtro(datos, "sector"),
        key="detalle_sector"
    )

    periodo = col6.selectbox(
        "Periodo",
        obtener_opciones_filtro(datos, "periodo"),
        key="detalle_periodo"
    )

    filtros_brecha = {
        "tipo_competencia": tipo_competencia,
        "nivel_demanda": nivel_demanda,
        "nivel_brecha": nivel_brecha,
        "estado_brecha": estado_brecha,
        "sector": sector,
        "periodo": periodo
    }

    for columna, valor in filtros_brecha.items():
        if valor != "Todos" and columna in datos.columns:
            datos = datos[datos[columna].astype(str) == valor]

    st.divider()

    if datos.empty:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    columnas = [
        "nombre_programa",
        "facultad",
        "nombre_competencia",
        "tipo_competencia",
        "categoria",
        "sector",
        "cobertura_geografica",
        "fuente",
        "periodo",
        "nivel_demanda",
        "estado_brecha",
        "nivel_brecha",
        "frecuencia_aparicion",
        "cantidad_fuentes",
        "justificacion",
        "recomendacion"
    ]

    columnas_existentes = [col for col in columnas if col in datos.columns]

    st.dataframe(datos[columnas_existentes], use_container_width=True)

def mostrar_programas_en_riesgo(programas_riesgo):
    st.title("Programas en riesgo")
    st.write(
        "Este módulo identifica programas con señales de riesgo por demanda decreciente, "
        "baja cobertura frente al mercado, concentración de brechas altas y transformación "
        "acelerada del perfil profesional."
    )

    datos = programas_riesgo.copy()

    st.markdown("### Filtros del módulo")

    col1, col2, col3 = st.columns(3)

    programa = col1.selectbox(
        "Programa académico",
        obtener_opciones_filtro(datos, "nombre_programa"),
        key="riesgo_programa"
    )

    cobertura = col2.selectbox(
        "Cobertura geográfica",
        obtener_opciones_filtro(datos, "cobertura_geografica"),
        key="riesgo_cobertura"
    )

    fuente = col3.selectbox(
        "Fuente",
        obtener_opciones_filtro(datos, "fuente"),
        key="riesgo_fuente"
    )

    col4, col5, col6 = st.columns(3)

    tendencia_demanda = col4.selectbox(
        "Tendencia de demanda",
        obtener_opciones_filtro(datos, "tendencia_demanda"),
        key="riesgo_tendencia_demanda"
    )

    nivel_riesgo = col5.selectbox(
        "Nivel de riesgo",
        obtener_opciones_filtro(datos, "nivel_riesgo"),
        key="riesgo_nivel"
    )

    tipo_senal = col6.selectbox(
        "Tipo de señal de riesgo",
        [
            "Todas",
            "Demanda decreciente",
            "Baja cobertura frente al mercado",
            "Concentración de brechas altas",
            "Transformación acelerada del perfil"
        ],
        key="riesgo_senal"
    )

    orden = st.selectbox(
        "Ordenar por",
        [
            "Mayor riesgo",
            "Demanda decreciente primero",
            "Mayor no cobertura",
            "Mayor transformación del perfil",
            "Mayor brecha alta"
        ],
        key="riesgo_orden"
    )

    if programa != "Todos" and "nombre_programa" in datos.columns:
        datos = datos[datos["nombre_programa"].astype(str) == programa]

    if cobertura != "Todos" and "cobertura_geografica" in datos.columns:
        datos = datos[datos["cobertura_geografica"].astype(str) == cobertura]

    if fuente != "Todos" and "fuente" in datos.columns:
        datos = datos[datos["fuente"].astype(str) == fuente]

    if tendencia_demanda != "Todos" and "tendencia_demanda" in datos.columns:
        datos = datos[datos["tendencia_demanda"].astype(str) == tendencia_demanda]

    if nivel_riesgo != "Todos" and "nivel_riesgo" in datos.columns:
        datos = datos[datos["nivel_riesgo"].astype(str) == nivel_riesgo]

    if tipo_senal == "Demanda decreciente" and "tendencia_demanda" in datos.columns:
        datos = datos[datos["tendencia_demanda"].astype(str) == "Demanda decreciente"]

    elif tipo_senal == "Baja cobertura frente al mercado" and "tipo_riesgo_principal" in datos.columns:
        datos = datos[datos["tipo_riesgo_principal"].astype(str) == "Baja cobertura frente al mercado"]

    elif tipo_senal == "Concentración de brechas altas" and "tipo_riesgo_principal" in datos.columns:
        datos = datos[datos["tipo_riesgo_principal"].astype(str) == "Concentración de brechas altas"]

    elif tipo_senal == "Transformación acelerada del perfil" and "tipo_riesgo_principal" in datos.columns:
        datos = datos[datos["tipo_riesgo_principal"].astype(str) == "Transformación acelerada del perfil"]

    if datos.empty:
        st.warning("No hay programas en riesgo para los filtros seleccionados.")
        return

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Programas evaluados",
        datos["nombre_programa"].nunique() if "nombre_programa" in datos.columns else 0
    )

    col2.metric(
        "Riesgo alto",
        int((datos["nivel_riesgo"] == "Alto").sum()) if "nivel_riesgo" in datos.columns else 0
    )

    col3.metric(
        "Demanda decreciente",
        int((datos["tendencia_demanda"] == "Demanda decreciente").sum()) if "tendencia_demanda" in datos.columns else 0
    )

    col4.metric(
        "Transformación promedio",
        f"{datos['porcentaje_transformacion_perfil'].mean():.1f}%" if "porcentaje_transformacion_perfil" in datos.columns else "0.0%"
    )

    orden_riesgo = {
        "Alto": 1,
        "Medio": 2,
        "Bajo": 3
    }

    orden_tendencia = {
        "Demanda decreciente": 1,
        "Demanda estable": 2,
        "Demanda creciente": 3,
        "Sin histórico suficiente": 4,
        "Pendiente de histórico": 5
    }

    datos_ordenados = datos.copy()

    if "nivel_riesgo" in datos_ordenados.columns:
        datos_ordenados["orden_riesgo"] = datos_ordenados["nivel_riesgo"].map(orden_riesgo).fillna(4)
    else:
        datos_ordenados["orden_riesgo"] = 4

    if "tendencia_demanda" in datos_ordenados.columns:
        datos_ordenados["orden_tendencia"] = datos_ordenados["tendencia_demanda"].map(orden_tendencia).fillna(6)
    else:
        datos_ordenados["orden_tendencia"] = 6

    if orden == "Mayor riesgo":
        columnas_orden = ["orden_riesgo"]
        ascendentes = [True]

        if "porcentaje_no_cobertura" in datos_ordenados.columns:
            columnas_orden.append("porcentaje_no_cobertura")
            ascendentes.append(False)

        datos_ordenados = datos_ordenados.sort_values(columnas_orden, ascending=ascendentes)

    elif orden == "Demanda decreciente primero":
        datos_ordenados = datos_ordenados.sort_values(
            ["orden_tendencia", "orden_riesgo"],
            ascending=[True, True]
        )

    elif orden == "Mayor no cobertura" and "porcentaje_no_cobertura" in datos_ordenados.columns:
        datos_ordenados = datos_ordenados.sort_values("porcentaje_no_cobertura", ascending=False)

    elif orden == "Mayor transformación del perfil" and "porcentaje_transformacion_perfil" in datos_ordenados.columns:
        datos_ordenados = datos_ordenados.sort_values("porcentaje_transformacion_perfil", ascending=False)

    elif orden == "Mayor brecha alta" and "porcentaje_brecha_alta" in datos_ordenados.columns:
        datos_ordenados = datos_ordenados.sort_values("porcentaje_brecha_alta", ascending=False)

    st.divider()

    col_graf1, col_graf2 = st.columns(2)

    if "nivel_riesgo" in datos_ordenados.columns:
        conteo_riesgo = datos_ordenados["nivel_riesgo"].value_counts().reset_index()
        conteo_riesgo.columns = ["nivel_riesgo", "cantidad"]

        fig_riesgo = px.bar(
            conteo_riesgo,
            x="nivel_riesgo",
            y="cantidad",
            title="Distribución de programas por nivel de riesgo",
            labels={
                "nivel_riesgo": "Nivel de riesgo",
                "cantidad": "Cantidad"
            }
        )
        col_graf1.plotly_chart(fig_riesgo, use_container_width=True)

    if "tendencia_demanda" in datos_ordenados.columns:
        conteo_tendencia = datos_ordenados["tendencia_demanda"].value_counts().reset_index()
        conteo_tendencia.columns = ["tendencia_demanda", "cantidad"]

        fig_tendencia = px.bar(
            conteo_tendencia,
            x="tendencia_demanda",
            y="cantidad",
            title="Distribución por tendencia de demanda",
            labels={
                "tendencia_demanda": "Tendencia de demanda",
                "cantidad": "Cantidad"
            }
        )
        col_graf2.plotly_chart(fig_tendencia, use_container_width=True)

    columnas = [
        "nombre_programa",
        "cobertura_geografica",
        "tendencia_demanda",
        "nivel_riesgo",
        "tipo_riesgo_principal",
        "diagnostico_riesgo",
        "recomendacion",
        "fuente"
    ]

    columnas_existentes = [col for col in columnas if col in datos_ordenados.columns]

    st.subheader("Tabla ejecutiva de programas en riesgo")

    tabla_riesgo = datos_ordenados[columnas_existentes].rename(columns={
        "nombre_programa": "Programa",
        "cobertura_geografica": "Cobertura",
        "tendencia_demanda": "Tendencia de demanda",
        "nivel_riesgo": "Nivel de riesgo",
        "tipo_riesgo_principal": "Tipo de riesgo principal",
        "diagnostico_riesgo": "Diagnóstico",
        "recomendacion": "Recomendación",
        "fuente": "Fuente"
    })

    st.dataframe(tabla_riesgo, use_container_width=True)

def mostrar_nuevas_oportunidades(nuevas_oportunidades):
    st.title("Nuevas oportunidades")
    st.write(
        "Este módulo identifica oportunidades laborales a partir de las fuentes cargadas. "
        "Se enfoca únicamente en tendencias de empleo, competencias y rangos salariales."
    )

    datos = nuevas_oportunidades.copy()

    st.markdown("### Filtros del módulo")

    col1, col2, col3 = st.columns(3)

    programa = col1.selectbox(
        "Programa académico",
        obtener_opciones_filtro(datos, "nombre_programa"),
        key="oportunidades_programa"
    )

    cobertura = col2.selectbox(
        "Cobertura geográfica",
        obtener_opciones_filtro(datos, "cobertura_geografica"),
        key="oportunidades_cobertura"
    )

    fuente = col3.selectbox(
        "Fuente",
        obtener_opciones_filtro(datos, "fuente"),
        key="oportunidades_fuente"
    )

    if programa != "Todos" and "nombre_programa" in datos.columns:
        datos = datos[datos["nombre_programa"].astype(str) == programa]

    if cobertura != "Todos" and "cobertura_geografica" in datos.columns:
        datos = datos[datos["cobertura_geografica"].astype(str) == cobertura]

    if fuente != "Todos" and "fuente" in datos.columns:
        datos = datos[datos["fuente"].astype(str) == fuente]

    if datos.empty:
        st.warning("No hay nuevas oportunidades para los filtros seleccionados.")
        return

    st.divider()

    col1, col2, col3 = st.columns(3)

    col1.metric("Oportunidades detectadas", len(datos))
    col2.metric("Competencias únicas", datos["competencia"].nunique())
    col3.metric("Fuentes", datos["fuente"].nunique())

    st.divider()

    conteo_tendencias = datos["tendencia_empleo"].value_counts().reset_index()
    conteo_tendencias.columns = ["tendencia_empleo", "cantidad"]

    fig_tendencias = px.bar(
        conteo_tendencias,
        x="tendencia_empleo",
        y="cantidad",
        title="Tendencias de empleo detectadas",
        labels={
            "tendencia_empleo": "Tendencia de empleo",
            "cantidad": "Cantidad"
        }
    )
    st.plotly_chart(fig_tendencias, use_container_width=True)

    columnas = [
        "tendencia_empleo",
        "competencia",
        "rango_salarial"
    ]

    tabla_oportunidades = datos[columnas].rename(columns={
        "tendencia_empleo": "Tendencia de empleo",
        "competencia": "Competencia",
        "rango_salarial": "Rango salarial"
    })

    st.subheader("Tabla ejecutiva de nuevas oportunidades")
    st.dataframe(tabla_oportunidades, use_container_width=True)


def mostrar_competencias_emergentes(competencias_emergentes):
    st.title("Competencias emergentes")
    st.write(
        "Este módulo mapea competencias técnicas y transversales/blandas con mayor "
        "proyección para el mercado laboral, a partir de las fuentes cargadas en el observatorio."
    )

    datos = competencias_emergentes.copy()

    st.markdown("### Filtros del módulo")

    col1, col2, col3 = st.columns(3)

    programa = col1.selectbox(
        "Programa académico",
        obtener_opciones_filtro(datos, "nombre_programa"),
        key="emergentes_programa"
    )

    cobertura = col2.selectbox(
        "Cobertura geográfica",
        obtener_opciones_filtro(datos, "cobertura_geografica"),
        key="emergentes_cobertura"
    )

    fuente = col3.selectbox(
        "Fuente",
        obtener_opciones_filtro(datos, "fuente"),
        key="emergentes_fuente"
    )

    col4, col5 = st.columns(2)

    tipo_competencia = col4.selectbox(
        "Tipo de competencia",
        obtener_opciones_filtro(datos, "tipo_competencia"),
        key="emergentes_tipo"
    )

    nivel_proyeccion = col5.selectbox(
        "Nivel de proyección",
        obtener_opciones_filtro(datos, "nivel_proyeccion"),
        key="emergentes_proyeccion"
    )

    if programa != "Todos" and "nombre_programa" in datos.columns:
        datos = datos[datos["nombre_programa"].astype(str) == programa]

    if cobertura != "Todos" and "cobertura_geografica" in datos.columns:
        datos = datos[datos["cobertura_geografica"].astype(str) == cobertura]

    if fuente != "Todos" and "fuente" in datos.columns:
        datos = datos[datos["fuente"].astype(str) == fuente]

    if tipo_competencia != "Todos" and "tipo_competencia" in datos.columns:
        datos = datos[datos["tipo_competencia"].astype(str) == tipo_competencia]

    if nivel_proyeccion != "Todos" and "nivel_proyeccion" in datos.columns:
        datos = datos[datos["nivel_proyeccion"].astype(str) == nivel_proyeccion]

    if datos.empty:
        st.warning("No hay competencias emergentes para los filtros seleccionados.")
        return

    st.divider()

    col1, col2, col3 = st.columns(3)

    col1.metric("Competencias emergentes", datos["competencia"].nunique())
    col2.metric("Técnicas", int((datos["tipo_competencia"] == "Técnica").sum()) if "tipo_competencia" in datos.columns else 0)
    col3.metric("Transversales", int((datos["tipo_competencia"] == "Transversal").sum()) if "tipo_competencia" in datos.columns else 0)

    st.divider()

    conteo_tipo = datos["tipo_competencia"].value_counts().reset_index()
    conteo_tipo.columns = ["tipo_competencia", "cantidad"]

    fig_tipo = px.bar(
        conteo_tipo,
        x="tipo_competencia",
        y="cantidad",
        title="Competencias emergentes por tipo",
        labels={
            "tipo_competencia": "Tipo de competencia",
            "cantidad": "Cantidad"
        }
    )
    st.plotly_chart(fig_tipo, use_container_width=True)

    columnas = [
        "competencia",
        "tipo_competencia",
        "nivel_proyeccion"
    ]

    columnas_existentes = [col for col in columnas if col in datos.columns]

    tabla_emergentes = datos[columnas_existentes].rename(columns={
        "competencia": "Competencia",
        "tipo_competencia": "Tipo de competencia",
        "nivel_proyeccion": "Nivel de proyección"
    })

    st.subheader("Tabla ejecutiva de competencias emergentes")
    st.dataframe(tabla_emergentes, use_container_width=True)


def mostrar_sectores_crecimiento(sectores_crecimiento):
    st.title("Sectores con mayor crecimiento")
    st.write(
        "Este módulo identifica sectores con señales de expansión a partir de las fuentes cargadas. "
        "Su objetivo es orientar decisiones de empleabilidad, orientación profesional y posibles "
        "alianzas estratégicas con el sector productivo."
    )

    datos = sectores_crecimiento.copy()

    st.markdown("### Filtros del módulo")

    col1, col2, col3 = st.columns(3)

    programa = col1.selectbox(
        "Programa académico",
        obtener_opciones_filtro(datos, "nombre_programa"),
        key="sectores_programa"
    )

    cobertura = col2.selectbox(
        "Cobertura geográfica",
        obtener_opciones_filtro(datos, "cobertura_geografica"),
        key="sectores_cobertura"
    )

    fuente = col3.selectbox(
        "Fuente",
        obtener_opciones_filtro(datos, "fuente"),
        key="sectores_fuente"
    )

    col4, col5 = st.columns(2)

    nivel_crecimiento = col4.selectbox(
        "Nivel de crecimiento",
        obtener_opciones_filtro(datos, "nivel_crecimiento"),
        key="sectores_nivel_crecimiento"
    )

    orientacion_estrategica = col5.selectbox(
        "Orientación estratégica",
        obtener_opciones_filtro(datos, "orientacion_estrategica"),
        key="sectores_orientacion"
    )

    if programa != "Todos" and "nombre_programa" in datos.columns:
        datos = datos[datos["nombre_programa"].astype(str) == programa]

    if cobertura != "Todos" and "cobertura_geografica" in datos.columns:
        datos = datos[datos["cobertura_geografica"].astype(str) == cobertura]

    if fuente != "Todos" and "fuente" in datos.columns:
        datos = datos[datos["fuente"].astype(str) == fuente]

    if nivel_crecimiento != "Todos" and "nivel_crecimiento" in datos.columns:
        datos = datos[datos["nivel_crecimiento"].astype(str) == nivel_crecimiento]

    if orientacion_estrategica != "Todos" and "orientacion_estrategica" in datos.columns:
        datos = datos[datos["orientacion_estrategica"].astype(str) == orientacion_estrategica]

    if datos.empty:
        st.warning("No hay sectores con crecimiento para los filtros seleccionados.")
        return

    st.divider()

    col1, col2, col3 = st.columns(3)

    col1.metric("Sectores identificados", datos["sector"].nunique() if "sector" in datos.columns else 0)
    col2.metric("Registros de crecimiento", len(datos))
    col3.metric("Fuentes", datos["fuente"].nunique() if "fuente" in datos.columns else 0)

    st.divider()

    conteo_sectores = datos["sector"].value_counts().reset_index()
    conteo_sectores.columns = ["sector", "cantidad"]

    fig_sectores = px.bar(
        conteo_sectores,
        x="sector",
        y="cantidad",
        title="Sectores con señales de crecimiento",
        labels={
            "sector": "Sector",
            "cantidad": "Cantidad de señales"
        }
    )
    st.plotly_chart(fig_sectores, use_container_width=True)

    columnas = [
        "sector",
        "nivel_crecimiento",
        "orientacion_estrategica"
    ]

    columnas_existentes = [col for col in columnas if col in datos.columns]

    tabla_sectores = datos[columnas_existentes].rename(columns={
        "sector": "Sector",
        "nivel_crecimiento": "Nivel de crecimiento",
        "orientacion_estrategica": "Orientación estratégica"
    })

    st.subheader("Tabla ejecutiva de sectores con mayor crecimiento")
    st.dataframe(tabla_sectores, use_container_width=True)

def mostrar_administrador_fuentes():
    st.title("Administrador de fuentes")
    st.write(
        "Carga fuentes del mercado laboral y de oferta académica. Los PDFs se analizan "
        "por palabras clave y los Excels se cargan como datos estructurados para alimentar "
        "las tablas del observatorio."
    )

    tipo_fuente = st.radio(
        "Selecciona el tipo de fuente que quieres cargar",
        ["PDFs", "Excels"],
        horizontal=True
    )

    if tipo_fuente == "PDFs":
        archivos = st.file_uploader(
            "Sube PDFs para alimentar el observatorio",
            type=["pdf"],
            accept_multiple_files=True,
            key="uploader_pdfs"
        )

        if not archivos:
            st.info("Sube al menos un PDF para iniciar el procesamiento.")
            return

        st.write(f"PDFs cargados: {len(archivos)}")

        if st.button("Procesar PDFs y actualizar observatorio", type="primary"):
            todos_resultados = []

            progreso = st.progress(0)
            estado_proceso = st.empty()
            tiempo_proceso = st.empty()
            inicio_proceso = time.time()
            total_archivos = len(archivos)

            for indice, archivo in enumerate(archivos, start=1):
                estado_proceso.info(
                    f"Procesando archivo {indice} de {total_archivos}: {archivo.name}"
                )

                paginas = extraer_texto_pdf_subido(archivo)
                resultados_pdf = buscar_variables_en_paginas(archivo.name, paginas)
                todos_resultados.extend(resultados_pdf)

                porcentaje_avance = indice / total_archivos
                progreso.progress(porcentaje_avance)

                tiempo_transcurrido = time.time() - inicio_proceso
                tiempo_promedio = tiempo_transcurrido / indice
                archivos_restantes = total_archivos - indice
                tiempo_estimado_restante = tiempo_promedio * archivos_restantes

                tiempo_proceso.write(
                    f"Tiempo transcurrido: {tiempo_transcurrido:.1f} s | "
                    f"Tiempo estimado restante: {tiempo_estimado_restante:.1f} s"
                )

            estado_proceso.success("Extracción de PDFs terminada.")
            progreso.progress(1.0)

            if not todos_resultados:
                st.warning("No se detectaron variables laborales en los PDFs cargados.")
                return

            df_resultados = pd.DataFrame(todos_resultados)

            estado_proceso.info("Guardando resultados en Supabase...")
            tiempo_guardado_inicio = time.time()
            resumen_carga = guardar_resultados_pdf_en_supabase(todos_resultados)
            tiempo_guardado = time.time() - tiempo_guardado_inicio

            estado_proceso.info("Recalculando módulos analíticos...")
            tiempo_recalculo_inicio = time.time()
            resultados_recalculo = recalcular_modulos_analiticos()
            tiempo_recalculo = time.time() - tiempo_recalculo_inicio

            modulos_con_error = [
                resultado for resultado in resultados_recalculo
                if resultado["estado"] == "error"
            ]

            if modulos_con_error:
                st.warning(
                    "La fuente se guardó, pero uno o más módulos analíticos no se recalcularon por completo. "
                    "Puedes intentarlo nuevamente o recalcular desde Supabase."
                )
                st.dataframe(pd.DataFrame(modulos_con_error), use_container_width=True)

            tiempo_total = time.time() - inicio_proceso
            tiempo_proceso.write(
                f"Tiempo total: {tiempo_total:.1f} s | "
                f"Guardado en Supabase: {tiempo_guardado:.1f} s | "
                f"Recálculo analítico: {tiempo_recalculo:.1f} s"
            )
            estado_proceso.success("Proceso completo.")

            st.cache_data.clear()

            st.success("Procesamiento terminado. Los módulos del observatorio fueron actualizados.")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Variables detectadas", len(df_resultados))
            col2.metric("PDFs procesados", df_resultados["archivo"].nunique())
            col3.metric("Variables nuevas", resumen_carga["variables_insertadas"])
            col4.metric("Competencias nuevas", resumen_carga["competencias_insertadas"])

            if resumen_carga["registros_omitidos"] > 0:
                st.info(
                    f"Registros omitidos por duplicado o datos incompletos: "
                    f"{resumen_carga['registros_omitidos']}"
                )

            st.subheader("Vista previa de variables extraídas")
            st.dataframe(df_resultados, use_container_width=True)

    elif tipo_fuente == "Excels":
        st.markdown("### Cargar datos estructurados desde Excel")
        st.write(
            "El Excel debe tener encabezados claros. La plataforma reconoce columnas como "
            "competencia, nombre_competencia, tipo, categoria, sector, cargo, programa, "
            "facultad, nivel y evidencia."
        )

        tipo_excel = st.selectbox(
            "¿Qué información contiene el Excel?",
            [
                "Competencias de mercado",
                "Programas académicos",
                "Competencias de programas"
            ]
        )

        archivo_excel = st.file_uploader(
            "Sube un archivo Excel",
            type=["xlsx", "xls"],
            accept_multiple_files=False,
            key="uploader_excels"
        )

        if not archivo_excel:
            st.info("Sube un Excel para revisar su contenido.")
            return

        hojas = leer_excel_subido(archivo_excel)
        nombres_hojas = list(hojas.keys())

        hoja_seleccionada = st.selectbox("Selecciona la hoja que quieres cargar", nombres_hojas)
        df_excel = hojas[hoja_seleccionada]

        st.subheader("Vista previa del Excel")
        st.dataframe(df_excel.head(50), use_container_width=True)

        if st.button("Cargar Excel a Supabase", type="primary"):
            progreso = st.progress(0)
            estado_proceso = st.empty()
            tiempo_proceso = st.empty()
            inicio_proceso = time.time()

            estado_proceso.info("Cargando Excel en Supabase...")
            progreso.progress(0.25)

            if tipo_excel == "Competencias de mercado":
                resultado = guardar_excel_competencias_mercado(archivo_excel.name, df_excel)
            elif tipo_excel == "Programas académicos":
                resultado = guardar_excel_programas_academicos(df_excel)
            else:
                resultado = guardar_excel_competencias_programa(df_excel)

            progreso.progress(0.65)
            tiempo_carga = time.time() - inicio_proceso
            tiempo_proceso.write(
                f"Tiempo de carga a Supabase: {tiempo_carga:.1f} s | "
                "Recalculando módulos analíticos..."
            )

            estado_proceso.info("Recalculando módulos analíticos...")
            tiempo_recalculo_inicio = time.time()
            resultados_recalculo = recalcular_modulos_analiticos()
            tiempo_recalculo = time.time() - tiempo_recalculo_inicio

            modulos_con_error = [
                resultado for resultado in resultados_recalculo
                if resultado["estado"] == "error"
            ]

            if modulos_con_error:
                st.warning(
                    "El Excel se guardó, pero uno o más módulos analíticos no se recalcularon por completo. "
                    "Puedes intentarlo nuevamente o recalcular desde Supabase."
                )
                st.dataframe(pd.DataFrame(modulos_con_error), use_container_width=True)

            progreso.progress(1.0)
            tiempo_total = time.time() - inicio_proceso
            tiempo_proceso.write(
                f"Tiempo total: {tiempo_total:.1f} s | "
                f"Carga Excel: {tiempo_carga:.1f} s | "
                f"Recálculo analítico: {tiempo_recalculo:.1f} s"
            )
            estado_proceso.success("Proceso completo.")

            st.cache_data.clear()

            st.success("Excel cargado correctamente. Los módulos del observatorio fueron actualizados.")

            col1, col2 = st.columns(2)
            col1.metric("Registros insertados", resultado["registros_insertados"])
            col2.metric("Registros omitidos", resultado["registros_omitidos"])

try:
    resumen = cargar_resumen_brechas()
    criticas = cargar_competencias_criticas()
    brecha_completa = cargar_brecha_completa()
    programas_riesgo = cargar_programas_en_riesgo()
    nuevas_oportunidades = cargar_nuevas_oportunidades()
    competencias_emergentes = cargar_competencias_emergentes()
    sectores_crecimiento = cargar_sectores_crecimiento()

    st.sidebar.title("Observatorio Laboral")
    st.sidebar.write("Alumni UniSabana - IN-DES Challenge")

    modulo_principal = st.sidebar.radio(
        "Navegación principal",
        [
            "Inicio",
            "Brechas oferta-demanda",
            "Programas en riesgo",
            "Nuevas oportunidades",
            "Competencias emergentes",
            "Sectores con mayor crecimiento",
            "Administrador de fuentes"
        ]
    )

    seccion_brechas = None

    if modulo_principal == "Brechas oferta-demanda":
        with st.sidebar.expander("Opciones de brecha", expanded=True):
            seccion_brechas = st.radio(
                "Selecciona una sección",
                [
                    "Resumen ejecutivo por programa",
                    "Brechas por tipo de competencia",
                    "Top competencias no cubiertas",
                    "Competencias críticas",
                    "Detalle de brecha"
                ],
                label_visibility="collapsed"
            )

    st.sidebar.divider()
    st.sidebar.caption("Fuente: Supabase PostgreSQL")
    st.sidebar.caption("MVP: Observatorio laboral con 5 módulos analíticos")

    if st.sidebar.button("Actualizar datos desde Supabase"):
        st.cache_data.clear()
        st.rerun()

    if modulo_principal == "Inicio":
        mostrar_inicio(resumen, criticas, brecha_completa)
    elif modulo_principal == "Brechas oferta-demanda":
        if seccion_brechas == "Resumen ejecutivo por programa":
            mostrar_resumen_programas(brecha_completa)
        elif seccion_brechas == "Brechas por tipo de competencia":
            mostrar_brechas_por_tipo(brecha_completa)
        elif seccion_brechas == "Top competencias no cubiertas":
            mostrar_top_brechas_no_cubiertas(brecha_completa)
        elif seccion_brechas == "Competencias críticas":
            mostrar_competencias_criticas(criticas)
        elif seccion_brechas == "Detalle de brecha":
            mostrar_brecha_detallada(brecha_completa)
    elif modulo_principal == "Programas en riesgo":
        mostrar_programas_en_riesgo(programas_riesgo)
    elif modulo_principal == "Nuevas oportunidades":
        mostrar_nuevas_oportunidades(nuevas_oportunidades)
    elif modulo_principal == "Competencias emergentes":
        mostrar_competencias_emergentes(competencias_emergentes)
    elif modulo_principal == "Sectores con mayor crecimiento":
        mostrar_sectores_crecimiento(sectores_crecimiento)
    elif modulo_principal == "Administrador de fuentes":
        mostrar_administrador_fuentes()

except Exception as e:
    st.error("No se pudo conectar con Supabase o cargar los datos.")
    st.exception(e)