# API_DataAnalytics_HR

Este proyecto se encuentra en proceso, pero permite crear tu Primera API de consultas en lenguaje natural a través de AI y un modelo basado en consultas SQL:
 
✅ Check Point: Consulta Inteligente de Datos con IA y SQL 

Este documento resume todos los pasos clave para configurar y ejecutar exitosamente la aplicación que permite realizar consultas en lenguaje natural a una base de datos SQLite usando LM Studio, Meta-Llama-3-8B-Instruct y Streamlit. 

 

1️⃣ Instalaciones Requeridas 

Antes de comenzar, asegúrate de contar con las siguientes herramientas instaladas: 

🔹 1.1 Instalar Python y Dependencias 

🔹 Descargar e instalar Python 3.x: 

 👉 https://www.python.org/downloads/ 

🔹 Crear y activar un entorno virtual (opcional, pero recomendado): 

python -m venv venv 
 # En Windows 
venv\Scripts\activate 
# En Mac/Linux 
source venv/bin/activate 
  

🔹1.2 Instalar dependencias necesarias: 

pip install streamlit pandas sqlite3 requests 
  
✅ 2. Descargar la Base de Datos 

El dataset que utilizaremos en este proyecto es HR Analytics Dataset, disponible en Kaggle. Puedes descargarlo directamente desde este enlace: 🔗 https://www.kaggle.com/datasets/anshika2301/hr-analytics-dataset 

Una vez descargado, guárdalo en la carpeta del proyecto para su posterior uso. 
 

🔹 3 Instalar LM Studio 

LM Studio nos permite ejecutar modelos de IA localmente sin conexión a la nube. 

👉 Descargar desde: 

 https://lmstudio.ai 

1️⃣ Instalar y abrir LM Studio. 

 2️⃣ Ir a la pestaña "Model Search". 

 3️⃣ Buscar el modelo meta-llama-3-8b-instruct. 

 4️⃣ Descargar la versión Q4_K_M (balance entre rendimiento y precisión). 

 5️⃣ Cargar el modelo en LM Studio y activar el servidor local. 

 6️⃣ Verificar que el servidor está activo visitando: 

ej: "http://127.0.0.1:1234/v1/models" 
  

Si ves meta-llama-3-8b-instruct, ¡todo está correcto! ✅ 

 

2️⃣ Preparación de la Base de Datos 

🔹 3.1 Cargar el archivo CSV 

El archivo de datos debe estar en formato CSV. 

 Asegúrate de tenerlo en la ruta correcta: 

C:\Users\magal\Projects\PromptEng\HR_Analytics.csv 
  

🔹 3.2 Creación de la Base de Datos SQLite 

El código se encarga automáticamente de convertir el CSV en una tabla SQLite llamada hr_data. 

🔹 La base de datos se crea en: 

hr_analytics.db 
  

Para verificar que la base de datos se ha generado correctamente, puedes usar: 

sqlite3 hr_analytics.db 
 SELECT * FROM hr_data LIMIT 5; 
  

 

3️⃣ Código de la Aplicación 

Aquí tienes el código completo y optimizado para ejecutar la aplicación en Streamlit. (Ya probado y funcional) 

import requests 
import pandas as pd 
import sqlite3 
import streamlit as st 
import re 
import time 
 
# 🚀 PRIMER COMANDO STREAMLIT (Debe ir primero) 🚀 
st.set_page_config(page_title="🔍 AI SQL Query", layout="wide") 
 
# ---- CONFIGURACIÓN ---- 
CSV_FILE = r"C:\Users\magal\Projects\PromptEng\HR_Analytics.csv" 
DB_FILE = "hr_analytics.db" 
LM_STUDIO_API = "http://localhost:1234/v1/completions" 
MODEL_NAME = "meta-llama-3-8b-instruct:2" 
 
# ---- CARGAR CSV Y ANALIZAR COLUMNAS ---- 
@st.cache_data 
def load_and_prepare_data(): 
    df = pd.read_csv(CSV_FILE) 
    df.columns = df.columns.str.lower().str.replace(" ", "_").str.replace("-", "_") 
    df = df.astype(str).fillna("") 
     
    conn = sqlite3.connect(DB_FILE) 
    df.to_sql("hr_data", conn, if_exists="replace", index=False) 
    conn.close() 
    return df 
 
df = load_and_prepare_data() 
 
# ---- OBTENER COLUMNAS REALES DE LA BASE DE DATOS ---- 
def get_real_columns(): 
    conn = sqlite3.connect(DB_FILE) 
    cursor = conn.cursor() 
    cursor.execute("PRAGMA table_info(hr_data);") 
    columns = {col[1]: col[2] for col in cursor.fetchall()} 
    conn.close() 
    return columns 
 
REAL_COLUMNS = get_real_columns() 
 
# ---- FUNCIÓN PARA EXTRAER SOLO SQL DE LA RESPUESTA ---- 
def extract_sql(response_text): 
    sql_match = re.search(r"```sql\n(.*?)\n```", response_text, re.DOTALL) 
    if sql_match: 
        return sql_match.group(1).strip() 
    return response_text.strip() 
 
# ---- FUNCIÓN PARA CONSULTAS ---- 
def query_ai(natural_language_query): 
    prompt = f""" 
    Eres un asistente experto en SQL. Convierte la siguiente consulta en lenguaje natural a SQL para SQLite. 
 
    🔹 **Instrucciones**: 
    - Devuelve **únicamente** la consulta SQL, sin explicaciones ni texto adicional. 
    - Usa la tabla `hr_data` de la base de datos `hr_analytics.db`. 
    - **No inventes columnas**, usa solo estas: {', '.join(REAL_COLUMNS.keys())}. 
    - Responde siempre en español. 
 
    🔹 **Consulta a convertir**: 
    "{natural_language_query}" 
    """ 
 
    payload = { 
        "model": MODEL_NAME, 
        "prompt": prompt, 
        "temperature": 0, 
        "max_tokens": 150 
    } 
 
    try: 
        response = requests.post(LM_STUDIO_API, json=payload) 
        if response.status_code == 200: 
            sql_query = response.json().get("choices", [{}])[0].get("text", "").strip() 
            sql_query = extract_sql(sql_query) 
 
            if not sql_query.lower().startswith("select"): 
                return "Error: La consulta generada no es válida." 
 
            conn = sqlite3.connect(DB_FILE) 
            result = pd.read_sql(sql_query, conn) 
            conn.close() 
            return result 
        else: 
            return f"Error en LM Studio: {response.text}" 
    except Exception as e: 
        return f"Error ejecutando la consulta: {e}" 
 
# ---- INTERFAZ STREAMLIT ---- 
st.title("🔍 Consulta Inteligente de Datos con IA y SQL") 
st.write("Realiza consultas en lenguaje natural y obtén respuestas desde la base de datos SQLite.") 
 
# ---- HISTORIAL DE CONSULTAS ---- 
if "query_history" not in st.session_state: 
    st.session_state.query_history = [] 
 
user_query = st.text_input("Escribe tu consulta en lenguaje natural:") 
 
if st.button("Consultar"): 
    if user_query: 
        result = query_ai(user_query) 
 
        if isinstance(result, pd.DataFrame) and not result.empty: 
            st.success("✅ Consulta ejecutada correctamente.") 
            st.dataframe(result) 
 
            st.session_state.query_history.append(user_query) 
 
            if "department" in result.columns and "total" in result.columns: 
                st.bar_chart(result.set_index("department")["total"]) 
 
            csv_data = result.to_csv(index=False).encode("utf-8") 
            st.download_button("⬇️ Descargar resultados en CSV", csv_data, "consulta_resultado.csv", "text/csv") 
 
        else: 
            st.error("⚠️ No se encontraron resultados o la consulta no es válida.") 
 
st.subheader("📜 Historial de Consultas") 
if st.session_state.query_history: 
    for query in st.session_state.query_history[::-1]: 
        st.write(f"🔹 {query}") 
 
if st.button("❌ Cerrar Aplicación"): 
    st.write("Cerrando la aplicación... 🚪") 
    time.sleep(2) 
    st.stop() 
  

 

4️⃣ Ejecutar la Aplicación 

Abre la terminal y corre el siguiente comando: 

streamlit run hr_analytics_ai.py 
  

 
Continuará...
 
