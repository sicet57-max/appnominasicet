# --- INICIO DEL GUARDIÁN DE SEGURIDAD ---
import streamlit as st

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("⚠️ Por favor, inicie sesión en la página 'Home' para acceder.")
    st.stop()
# --- FIN DEL GUARDIÁN DE SEGURIDAD ---

# ... (el resto de tu código de la página va aquí) ...
# (ej. import pandas as pd, import google_connector as gc, etc.)

# pages/6_Ficha_Empleado.py
import streamlit as st
import pandas as pd
import google_connector as gc # Importamos nuestro conector

# --- 1. Configuración de la Página y Título ---
st.set_page_config(layout="wide")
st.title("🔖 6. Ficha 360 del Empleado")
st.markdown("Vea toda la información consolidada de un empleado en un solo lugar.")

# --- 2. Verificar que los datos están cargados ---
# Esta página necesita casi todos los dataframes
required_dfs = ['df_info', 'df_comentarios', 'df_reporte_indi', 'df_especial_res']
if not all(df in st.session_state for df in required_dfs):
    st.error("Error: Faltan datos para generar la ficha (info, comentarios, reportes).")
    st.info("Por favor, vaya a 'Home' y refresque los datos. Asegúrese de haber ejecutado un cálculo.")
    st.stop()

# --- 3. Limpiar Nombres de Columnas (Crucial para las uniones) ---
try:
    st.session_state.df_info.columns = [col.strip() if isinstance(col, str) else col for col in st.session_state.df_info.columns]
    st.session_state.df_comentarios.columns = [col.strip() if isinstance(col, str) else col for col in st.session_state.df_comentarios.columns]
    st.session_state.df_reporte_indi.columns = [col.strip() if isinstance(col, str) else col for col in st.session_state.df_reporte_indi.columns]
    st.session_state.df_especial_res.columns = [col.strip() if isinstance(col, str) else col for col in st.session_state.df_especial_res.columns]
except Exception as e:
    st.error(f"Error al limpiar nombres de columnas: {e}")
    st.stop()

# --- 4. Selector de Empleado ---
df_info = st.session_state.df_info.copy()

# Crear una columna amigable para el selector
df_info['display_name'] = df_info['Nombre del técnico'] + " (Cédula: " + df_info['Cédula'].astype(str) + ")"
lista_empleados = ['Seleccione un empleado'] + sorted(df_info['display_name'].tolist())

selected_display_name = st.selectbox("Seleccione un Empleado", options=lista_empleados)

# --- 5. Lógica de Visualización ---
if selected_display_name != 'Seleccione un empleado':
    
    # 1. Obtener la Cédula del empleado seleccionado
    selected_cedula = df_info[df_info['display_name'] == selected_display_name]['Cédula'].iloc[0]
    
    # 2. Filtrar todos los DataFrames por esa Cédula
    info_empleado = df_info[df_info['Cédula'] == selected_cedula].iloc[0] # Es una Serie (una fila)
    comentarios_empleado = st.session_state.df_comentarios[st.session_state.df_comentarios['Cédula'] == selected_cedula]
    reporte_empleado = st.session_state.df_reporte_indi[st.session_state.df_reporte_indi['Cédula'] == selected_cedula]
    especial_empleado = st.session_state.df_especial_res[st.session_state.df_especial_res['Cédula'] == selected_cedula]

    # --- SECCIÓN 1: DATOS PERSONALES Y CLAVE ---
    st.header(f"Ficha de: {info_empleado['Nombre del técnico']}")
    st.markdown(f"**Cédula:** {info_empleado['Cédula']}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Cargo", info_empleado.get('Cargo', 'N/A'))
    col2.metric("Empresa", info_empleado.get('Empresa', 'N/A'))
    col3.metric("Tipo de Contrato", info_empleado.get('Tipo de contrato', 'N/A'))

    st.divider()

    # --- SECCIÓN 2: RESULTADOS DE NÓMINA ---
    st.header("Resultados del Último Cálculo")
    
    tab1, tab2 = st.tabs(["Cálculo Mensual (Reporte indi)", "Cálculo Prestaciones (Especial)"])
    
    with tab1:
        st.subheader("Resultados del Último Cálculo Mensual")
        if not reporte_empleado.empty:
            # Transponer los datos para verlos como (Item: Valor)
            reporte_transpuesto = reporte_empleado.iloc[0].transpose()
            reporte_transpuesto.name = "Valor"
            st.dataframe(reporte_transpuesto, use_container_width=True)
        else:
            st.warning("No hay datos de cálculo mensual para este empleado. (Ejecute el cálculo en Página 3).")

    with tab2:
        st.subheader("Resultados del Último Cálculo de Prestaciones")
        if not especial_empleado.empty:
            # Transponer
            especial_transpuesto = especial_empleado.iloc[0].transpose()
            especial_transpuesto.name = "Valor"
            st.dataframe(especial_transpuesto, use_container_width=True)
        else:
            st.warning("No hay datos de cálculo de prestaciones para este empleado. (Ejecute el cálculo en Página 4).")

    st.divider()

    # --- SECCIÓN 3: COMENTARIOS ---
    st.header("Historial de Comentarios")
    if not comentarios_empleado.empty:
        # Quitar Cédula y Nombre, y transponer (para ver Mes: Comentario)
        comentarios_display = comentarios_empleado.drop(columns=['Cédula', 'Nombre del técnico']).iloc[0]
        comentarios_display.name = "Comentario"
        st.dataframe(comentarios_display, use_container_width=True)
    else:
        st.warning("No se encontraron comentarios para este empleado.")

else:
    st.info("Seleccione un empleado de la lista para ver su ficha completa.")