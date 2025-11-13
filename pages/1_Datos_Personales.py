# --- INICIO DEL GUARDIÁN DE SEGURIDAD ---
import streamlit as st

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("⚠️ Por favor, inicie sesión en la página 'Home' para acceder.")
    st.stop()
# --- FIN DEL GUARDIÁN DE SEGURIDAD ---

# ... (el resto de tu código de la página va aquí) ...
# (ej. import pandas as pd, import google_connector as gc, etc.)

# pages/1_Datos_Personales.py
import streamlit as st
import pandas as pd
import google_connector as gc # Importamos nuestro conector
import time

# --- 1. Configuración de la Página y Título ---
st.set_page_config(layout="wide")
st.title("👤 1. Gestión de Datos Personales")
st.markdown("Vea, edite, agregue o elimine empleados de la base de datos maestra.")

# --- 2. Verificar que los datos están cargados (desde Home.py) ---
if 'df_info' not in st.session_state or st.session_state.df_info.empty:
    st.error("Error: Los datos de empleados no se han cargado.")
    st.info("Por favor, vaya a la página 'Home' y refresque los datos.")
    st.stop()

# --- 3. Obtener Conexión y Claves ---
client = gc.connect_to_gsheets()
KEY_NOMINA = st.secrets["google_sheets"]["rendimiento_pro_key"]
HOJA_INFO_EMPLEADOS = "Informacion"

# --- 4. Crear copia y LIMPIAR Nombres de Columnas ---
df_para_editar = st.session_state.df_info.copy()
df_para_editar.columns = [col.strip() if isinstance(col, str) else col for col in df_para_editar.columns]

# --- 5. Filtros de Búsqueda (Mejorados con Selectbox) ---
with st.expander("🔍 Ver Filtros de Búsqueda"):
    col1, col2 = st.columns(2)
    
    try:
        # --- FILTRO 1: NOMBRE (MODIFICADO) ---
        # Creamos una lista de nombres únicos para el selectbox
        lista_nombres = ['Todos'] + sorted(df_para_editar['Nombre del técnico'].unique().tolist())
        filtro_nombre = col1.selectbox(
            "Buscar por Nombre del Técnico (Escriba o seleccione)", 
            options=lista_nombres,
            index=0 # Por defecto 'Todos'
        )
        if filtro_nombre != 'Todos':
            df_para_editar = df_para_editar[df_para_editar['Nombre del técnico'] == filtro_nombre]
        
        # --- FILTRO 2: CÉDULA (MODIFICADO) ---
        lista_cedulas = ['Todas'] + sorted(df_para_editar['Cédula'].astype(str).unique().tolist())
        filtro_cedula = col2.selectbox(
            "Buscar por Cédula (Escriba o seleccione)", 
            options=lista_cedulas,
            index=0 # Por defecto 'Todos'
        )
        if filtro_cedula != 'Todas':
            df_para_editar = df_para_editar[df_para_editar['Cédula'].astype(str) == filtro_cedula]

        col3, col4 = st.columns(2)
        
        # Filtro 3: Empresa
        lista_empresas = ['Todas'] + sorted(df_para_editar['Empresa'].unique().tolist())
        filtro_empresa = col3.selectbox("Filtrar por Empresa", options=lista_empresas, index=0)
        if filtro_empresa != 'Todas':
            df_para_editar = df_para_editar[df_para_editar['Empresa'] == filtro_empresa]
        
        # Filtro 4: Tipo de Contrato
        lista_contratos = ['Todos'] + sorted(df_para_editar['Tipo de contrato'].unique().tolist())
        filtro_contrato = col4.selectbox("Filtrar por Tipo de contrato", options=lista_contratos, index=0)
        if filtro_contrato != 'Todos':
            df_para_editar = df_para_editar[df_para_editar['Tipo de contrato'] == filtro_contrato]
            
    except KeyError as e:
        st.error(f"Error en filtros: No se encontró la columna '{e}'. Refresque los datos desde 'Home'.")
    except Exception as e:
        st.error(f"Error inesperado en los filtros: {e}")

# --- 6. Editor de Datos (st.data_editor) ---
st.header("Editor de Empleados")

# --- LÓGICA DE GUARDADO INTELIGENTE (COMO EN PÁGINA 2) ---
# Ahora que usamos filtros, necesitamos el guardado inteligente aquí también.
# 'edited_df' contendrá solo las filas filtradas
edited_df = st.data_editor(
    df_para_editar,
    num_rows="dynamic", # Permitimos agregar/eliminar en esta página
    use_container_width=True,
    key="editor_empleados"
)


# --- 7. Lógica de Guardado (INTELIGENTE) ---
st.divider()
if st.button("Guardar Cambios en Google Sheets", type="primary"):
    
    with st.spinner("Guardando en Google Sheets..."):
        
        # 1. Obtener la base de datos COMPLETA desde la memoria
        df_original = st.session_state.df_info.copy()
        df_original.columns = [col.strip() if isinstance(col, str) else col for col in df_original.columns]
        
        # 2. Preparar los cambios (el dataframe editado)
        # Asegurarnos de que las columnas coincidan
        df_cambios = edited_df.copy()
        
        # 3. Identificar si hay filtros activos
        filtros_activos = bool(filtro_nombre != 'Todos' or filtro_cedula != 'Todas' or filtro_empresa != 'Todas' or filtro_contrato != 'Todos')
        
        if filtros_activos:
            # --- Modo Fusión (con filtros) ---
            # Usar Cédula como llave para fusionar
            df_original = df_original.set_index('Cédula')
            df_cambios = df_cambios.set_index('Cédula')
            
            # Actualizar el DF original SOLO con los cambios.
            df_original.update(df_cambios)
            
            # Restaurar el índice
            df_final_para_guardar = df_original.reset_index()
        else:
            # --- Modo Reemplazo (sin filtros) ---
            # Si no hay filtros, el 'edited_df' es la nueva verdad completa
            df_final_para_guardar = edited_df.copy()

        # 4. Guardar
        df_final_para_guardar.columns = df_final_para_guardar.columns.astype(str)
        success = gc.update_sheet(client, KEY_NOMINA, HOJA_INFO_EMPLEADOS, df_final_para_guardar)
        
        if success:
            st.session_state.df_info = df_final_para_guardar.copy()
            st.toast("✅ ¡Datos guardados con éxito!", icon="🎉")
            time.sleep(2)
            st.rerun()
        else:
            pass 
        
        