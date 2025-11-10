# --- INICIO DEL GUARDIÁN DE SEGURIDAD ---
import streamlit as st

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("⚠️ Por favor, inicie sesión en la página 'Home' para acceder.")
    st.stop()
# --- FIN DEL GUARDIÁN DE SEGURIDAD ---

# ... (el resto de tu código de la página va aquí) ...
# (ej. import pandas as pd, import google_connector as gc, etc.)

# pages/4_Visualizacion_General.py
import streamlit as st
import pandas as pd
import google_connector as gc # Importamos nuestro conector
import plotly.express as px # Nueva librería para gráficos profesionales

# --- 1. Configuración de la Página y Título ---
st.set_page_config(layout="wide")
st.title("📈 4. Visualización General de Nómina")
st.markdown("Análisis gráfico interactivo de los costos de nómina y reportes.")

# --- 2. Verificar que los datos están cargados ---
if 'df_reporte_indi' not in st.session_state or 'df_reporte_mensual' not in st.session_state:
    st.error("Error: Faltan datos de reportes para visualizar.")
    st.info("Por favor, vaya a la página 'Home' y refresque los datos. Asegúrese de haber ejecutado un cálculo en la 'Página 3'.")
    st.stop()

# --- 3. Cargar y Preparar Datos ---
try:
    # Cargar datos del último cálculo
    df_reporte_raw = st.session_state.df_reporte_indi.copy()
    
    # Cargar historial
    df_historial_raw = st.session_state.df_reporte_mensual.copy()

    # --- Limpieza de Datos para Gráficos ---
    cols_moneda_reporte = ['Total devengado', 'Total Deducciones', 'Salario Neto pagado al empleado', 'Total pagado por la empresa']
    for col in cols_moneda_reporte:
        df_reporte_raw[col] = pd.to_numeric(df_reporte_raw[col], errors='coerce').fillna(0)
    
    cols_moneda_historial = ['Total devengado', 'Total Deducciones', 'Salario Neto pagado al empleado', 'Total pagado por la empresa']
    for col in cols_moneda_historial:
        df_historial_raw[col] = pd.to_numeric(df_historial_raw[col], errors='coerce').fillna(0)
        
    # --- ¡SOLUCIÓN AL ERROR DE CONTEO (7 vs 8)! ---
    # Rellenar campos de texto vacíos para que no sean ignorados por los filtros
    df_reporte_raw['Cargo'] = df_reporte_raw['Cargo'].fillna("Sin Asignar")
    df_reporte_raw['Empresa'] = df_reporte_raw['Empresa'].fillna("Sin Asignar")
    df_reporte_raw['Tipo de contrato'] = df_reporte_raw['Tipo de contrato'].fillna("Sin Asignar")
    df_reporte_raw['Nombre'] = df_reporte_raw['Nombre'].fillna("Sin Nombre")
    
except Exception as e:
    st.error(f"Error al procesar los datos para los gráficos: {e}")
    st.stop()
    
# Verificar que las columnas de filtro existan
if 'Cargo' not in df_reporte_raw.columns or 'Empresa' not in df_reporte_raw.columns:
    st.error("Error: Las columnas 'Cargo' o 'Empresa' no se encuentran en 'Reporte indi'.")
    st.info("Por favor, vaya a la Página 3 y vuelva a ejecutar el cálculo para que se añadan las columnas que faltan.")
    st.stop()

# --- 4. FILTROS AVANZADOS EN BARRA LATERAL ---
st.sidebar.header("Filtros de Visualización")

# --- Filtros Categóricos ---
lista_nombres = ['Todos'] + sorted(df_reporte_raw['Nombre'].unique().tolist())
lista_cargos = ['Todos'] + sorted(df_reporte_raw['Cargo'].unique().tolist())
lista_empresas = ['Todos'] + sorted(df_reporte_raw['Empresa'].unique().tolist())
lista_contratos = ['Todos'] + sorted(df_reporte_raw['Tipo de contrato'].unique().tolist())

filtro_nombre = st.sidebar.selectbox("Filtrar por Nombre", options=lista_nombres)
filtro_empresa = st.sidebar.selectbox("Filtrar por Empresa", options=lista_empresas)
filtro_cargo = st.sidebar.selectbox("Filtrar por Cargo", options=lista_cargos)
filtro_contrato = st.sidebar.selectbox("Filtrar por Tipo de contrato", options=lista_contratos)

# Aplicar filtros categóricos
df_filtrado = df_reporte_raw.copy()
if filtro_nombre != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['Nombre'] == filtro_nombre]
if filtro_empresa != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['Empresa'] == filtro_empresa]
if filtro_cargo != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['Cargo'] == filtro_cargo]
if filtro_contrato != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['Tipo de contrato'] == filtro_contrato]

# --- ¡FILTRO DE RANGO (SLIDER) ELIMINADO! ---


# --- 5. KPIs (Indicadores Clave) (MODIFICADOS SEGÚN TU SOLICITUD) ---
st.header("Indicadores Clave (Datos Filtrados)")
if not df_filtrado.empty:
    col1, col2, col3, col4 = st.columns(4)
    
    # (REQ 2) Total que paga la empresa
    total_costo_empresa = df_filtrado['Total pagado por la empresa'].sum()
    # (NUEVO) Total pagado a empleados (NETO)
    total_neto_pagado = df_filtrado['Salario Neto pagado al empleado'].sum()
    # (REQ 1) Promedio que se le paga a los empleados
    promedio_neto_empleado = df_filtrado['Salario Neto pagado al empleado'].mean()
    # (Recomendación) Promedio costo por empleado
    promedio_costo_empresa = df_filtrado['Total pagado por la empresa'].mean()
    
    col1.metric("Costo Total para SICET", f"${total_costo_empresa:,.0f}")
    col2.metric("Total Pagado a Empleados (Neto)", f"${total_neto_pagado:,.0f}")
    col3.metric("Promedio Costo p/ Empleado", f"${promedio_costo_empresa:,.0f}")
    col4.metric("Promedio Neto p/ Empleado", f"${promedio_neto_empleado:,.0f}")
    
else:
    st.info("No hay datos que coincidan con los filtros seleccionados.")

st.divider()

# --- 6. Gráficos Agregados (Cargo y Empresa) ---
st.header("Análisis de Costo por Categoría")
if not df_filtrado.empty:
    metrica_graficos = 'Total pagado por la empresa'
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"{metrica_graficos} por Cargo")
        df_cargo = df_filtrado.groupby('Cargo')[metrica_graficos].sum().reset_index()
        tipo_grafico_cargo = st.selectbox("Tipo de Gráfico (Cargo)", ["Gráfico de Barras", "Gráfico de Torta (Pie)"], key="cargo_chart")
        
        if tipo_grafico_cargo == "Gráfico de Barras":
            fig_cargo = px.bar(df_cargo, x='Cargo', y=metrica_graficos, title=f"{metrica_graficos} por Cargo", text_auto='.2s')
        else:
            fig_cargo = px.pie(df_cargo, names='Cargo', values=metrica_graficos, title=f"Distribución por Cargo")
        st.plotly_chart(fig_cargo, use_container_width=True)

    with col2:
        st.subheader(f"{metrica_graficos} por Empresa")
        df_empresa = df_filtrado.groupby('Empresa')[metrica_graficos].sum().reset_index()
        tipo_grafico_empresa = st.selectbox("Tipo de Gráfico (Empresa)", ["Gráfico de Barras", "Gráfico de Torta (Pie)"], key="empresa_chart")
        
        if tipo_grafico_empresa == "Gráfico de Barras":
            fig_empresa = px.bar(df_empresa, x='Empresa', y=metrica_graficos, title=f"{metrica_graficos} por Empresa", text_auto='.2s')
        else:
            fig_empresa = px.pie(df_empresa, names='Empresa', values=metrica_graficos, title=f"Distribución por Empresa")
        st.plotly_chart(fig_empresa, use_container_width=True)
else:
    st.info("No hay datos para mostrar en los gráficos agregados.")

st.divider()

# --- 7. Gráfico Histórico (Evolución Mensual) (CORREGIDO) ---
st.header("Evolución Histórica de la Nómina")
if not df_historial_raw.empty:
    st.info("Datos tomados de la hoja 'Reporte mensual'.")
    
    df_historial_chart = df_historial_raw.set_index('Mes')
    
    columnas_a_ver = st.multiselect(
        "Seleccione métricas para ver la evolución:",
        options=cols_moneda_historial,
        default=['Total pagado por la empresa', 'Salario Neto pagado al empleado']
    )
    
    if columnas_a_ver:
        # --- ¡AQUÍ ESTÁ LA CORRECCIÓN! ---
        if len(df_historial_chart) < 2:
            st.warning("Mostrando gráfico de barras (se necesita más de 1 mes para un gráfico de líneas).")
            st.bar_chart(df_historial_chart[columnas_a_ver])
        else:
            st.line_chart(df_historial_chart[columnas_a_ver])
    
else:
    st.info("No hay datos en 'Reporte mensual'. Guarde un reporte en la Página 4 para ver el historial.")