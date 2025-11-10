# --- INICIO DEL GUARDIÁN DE SEGURIDAD ---
import streamlit as st

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("⚠️ Por favor, inicie sesión en la página 'Home' para acceder.")
    st.stop()
# --- FIN DEL GUARDIÁN DE SEGURIDAD ---

# ... (el resto de tu código de la página va aquí) ...
# (ej. import pandas as pd, import google_connector as gc, etc.)

# pages/5_Administrar_Indicadores.py
import streamlit as st
import pandas as pd
import google_connector as gc # Importamos nuestro conector
import time

# --- 1. Configuración de la Página y Título ---
st.set_page_config(layout="wide")
st.title("⚙️ 5. Administrar Indicadores")
st.markdown("Vea, edite, agregue o elimine los indicadores de cálculo (porcentajes y valores).")

# --- 2. Obtener Conexión y Claves ---
try:
    client = gc.connect_to_gsheets()
    KEY_NOMINA = st.secrets["google_sheets"]["rendimiento_pro_key"]
    KEY_INDICADORES = st.secrets["google_sheets"]["calculo_rendimiento_key"]
except Exception as e:
    st.error(f"Error al cargar las claves de secrets.toml: {e}")
    st.stop()
    
# --- 3. Verificar que los datos están cargados ---
if 'df_ind_empleado' not in st.session_state or 'df_ind_empleador' not in st.session_state or \
   'df_ind_especial' not in st.session_state or 'df_ind_horas' not in st.session_state:
    st.error("Error: Faltan datos de indicadores.")
    st.info("Por favor, vaya a la página 'Home' y refresque los datos.")
    st.stop()

# --- 4. Crear una función genérica para editar ---
# Esto evita repetir el mismo código 4 veces
def crear_editor_indicadores(titulo_seccion, df_en_sesion, nombre_hoja_gsheets, key_unica):
    """
    Crea una sección con un st.data_editor para un DataFrame de indicador.
    """
    st.subheader(titulo_seccion)
    
    # 1. Cargar datos desde la sesión (usamos .copy() para editar)
    df_para_editar = st.session_state[df_en_sesion].copy()
    
    # 2. Mostrar el editor de datos (¡con num_rows="dynamic"!)
    edited_df = st.data_editor(
        df_para_editar,
        use_container_width=True,
        num_rows="dynamic", # ¡Permite agregar y eliminar!
        key=key_unica
    )
    
    # 3. Crear un botón de guardado único para esta sección
    if st.button(f"Guardar Cambios en '{nombre_hoja_gsheets}'", key=f"guardar_{key_unica}"):
        with st.spinner(f"Guardando cambios en '{nombre_hoja_gsheets}'..."):
            
            # Limpiar filas vacías que el editor pueda crear
            edited_df.dropna(how='all', inplace=True)
            edited_df.columns = edited_df.columns.astype(str)
            
            # Guardar en Google Sheets
            success = gc.update_sheet(client, KEY_INDICADORES, nombre_hoja_gsheets, edited_df)
            
            if success:
                # Actualizar la sesión
                st.session_state[df_en_sesion] = edited_df.copy()
                st.toast(f"¡Indicadores de '{nombre_hoja_gsheets}' guardados!", icon="✅")
                time.sleep(1)
                st.rerun() # Recargar para reflejar los cambios
            else:
                st.error(f"No se pudieron guardar los cambios en '{nombre_hoja_gsheets}'.")

# --- 5. Mostrar los 4 Editores ---

st.info("Aquí puede modificar los valores base para todos los cálculos. Los cambios se aplicarán la próxima vez que ejecute la 'Página 3'.")

# Usar pestañas (tabs) para organizar
tab1, tab2, tab3, tab4 = st.tabs(["Indicadores Empleado", "Indicadores Empleador", "Horas Extra", "Base Especial"])

with tab1:
    crear_editor_indicadores(
        titulo_seccion="Indicadores del Empleado (Deducciones)",
        df_en_sesion='df_ind_empleado',
        nombre_hoja_gsheets="Empleado",
        key_unica="editor_empleado"
    )

with tab2:
    crear_editor_indicadores(
        titulo_seccion="Indicadores del Empleador (Aportes)",
        df_en_sesion='df_ind_empleador',
        nombre_hoja_gsheets="Empleador",
        key_unica="editor_empleador"
    )

with tab3:
    crear_editor_indicadores(
        titulo_seccion="Recargos de Horas Extra",
        df_en_sesion='df_ind_horas',
        nombre_hoja_gsheets="Horas extra",
        key_unica="editor_horas"
    )

with tab4:
    crear_editor_indicadores(
        titulo_seccion="Base de Prestaciones Especiales",
        df_en_sesion='df_ind_especial',
        nombre_hoja_gsheets="Especial",
        key_unica="editor_especial"
    )