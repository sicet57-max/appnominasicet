# --- INICIO DEL GUARDIÁN DE SEGURIDAD ---
import streamlit as st

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("⚠️ Por favor, inicie sesión en la página 'Home' para acceder.")
    st.stop()
# --- FIN DEL GUARDIÁN DE SEGURIDAD ---

# ... (el resto de tu código de la página va aquí) ...
# (ej. import pandas as pd, import google_connector as gc, etc.)

# pages/7_Consolidado_Costos.py
import streamlit as st
import pandas as pd
import google_connector as gc # Importamos nuestro conector

# --- INICIO DEL GUARDIÁN DE SEGURIDAD ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("⚠️ Por favor, inicie sesión en la página 'Home' para acceder.")
    st.stop()
# --- FIN DEL GUARDIÁN DE SEGURIDAD ---

# --- 1. Configuración de la Página y Título ---
st.set_page_config(layout="wide")
st.title("📊 7. Consolidado de Costos y Deducciones")
st.markdown("Un resumen de todos los costos, deducciones y provisiones calculados en la plataforma.")

# --- 2. Verificar que los datos están cargados ---
if 'df_calculo_completo' not in st.session_state or 'df_especial_res' not in st.session_state:
    st.error("Error: Faltan datos para generar el consolidado.")
    st.info("Por favor, ejecute un cálculo en la 'Página 3' y en la 'Página 4' para ver este reporte.")
    st.stop()

# --- 3. Cargar Datos de la Sesión ---
try:
    df_calc = st.session_state.df_calculo_completo.copy().fillna(0)
    df_prest = st.session_state.df_especial_res.copy().fillna(0)
except Exception as e:
    st.error(f"Error al leer los datos de la sesión: {e}")
    st.stop()

st.info("Los siguientes son los **totales sumados** del último cálculo mensual (Página 3) y el último cálculo de prestaciones (Página 4).")

# --- 4. Mostrar Resúmenes ---

col1, col2, col3 = st.columns(3)

# --- Columna 1: Deducciones al Empleado ---
with col1:
    st.subheader("Total Deducciones al Empleado")
    
    total_deduc_salud = df_calc['Aportes a salud'].sum()
    total_deduc_pension = df_calc['Aportes a pensión'].sum()
    total_retefuente = df_calc['Retención en la Fuente'].sum()
    total_prestamos = df_calc['Prestamos'].sum()
    total_otros_desc = df_calc['Otros Descuentos'].sum()
    
    st.metric("Salud (4%)", f"${total_deduc_salud:,.0f}")
    st.metric("Pensión (4%)", f"${total_deduc_pension:,.0f}")
    st.metric("Retención en la Fuente", f"${total_retefuente:,.0f}")
    st.metric("Préstamos", f"${total_prestamos:,.0f}")
    st.metric("Otros Descuentos", f"${total_otros_desc:,.0f}")
    st.divider()
    st.metric("TOTAL DEDUCIDO AL EMPLEADO", f"${df_calc['Total_Deducciones'].sum():,.0f}", delta_color="inverse")

# --- Columna 2: Aportes de la Empresa (SICET) ---
with col2:
    st.subheader("Total Aportes (Pagado por SICET)")
    
    total_aporte_salud = df_calc['Aporte_Salud_Empresa'].sum()
    total_aporte_pension = df_calc['Aporte_Pension_Empresa'].sum()
    total_arl = df_calc['Aporte_ARL'].sum()
    total_caja = df_calc['Aporte_Caja'].sum()
    total_icbf = df_calc['Aporte_ICBF'].sum()
    total_sena = df_calc['Aporte_SENA'].sum()
    
    st.metric("Salud (8.5%)", f"${total_aporte_salud:,.0f}")
    st.metric("Pensión (12%)", f"${total_aporte_pension:,.0f}")
    st.metric("ARL", f"${total_arl:,.0f}")
    st.metric("Caja de Compensación", f"${total_caja:,.0f}")
    st.metric("ICBF", f"${total_icbf:,.0f}")
    st.metric("SENA", f"${total_sena:,.0f}")
    st.divider()
    st.metric("TOTAL APORTES EMPRESA", f"${df_calc['Total_Aportes_Empresa'].sum():,.0f}", delta_color="inverse")

# --- Columna 3: Provisiones (Tu solicitud) ---
with col3:
    st.subheader("Total Provisiones (Prestaciones)")
    
    total_cesantias = df_prest['Cesantías'].sum()
    total_intereses = df_prest['Intereses a las Cesantías'].sum()
    total_prima = df_prest['Prima de Servicios'].sum()
    
    st.metric("Cesantías", f"${total_cesantias:,.0f}")
    st.metric("Intereses a las Cesantías", f"${total_intereses:,.0f}")
    st.metric("Prima de Servicios", f"${total_prima:,.0f}")
    
    st.divider()
    st.metric("TOTAL PRESTACIONES", f"${df_prest['Total'].sum():,.0f}", delta_color="inverse")

st.divider()

# --- Gran Total ---
st.header("Gran Total: Costo Empresa")
total_costo_empresa = df_calc['Costo_Total_Empresa'].sum()
total_prestaciones = df_prest['Total'].sum()

st.info("El costo total para la empresa es la suma del Costo Mensual (Página 3) y las Provisiones de Prestaciones (Página 4).")

col_final_1, col_final_2 = st.columns(2)
col_final_1.metric("Costo Total Mensual (Nómina + Aportes)", f"${total_costo_empresa:,.0f}")
col_final_2.metric("Provisión Total (Prestaciones)", f"${total_prestaciones:,.0f}")

st.subheader(f"COSTO TOTAL CONSOLIDADO: ${total_costo_empresa + total_prestaciones:,.0f}")