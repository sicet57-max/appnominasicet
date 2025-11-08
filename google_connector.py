# google_connector.py
import streamlit as st
import gspread
import pandas as pd
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials

# --- CONFIGURACIÓN DE ACCESO A GOOGLE SHEETS ---
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

@st.cache_resource
def connect_to_gsheets():
    """
    Conecta con Google Sheets usando las credenciales de st.secrets.
    """
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        st.stop()

# --- Versión de Carga Robusta ---
@st.cache_data(ttl=600) # Cache por 10 minutos
def load_data(_client, sheet_key, sheet_name):
    """
    Carga una hoja específica de Google Sheets en un DataFrame de Pandas.
    Usa .get_all_values() para cargar todo como TEXTO.
    """
    try:
        spreadsheet = _client.open_by_key(sheet_key) 
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # Le pedimos a Google los números "crudos" (UNFORMATTED_VALUE)
        data = worksheet.get_all_values(value_render_option='UNFORMATTED_VALUE') 
        
        if not data:
            return pd.DataFrame() # Hoja vacía
            
        # Usa la Fila 1 como cabeceras, y el resto como datos
        df = pd.DataFrame(data[1:], columns=data[0])
            
        return df
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Error: No se encontró la hoja de cálculo con la KEY: {sheet_key}")
        return pd.DataFrame()
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Error: No se encontró la hoja (tab) '{sheet_name}' en el archivo.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al cargar datos de '{sheet_name}': {e}")
        return pd.DataFrame()

def update_sheet(_client, sheet_key, sheet_name, df):
    """
    Actualiza (SOBREESCRIBE) una hoja de Google Sheets con un DataFrame.
    """
    try:
        if df.empty:
            st.error("⚠️ GUARDADO BLOQUEADO: Se intentó guardar una tabla vacía.")
            st.info("Esto es una medida de seguridad para prevenir la pérdida de datos.")
            return False 

        spreadsheet = _client.open_by_key(sheet_key)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        worksheet.clear()
        set_with_dataframe(worksheet, df) 
        
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error al actualizar la hoja '{sheet_name}': {e}")
        return False

# --- ¡NUEVA FUNCIÓN PARA EL HISTORIAL! ---
def append_row(_client, sheet_key, sheet_name, row_data_list):
    """
    AÑADE una sola fila de datos al final de una hoja de Google Sheets.
    'row_data_list' debe ser una lista, ej: ['Enero', 10, 20000]
    """
    try:
        spreadsheet = _client.open_by_key(sheet_key)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # --- LÍNEA MODIFICADA (LA SOLUCIÓN) ---
        # Añadimos 'value_input_option='USER_ENTERED'' para forzar
        # a Google Sheets a interpretar "enero 2024" como texto.
        worksheet.append_row(row_data_list, value_input_option='USER_ENTERED')
        
        # Limpia el cache de 'load_data' para que la próxima lectura vea la nueva fila
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error al AÑADIR fila en la hoja '{sheet_name}': {e}")
        return False