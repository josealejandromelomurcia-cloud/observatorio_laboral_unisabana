import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

st.set_page_config(
    page_title="Observatorio Laboral UniSabana",
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
    respuesta = supabase.table("resumen_brechas_por_programa").select("*").execute()
    return pd.DataFrame(respuesta.data)

@st.cache_data(ttl=600)
def cargar_competencias_criticas():
    supabase = conectar_supabase()
    respuesta = supabase.table("vista_competencias_criticas").select("*").execute()
    return pd.DataFrame(respuesta.data)

st.title("Observatorio Laboral UniSabana")
st.subheader("Brecha oferta-demanda")

st.write(
    "Esta plataforma permite analizar la alineación entre las competencias "
    "demandadas por el mercado laboral y las competencias desarrolladas por "
    "los programas académicos."
)

try:
    resumen = cargar_resumen_brechas()
    criticas = cargar_competencias_criticas()

    st.success("Conexión exitosa con Supabase.")

    col1, col2, col3 = st.columns(3)

    total_programas = resumen["nombre_programa"].nunique()
    total_brechas_altas = resumen["brechas_altas"].sum()
    total_no_cubiertas = resumen["competencias_no_cubiertas"].sum()

    col1.metric("Programas evaluados", total_programas)
    col2.metric("Brechas altas", int(total_brechas_altas))
    col3.metric("Competencias no cubiertas", int(total_no_cubiertas))

    st.divider()

    st.subheader("Resumen de brechas por programa")
    st.dataframe(resumen, use_container_width=True)

    fig = px.bar(
        resumen,
        x="nombre_programa",
        y=["brechas_altas", "brechas_medias", "brechas_bajas"],
        title="Niveles de brecha por programa",
        barmode="group"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("Competencias críticas")
    st.write("Competencias con brecha alta o media.")

    programa = st.selectbox(
        "Selecciona un programa académico",
        ["Todos"] + sorted(criticas["nombre_programa"].unique().tolist())
    )

    if programa != "Todos":
        criticas_filtradas = criticas[criticas["nombre_programa"] == programa]
    else:
        criticas_filtradas = criticas

    st.dataframe(criticas_filtradas, use_container_width=True)

except Exception as e:
    st.error("No se pudo conectar con Supabase o cargar los datos.")
    st.exception(e)