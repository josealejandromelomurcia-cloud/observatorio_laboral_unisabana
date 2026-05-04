import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

st.set_page_config(
    page_title="Observatorio Laboral UniSabana",
    page_icon="📊",
    layout="wide"
)


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

def mostrar_brechas_automaticas(brechas_automaticas):
    st.title("Brechas automáticas desde PDFs")
    st.write(
        "Esta sección muestra una comparación preliminar entre las competencias "
        "detectadas automáticamente en PDFs del mercado laboral y las competencias "
        "registradas para cada programa académico."
    )

    programas = ["Todos"] + sorted(brechas_automaticas["nombre_programa"].dropna().unique().tolist())
    estados = ["Todos"] + sorted(brechas_automaticas["estado_brecha"].dropna().unique().tolist())
    niveles = ["Todos"] + sorted(brechas_automaticas["nivel_brecha"].dropna().unique().tolist())

    col1, col2, col3 = st.columns(3)
    programa = col1.selectbox("Programa académico", programas, key="programa_auto")
    estado = col2.selectbox("Estado de brecha", estados, key="estado_auto")
    nivel = col3.selectbox("Nivel de brecha", niveles, key="nivel_auto")

    datos = brechas_automaticas.copy()

    if programa != "Todos":
        datos = datos[datos["nombre_programa"] == programa]

    if estado != "Todos":
        datos = datos[datos["estado_brecha"] == estado]

    if nivel != "Todos":
        datos = datos[datos["nivel_brecha"] == nivel]

    st.divider()

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Registros analizados", len(datos))
    kpi2.metric("Competencias únicas", datos["nombre_competencia"].nunique())
    kpi3.metric("Brechas altas", int((datos["nivel_brecha"] == "Alta").sum()))
    kpi4.metric("No cubiertas", int((datos["estado_brecha"] == "No cubierta").sum()))

    st.divider()

    conteo_brechas = (
        datos.groupby(["nombre_programa", "nivel_brecha"])
        .size()
        .reset_index(name="cantidad")
    )

    if not conteo_brechas.empty:
        fig = px.bar(
            conteo_brechas,
            x="nombre_programa",
            y="cantidad",
            color="nivel_brecha",
            title="Brechas automáticas por programa",
            barmode="group",
            labels={
                "nombre_programa": "Programa académico",
                "cantidad": "Cantidad",
                "nivel_brecha": "Nivel de brecha"
            }
        )
        st.plotly_chart(fig, use_container_width=True)

    columnas = [
        "nombre_programa",
        "nombre_competencia",
        "tipo_competencia",
        "categoria",
        "nivel_demanda",
        "frecuencia_aparicion",
        "cantidad_fuentes",
        "estado_brecha",
        "nivel_brecha",
        "justificacion",
        "recomendacion"
    ]

    st.subheader("Tabla de comparación automática")
    st.dataframe(datos[columnas], use_container_width=True)

try:
    resumen = cargar_resumen_brechas()
    criticas = cargar_competencias_criticas()
    brecha_completa = cargar_brecha_completa()
    brechas_automaticas = cargar_brechas_automaticas()

    st.sidebar.title("Observatorio Laboral")
    st.sidebar.write("Alumni UniSabana - IN-DES Challenge")

    modulo_principal = st.sidebar.radio(
        "Navegación principal",
        [
            "Inicio",
            "Brechas oferta-demanda"
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

except Exception as e:
    st.error("No se pudo conectar con Supabase o cargar los datos.")
    st.exception(e)