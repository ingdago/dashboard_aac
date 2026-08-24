import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA (UI/UX)
st.set_page_config(page_title="Dashboard Gerencial AAC", page_icon="📊", layout="wide")

# Estilo corporativo personalizado para los KPIs
st.markdown("""
    <style>
    .kpi-container {
        background-color: #f8f9fa;
        border-left: 5px solid #002b5e;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .kpi-label { color: #475569; font-size: 1rem; font-weight: 500; margin-bottom: 0.2rem; }
    .kpi-value { color: #0f172a; font-size: 2rem; font-weight: 700; margin: 0; }
    </style>
""", unsafe_allow_html=True)

# 2. CARGA Y PROCESAMIENTO DE DATOS
@st.cache_data
def cargar_datos():
    # Lectura del archivo local en el repositorio
    df = pd.read_csv('base_aac.csv', sep=None, engine='python', encoding='utf-8-sig')
    
    # Normalización de la columna Costo Neto (Manejo de formato $ 1.292,00)
    if df['Costo neto'].dtype == 'O':
        df['Costo neto'] = df['Costo neto'].str.replace('$', '', regex=False)
        df['Costo neto'] = df['Costo neto'].str.replace('.', '', regex=False)
        df['Costo neto'] = df['Costo neto'].str.replace(',', '.', regex=False)
    
    df['Costo neto'] = pd.to_numeric(df['Costo neto'], errors='coerce').fillna(0)
    df['Unds'] = pd.to_numeric(df['Unds'], errors='coerce').fillna(0)
    
    # Procesamiento temporal
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    df['Año'] = df['Fecha'].dt.year
    df['Mes'] = df['Fecha'].dt.month
    
    return df.dropna(subset=['Fecha'])

df = cargar_datos()

# 3. BARRA LATERAL - FILTROS REACTIVOS
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2936/2936690.png", width=80)
st.sidebar.title("Filtros de Análisis")
st.sidebar.markdown("---")

# Filtro 1: Año
años_disp = sorted(df['Año'].unique().tolist())
sel_años = st.sidebar.multiselect("📅 Año", años_disp, default=años_disp)
df_filtro = df[df['Año'].isin(sel_años)] if sel_años else df

# Filtro 2: Mes (Dependiente del Año)
meses_disp = sorted(df_filtro['Mes'].unique().tolist())
sel_meses = st.sidebar.multiselect("📆 Mes", meses_disp, default=meses_disp)
df_filtro = df_filtro[df_filtro['Mes'].isin(sel_meses)] if sel_meses else df_filtro

# Filtro 3: Departamento (Dependiente del Mes)
dptos_disp = sorted(df_filtro['Dpto.'].dropna().unique().tolist())
sel_dptos = st.sidebar.multiselect("📍 Departamento (Dpto.)", dptos_disp, default=dptos_disp)
df_filtro = df_filtro[df_filtro['Dpto.'].isin(sel_dptos)] if sel_dptos else df_filtro

# Filtro 4: Bodega (Dependiente del Dpto.)
bodegas_disp = sorted(df_filtro['Bodega'].dropna().astype(str).unique().tolist())
sel_bodegas = st.sidebar.multiselect("🏭 Bodega", bodegas_disp, default=bodegas_disp)
df_filtro = df_filtro[df_filtro['Bodega'].astype(str).isin(sel_bodegas)] if sel_bodegas else df_filtro

# 4. INTERFAZ PRINCIPAL Y KPIs
st.title("Sistema de Control: Ajustes por Acumulación (AAC)")
st.markdown("Monitorización en tiempo real del impacto en unidades y costo neto.")
st.markdown("---")

# Recálculo de métricas
total_unds = df_filtro['Unds'].sum()
total_costo = df_filtro['Costo neto'].sum()

# Renderizado de Tarjetas HTML
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-label">📦 Total Unidades Ajustadas</div>
            <div class="kpi-value">{total_unds:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
        <div class="kpi-container" style="border-left-color: #059669;">
            <div class="kpi-label">💵 Costo Neto Total</div>
            <div class="kpi-value">${total_costo:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)

st.write("") # Espaciador

# 5. GRÁFICO DE TENDENCIA TEMPORAL (Plotly)
st.subheader("📈 Tendencia Temporal del Costo por Ajustes")

# Agrupar datos para la gráfica
if not df_filtro.empty:
    df_tendencia = df_filtro.groupby('Fecha', as_index=False)['Costo neto'].sum()
    df_tendencia = df_tendencia.sort_values('Fecha')
    
    fig = px.line(
        df_tendencia, 
        x='Fecha', 
        y='Costo neto',
        markers=True,
        line_shape='spline',
        color_discrete_sequence=['#002b5e']
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis_title="Fecha de Transacción",
        yaxis_title="Costo Neto Total ($)",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20)
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor='#e2e8f0')
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No hay datos disponibles para los filtros seleccionados.")