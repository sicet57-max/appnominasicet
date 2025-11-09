# Home.py
import streamlit as st
import google_connector as gc # Importamos nuestro conector
import pandas as pd

# --- 1. Configuración de la Página ---
st.set_page_config(
    page_title="SICET - Gestión de Nómina",
    page_icon="assets/logo_sicet.png",
    layout="wide" # Usamos 'wide' por defecto
)

# --- 2. Función de Carga de Datos ---
def load_all_data(client):
    """Carga todos los DataFrames necesarios en st.session_state."""
    try:
        KEY_NOMINA = st.secrets["google_sheets"]["rendimiento_pro_key"]
        KEY_INDICADORES = st.secrets["google_sheets"]["calculo_rendimiento_key"]
    except KeyError:
        st.error("Error: No se encontraron las 'keys' de Google Sheets en 'secrets.toml'.")
        st.stop()
    
    # Lista de todas las hojas a cargar
    hojas_nomina = {
        "df_info": "Informacion",
        "df_comentarios": "comentarios",
        "df_datos_liq": "Datos liquidación",
        "df_liquidacion": "Liquidación",
        "df_descuentos": "Descuentos",
        "df_aportes": "Aportes",
        "df_especial_res": "Especial",
        "df_reporte_indi": "Reporte indi",
        "df_reporte_mensual": "Reporte mensual"
    }
    
    hojas_indicadores = {
        "df_ind_empleado": "Empleado",
        "df_ind_empleador": "Empleador",
        "df_ind_especial": "Especial",
        "df_ind_horas": "Horas extra"
    }
    
    with st.spinner("Cargando datos maestros..."):
        all_loaded = True
        for df_name, sheet_name in hojas_nomina.items():
            st.session_state[df_name] = gc.load_data(client, KEY_NOMINA, sheet_name)
            if st.session_state[df_name] is None: all_loaded = False
        
        for df_name, sheet_name in hojas_indicadores.items():
            st.session_state[df_name] = gc.load_data(client, KEY_INDICADORES, sheet_name)
            if st.session_state[df_name] is None: all_loaded = False
    
    if all_loaded:
        st.success("¡Datos cargados con éxito!")
    else:
        st.warning("Algunas hojas de datos no se pudieron cargar. Revise los errores.")
        
    return all_loaded

# --- 3. Lógica de Login ---

# Inicializar el estado de sesión para 'logged_in' si no existe
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Función de "callback" para el botón de login
def set_login_true():
    # Validar credenciales
    if (
        st.session_state["username"] == st.secrets["credentials"]["username"] and
        st.session_state["password"] == st.secrets["credentials"]["password"]
    ):
        st.session_state.logged_in = True
    else:
        st.error("Usuario o contraseña incorrectos.")
        st.session_state.logged_in = False # Asegurarse de que siga siendo Falso

# Función de "callback" para el botón de logout
def set_login_false():
    st.session_state.logged_in = False
    # Limpiar todos los datos cargados de la sesión
    for key in list(st.session_state.keys()):
        if key not in ['logged_in']:
            del st.session_state[key]

# --- 4. Mostrar Contenido ---

# Si el usuario NO está logueado, mostrar el formulario
if not st.session_state.logged_in:
    # Asegurar layout centrado para el login
    st.set_page_config(layout="centered") 
    
    st.image("assets/logo_sicet.png", width=150)
    st.title("Gestión de Nómina SICET")
    st.header("Inicio de Sesión")
    
    with st.form(key="login_form"):
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password")
        st.form_submit_button("Iniciar Sesión", on_click=set_login_true)

# Si el usuario SÍ está logueado, mostrar la app normal
else:
    # Asegurar layout ancho para la app
    st.set_page_config(layout="wide")
    
    # --- Branding y Barra Lateral ---
    st.sidebar.image("assets/logo_sicet.png", width=200)
    st.sidebar.title("SICET INGENIERÍA")
    st.sidebar.header("Gestión de Nómina")
    
    # Botón de Logout
    st.sidebar.button("Cerrar Sesión", on_click=set_login_false)
    
    # --- Cargar datos si no están cargados ---
    client = gc.connect_to_gsheets()
    if 'df_info' not in st.session_state:
        load_all_data(client)
    
    # Botón de Refrescar
    if st.sidebar.button("Refrescar Datos de Google Sheets"):
        st.cache_data.clear() # Limpia el cache
        load_all_data(client) # Vuelve a cargar todo
        st.rerun()

    # --- (REQ 1) Indicador de Conexión General ---
    st.sidebar.divider()
    if 'df_info' in st.session_state and not st.session_state.df_info.empty:
        st.sidebar.success("✅ Conexión: Activa")
    else:
        st.sidebar.error("❌ Conexión: Fallida")
    
    
    # --- (REQ 2) Saludo Profesional ---
    st.title("Plataforma de Gestión de Nómina")
    st.header("Bienvenido al sistema de SICET INGENIERÍA")
    st.markdown("Esta aplicación centraliza el cálculo, gestión y análisis de la nómina de la compañía.")

    st.divider()

    # --- (REQ 3) Descripción de Opciones ---
    st.subheader("Navegación de la Aplicación")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 👤 Datos Personales")
        st.markdown("Gestione la base de datos de empleados (crear, editar, eliminar).")
        
        st.markdown("#### 💬 Comentarios")
        st.markdown("Añada y edite comentarios de desempeño para cada empleado.")
        
        # --- LÍNEA CORREGIDA ---
        st.markdown("#### 🧮 Cálculo Rendimiento")
        st.markdown("El motor principal. Ingrese variables (horas, días) y calcule la nómina mensual.")

        st.markdown("#### ✨ Cálculo Prestaciones")
        st.markdown("Calcule las prestaciones semestrales/anuales (Cesantías, Primas, Vacaciones).")

    with col2:
        st.markdown("#### 🗓️ Reporte Mensual")
        st.markdown("Vea y guarde el historial de totales de la nómina (costos, pagos) mes a mes.")

        st.markdown("#### 📈 Visualización General")
        st.markdown("Dashboard gerencial con gráficos de costos por empleado, empresa y cargo.")

        st.markdown("#### ⚙️ Administrar Indicadores")
        st.markdown("Panel de control para modificar porcentajes (Salud, ARL) y valores de cálculo.")

        st.markdown("#### 🔖 Ficha Empleado")
        st.markdown("Vea la 'Ficha 360' con toda la información de un solo empleado.")

    st.divider()

    # --- (REQ 4) Agradecimiento ---
    st.info("""
    **Un agradecimiento especial a SICET INGENIERÍA por la oportunidad de desarrollar esta herramienta.**
    
    Esperamos que disfrute la eficiencia y precisión que esta plataforma puede ofrecer.
    """)