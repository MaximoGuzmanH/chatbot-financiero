import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# ---------- CONFIGURACIÓN INICIAL ----------
st.set_page_config(page_title="📊 Visor Financiero", layout="wide")

st.title("📋 Historial Financiero Interactivo")

# ---------- CARGA DE ARCHIVOS ----------
RUTA_TRANSACCIONES = os.path.join(os.path.dirname(__file__), "..", "transacciones.json")
RUTA_ALERTAS = os.path.join(os.path.dirname(__file__), "..", "alertas.json")

def cargar_datos_json(ruta):
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    return []

# ---------- TRANSACCIONES ----------
transacciones = cargar_datos_json(RUTA_TRANSACCIONES)
df_transacciones = pd.DataFrame(transacciones)

# Normalización para evitar errores
if not df_transacciones.empty:
    df_transacciones["monto"] = pd.to_numeric(df_transacciones.get("monto", 0), errors="coerce")
    df_transacciones["fecha"] = df_transacciones.get("fecha", "")
    df_transacciones["categoria"] = df_transacciones.get("categoria", "").fillna("Sin categoría")
    df_transacciones["tipo"] = df_transacciones.get("tipo", "").fillna("Sin tipo")
    df_transacciones["medio"] = df_transacciones.get("medio", "").fillna("Sin medio")
    df_transacciones["status"] = df_transacciones.get("status", 1).fillna(1).astype(int)
    df_transacciones["mes"] = df_transacciones.get("mes", "").fillna("desconocido").str.lower()
    df_transacciones["año"] = df_transacciones.get("año", datetime.now().year).fillna(datetime.now().year).astype(int)

# ---------- ALERTAS ----------
alertas = cargar_datos_json(RUTA_ALERTAS)
df_alertas = pd.DataFrame(alertas)

if not df_alertas.empty:
    df_alertas["tipo"] = "alerta"
    df_alertas["monto"] = pd.to_numeric(df_alertas.get("monto", 0), errors="coerce")
    df_alertas["categoria"] = df_alertas.get("categoria", "").fillna("Sin categoría")
    df_alertas["periodo"] = df_alertas.get("periodo", "").fillna("")
    df_alertas["status"] = df_alertas.get("status", 1).astype(int)
    df_alertas["mes"] = df_alertas.get("mes", "").str.lower()
    df_alertas["año"] = df_alertas.get("año", datetime.now().year).astype(int)
    df_alertas["medio"] = "N/A"
    df_alertas["fecha"] = df_alertas.get("timestamp", "")
else:
    df_alertas = pd.DataFrame(columns=df_transacciones.columns)

# ---------- UNIÓN Y FILTRADO ----------
df = pd.concat([df_transacciones, df_alertas], ignore_index=True)

# ---------- BARRA LATERAL DE FILTROS ----------
st.sidebar.header("📂 Filtros")

tipos = sorted(df["tipo"].dropna().unique())
tipo_sel = st.sidebar.multiselect("Tipo", tipos, default=tipos)

anios = sorted(df["año"].dropna().unique())
anio_sel = st.sidebar.multiselect("Año", anios, default=anios)

meses = sorted(df["mes"].dropna().unique())
mes_sel = st.sidebar.multiselect("Mes", meses, default=meses)

categorias = sorted(df["categoria"].dropna().unique())
categoria_sel = st.sidebar.multiselect("Categoría", categorias, default=categorias)

medios = sorted(df["medio"].dropna().unique())
medio_sel = st.sidebar.multiselect("Medio", medios, default=medios)

estado_sel = st.sidebar.radio("Estado", ["Activos", "Inactivos", "Todos"], index=0)

# ---------- APLICACIÓN DE FILTROS ----------
df_filtrado = df[
    df["tipo"].isin(tipo_sel) &
    df["año"].isin(anio_sel) &
    df["mes"].isin(mes_sel) &
    df["categoria"].isin(categoria_sel) &
    df["medio"].isin(medio_sel)
]

if estado_sel == "Activos":
    df_filtrado = df_filtrado[df_filtrado["status"] == 1]
elif estado_sel == "Inactivos":
    df_filtrado = df_filtrado[df_filtrado["status"] == 0]

# ---------- TABLA RESULTANTE ----------
st.markdown(f"### Resultados ({len(df_filtrado)} registros)")
st.dataframe(df_filtrado.sort_values(by="fecha", ascending=False).reset_index(drop=True), use_container_width=True)

# ---------- RESÚMENES ----------
if not df_filtrado.empty:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💰 Totales por tipo")
        total_por_tipo = df_filtrado.groupby("tipo")["monto"].sum().sort_values(ascending=False)
        st.table(total_por_tipo.apply(lambda x: f"{x:.2f} soles"))

    with col2:
        st.subheader("📊 Totales por categoría")
        total_por_categoria = df_filtrado.groupby("categoria")["monto"].sum().sort_values(ascending=False)
        st.table(total_por_categoria.apply(lambda x: f"{x:.2f} soles"))

# ---------- DESCARGA ----------
st.markdown("### 📥 Descargar datos filtrados")
st.download_button(
    label="📄 Descargar CSV",
    data=df_filtrado.to_csv(index=False).encode("utf-8"),
    file_name="transacciones_filtradas.csv",
    mime="text/csv"
)