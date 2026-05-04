from io import BytesIO
import re

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


def limpiar_valor(valor):
    if pd.isna(valor):
        return None
    return str(valor)


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


def guardar_resultados_pdf_en_supabase(resultados):
    supabase = conectar_supabase()
    variables_insertadas = 0
    competencias_insertadas = 0
    registros_omitidos = 0

    for resultado in resultados:
        archivo = resultado.get("archivo")
        pagina = resultado.get("pagina")
        variable_detectada = resultado.get("variable_detectada")
        evidencia = resultado.get("evidencia")

        if not archivo or not pagina or not variable_detectada:
            registros_omitidos += 1
            continue

        if not variable_ya_existe(supabase, archivo, pagina, variable_detectada):
            supabase.table("variables_extraidas_pdf").insert({
                "archivo": limpiar_valor(resultado.get("archivo")),
                "pagina": int(resultado.get("pagina")),
                "variable_detectada": limpiar_valor(resultado.get("variable_detectada")),
                "tipo": limpiar_valor(resultado.get("tipo")),
                "categoria": limpiar_valor(resultado.get("categoria")),
                "palabras_clave_encontradas": limpiar_valor(resultado.get("palabras_clave_encontradas")),
                "porcentajes_en_pagina": limpiar_valor(resultado.get("porcentajes_en_pagina")),
                "evidencia": limpiar_valor(resultado.get("evidencia"))
            }).execute()
            variables_insertadas += 1
        else:
            registros_omitidos += 1

        fuente_pdf_id = obtener_o_crear_fuente_pdf(supabase, archivo)

        if not competencia_ya_existe(supabase, fuente_pdf_id, variable_detectada, evidencia):
            supabase.table("competencias_mercado").insert({
                "fuente_pdf_id": fuente_pdf_id,
                "nombre_competencia": limpiar_valor(variable_detectada),
                "tipo_competencia": transformar_tipo(resultado.get("tipo")),
                "categoria": limpiar_valor(resultado.get("categoria")),
                "sector": "No especificado",
                "cargo_asociado": "No especificado",
                "nivel_demanda": estimar_nivel_demanda(resultado.get("porcentajes_en_pagina")),
                "evidencia": limpiar_valor(evidencia)
            }).execute()
            competencias_insertadas += 1

    return {
        "variables_insertadas": variables_insertadas,
        "competencias_insertadas": competencias_insertadas,
        "registros_omitidos": registros_omitidos
    }


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


def mostrar_inicio(resumen, criticas, brecha_completa):
    st.title("Observatorio Laboral UniSabana")
    st.subheader("Monitoreo de brecha oferta-demanda")

    st.write(
        "Esta plataforma analiza la alineación entre las competencias demandadas "
        "por el mercado laboral y las competencias desarrolladas por los programas "
        "académicos. El objetivo es generar evidencia para orientar decisiones sobre "
        "oferta académica, fortalecimiento curricular y empleabilidad."
    )

    st.success("Conexión exitosa con Supabase.")
    mostrar_kpis(resumen, criticas, brecha_completa)

    st.divider()

    st.markdown("### Lectura ejecutiva")
    st.write(
        "El sistema permite identificar competencias cubiertas, parcialmente cubiertas "
        "y no cubiertas por programa académico. Para el MVP se prioriza la dimensión "
        "de brecha oferta-demanda, porque permite construir un diagnóstico inicial sin "
        "depender todavía de series históricas."
    )


def mostrar_resumen_programas(resumen):
    st.title("Resumen por programa")
    st.write(
        "Esta sección muestra la cantidad de competencias evaluadas y el nivel de brecha "
        "identificado para cada programa académico."
    )

    st.dataframe(resumen, use_container_width=True)

    fig = px.bar(
        resumen,
        x="nombre_programa",
        y=["brechas_altas", "brechas_medias", "brechas_bajas"],
        title="Niveles de brecha por programa",
        barmode="group",
        labels={
            "nombre_programa": "Programa académico",
            "value": "Cantidad de competencias",
            "variable": "Nivel de brecha"
        }
    )
    st.plotly_chart(fig, use_container_width=True)


def mostrar_competencias_criticas(criticas):
    st.title("Competencias críticas")
    st.write(
        "Aquí se muestran las competencias con brecha alta o media. Estas son las más "
        "importantes para priorizar acciones académicas o formativas."
    )

    programas = ["Todos"] + sorted(criticas["nombre_programa"].dropna().unique().tolist())
    programa = st.selectbox("Selecciona un programa académico", programas)

    if programa != "Todos":
        datos = criticas[criticas["nombre_programa"] == programa]
    else:
        datos = criticas

    col1, col2 = st.columns(2)

    conteo_nivel = datos["nivel_brecha"].value_counts().reset_index()
    conteo_nivel.columns = ["nivel_brecha", "cantidad"]

    fig_nivel = px.pie(
        conteo_nivel,
        names="nivel_brecha",
        values="cantidad",
        title="Distribución de competencias críticas por nivel de brecha"
    )
    col1.plotly_chart(fig_nivel, use_container_width=True)

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
    col2.plotly_chart(fig_tipo, use_container_width=True)

    st.dataframe(datos, use_container_width=True)


def mostrar_brecha_detallada(brecha_completa):
    st.title("Detalle de brecha oferta-demanda")
    st.write(
        "Esta tabla integra programa académico, competencia de mercado, estado de brecha, "
        "justificación y recomendación. Es la vista principal para análisis detallado."
    )

    programas = ["Todos"] + sorted(brecha_completa["nombre_programa"].dropna().unique().tolist())
    estados = ["Todos"] + sorted(brecha_completa["estado_brecha"].dropna().unique().tolist())
    niveles = ["Todos"] + sorted(brecha_completa["nivel_brecha"].dropna().unique().tolist())

    col1, col2, col3 = st.columns(3)
    programa = col1.selectbox("Programa", programas)
    estado = col2.selectbox("Estado de brecha", estados)
    nivel = col3.selectbox("Nivel de brecha", niveles)

    datos = brecha_completa.copy()

    if programa != "Todos":
        datos = datos[datos["nombre_programa"] == programa]

    if estado != "Todos":
        datos = datos[datos["estado_brecha"] == estado]

    if nivel != "Todos":
        datos = datos[datos["nivel_brecha"] == nivel]

    columnas = [
        "nombre_programa",
        "nombre_competencia",
        "tipo_competencia",
        "categoria",
        "nivel_demanda",
        "estado_brecha",
        "nivel_brecha",
        "justificacion",
        "recomendacion"
    ]

    st.dataframe(datos[columnas], use_container_width=True)


def mostrar_administrador_fuentes():
    st.title("Administrador de fuentes")
    st.write(
        "Carga uno o varios PDFs del mercado laboral. La plataforma extrae variables, "
        "las guarda en Supabase y actualiza las vistas usadas por el módulo de brecha "
        "oferta-demanda."
    )

    archivos = st.file_uploader(
        "Sube PDFs para alimentar el observatorio",
        type=["pdf"],
        accept_multiple_files=True
    )

    if not archivos:
        st.info("Sube al menos un PDF para iniciar el procesamiento.")
        return

    st.write(f"PDFs cargados: {len(archivos)}")

    if st.button("Procesar PDFs y actualizar observatorio", type="primary"):
        todos_resultados = []

        with st.spinner("Extrayendo variables desde los PDFs..."):
            for archivo in archivos:
                paginas = extraer_texto_pdf_subido(archivo)
                resultados_pdf = buscar_variables_en_paginas(archivo.name, paginas)
                todos_resultados.extend(resultados_pdf)

        if not todos_resultados:
            st.warning("No se detectaron variables laborales en los PDFs cargados.")
            return

        df_resultados = pd.DataFrame(todos_resultados)

        with st.spinner("Guardando resultados en Supabase..."):
            resumen_carga = guardar_resultados_pdf_en_supabase(todos_resultados)

        st.cache_data.clear()

        st.success("Procesamiento terminado. El observatorio ya usa la información cargada.")

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


try:
    resumen = cargar_resumen_brechas()
    criticas = cargar_competencias_criticas()
    brecha_completa = cargar_brecha_completa()

    st.sidebar.title("Observatorio Laboral")
    st.sidebar.write("Alumni UniSabana - IN-DES Challenge")

    modulo_principal = st.sidebar.radio(
        "Navegación principal",
        [
            "Inicio",
            "Brechas oferta-demanda",
            "Administrador de fuentes"
        ]
    )

    seccion_brechas = None

    if modulo_principal == "Brechas oferta-demanda":
        with st.sidebar.expander("Opciones de brecha", expanded=True):
            seccion_brechas = st.radio(
                "Selecciona una sección",
                [
                    "Resumen por programa",
                    "Competencias críticas",
                    "Detalle de brecha"
                ],
                label_visibility="collapsed"
            )

    st.sidebar.divider()
    st.sidebar.caption("Fuente: Supabase PostgreSQL")
    st.sidebar.caption("MVP: Brecha oferta-demanda")

    if modulo_principal == "Inicio":
        mostrar_inicio(resumen, criticas, brecha_completa)
    elif modulo_principal == "Brechas oferta-demanda":
        if seccion_brechas == "Resumen por programa":
            mostrar_resumen_programas(resumen)
        elif seccion_brechas == "Competencias críticas":
            mostrar_competencias_criticas(criticas)
        elif seccion_brechas == "Detalle de brecha":
            mostrar_brecha_detallada(brecha_completa)
    elif modulo_principal == "Administrador de fuentes":
        mostrar_administrador_fuentes()

except Exception as e:
    st.error("No se pudo conectar con Supabase o cargar los datos.")
    st.exception(e)