import requests
import pandas as pd
import sqlite3
import streamlit as st
import re
import time

# 🚀 🔹 PRIMER COMANDO STREAMLIT (Debe ir primero) 🔹 🚀
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
    """
    Convierte lenguaje natural en SQL usando LM Studio y ejecuta la consulta en SQLite.
    """
    prompt = f"""
    Eres un asistente experto en SQL. Convierte la siguiente consulta en lenguaje natural a SQL para SQLite.

    🔹 **Instrucciones**:
    - Devuelve **únicamente** la consulta SQL, sin explicaciones ni texto adicional.
    - Usa la tabla `hr_data` de la base de datos `hr_analytics.db`.
    - **No inventes columnas**, usa solo estas: {', '.join(REAL_COLUMNS.keys())}.
    - Responde siempre en español.

    🔹 **Ejemplo**:
    - **Entrada**: "¿Cuál es el departamento con más empleados?"
    - **Salida esperada**:
    ```sql
    SELECT department, COUNT(*) as total 
    FROM hr_data 
    GROUP BY department 
    ORDER BY total DESC 
    LIMIT 1;
    ```

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
st.markdown(
    """
    <style>
    .main {
        background-color: #111;
        color: white;
        text-align: center;
    }
    .stButton>button {
        background-color: #FF4B4B;
        color: white;
        font-size: 18px;
        border-radius: 8px;
        padding: 10px;
    }
    .stTextInput>div>div>input {
        font-size: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🔍 Consulta Inteligente de Datos con IA y SQL")
st.write("Realiza consultas en lenguaje natural y obtén respuestas desde la base de datos SQLite.")

# ---- HISTORIAL DE CONSULTAS ----
if "query_history" not in st.session_state:
    st.session_state.query_history = []

# ---- INPUT DEL USUARIO ----
user_query = st.text_input("Escribe tu consulta en lenguaje natural:", key="query_input")

# ---- PROCESAR CONSULTA ----
if st.button("Consultar"):
    if user_query:
        result = query_ai(user_query)

        if isinstance(result, pd.DataFrame) and not result.empty:
            st.success("✅ Consulta ejecutada correctamente.")
            st.write("🔹 **Resultado de la consulta:**")
            st.dataframe(result)

            # Agregar consulta al historial
            st.session_state.query_history.append(user_query)

            # Mostrar gráfico de barras si hay datos adecuados
            if "department" in result.columns and "total" in result.columns:
                st.bar_chart(result.set_index("department")["total"])

            # Opción para exportar a CSV
            csv_data = result.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Descargar resultados en CSV",
                data=csv_data,
                file_name="consulta_resultado.csv",
                mime="text/csv",
            )

        else:
            st.error("⚠️ No se encontraron resultados o la consulta no es válida.")
    else:
        st.warning("⚠️ Ingresa una pregunta antes de consultar.")

# ---- MOSTRAR HISTORIAL DE CONSULTAS ----
st.subheader("📜 Historial de Consultas")
if st.session_state.query_history:
    for query in st.session_state.query_history[::-1]:  # Mostrar últimas primero
        st.write(f"🔹 {query}")

# ---- BOTÓN PARA CERRAR APP ----
if st.button("❌ Cerrar Aplicación"):
    st.write("Cerrando la aplicación... 🚪")
    time.sleep(2)
    st.stop()
