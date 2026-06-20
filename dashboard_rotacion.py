import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Rotación de Productos", layout="wide")

# =========================
# ESTILO VISUAL BAKARIA
# =========================
st.markdown("""
<style>

[data-testid="stAppViewContainer"] {
    background-color: #F5F5F5;
}

[data-testid="stSidebar"] {
    background-color: #F5F5F5;
    border-right: 1px solid #E5E5E5;
}

.block-container {
    padding-top: 1rem;
}

h1, h2, h3 {
    color: #7A1E2C;
    font-weight: 700;
}

.card {
    background-color: #FFFFFF;
    padding: 20px;
    border-radius: 12px;
    border-left: 6px solid #D4A017;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.08);
    text-align: center;
}

.card-title {
    color: #666666;
    font-size: 14px;
}

.card-value {
    color: #7A1E2C;
    font-size: 32px;
    font-weight: bold;
}

.card-small {
    color: #333333;
    font-size: 15px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# CONFIGURACIÓN
# =========================
SEDES = {
    "FEVD": "Venta Digital",
    "FEFL": "Florida",
    "FEAS": "Alta Suiza",
    "FEMP": "Mall Plaza",
    "FEPL": "Palermo",
    "FEFS": "Fundadores 2",
    "FEFD": "Fundadores 1"
}

st.title(" Rotación de Productos ")
st.caption("Análisis de unidades vendidas por producto, sede, mes y lista de precios.")

archivo = st.sidebar.file_uploader(
    "Sube el archivo Excel de Alegra",
    type=["xlsx"]
)

if archivo is None:
    st.info("Sube el archivo Excel para iniciar el análisis.")
    st.stop()

# =========================
# LECTURA DEL ARCHIVO
# =========================
df = pd.read_excel(archivo)

df = df.iloc[:, 0:6]

df.columns = [
    "FECHA",
    "CODIGO",
    "CENTRO_COSTO",
    "LISTA_PRECIOS",
    "PRODUCTO",
    "CANTIDAD"
]

df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")
df["CODIGO"] = df["CODIGO"].astype(str).str.strip()
df["CENTRO_COSTO"] = df["CENTRO_COSTO"].astype(str).str.strip()
df["LISTA_PRECIOS"] = df["LISTA_PRECIOS"].astype(str).str.strip()
df["PRODUCTO"] = df["PRODUCTO"].astype(str).str.strip()
df["CANTIDAD"] = pd.to_numeric(df["CANTIDAD"], errors="coerce").fillna(0)

df["MES"] = df["FECHA"].dt.strftime("%B")
df["PREFIJO"] = df["CODIGO"].str[:4]
df["SEDE"] = df["PREFIJO"].map(SEDES).fillna("Otra / Sin identificar")

# =========================
# EXCLUIR NO PRODUCTOS
# =========================
palabras_excluir = [
    "DOMICILIO",
    "EMPAQUE",
    "BOLSA",
    "CAJA",
    "PROPINA",
    "RECARGO"
]

patron_excluir = "|".join(palabras_excluir)

df_base = df[
    ~df["PRODUCTO"].str.upper().str.contains(patron_excluir, na=False)
].copy()

# =========================
# FILTROS
# =========================
st.sidebar.header("Filtros")

meses = ["Todos"] + sorted(df_base["MES"].dropna().unique().tolist())
sedes = ["Todas"] + sorted(df_base["SEDE"].dropna().unique().tolist())
listas = ["Todas"] + sorted(df_base["LISTA_PRECIOS"].dropna().unique().tolist())

mes_sel = st.sidebar.selectbox("Mes", meses)
sede_sel = st.sidebar.selectbox("Sede", sedes)
lista_sel = st.sidebar.selectbox("Lista de precios", listas)
top_n = st.sidebar.slider("Cantidad de productos en el Top", 10, 50, 20)
buscar = st.sidebar.text_input("Buscar producto")

df_filtrado = df_base.copy()

if mes_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["MES"] == mes_sel]

if sede_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["SEDE"] == sede_sel]

if lista_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["LISTA_PRECIOS"] == lista_sel]

if buscar:
    df_filtrado = df_filtrado[
        df_filtrado["PRODUCTO"].str.upper().str.contains(buscar.upper(), na=False)
    ]

# =========================
# RESUMEN
# =========================
rotacion_producto = (
    df_filtrado
    .groupby("PRODUCTO", as_index=False)["CANTIDAD"]
    .sum()
    .sort_values("CANTIDAD", ascending=True)
)

total_productos = df_filtrado["PRODUCTO"].nunique()
total_unidades = int(df_filtrado["CANTIDAD"].sum())
total_facturas = df_filtrado["CODIGO"].nunique()
total_sedes = df_filtrado["SEDE"].nunique()

if not rotacion_producto.empty:
    producto_menor = rotacion_producto.iloc[0]["PRODUCTO"]
else:
    producto_menor = "Sin datos"

# =========================
# TARJETAS
# =========================
col1, col2, col3, col4 = st.columns(4)

col1.markdown(f"""
<div class="card">
    <div class="card-title">Productos analizados</div>
    <div class="card-value">{total_productos}</div>
</div>
""", unsafe_allow_html=True)

col2.markdown(f"""
<div class="card">
    <div class="card-title">Unidades vendidas</div>
    <div class="card-value">{total_unidades:,}</div>
</div>
""", unsafe_allow_html=True)

col3.markdown(f"""
<div class="card">
    <div class="card-title">Facturas</div>
    <div class="card-value">{total_facturas:,}</div>
</div>
""", unsafe_allow_html=True)

col4.markdown(f"""
<div class="card">
    <div class="card-title">Sedes con ventas</div>
    <div class="card-value">{total_sedes}</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown(f"""
<div class="card">
    <div class="card-title">Producto con menor rotación según filtros actuales</div>
    <div class="card-small"><b>{producto_menor}</b></div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =========================
# GRÁFICAS
# =========================
top_menor = rotacion_producto.head(top_n)

col_g1, col_g2 = st.columns([2, 1])

with col_g1:
    st.subheader("Productos con menor rotación")

    if top_menor.empty:
        st.warning("No hay datos con los filtros seleccionados.")
    else:
        fig_menor = px.bar(
            top_menor.sort_values("CANTIDAD", ascending=True),
            x="CANTIDAD",
            y="PRODUCTO",
            orientation="h",
            text="CANTIDAD",
            title=f"Top {top_n} menor rotación"
        )

        fig_menor.update_traces(
            marker_color="#7A1E2C",
            textposition="outside"
        )

        fig_menor.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            title_font=dict(size=20, color="#7A1E2C"),
            font=dict(size=12, color="#333333"),
            xaxis_title="Unidades vendidas",
            yaxis_title="",
            height=650,
            margin=dict(l=20, r=80, t=60, b=30)
        )

        fig_menor.update_xaxes(
            showgrid=True,
            gridcolor="#E5E5E5",
            zeroline=False
        )

        fig_menor.update_yaxes(showgrid=False)

        st.plotly_chart(
            fig_menor,
            use_container_width=True,
            key="grafico_menor"
        )

with col_g2:
    st.subheader("Participación por sede")

    sede_resumen = (
        df_filtrado
        .groupby("SEDE", as_index=False)["CANTIDAD"]
        .sum()
        .sort_values("CANTIDAD", ascending=False)
    )

    if sede_resumen.empty:
        st.warning("No hay datos.")
    else:
        fig_sede = px.pie(
            sede_resumen,
            names="SEDE",
            values="CANTIDAD",
            hole=0.45,
            title="Unidades vendidas por sede",
            color_discrete_sequence=[
                "#7A1E2C",
                "#8D2B3A",
                "#A63A49",
                "#D4A017",
                "#E3BF4B",
                "#C9A96A",
                "#F0E4C2"
            ]
        )

        fig_sede.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            title_font=dict(size=18, color="#7A1E2C"),
            font=dict(size=12, color="#333333"),
            height=650
        )

        st.plotly_chart(
            fig_sede,
            use_container_width=True,
            key="grafico_sede"
        )

# =========================
# PESTAÑAS
# =========================
tab1, tab2, tab3, tab4 = st.tabs([
    "📍 Rotación por sede",
    "📅 Rotación por mes",
    "🏷️ Lista de precios",
    "📋 Detalle"
])

with tab1:
    tabla_sede = pd.pivot_table(
        df_filtrado,
        values="CANTIDAD",
        index="PRODUCTO",
        columns="SEDE",
        aggfunc="sum",
        fill_value=0
    )

    tabla_sede["TOTAL"] = tabla_sede.sum(axis=1)
    tabla_sede = tabla_sede.sort_values("TOTAL", ascending=True)

    st.dataframe(tabla_sede, use_container_width=True)

with tab2:
    tabla_mes = pd.pivot_table(
        df_filtrado,
        values="CANTIDAD",
        index="PRODUCTO",
        columns="MES",
        aggfunc="sum",
        fill_value=0
    )

    tabla_mes["TOTAL"] = tabla_mes.sum(axis=1)
    tabla_mes = tabla_mes.sort_values("TOTAL", ascending=True)

    st.dataframe(tabla_mes, use_container_width=True)

with tab3:
    tabla_lista = pd.pivot_table(
        df_filtrado,
        values="CANTIDAD",
        index="PRODUCTO",
        columns="LISTA_PRECIOS",
        aggfunc="sum",
        fill_value=0
    )

    tabla_lista["TOTAL"] = tabla_lista.sum(axis=1)
    tabla_lista = tabla_lista.sort_values("TOTAL", ascending=True)

    st.dataframe(tabla_lista, use_container_width=True)

with tab4:
    st.dataframe(df_filtrado, use_container_width=True)

# =========================
# DESCARGA
# =========================
st.markdown("---")

csv = rotacion_producto.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    label=" Descargar productos ordenados por menor rotación",
    data=csv,
    file_name="productos_menor_rotacion.csv",
    mime="text/csv"
)