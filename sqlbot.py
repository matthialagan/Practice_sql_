import streamlit as st
import sqlite3
import pandas as pd
from io import StringIO
import requests
import os

# Load environment variables
HF_API_TOKEN =   # Replace with your actual token or load from .env

HF_MODEL_URL = "https://api-inference.huggingface.co/models/google/gemma-3-270m"

# -------------------- Hugging Face Helper --------------------
def ask_huggingface(prompt):
    """
    Calls Hugging Face Inference API to get help/explanation.
    """
    if not HF_API_TOKEN:
        return "⚠️ Hugging Face API token is missing."

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": prompt}

    try:
        response = requests.post(HF_MODEL_URL, headers=headers, json=payload)
        response.raise_for_status()
        output = response.json()
        # Extract generated_text if present
        if isinstance(output, list) and "generated_text" in output[0]:
            return output[0]["generated_text"]
        return str(output)
    except Exception as e:
        return f"❌ Error calling Hugging Face API: {e}"

# -------------------- SQLite Memory Setup --------------------
conn = sqlite3.connect(":memory:", check_same_thread=False)
cursor = conn.cursor()

# -------------------- Streamlit App --------------------
st.set_page_config(page_title="SQL Practice Agent", layout="wide")
st.title("🗂️ SQL Practice Chatbot")

# Section: Manual DDL input
st.subheader("📌 Enter Small Data (DDL + DML)")
ddl_input = st.text_area("Write SQL (CREATE TABLE, INSERT INTO ...):", height=150)
if st.button("Run DDL/DML"):
    with st.spinner("Executing SQL..."):
        try:
            cursor.executescript(ddl_input)
            conn.commit()
            st.success("✅ Query executed successfully!")
        except Exception as e:
            st.error(f"❌ Error: {e}")

st.divider()

# Section: File Upload
st.subheader("📂 Upload CSV/Excel or Enter Kaggle Dataset ID")
uploaded_file = st.file_uploader("Upload CSV/Excel", type=["csv", "xlsx"])
kaggle_url = st.text_input("Or enter Kaggle Dataset ID (example: zynicide/wine-reviews)")

if uploaded_file:
    with st.spinner("Loading file..."):
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            df.to_sql("uploaded_table", conn, if_exists="replace", index=False)
            st.success("✅ File uploaded and stored in SQLite as 'uploaded_table'")
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")

elif kaggle_url:
    with st.spinner("Fetching Kaggle dataset..."):
        try:
            # Use KaggleHub to download dataset
            import kagglehub
            path = kagglehub.dataset_download(kaggle_url)
            files = os.listdir(path)
            dataset_file = None
            for f in files:
                if f.endswith(".csv") or f.endswith(".xlsx"):
                    dataset_file = os.path.join(path, f)
                    break
            if not dataset_file:
                st.error("❌ No CSV/Excel file found in dataset")
            else:
                if dataset_file.endswith(".csv"):
                    df = pd.read_csv(dataset_file)
                else:
                    df = pd.read_excel(dataset_file)

                df.to_sql("uploaded_table", conn, if_exists="replace", index=False)
                st.success("✅ Kaggle dataset loaded into SQLite as 'uploaded_table'")
                st.dataframe(df.head())
        except Exception as e:
            st.error(f"❌ Error fetching Kaggle dataset: {e}")

st.divider()

# Section: Run SQL Queries
st.subheader("📝 Run SQL Query")
sql_query = st.text_area("Write your SQL SELECT query:", height=120)
if st.button("Run Query"):
    with st.spinner("Running query..."):
        try:
            result = pd.read_sql_query(sql_query, conn)
            st.success("✅ Query executed successfully!")
            st.dataframe(result)
        except Exception as e:
            st.error(f"❌ Query Error: {e}")

st.divider()

# Section: Help Button
st.subheader("🆘 Need Help?")
help_input = st.text_area("Type your question (about SQL, errors, or dataset):", height=100)
if st.button("Get Help from AI"):
    with st.spinner("Contacting Hugging Face..."):
        help_response = ask_huggingface(help_input)
        st.info(help_response)

