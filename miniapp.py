
import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# Configuración base de la app
# -----------------------------
st.set_page_config(page_title="Dashboard de Ventas", layout="wide")

# -----------------------------
# Funciones auxiliares
# -----------------------------
@st.cache_data
def load_data(file):
    """
    Carga el archivo subido por el usuario:
    - Si es .xlsx lo lee con openpyxl.
    - Si es .csv lo lee con pandas.
    Devuelve un DataFrame.
    NOTA: No se crean archivos; todo es en memoria.
    """
    if file.name.lower().endswith(".xlsx"):
        return pd.read_excel(file, engine="openpyxl")
    # Por defecto intentamos como CSV con utf-8
    return pd.read_csv(file, encoding="utf-8")

def normalize_columns(df):
    """
    Normaliza nombres de columnas a las esperadas por el dashboard.
    Si el archivo viene con mayúsculas/minúsculas distintas o espacios,
    este mapeo las alinea a:
    REGION, ID, NOMBRE, APELLIDO, SALARIO,
    UNIDADES VENDIDAS, VENTAS TOTALES, PORCENTAJE DE VENTAS
    """
    mapping = {
        "region": "REGION",
        "id": "ID",
        "nombre": "NOMBRE",
        "apellido": "APELLIDO",
        "salario": "SALARIO",
        "unidades vendidas": "UNIDADES VENDIDAS",
        "ventas totales": "VENTAS TOTALES",
        "porcentaje de ventas": "PORCENTAJE DE VENTAS",
    }
    # Diccionario case-insensitive de las columnas actuales
    current = {c.strip().lower(): c for c in df.columns}
    renamed = {}
    for k, v in mapping.items():
        if k in current:
            renamed[current[k]] = v
    return df.rename(columns=renamed)

def fmt_money(x):
    """Formatea números como dinero sin decimales para KPIs."""
    try:
        return f"${x:,.0f}".replace(",", " ")
    except Exception:
        return x

# -----------------------------
# Barra lateral (inputs)
# -----------------------------
with st.sidebar:
    st.header("Configuración")
    # Uploader: el usuario sube xlsx o csv (no se crean archivos locales)
    file = st.file_uploader("Subir archivo (.xlsx o .csv)", type=["xlsx", "csv"])
    # Mostrar/ocultar tabla
    show_table = st.checkbox("Mostrar tabla", value=True)

# Si no hay archivo, detenemos la app y damos instrucciones
if not file:
    st.info(
        "Sube un archivo para comenzar (.xlsx o .csv) con columnas:\n"
        "REGION, NOMBRE, APELLIDO, UNIDADES VENDIDAS, VENTAS TOTALES, PORCENTAJE DE VENTAS "
        "(opcional: SALARIO)."
    )
    st.stop()

# -----------------------------
# Carga y validación de datos
# -----------------------------
df = load_data(file)
df = normalize_columns(df)

# Validamos columnas mínimas
required_cols = ["REGION", "NOMBRE", "APELLIDO", "UNIDADES VENDIDAS", "VENTAS TOTALES", "PORCENTAJE DE VENTAS"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"Faltan columnas requeridas: {missing}")
    st.stop()

# Coerción a numérico de métricas relevantes (si vienen como texto)
for col in ["UNIDADES VENDIDAS", "VENTAS TOTALES", "PORCENTAJE DE VENTAS", "SALARIO"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Creamos campo VENDEDOR (Nombre + Apellido) para facilitar filtros y gráficas
df["VENDEDOR"] = df["NOMBRE"].astype(str).str.strip() + " " + df["APELLIDO"].astype(str).str.strip()

# -----------------------------
# Encabezado
# -----------------------------
st.title("Dashboard de Ventas")

# -----------------------------
# Filtros (contenedor)
# -----------------------------
with st.container():
    st.subheader("Filtros")
    colf1, colf2, colf3, colf4 = st.columns([2, 2, 1, 1])

    # Filtro por Región (multiselección)
    with colf1:
        regiones = sorted(df["REGION"].dropna().unique().tolist())
        regiones_sel = st.multiselect("Región", options=regiones, default=regiones)

    # Filtro por Vendedor (select único, depende de Región)
    with colf2:
        vendedores_disp = df.loc[df["REGION"].isin(regiones_sel), "VENDEDOR"].sort_values().unique().tolist()
        vendedor_sel = st.selectbox("Vendedor", options=["(Todos)"] + vendedores_disp, index=0)

    # Control para Top N en los rankings
    with colf3:
        top_n = st.slider("Top N", min_value=3, max_value=20, value=10)

    # Botón para limpiar filtros (reinicia el estado)
    with colf4:
        if st.button("Limpiar filtros"):
            st.session_state.clear()
            st.rerun()

# Aplicamos filtros al DataFrame
df_f = df[df["REGION"].isin(regiones_sel)].copy()
if vendedor_sel != "(Todos)":
    df_f = df_f[df_f["VENDEDOR"] == vendedor_sel]

# Si tras filtros no hay datos, detenemos
if df_f.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

# -----------------------------
# KPIs principales (contenedor)
# -----------------------------
with st.container():
    st.subheader("Indicadores")
    k1, k2, k3, k4 = st.columns(4)

    total_unidades = int(df_f["UNIDADES VENDIDAS"].sum())
    total_ventas = float(df_f["VENTAS TOTALES"].sum())
    prom_pct = float(df_f["PORCENTAJE DE VENTAS"].mean())
    ticket_prom = (total_ventas / total_unidades) if total_unidades else 0.0

    k1.metric("Unidades Totales", f"{total_unidades:,}".replace(",", " "))
    k2.metric("Ventas Totales", fmt_money(total_ventas))
    k3.metric("% Ventas Promedio", f"{prom_pct:.2f}%")
    k4.metric("Ticket Promedio", fmt_money(ticket_prom))

# -----------------------------
# Gráficas principales (contenedor)
# -----------------------------
with st.container():
    st.subheader("Gráficas principales (Top N)")

    # Ordenamos por Ventas Totales y tomamos Top N
    ranked = df_f.sort_values("VENTAS TOTALES", ascending=False).head(top_n)

    c1, c2, c3 = st.columns(3)

    # Gráfica 1: Ventas Totales por Vendedor (Top N)
    with c1:
        fig_s = px.bar(
            ranked, x="VENDEDOR", y="VENTAS TOTALES", color="REGION",
            labels={"VENDEDOR": "Vendedor", "VENTAS TOTALES": "Ventas", "REGION": "Región"},
            title="Top N por Ventas Totales"
        )
        fig_s.update_layout(xaxis_title="", yaxis_title="Ventas totales")
        st.plotly_chart(fig_s, use_container_width=True)

    # Gráfica 2: Unidades Vendidas por Vendedor (Top N)
    with c2:
        fig_u = px.bar(
            ranked, x="VENDEDOR", y="UNIDADES VENDIDAS", color="REGION",
            labels={"VENDEDOR": "Vendedor", "UNIDADES VENDIDAS": "Unidades", "REGION": "Región"},
            title="Top N por Unidades Vendidas"
        )
        fig_u.update_layout(xaxis_title="", yaxis_title="Unidades vendidas")
        st.plotly_chart(fig_u, use_container_width=True)

    # Gráfica 3: % de Ventas por Vendedor (Top N)
    with c3:
        fig_p = px.bar(
            ranked, x="VENDEDOR", y="PORCENTAJE DE VENTAS", color="REGION",
            labels={"VENDEDOR": "Vendedor", "PORCENTAJE DE VENTAS": "% Ventas", "REGION": "Región"},
            title="Top N por % de Ventas"
        )
        fig_p.update_layout(xaxis_title="", yaxis_title="% de Ventas")
        st.plotly_chart(fig_p, use_container_width=True)

# -----------------------------
# Contribución por Región y Vendedor (barras apiladas 100%)
# -----------------------------
with st.container():
    st.subheader("Contribución por Región y Vendedor")

    # Elegimos la métrica a usar y cuántos Top K por región conservar
    metrica = st.selectbox("Métrica", ["VENTAS TOTALES", "UNIDADES VENDIDAS"], index=0)
    top_k = st.slider("Top K por región", min_value=3, max_value=10, value=5)

    def topk_mas_otros(df_in, k, value_col):
        """
        Agrega por REGIÓN y VENDEDOR, conserva Top-K por región y agrupa el resto como 'Otros'.
        Calcula además el porcentaje de contribución dentro de cada región.
        """
        base = (df_in.groupby(["REGION", "VENDEDOR"], as_index=False)[value_col]
                  .sum()
                  .rename(columns={value_col: "VALOR"}))
        # Rank por región
        base["RANK"] = base.groupby("REGION")["VALOR"].rank(method="first", ascending=False)
        top = base[base["RANK"] <= k].copy()
        # Suma de los que no entran en Top-K
        otros = (base[base["RANK"] > k].groupby("REGION", as_index=False)["VALOR"].sum())
        if not otros.empty:
            otros["VENDEDOR"] = "Otros"
            top = pd.concat([top[["REGION", "VENDEDOR", "VALOR"]], otros], ignore_index=True)
        # Porcentaje dentro de la región
        totales = top.groupby("REGION", as_index=False)["VALOR"].sum().rename(columns={"VALOR": "TOTAL_REGION"})
        top = top.merge(totales, on="REGION", how="left")
        top["PCT_REGION"] = (top["VALOR"] / top["TOTAL_REGION"]) * 100
        return top

    datos = topk_mas_otros(df_f, top_k, metrica)
    datos = datos.sort_values(["REGION", "VALOR"], ascending=[True, False])

    fig_stack = px.bar(
        datos, x="REGION", y="PCT_REGION", color="VENDEDOR",
        text=datos["PCT_REGION"].map(lambda v: f"{v:.1f}%"),
        labels={"REGION": "Región", "PCT_REGION": "Participación (%)", "VENDEDOR": "Vendedor"},
        title="Participación relativa por región (Top K + Otros)"
    )
    fig_stack.update_layout(barmode="stack", yaxis_title="% dentro de la región")
    fig_stack.update_traces(
        textposition="inside",
        hovertemplate="Región: %{x}<br>Vendedor: %{legendgroup}<br>%: %{y:.1f}%<extra></extra>"
    )
    st.plotly_chart(fig_stack, use_container_width=True)

# -----------------------------
# Detalle por Vendedor (contenedor)
# -----------------------------
with st.container():
    st.subheader("Detalle por Vendedor")
    # Si hay un vendedor seleccionado distinto de "(Todos)", mostramos su detalle
    if vendedor_sel != "(Todos)":
        d = df[df["VENDEDOR"] == vendedor_sel].copy()

        # KPIs del vendedor seleccionado
        ck1, ck2, ck3 = st.columns(3)
        ck1.metric("Unidades (vendedor)", f"{int(d['UNIDADES VENDIDAS'].sum()):,}".replace(",", " "))
        ck2.metric("Ventas (vendedor)", fmt_money(d["VENTAS TOTALES"].sum()))
        ck3.metric("% Ventas Prom (vendedor)", f"{float(d['PORCENTAJE DE VENTAS'].mean()):.2f}%")

        # Gráficas por región para ese vendedor
        g1, g2 = st.columns(2)
        with g1:
            fig_vu = px.bar(d, x="REGION", y="UNIDADES VENDIDAS", title="Unidades por Región (vendedor)")
            st.plotly_chart(fig_vu, use_container_width=True)
        with g2:
            fig_vs = px.bar(d, x="REGION", y="VENTAS TOTALES", title="Ventas por Región (vendedor)")
            st.plotly_chart(fig_vs, use_container_width=True)
    else:
        st.info("Selecciona un vendedor en los filtros para ver su detalle.")

# -----------------------------
# Tabla (contenedor)
# -----------------------------
with st.container():
    st.subheader("Tabla de datos filtrada")
    if show_table:
        st.dataframe(df_f, use_container_width=True)
