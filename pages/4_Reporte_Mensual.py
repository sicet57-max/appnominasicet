# --- INICIO DEL GUARDIÁN DE SEGURIDAD ---
import streamlit as st

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("⚠️ Por favor, inicie sesión en la página 'Home' para acceder.")
    st.stop()
# --- FIN DEL GUARDIÁN DE SEGURIDAD ---

# ... (el resto de tu código de la página va aquí) ...
# (ej. import pandas as pd, import google_connector as gc, etc.)

# pages/4_Reporte_Mensual.py
import streamlit as st
import pandas as pd
import google_connector as gc # Importamos nuestro conector
import time

# --- 1. Configuración de la Página y Título ---
st.set_page_config(layout="wide")
st.title("🗓️ 4. Historial de Reportes Mensuales")
st.markdown("Guarde los totales del último cálculo mensual en el historial.")

# --- 2. Obtener Conexión y Claves ---
client = gc.connect_to_gsheets()
KEY_NOMINA = st.secrets["google_sheets"]["rendimiento_pro_key"]
HOJA_REPORTE_MENSUAL = "Reporte mensual"

# --- 3. Lógica para Guardar el Resumen ---
st.header("Guardar Cálculo Actual en el Historial")

# Primero, verificamos si hay un cálculo en la memoria (hecho en Página 3)
if 'df_calculo_completo' in st.session_state:
    df_resumen = st.session_state.df_calculo_completo.copy().fillna(0)
    
    # Calculamos los totales
    num_trabajadores = len(df_resumen)
    total_devengado = df_resumen['Total_Devengado'].sum()
    total_deducciones = df_resumen['Total_Deducciones'].sum()
    total_neto_pagado = df_resumen['Salario_Neto'].sum()
    total_costo_empresa = df_resumen['Costo_Total_Empresa'].sum() 
    
    st.info("Se han detectado los siguientes totales del último cálculo realizado en la 'Página 3'.")
    
    # Mostramos los totales como confirmación
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Número de Trabajadores", num_trabajadores)
    col2.metric("Total Devengado", f"${total_devengado:,.0f}")
    col3.metric("Salario Neto Pagado", f"${total_neto_pagado:,.0f}")
    col4.metric("Total Pagado por Empresa", f"${total_costo_empresa:,.0f}")
    
    st.divider()
    
    # --- Pedir el Mes (¡Tu requerimiento!) ---
    mes_actual = st.text_input("Por favor, ingrese el Mes o Periodo para este reporte (Ej: 'Enero 2024')")
    
    if st.button("Guardar en Historial Mensual", type="primary"):
        if not mes_actual:
            st.error("Debe ingresar un nombre para el 'Mes' antes de guardar.")
        else:
            with st.spinner("Guardando en el historial..."):
                # Preparamos la fila en el orden de tu hoja "Reporte mensual"
                nueva_fila = [
                    mes_actual,
                    num_trabajadores,
                    total_devengado,
                    total_deducciones,
                    total_neto_pagado,
                    total_costo_empresa
                ]
                
                # Usamos la nueva función 'append_row'
                success = gc.append_row(client, KEY_NOMINA, HOJA_REPORTE_MENSUAL, nueva_fila)
                
                if success:
                    st.success(f"¡Reporte del mes '{mes_actual}' guardado en el historial!")
                    st.toast("Actualizando vista del historial...")
                    # Limpiamos el cache de la hoja de historial
                    st.session_state.pop('df_historial', None) 
                    time.sleep(2)
                    st.rerun() 
                else:
                    st.error("Error al guardar en Google Sheets. Revise la consola.")
else:
    st.warning("No se ha ejecutado ningún cálculo en esta sesión.")
    st.info("Por favor, primero vaya a la `Página 3` y presione 'Calcular Nómina Mensual' para generar los totales que desea guardar.")

# --- 4. Mostrar el Historial (MODIFICADO a st.data_editor) ---
st.divider()
st.header("Historial de Cálculos")
st.info("Estos son los datos guardados en la hoja 'Reporte mensual'. Puede editar o eliminar filas.")

try:
    # Cargamos los datos solo si no están en la sesión
    if 'df_historial' not in st.session_state:
        df_historial_raw = gc.load_data(client, KEY_NOMINA, HOJA_REPORTE_MENSUAL)
        
        if df_historial_raw.empty:
            st.info("El historial está vacío.")
            # Crear un DF vacío con las columnas correctas si está vacío
            cols_historial = ['Mes', 'Numero de trabajadores', 'Total devengado', 'Total Deducciones', 'Salario Neto pagado al empleado', 'Total pagado por la empresa']
            st.session_state.df_historial = pd.DataFrame(columns=cols_historial)
        else:
            # Limpiar y convertir tipos de datos
            df_historial = df_historial_raw.copy()
            cols_num_historial = [
                'Numero de trabajadores', 'Total devengado', 'Total Deducciones', 
                'Salario Neto pagado al empleado', 'Total pagado por la empresa'
            ]
            for col in cols_num_historial:
                df_historial[col] = pd.to_numeric(df_historial[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
            st.session_state.df_historial = df_historial.copy()

    # Usar el editor de datos
    edited_df_historial = st.data_editor(
        st.session_state.df_historial,
        use_container_width=True,
        num_rows="dynamic", # Permite añadir y eliminar filas
        key="editor_historial"
    )

    if st.button("Guardar Cambios en Historial", key="guardar_historial"):
        with st.spinner("Actualizando historial en Google Sheets..."):
            
            # Usamos update_sheet para SOBREESCRIBIR la hoja con la versión editada
            df_guardar = edited_df_historial.copy()
            df_guardar.columns = df_guardar.columns.astype(str)
            
            success = gc.update_sheet(client, KEY_NOMINA, HOJA_REPORTE_MENSUAL, df_guardar)
            
            if success:
                st.session_state.df_historial = df_guardar.copy()
                st.toast("¡Historial actualizado con éxito!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Error al guardar el historial en Google Sheets.")
        
except Exception as e:
    st.error(f"No se pudo cargar o editar el historial: {e}")