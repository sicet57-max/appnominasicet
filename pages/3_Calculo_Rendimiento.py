# --- INICIO DEL GUARDIÁN DE SEGURIDAD ---
import streamlit as st

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("⚠️ Por favor, inicie sesión en la página 'Home' para acceder.")
    st.stop()
# --- FIN DEL GUARDIÁN DE SEGURIDAD ---

# ... (el resto de tu código de la página va aquí) ...
# (ej. import pandas as pd, import google_connector as gc, etc.)

# pages/3_Calculo_Rendimento.py
import streamlit as st
import pandas as pd
import google_connector as gc # Importamos nuestro conector
import time
import numpy as np

# --- 1. Configuración de la Página y Título ---
st.set_page_config(layout="wide")
st.title("🧮 3. Cálculo de Nómina (Mensual)")
st.markdown("Ingrese las variables del mes y ejecute el cálculo **mensual** (Salud, Pensión, ARL, Horas Extra).")

# --- 2. Verificar que todos los datos están cargados ---
if 'df_info' not in st.session_state or 'df_datos_liq' not in st.session_state or \
   'df_ind_empleado' not in st.session_state or 'df_ind_empleador' not in st.session_state or \
   'df_ind_horas' not in st.session_state:
    st.error("Error: Faltan datos maestros para calcular.")
    st.info("Por favor, vaya a la página 'Home' y refresque los datos.")
    st.stop()

# --- 3. Obtener Conexión y Claves ---
client = gc.connect_to_gsheets()
KEY_NOMINA = st.secrets["google_sheets"]["rendimiento_pro_key"]
KEY_INDICADORES = st.secrets["google_sheets"]["calculo_rendimiento_key"] 

# --- 4. Preparación de Datos de ENTRADA (Etapa 1: "Opción 4") ---
st.header("Etapa 1: Ingresar Variables del Mes")

# Limpiamos nombres de columnas
try:
    st.session_state.df_info.columns = [col.strip() if isinstance(col, str) else col for col in st.session_state.df_info.columns]
    st.session_state.df_datos_liq.columns = [col.strip() if isinstance(col, str) else col for col in st.session_state.df_datos_liq.columns]
except Exception as e:
    st.error(f"Error al limpiar nombres de columnas: {e}")
    st.stop()

# 1. Obtenemos la lista MAESTRA de empleados
df_base_empleados = st.session_state.df_info[['Cédula', 'Nombre del técnico']].copy()
df_base_empleados.rename(columns={'Nombre del técnico': 'Nombre completo'}, inplace=True)

# 2. Obtenemos la plantilla de la hoja "Datos liquidación"
df_plantilla_liq = st.session_state.df_datos_liq.copy()

# 3. Sincronizamos la lista de empleados de Página 1 con esta hoja
columnas_liq_completas = [
    'Cédula', 'Nombre completo', 'Salario del trabajador', 'Aux Transporte', 'Días trabajados', 'Días incapacidad', 
    'Horas extras diurna', 'Nocturna ordinaria', 'Extra nocturna', 'Dominical/festiva ordinaria', 
    'Extra diurna dominical/festiva', 'Extra nocturna dominical/festiva', 'Días vacaciones',
    'Prestamos', 'Otros Descuentos', 'Retención en la Fuente'
]

# Definir las columnas a limpiar (todo después de Aux Transporte)
columnas_a_limpiar = [
    'Días trabajados', 'Días incapacidad', 'Horas extras diurna', 'Nocturna ordinaria', 'Extra nocturna', 
    'Dominical/festiva ordinaria', 'Extra diurna dominical/festiva', 'Extra nocturna dominical/festiva', 
    'Días vacaciones', 'Prestamos', 'Otros Descuentos', 'Retención en la Fuente'
]

if not df_plantilla_liq.empty:
    df_para_editar = pd.merge(
        df_base_empleados,
        df_plantilla_liq.drop(columns=['Nombre completo'], errors='ignore'),
        on='Cédula',
        how='left'
    )
else:
    df_plantilla_vacia = pd.DataFrame(columns=columnas_liq_completas)
    df_para_editar = pd.merge(
        df_base_empleados,
        df_plantilla_vacia.drop(columns=['Cédula', 'Nombre completo'], errors='ignore'),
        on='Cédula',
        how='left'
    )

for col in columnas_liq_completas:
    if col not in df_para_editar.columns:
        df_para_editar[col] = 0

# 4. Rellenamos valores nulos (NaN) y convertimos a 0
numeric_cols = df_para_editar.columns.drop(['Cédula', 'Nombre completo'])
# Reemplazar '' (texto vacío) con 0 antes de convertir
df_para_editar[numeric_cols] = df_para_editar[numeric_cols].replace('', 0).fillna(0).astype(float)
df_para_editar = df_para_editar[columnas_liq_completas] 

st.info("Ingrese el salario, días, horas extra, vacaciones y descuentos (Préstamos, ReteFuente, etc.) para el período actual.")

# --- Botón de Limpieza ---
if st.button("Limpiar Variables del Mes (Poner en Cero)", help="Pone en 0 todas las columnas desde 'Días trabajados' en adelante."):
    with st.spinner("Limpiando datos..."):
        # 1. Cargar la hoja de datos de liquidación de la sesión
        df_a_limpiar = st.session_state.df_datos_liq.copy()
        
        # 2. Poner las columnas en 0
        for col in columnas_a_limpiar:
            if col in df_a_limpiar.columns:
                df_a_limpiar[col] = 0
        
        # 3. Guardar la versión limpia de nuevo en la sesión Y en Google Sheets
        st.session_state.df_datos_liq = df_a_limpiar.copy()
        gc.update_sheet(client, KEY_NOMINA, "Datos liquidación", df_a_limpiar)
        
        # 4. Forzar una recarga de la página
        st.toast("¡Campos limpiados!")
        time.sleep(1)
        st.rerun()

edited_df_inputs = st.data_editor(
    df_para_editar,
    use_container_width=True,
    key="editor_datos_liquidacion",
    disabled=['Cédula', 'Nombre completo']
)

# --- 5. Botón de Cálculo (Etapa 2: "Opción 5") ---
st.divider()
st.header("Etapa 2: Ejecutar Cálculo de Nómina Mensual")

# --- Función Robusta para Limpiar Porcentajes ---
def limpiar_pesos(df_indicador):
    df_limpio = df_indicador.copy()
    df_limpio['Peso'] = df_limpio['Peso'].replace('', '0').fillna('0')
    es_porcentaje = df_limpio['Peso'].astype(str).str.contains('%')
    df_limpio['Peso_Limpio'] = df_limpio['Peso'].astype(str).str.replace(r'[%,]', '', regex=True)
    df_limpio['Peso_Limpio'] = pd.to_numeric(df_limpio['Peso_Limpio'], errors='coerce').fillna(0)
    df_limpio.loc[es_porcentaje, 'Peso_Limpio'] = df_limpio.loc[es_porcentaje, 'Peso_Limpio'] / 100
    return df_limpio.set_index('Indicador')['Peso_Limpio']


if st.button("Guardar Variables y Calcular Nómina Mensual", type="primary"):
    
    # --- PASO A: Guardar los datos de entrada ---
    with st.spinner("Paso 1/3: Guardando variables del mes..."):
        df_inputs_guardar = edited_df_inputs.copy()
        df_inputs_guardar.columns = df_inputs_guardar.columns.astype(str)
        success_save_inputs = gc.update_sheet(client, KEY_NOMINA, "Datos liquidación", df_inputs_guardar)
        if not success_save_inputs:
            st.error("Error al guardar las variables de entrada. Cálculo cancelado.")
            st.stop()
        st.session_state.df_datos_liq = df_inputs_guardar.copy()
        st.toast("Variables de entrada guardadas.")
        time.sleep(1)

    # --- PASO B: Iniciar el proceso de cálculo ---
    with st.spinner("Paso 2/3: Realizando cálculos mensuales..."):
        
        df_master = st.session_state.df_info.copy()
        df_calculo = pd.merge(
            df_master,
            edited_df_inputs, # Usamos los datos frescos que acabamos de guardar
            on='Cédula',
            how='left',
            suffixes=('_maestro', '')
        )
        
        cols_numericas = [
            'Salario del trabajador', 'Aux Transporte', 'Días trabajados', 'Días incapacidad', 
            'Horas extras diurna', 'Nocturna ordinaria', 'Extra nocturna', 'Dominical/festiva ordinaria', 
            'Extra diurna dominical/festiva', 'Extra nocturna dominical/festiva', 'Días vacaciones',
            'Prestamos', 'Otros Descuentos', 'Retención en la Fuente'
        ]
        for col in cols_numericas:
             df_calculo[col] = pd.to_numeric(df_calculo[col], errors='coerce').fillna(0)
        
        # --- LÓGICA DE CARGA DE INDICADORES (MODIFICADA) ---
        df_ind_horas_raw = st.session_state.df_ind_horas.copy()
        df_ind_horas_raw['Recargo'] = df_ind_horas_raw['Recargo'].astype(str).str.replace('%', '').fillna('0').astype(float) / 100
        ind_horas = df_ind_horas_raw.set_index('Tipo de hora')['Recargo']

        ind_empleado = limpiar_pesos(st.session_state.df_ind_empleado)
        ind_empleador = limpiar_pesos(st.session_state.df_ind_empleador)
        
        
        # --- LÓGICA DE CÁLCULO (Sin cambios, ahora debería funcionar) ---
        
        # 1. Valor Hora
        df_calculo['Valor_hora_ordinaria'] = (df_calculo['Salario del trabajador'] / 240)
        
        # 2. Horas Extra
        df_calculo['Val_Horas_extras_diurna'] = df_calculo['Horas extras diurna'] * df_calculo['Valor_hora_ordinaria'] * ind_horas['Extra diurna']
        df_calculo['Val_Nocturna_ordinaria'] = df_calculo['Nocturna ordinaria'] * df_calculo['Valor_hora_ordinaria'] * ind_horas['Nocturna ordinaria']
        df_calculo['Val_Extra_nocturna'] = df_calculo['Extra nocturna'] * df_calculo['Valor_hora_ordinaria'] * ind_horas['Extra nocturna']
        df_calculo['Val_Dominical_festiva_ordinaria'] = df_calculo['Dominical/festiva ordinaria'] * df_calculo['Valor_hora_ordinaria'] * ind_horas['Dominical/festiva ordinaria']
        df_calculo['Val_Extra_diurna_dominical_festiva'] = df_calculo['Extra diurna dominical/festiva'] * df_calculo['Valor_hora_ordinaria'] * ind_horas['Extra diurna dominical/festiva']
        df_calculo['Val_Extra_nocturna_dominical_festiva'] = df_calculo['Extra nocturna dominical/festiva'] * df_calculo['Valor_hora_ordinaria'] * ind_horas['Extra nocturna dominical/festiva']
        df_calculo['Total_Horas_Extra'] = df_calculo[['Val_Horas_extras_diurna', 'Val_Nocturna_ordinaria', 'Val_Extra_nocturna', 'Val_Dominical_festiva_ordinaria', 'Val_Extra_diurna_dominical_festiva', 'Val_Extra_nocturna_dominical_festiva']].sum(axis=1)

        # 3. Vacaciones
        df_calculo['Val_Vacaciones'] = (df_calculo['Salario del trabajador'] / 30) * df_calculo['Días vacaciones']

        # 4. IBC (Ingreso Base de Cotización)
        df_calculo['IBC'] = df_calculo['Salario del trabajador']
        
        # 5. Total Devengado
        df_calculo['Total_Devengado'] = df_calculo['Salario del trabajador'] + \
                                       df_calculo['Total_Horas_Extra'] + \
                                       df_calculo['Val_Vacaciones'] + \
                                       df_calculo['Aux Transporte']
        
        # 6. Deducciones (Empleado)
        df_calculo['Aportes a salud'] = df_calculo['IBC'] * ind_empleado['Salud']
        df_calculo['Aportes a pensión'] = df_calculo['IBC'] * ind_empleado['Pensión']
        df_calculo['Total_Deducciones'] = df_calculo['Aportes a salud'] + \
                                         df_calculo['Aportes a pensión'] + \
                                         df_calculo['Prestamos'] + \
                                         df_calculo['Otros Descuentos'] + \
                                         df_calculo['Retención en la Fuente']

        # 7. Salario Neto (Pago al Empleado)
        df_calculo['Salario_Neto'] = df_calculo['Total_Devengado'] - df_calculo['Total_Deducciones']

        # 8. Aportes Empleador
        df_calculo['Aporte_Salud_Empresa'] = df_calculo['IBC'] * ind_empleador['Salud']
        df_calculo['Aporte_Pension_Empresa'] = df_calculo['IBC'] * ind_empleador['Pensión']
        df_calculo['Aporte_ARL'] = df_calculo['IBC'] * ind_empleador['ARL (Riesgos Laborales)']
        df_calculo['Aporte_Caja'] = df_calculo['IBC'] * ind_empleador['Caja de Compensación Familiar']
        df_calculo['Aporte_ICBF'] = df_calculo['IBC'] * ind_empleador['ICBF']
        df_calculo['Aporte_SENA'] = df_calculo['IBC'] * ind_empleador['SENA']
        df_calculo['Total_Aportes_Empresa'] = df_calculo['Aporte_Salud_Empresa'] + \
                                             df_calculo['Aporte_Pension_Empresa'] + \
                                             df_calculo['Aporte_ARL'] + \
                                             df_calculo['Aporte_Caja'] + \
                                             df_calculo['Aporte_ICBF'] + \
                                             df_calculo['Aporte_SENA']

        # 9. Costo Total para la Empresa
        df_calculo['Costo_Total_Empresa'] = df_calculo['Total_Devengado'] + df_calculo['Total_Aportes_Empresa']

        # Guardar tabla completa en sesión para la Etapa 4
        st.session_state.df_calculo_completo = df_calculo.copy()

        st.toast("Cálculos mensuales finalizados.")
        time.sleep(1)

    # --- PASO C: Preparar y Guardar Hojas de Resultados ---
    with st.spinner("Paso 3/3: Guardando resultados en Google Sheets..."):
        
        df_calculo_salida = df_calculo.copy()
        
        # Hoja "Liquidación"
        cols_liquidacion = [
            'Cédula', 'Nombre completo', 'Salario del trabajador', 'Aux Transporte', 'Días incapacidad', 
            'Val_Horas_extras_diurna', 'Val_Nocturna_ordinaria', 'Val_Extra_nocturna', 'Val_Dominical_festiva_ordinaria', 
            'Val_Extra_diurna_dominical_festiva', 'Val_Extra_nocturna_dominical_festiva', 'Val_Vacaciones', 'Total_Devengado'
        ]
        
        # --- LÓGICA CORREGIDA (Línea 234) ---
        # 1. Renombrar la columna en el DataFrame de salida
        df_calculo_salida_liq = df_calculo_salida.rename(columns={'Salario del trabajador': 'Salario_del_mes'})
        # 2. Actualizar la lista de columnas a seleccionar
        cols_liquidacion[2] = 'Salario_del_mes' 
        # 3. Seleccionar las columnas usando la lista actualizada
        df_res_liq = df_calculo_salida_liq[cols_liquidacion]
        
        # Hoja "Descuentos"
        cols_descuentos = ['Cédula', 'Nombre completo', 'Aportes a salud', 'Aportes a pensión', 'Prestamos', 'Otros Descuentos', 'Retención en la Fuente', 'Total_Deducciones']
        df_res_desc = df_calculo_salida[cols_descuentos]

        # Hoja "Aportes" (Empleador)
        cols_aportes = ['Cédula', 'Nombre completo', 'Aporte_Salud_Empresa', 'Aporte_Pension_Empresa', 'Aporte_ARL', 'Aporte_Caja', 'Aporte_ICBF', 'Aporte_SENA', 'Total_Aportes_Empresa']
        df_res_aportes = df_calculo_salida[cols_aportes]
        
        # Hoja "Reporte indi"
        cols_reporte_indi = [
            'Cédula', 'Nombre del técnico', 'Cargo', 'Tipo de contrato', 'Empresa', 'Aux Transporte', 
            'Total_Devengado', 'Total_Deducciones', 'Salario_Neto', 'Costo_Total_Empresa'
        ]
        df_calculo_salida_rep = df_calculo_salida.rename(columns={'Nombre del técnico': 'Nombre'})
        cols_reporte_indi[1] = 'Nombre' 
        df_res_reporte_indi = df_calculo_salida_rep[cols_reporte_indi]
        
        df_res_reporte_indi = df_res_reporte_indi.rename(columns={
            'Aux Transporte': 'Auxilio de transporte',
            'Total_Devengado': 'Total devengado',
            'Total_Deducciones': 'Total Deducciones',
            'Salario_Neto': 'Salario Neto pagado al empleado',
            'Costo_Total_Empresa': 'Total pagado por la empresa'
        })
        
        tareas_guardado = [
            ("Liquidación", df_res_liq),
            ("Descuentos", df_res_desc),
            ("Aportes", df_res_aportes),
            ("Reporte indi", df_res_reporte_indi) 
        ]
        
        exito_total = True
        for hoja, df in tareas_guardado:
            # Asegurarnos de que no haya NaNs antes de guardar
            df_guardar = df.fillna(0)
            df_guardar.columns = df_guardar.columns.astype(str)
            success = gc.update_sheet(client, KEY_NOMINA, hoja, df_guardar)
            if not success:
                st.error(f"Error al guardar la hoja '{hoja}'.")
                exito_total = False
        
        if exito_total:
            st.session_state.df_liquidacion = df_res_liq.copy()
            st.session_state.df_descuentos = df_res_desc.copy()
            st.session_state.df_aportes = df_res_aportes.copy()
            st.session_state.df_reporte_indi = df_res_reporte_indi.copy() 
            
            st.success("✅ ¡Cálculo Mensual completado y guardado con éxito!")
            st.balloons()
        else:
            st.error("Algunas hojas de resultados no pudieron guardarse. Revise los mensajes de error.")

# --- 6. Etapa 3: Ver Resultados (Tablas) ---
st.divider()
st.header("Etapa 3: Ver Resultados (Tablas de Google Sheets)")
st.info("Aquí se muestran los datos de las hojas de resultados. Los datos se actualizan después de ejecutar el cálculo.")

tab1, tab2, tab3, tab4 = st.tabs(["Resultados de Liquidación", "Resultados de Descuentos", "Resultados de Aportes", "Resultados Reporte Individual"])
with tab1:
    st.subheader("Hoja: Liquidación")
    if 'df_liquidacion' in st.session_state and not st.session_state.df_liquidacion.empty:
        st.dataframe(st.session_state.df_liquidacion.fillna(0), use_container_width=True)
    else:
        st.warning("Aún no se han calculado datos de liquidación.")
with tab2:
    st.subheader("Hoja: Descuentos")
    if 'df_descuentos' in st.session_state and not st.session_state.df_descuentos.empty:
        st.dataframe(st.session_state.df_descuentos.fillna(0), use_container_width=True)
    else:
        st.warning("Aún no se han calculado datos de descuentos.")
with tab3:
    st.subheader("Hoja: Aportes (Empleador)")
    if 'df_aportes' in st.session_state and not st.session_state.df_aportes.empty:
        st.dataframe(st.session_state.df_aportes.fillna(0), use_container_width=True)
    else:
        st.warning("Aún no se han calculado datos de aportes.")
with tab4:
    st.subheader("Hoja: Reporte indi")
    if 'df_reporte_indi' in st.session_state and not st.session_state.df_reporte_indi.empty:
        st.dataframe(st.session_state.df_reporte_indi.fillna(0), use_container_width=True)
    else:
        st.warning("Aún no se han calculado datos del Reporte Individual.")


# --- 7. Etapa 4: Resumen Gerencial de Costos ---
st.divider()
st.header("Etapa 4: Resumen Gerencial de Costos 📊")

if 'df_calculo_completo' in st.session_state:
    df_resumen = st.session_state.df_calculo_completo.copy().fillna(0)
    
    st.info("Este resumen muestra el total pagado a los empleados, el costo total para la empresa y los préstamos recuperados este mes.")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_nomina_pagada = df_resumen['Salario_Neto'].sum()
    total_costo_empresa = df_resumen['Costo_Total_Empresa'].sum()
    total_aportes = df_resumen['Total_Aportes_Empresa'].sum()
    total_prestamos_recuperados = df_resumen['Prestamos'].sum() 
    
    col1.metric("Total Pagado a Empleados", f"${total_nomina_pagada:,.0f}")
    col2.metric("Total Costo para SICET", f"${total_costo_empresa:,.0f}")
    col3.metric("Total Pagado a Fondos", f"${total_aportes:,.0f}")
    col4.metric("Total Recuperado (Préstamos)", f"${total_prestamos_recuperados:,.0f}") 
    
    st.subheader("Resumen Detallado por Empleado")
    df_resumen_display = df_resumen[[
        'Nombre completo',
        'Salario_Neto',
        'Prestamos', 
        'Total_Deducciones',
        'Total_Devengado',
        'Total_Aportes_Empresa',
        'Costo_Total_Empresa'
    ]].copy()
    
    # Formatear como moneda
    for col in df_resumen_display.columns.drop('Nombre completo'):
        df_resumen_display[col] = df_resumen_display[col].map('${:,.2f}'.format)
        
    st.dataframe(df_resumen_display, use_container_width=True)
    
else:
    st.warning("Presione el botón 'Calcular Nómina Mensual' para generar el resumen de costos.")