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
campos = ["tipo", "monto", "categoria", "fecha", "medio", "mes", "año", "status"]
for campo in campos:
    if campo not in df_transacciones.columns:
        df_transacciones[campo] = None

if not df_transacciones.empty:
    df_transacciones["monto"] = (pd.to_numeric(df_transacciones.get("monto", 0).astype(str).str.replace(",", ""), errors="coerce"))
    df_transacciones["fecha"] = df_transacciones.get("fecha", "")
    df_transacciones["categoria"] = df_transacciones.get("categoria", "").fillna("Sin categoría")
    df_transacciones["tipo"] = df_transacciones.get("tipo", "").fillna("Sin tipo")
    df_transacciones["medio"] = df_transacciones.get("medio", "").fillna("Sin medio")
    df_transacciones["status"] = df_transacciones.get("status", 1).fillna(1).astype(int)
    df_transacciones["mes"] = df_transacciones.get("mes", "").fillna("desconocido").str.lower()
    df_transacciones["año"] = pd.to_numeric(df_transacciones.get("año", datetime.now().year), errors="coerce").fillna(datetime.now().year).astype(int)

# ---------- ALERTAS ----------
alertas = cargar_datos_json(RUTA_ALERTAS)
df_alertas = pd.DataFrame(alertas)

if not df_alertas.empty:
    df_alertas["tipo"] = "alerta"
    df_alertas["monto"] = pd.to_numeric(df_alertas.get("monto", 0), errors="coerce")
    df_alertas["categoria"] = df_alertas.get("categoria", "").fillna("Sin categoría")
    df_alertas["periodo"] = df_alertas.get("periodo", "").fillna("")

    # Extraer mes y año del campo periodo si no vienen por separado
    def extraer_mes_y_anio(periodo):
        try:
            partes = periodo.lower().strip().split(" de ")
            if len(partes) == 2:
                return partes[0], int(partes[1])
        except:
            pass
        return "desconocido", datetime.now().year

    df_alertas[["mes", "año"]] = df_alertas["periodo"].apply(
        lambda p: pd.Series(extraer_mes_y_anio(p))
    )

    df_alertas["status"] = df_alertas.get("status", 1).fillna(1).astype(int)
    df_alertas["medio"] = "N/A"
    df_alertas["fecha"] = None
    df_alertas["timestamp"] = pd.to_datetime(df_alertas.get("timestamp", datetime.now().isoformat()), errors="coerce")
else:
    df_alertas = pd.DataFrame(columns=df_transacciones.columns)

# ---------- UNIÓN Y FILTRADO ----------
df = pd.concat([df_transacciones, df_alertas], ignore_index=True)

df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

if df.empty:
    st.warning("⚠️ No se encontraron datos en transacciones.json ni alertas.json.")
    st.stop()

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
st.dataframe(df_filtrado.sort_values(by="timestamp", ascending=False).reset_index(drop=True), use_container_width=True)

# ---------- RESÚMENES ----------
if not df_filtrado.empty:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💰 Totales por tipo")
        total_por_tipo = df_filtrado.groupby("tipo")["monto"].sum().sort_values(ascending=False)
        st.table(total_por_tipo.apply(lambda x: f"{x:.2f} soles"))

    with col2:
        st.subheader("📊 Totales por categoría")

        # Agrupar por tipo + categoría
        agrupado = df_filtrado.groupby(["tipo", "categoria"])["monto"].sum().reset_index()

        # Aplicar signo negativo si es gasto (solo visual)
        agrupado["monto"] = agrupado.apply(
            lambda row: -row["monto"] if row["tipo"] == "gasto" else row["monto"],
            axis=1
        ).round(2)

        # Ordenar por monto
        agrupado = agrupado.sort_values(by="monto", ascending=False)

        # Estilo condicional por tipo
        def estilo_condicional(row):
            tipo = row["tipo"]
            if tipo == "gasto":
                return ["color: red", "", ""]
            elif tipo == "ingreso":
                return ["color: green", "", ""]
            elif tipo == "alerta":
                return ["color: goldenrod", "", ""]
            else:
                return ["", "", ""]

        # Visualización estilizada
        st.dataframe(
            agrupado[["categoria", "monto", "tipo"]]
            .style
            .apply(estilo_condicional, axis=1)
            .format({"monto": lambda x: f"{x:,.2f} soles"})
        )
