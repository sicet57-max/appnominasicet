# --- INICIO DEL GUARDIÁN DE SEGURIDAD ---
import streamlit as st

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("⚠️ Por favor, inicie sesión en la página 'Home' para acceder.")
    st.stop()
# --- FIN DEL GUARDIÁN DE SEGURIDAD ---

# ... (el resto de tu código de la página va aquí) ...
# (ej. import pandas as pd, import google_connector as gc, etc.)

# pages/4_Calculo_Prestaciones.py
import streamlit as st
import pandas as pd
import google_connector as gc # Importamos nuestro conector
import time
import numpy as np

# --- 1. Configuración de la Página y Título ---
st.set_page_config(layout="wide")
st.title("✨ 4. Cálculo de Prestaciones (Especial)")
st.markdown("Calcule las prestaciones sociales (Cesantías, Prima, Intereses y Vacaciones) y guárdelas en la hoja 'Especial'.")

# --- 2. Verificar que los datos están cargados ---
# Necesitamos la info de liquidación (Salario, Aux, Días trabajados)
if 'df_info' not in st.session_state or 'df_datos_liq' not in st.session_state:
    st.error("Error: Faltan datos maestros o de liquidación para calcular.")
    st.info("Por favor, vaya a la página 'Home' y refresque los datos.")
    st.stop()

# --- 3. Obtener Conexión y Claves ---
client = gc.connect_to_gsheets()
KEY_NOMINA = st.secrets["google_sheets"]["rendimiento_pro_key"]
HOJA_ESPECIAL = "Especial" # Hoja de destino

# --- 4. Preparación de Datos ---
st.header("Paso 1: Confirmar Datos Base")
st.info("""
Aquí se muestran los datos base tomados de la hoja 'Datos liquidación'. 
**Importante:** Antes de calcular, asegúrese de que los 'Días trabajados' y el 'Salario' 
en la `Página 3` reflejen el periodo que desea liquidar (ej. 180 para prima, 360 para cesantías/vacaciones).
""")

# 1. Limpiar nombres de columnas
try:
    st.session_state.df_datos_liq.columns = [col.strip() if isinstance(col, str) else col for col in st.session_state.df_datos_liq.columns]
    st.session_state.df_info.columns = [col.strip() if isinstance(col, str) else col for col in st.session_state.df_info.columns]
except Exception as e:
    st.error(f"Error al limpiar nombres de columnas: {e}")
    st.stop()

# 2. Traer los datos base necesarios
df_base_liq = st.session_state.df_datos_liq.copy()
df_base_info = st.session_state.df_info[['Cédula', 'Nombre del técnico']].copy()

# 3. Unir para tener los nombres
df_calculo = pd.merge(
    df_base_info,
    df_base_liq,
    on='Cédula',
    how='left'
)

# 4. Convertir a numérico
cols_numericas = ['Salario del trabajador', 'Aux Transporte', 'Días trabajados']
for col in cols_numericas:
     # Limpiar comas y convertir
     df_calculo[col] = pd.to_numeric(df_calculo[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

# 5. Mostrar tabla de confirmación
st.dataframe(df_calculo[['Cédula', 'Nombre del técnico', 'Salario del trabajador', 'Aux Transporte', 'Días trabajados']], use_container_width=True)

# --- 5. Ejecución del Cálculo ---
st.divider()
st.header("Paso 2: Ejecutar Cálculo de Prestaciones")

# Campo para el periodo
periodo = st.text_input("Nombre del Periodo (Ej: 'Semestre 1 - 2024' o 'Anual 2024')")

if st.button("Calcular y Guardar Prestaciones", type="primary"):
    if not periodo:
        st.error("Por favor, ingrese un nombre para el 'Periodo' antes de calcular.")
    else:
        with st.spinner("Calculando y guardando prestaciones..."):
            
            # --- LÓGICA DE CÁLCULO (Prestaciones) ---
            
            # 1. Base para Prestaciones = Salario + Auxilio de Transporte
            df_calculo['Base_Prestaciones'] = df_calculo['Salario del trabajador'] + df_calculo['Aux Transporte']
            
            # 2. Cesantías
            # Fórmula: (Base * Días trabajados) / 360
            df_calculo['Cesantías'] = (df_calculo['Base_Prestaciones'] * df_calculo['Días trabajados']) / 360
            
            # 3. Intereses a las Cesantías
            # Fórmula: (Cesantías * Días trabajados * 0.12) / 360
            df_calculo['Intereses a las Cesantías'] = (df_calculo['Cesantías'] * df_calculo['Días trabajados'] * 0.12) / 360
            
            # 4. Prima de Servicios
            # Fórmula: (Base * Días trabajados en semestre) / 360
            # Asumimos que los 'Días trabajados' ingresados son los correctos para el periodo (ej. 180)
            df_calculo['Prima de Servicios'] = (df_calculo['Base_Prestaciones'] * df_calculo['Días trabajados']) / 360
            
            # 5. Vacaciones (¡NUEVO CÁLCULO!)
            # Fórmula: (Salario SIN Aux Transporte * Días trabajados) / 720
            df_calculo['Vacaciones'] = (df_calculo['Salario del trabajador'] * df_calculo['Días trabajados']) / 720
            
            # 6. Total (¡ACTUALIZADO!)
            df_calculo['Total'] = df_calculo['Cesantías'] + df_calculo['Intereses a las Cesantías'] + df_calculo['Prima de Servicios'] + df_calculo['Vacaciones']
            
            # 7. Periodo
            df_calculo['Periodo'] = periodo
            
            # --- Preparar Hoja de Salida ---
            # Coincidir con tu hoja "Especial" y añadir las nuevas columnas
            cols_finales = [
                'Cédula', 
                'Nombre del técnico', 
                'Cesantías', 
                'Intereses a las Cesantías', 
                'Prima de Servicios',
                'Vacaciones', # <-- AÑADIDO
                'Total',
                'Periodo'
            ]
            df_resultado_especial = df_calculo[cols_finales].copy()
            df_resultado_especial = df_resultado_especial.rename(columns={'Nombre del técnico': 'Nombre completo'})
            
            # --- Guardar en Google Sheets ---
            df_resultado_especial.columns = df_resultado_especial.columns.astype(str)
            success = gc.update_sheet(client, KEY_NOMINA, HOJA_ESPECIAL, df_resultado_especial)
            
            if success:
                # Actualizar el estado de sesión
                st.session_state.df_especial_res = df_resultado_especial.copy()
                st.success(f"¡Cálculo de Prestaciones para el periodo '{periodo}' guardado con éxito!")
                st.balloons()
            else:
                st.error("Error al guardar en Google Sheets. Revise la consola.")

# --- 6. Ver Resultados ---
st.divider()
st.header("Resultados Guardados en Hoja 'Especial'")
st.info("Aquí se muestra la información más reciente guardada en la hoja 'Especial'.")

if 'df_especial_res' in st.session_state and not st.session_state.df_especial_res.empty:
    st.dataframe(st.session_state.df_especial_res, use_container_width=True)
else:
    # Cargar datos si no están en sesión (para la primera carga)
    try:
        df_historial_especial = gc.load_data(client, KEY_NOMINA, HOJA_ESPECIAL)
        if not df_historial_especial.empty:
             st.dataframe(df_historial_especial, use_container_width=True)
        else:
            st.warning("Aún no se han calculado datos de prestaciones.")
    except Exception as e:
        st.error(f"No se pudo cargar el historial de prestaciones: {e}")