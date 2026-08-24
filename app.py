import streamlit as st
import pandas as pd
import datetime

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Dashboard Gerencial AAC", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .kpi-container {
        background-color: #f8f9fa;
        border-left: 5px solid #002b5e;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .kpi-label { color: #475569; font-size: 0.95rem; font-weight: 600; margin-bottom: 0.2rem; }
    .kpi-value { color: #0f172a; font-size: 1.8rem; font-weight: 700; margin: 0; }
    </style>
""", unsafe_allow_html=True)

MESES = {1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril', 5: 'mayo', 6: 'junio', 
         7: 'julio', 8: 'agosto', 9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'}

# 2. CARGA Y PROCESAMIENTO
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv('base_aac.csv', sep=None, engine='python')
    except Exception:
        df = pd.read_csv('base_aac.csv', sep=';')
    
    # Limpiar espacios en blanco en los nombres de las columnas
    df.columns = df.columns.str.strip()
    
    if 'Costo neto' not in df.columns:
        st.error(f"⚠️ No se encontró la columna 'Costo neto'. Columnas detectadas: {list(df.columns)}")
        st.stop()
    
    # Función robusta para limpiar valores numéricos (Costo neto y Unds)
    def limpiar_numero(val):
        if pd.isna(val):
            return 0.0
        val_s = str(val).strip().replace('$', '').replace('€', '').replace(' ', '')
        if val_s == '' or val_s.lower() == 'nan':
            return 0.0
        
        # Manejo de formatos con puntos y comas
        if '.' in val_s and ',' in val_s:
            if val_s.rfind('.') > val_s.rfind(','):
                val_s = val_s.replace(',', '')
            else:
                val_s = val_s.replace('.', '').replace(',', '.')
        elif ',' in val_s:
            val_s = val_s.replace(',', '.')
        elif '.' in val_s:
            if val_s.count('.') > 1:
                val_s = val_s.replace('.', '')
        
        try:
            return float(val_s)
        except ValueError:
            return 0.0

    df['Costo neto'] = df['Costo neto'].apply(limpiar_numero)
    df['Unds'] = df['Unds'].apply(limpiar_numero)
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    
    return df.dropna(subset=['Fecha'])

df = cargar_datos()

# 3. BARRA LATERAL - FILTROS INTERACTIVOS
st.sidebar.title("Filtros de Análisis")
st.sidebar.markdown("---")

fecha_min = df['Fecha'].min().date()
fecha_max = df['Fecha'].max().date()

st.sidebar.subheader("📅 Selección de Periodo / Fecha")
rango_fechas = st.sidebar.date_input(
    "Selecciona día o rango:",
    value=(fecha_max, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max
)

if isinstance(rango_fechas, tuple):
    if len(rango_fechas) == 2:
        fecha_inicio, fecha_fin = rango_fechas
    else:
        fecha_inicio = fecha_fin = rango_fechas[0]
else:
    fecha_inicio = fecha_fin = rango_fechas

es_dia_unico = (fecha_inicio == fecha_fin)

if es_dia_unico:
    mes_str = MESES[fecha_inicio.month]
    col_nombre_periodo = f"Costo {fecha_inicio.day} de {mes_str[:3]}."
    col_nombre_comparativa = f"Costo total {mes_str}"
else:
    col_nombre_periodo = f"Costo Periodo"
    col_nombre_comparativa = f"Costo total año {fecha_fin.year}"

df_año_base = df[df['Fecha'].dt.year == fecha_fin.year].copy()

st.sidebar.subheader("📍 Segmentación Geográfica")
dptos_disp = sorted(df_año_base['Dpto.'].dropna().unique().tolist())
sel_dptos = st.sidebar.multiselect("Departamento (Dpto.)", dptos_disp, default=dptos_disp)

df_filtro = df_año_base[df_año_base['Dpto.'].isin(sel_dptos)] if sel_dptos else df_año_base

bodegas_disp = sorted(df_filtro['Bodega'].dropna().astype(str).unique().tolist())
sel_bodegas = st.sidebar.multiselect("Bodega", bodegas_disp, default=bodegas_disp)

df_filtro = df_filtro[df_filtro['Bodega'].astype(str).isin(sel_bodegas)] if sel_bodegas else df_filtro

# 4. CÁLCULO DE MÉTRICAS PARA LAS 3 TARJETAS
mask_periodo = (df_filtro['Fecha'].dt.date >= fecha_inicio) & (df_filtro['Fecha'].dt.date <= fecha_fin)
df_periodo = df_filtro[mask_periodo]

total_unds_periodo = df_periodo['Unds'].sum()
total_costo_periodo = df_periodo['Costo neto'].sum()

if es_dia_unico:
    df_base_comparativa = df_filtro[(df_filtro['Fecha'].dt.year == fecha_inicio.year) & 
                                    (df_filtro['Fecha'].dt.month == fecha_inicio.month)]
    label_tarjeta_3 = f"Costo Total Mes ({mes_str.capitalize()})"
else:
    df_base_comparativa = df_filtro
    label_tarjeta_3 = f"Costo Total Año ({fecha_fin.year})"

total_costo_comparativa = df_base_comparativa['Costo neto'].sum()

# Interfaz Principal
st.title("Control de Ajustes por Acumulación (AAC)")
if es_dia_unico:
    st.markdown(f"**Análisis focalizado para el día:** {fecha_inicio.strftime('%d/%m/%Y')}")
else:
    st.markdown(f"**Análisis por rango del:** {fecha_inicio.strftime('%d/%m/%Y')} **al** {fecha_fin.strftime('%d/%m/%Y')}")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-label">📦 Unds. Ajustadas</div>
            <div class="kpi-value">{total_unds_periodo:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
        <div class="kpi-container" style="border-left-color: #059669;">
            <div class="kpi-label">💵 Costo Selección</div>
            <div class="kpi-value">${total_costo_periodo:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
        <div class="kpi-container" style="border-left-color: #d97706;">
            <div class="kpi-label">📊 {label_tarjeta_3}</div>
            <div class="kpi-value">${total_costo_comparativa:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)

st.write("")

# 5. CONSTRUCCIÓN DE LA TABLA DINÁMICA
st.subheader("📑 Resumen de Costos por Bodega")

df_grp_periodo = df_periodo.groupby(['Dpto.', 'Bodega'])['Costo neto'].sum().reset_index(name='Costo_Periodo')
df_grp_comparativa = df_base_comparativa.groupby(['Dpto.', 'Bodega'])['Costo neto'].sum().reset_index(name='Costo_Comparativa')

df_resumen = pd.merge(df_grp_comparativa, df_grp_periodo, on=['Dpto.', 'Bodega'], how='left').fillna(0)

filas_tabla = []
for dpto in sorted(df_resumen['Dpto.'].unique()):
    df_dpto = df_resumen[df_resumen['Dpto.'] == dpto].sort_values('Bodega')
    
    for _, row in df_dpto.iterrows():
        filas_tabla.append({
            'Dpto.': str(dpto),
            'Bodega': str(row['Bodega']),
            col_nombre_periodo: row['Costo_Periodo'],
            col_nombre_comparativa: row['Costo_Comparativa']
        })
    
    filas_tabla.append({
        'Dpto.': f"Total {dpto}",
        'Bodega': "",
        col_nombre_periodo: df_dpto['Costo_Periodo'].sum(),
        col_nombre_comparativa: df_dpto['Costo_Comparativa'].sum()
    })

if not df_resumen.empty:
    filas_tabla.append({
        'Dpto.': "Total general",
        'Bodega': "",
        col_nombre_periodo: df_resumen['Costo_Periodo'].sum(),
        col_nombre_comparativa: df_resumen['Costo_Comparativa'].sum()
    })

if filas_tabla:
    df_final = pd.DataFrame(filas_tabla)
    df_final['Bodega'] = df_final['Bodega'].astype(str)
    
    def resaltar_totales(row):
        if "Total" in str(row['Dpto.']):
            return ['background-color: #cbd5e1; font-weight: bold; color: #0f172a'] * len(row)
        return [''] * len(row)
    
    df_estilizado = df_final.style.apply(resaltar_totales, axis=1).format({
        col_nombre_periodo: lambda x: f"${x:,.0f}".replace(",", "."),
        col_nombre_comparativa: lambda x: f"${x:,.0f}".replace(",", ".")
    })
    
    altura_dinamica = (len(df_final) + 1) * 35 + 30
    
    st.dataframe(
        df_estilizado,
        hide_index=True,
        width='stretch',
        height=altura_dinamica
    )
else:
    st.info("No hay registros disponibles para los filtros seleccionados.")
