# --- INICIO DEL GUARDIÁN DE SEGURIDAD ---
import streamlit as st

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("⚠️ Por favor, inicie sesión en la página 'Home' para acceder.")
    st.stop()
# --- FIN DEL GUARDIÁN DE SEGURIDAD ---

# ... (el resto de tu código de la página va aquí) ...
# (ej. import pandas as pd, import google_connector as gc, etc.)

# pages/2_Comentarios.py
import streamlit as st
import pandas as pd
import google_connector as gc # Importamos nuestro conector
import time

# --- 1. Configuración de la Página y Título ---
st.set_page_config(layout="wide")
st.title("💬 2. Gestión de Comentarios")
st.markdown("Edite los comentarios mensuales. La lista de empleados se gestiona desde 'Datos Personales'.")

# --- 2. Verificar que los datos están cargados (desde Home.py) ---
# ¡AHORA NECESITAMOS AMBOS DATAFRAMES!
if 'df_info' not in st.session_state or st.session_state.df_info.empty:
    st.error("Error: Los datos maestros de empleados (df_info) no se han cargado.")
    st.info("Por favor, vaya a la página 'Home' y refresque los datos.")
    st.stop()
if 'df_comentarios' not in st.session_state:
    st.error("Error: Los datos de comentarios (df_comentarios) no se han cargado.")
    st.info("Por favor, vaya a la página 'Home' y refresque los datos.")
    st.stop()

# --- 3. Obtener Conexión y Claves ---
client = gc.connect_to_gsheets()
KEY_NOMINA = st.secrets["google_sheets"]["rendimiento_pro_key"]
HOJA_COMENTARIOS = "comentarios"

# --- 4. PREPARACIÓN DE DATOS (LA NUEVA LÓGICA) ---
# Limpiamos los nombres de las columnas de ambas tablas
st.session_state.df_info.columns = [col.strip() if isinstance(col, str) else col for col in st.session_state.df_info.columns]
st.session_state.df_comentarios.columns = [col.strip() if isinstance(col, str) else col for col in st.session_state.df_comentarios.columns]

# 1. Obtenemos la lista MAESTRA de empleados (la "fuente de la verdad")
df_base_empleados = st.session_state.df_info[['Cédula', 'Nombre del técnico']].copy()

# 2. Obtenemos los comentarios
df_comentarios = st.session_state.df_comentarios.copy()

# 3. Identificamos las columnas de meses (todo lo que no sea ID)
try:
    cols_meses = [col for col in df_comentarios.columns if col not in ['Cédula', 'Nombre del técnico']]
except KeyError:
    st.error("Error: La hoja 'comentarios' debe tener una columna 'Cédula'.")
    st.stop()

# 4. Unimos (join) la lista maestra CON los comentarios
#    Usamos 'Cédula' como llave. 'how='left'' asegura que TODOS los empleados
#    de Página 1 aparezcan, tengan o no comentarios.
df_para_editar = pd.merge(
    df_base_empleados,
    df_comentarios[['Cédula'] + cols_meses], # Solo traemos la cédula y los meses
    on='Cédula',
    how='left'
)

# 5. Rellenamos con "" los empleados nuevos que no tengan comentarios (NaN)
df_para_editar[cols_meses] = df_para_editar[cols_meses].fillna("")


# --- 5. Filtros de Búsqueda (Ahora se basan en la nueva tabla) ---
with st.expander("🔍 Ver Filtros de Búsqueda"):
    col1, col2 = st.columns(2)
    
    # Filtro 1: Nombre
    lista_nombres = ['Todos'] + sorted(df_para_editar['Nombre del técnico'].unique().tolist())
    filtro_nombre = col1.selectbox(
        "Buscar por Nombre (Escriba o seleccione)", 
        options=lista_nombres, index=0, key="filtro_nombre_coment"
    )
    if filtro_nombre != 'Todos':
        df_para_editar = df_para_editar[df_para_editar['Nombre del técnico'] == filtro_nombre]
    
    # Filtro 2: Cédula
    lista_cedulas = ['Todos'] + sorted(df_para_editar['Cédula'].astype(str).unique().tolist())
    filtro_cedula = col1.selectbox(
        "Buscar por Cédula (Escriba o seleccione)", 
        options=lista_cedulas, index=0, key="filtro_cedula_coment"
    )
    if filtro_cedula != 'Todos':
        df_para_editar = df_para_editar[df_para_editar['Cédula'].astype(str) == filtro_cedula]

    # Filtro 3: Meses
    filtro_meses = col2.multiselect(
        "Filtrar por Mes",
        options=cols_meses,
        default=cols_meses
    )

# Aplicar el filtro de columnas (meses)
cols_a_mostrar = ['Cédula', 'Nombre del técnico'] + filtro_meses
df_para_editar = df_para_editar[cols_a_mostrar]


# --- 6. Editor de Datos (CON COLUMNAS BLOQUEADAS) ---
st.header("Editor de Comentarios")
st.info("Las columnas 'Cédula' y 'Nombre del técnico' no se pueden editar aquí. Gestione los empleados en 'Datos Personales'.")

edited_df = st.data_editor(
    df_para_editar,
    use_container_width=True,
    key="editor_comentarios",
    # ¡LA CLAVE! Bloqueamos la edición de estas columnas
    disabled=['Cédula', 'Nombre del técnico'] 
)


# --- 7. Lógica de Guardado Inteligente (Actualizada) ---
st.divider()
if st.button("Guardar Cambios en Google Sheets", type="primary"):
    
    with st.spinner("Guardando en Google Sheets..."):
        # 1. Obtener la base de datos COMPLETA (incluyendo nombres actualizados de Página 1)
        #    Volvemos a construir la tabla completa que DEBERÍA existir.
        df_final_para_guardar = pd.merge(
            st.session_state.df_info[['Cédula', 'Nombre del técnico']],
            edited_df, # Los datos editados por el usuario
            on='Cédula',
            how='left',
            suffixes=('', '_editado') # Nombres temporal
        )
        
        # Nos aseguramos de quedarnos con el nombre correcto de Página 1
        df_final_para_guardar['Nombre del técnico'] = df_final_para_guardar['Nombre del técnico_editado']
        
        # Seleccionamos solo las columnas que van en la hoja 'comentarios'
        columnas_finales = ['Cédula', 'Nombre del técnico'] + cols_meses
        df_final_para_guardar = df_final_para_guardar[columnas_finales]
        
        # Limpiamos NaNs por si acaso
        df_final_para_guardar[cols_meses] = df_final_para_guardar[cols_meses].fillna("")
        df_final_para_guardar.columns = df_final_para_guardar.columns.astype(str)
            
        # 6. Guardar la base de datos COMPLETA y actualizada
        success = gc.update_sheet(client, KEY_NOMINA, HOJA_COMENTARIOS, df_final_para_guardar)
        
        if success:
            # Actualizamos el estado de sesión con la nueva versión
            st.session_state.df_comentarios = df_final_para_guardar.copy()
            st.toast("✅ ¡Comentarios guardados y sincronizados!", icon="💬")
            time.sleep(2)
            st.rerun()
        else:
            pass