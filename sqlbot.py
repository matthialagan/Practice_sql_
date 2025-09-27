import streamlit as st
import sqlite3
import pandas as pd
from io import StringIO
import requests
from kaggle.api.kaggle_api_extended import KaggleApi

# -------------------- Hugging Face Helper --------------------
HF_API_TOKEN = "hf_your_token_here"  # 🔹 Replace with your token
HF_MODEL_URL = "https://api-inference.huggingface.co/models/google/gemma-3-270m"

def ask_huggingface(prompt):
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": prompt}
    try:
        response = requests.post(HF_MODEL_URL, headers=headers, json=payload)
        response.raise_for_status()
        output = response.json()
        if isinstance(output, list) and "generated_text" in output[0]:
            return output[0]["generated_text"]
        return str(output)
    except Exception as e:
        return f"❌ Error calling Hugging Face API: {e}"


# -------------------- SQLite Setup --------------------
conn = sqlite3.connect(":memory:", check_same_thread=False)
cursor = conn.cursor()


# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="SQL Practice Agent", layout="wide")
st.title("🗂️ SQL Practice Chatbot with Hugging Face & Kaggle")

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
st.subheader("📂 Upload CSV/Excel")
uploaded_file = st.file_uploader("Upload CSV/Excel", type=["csv", "xlsx"])

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

st.divider()

# Section: Kaggle Dataset
st.subheader("📥 Load Dataset from Kaggle")
kaggle_url = st.text_input("Enter Kaggle Dataset URL (example: https://www.kaggle.com/datasets/anninasimon/employee-salary-dataset)")

if st.button("Load Kaggle Dataset"):
    with st.spinner("Downloading from Kaggle..."):
        try:
            dataset_ref = kaggle_url.split("datasets/")[-1]

            api = KaggleApi()
            api.authenticate()

            api.dataset_download_files(dataset_ref, path=".", unzip=True)

            # Try loading first CSV file
            import glob
            files = glob.glob("*.csv")
            if files:
                df = pd.read_csv(files[0])
                df.to_sql("kaggle_table", conn, if_exists="replace", index=False)
                st.success(f"✅ Kaggle dataset '{files[0]}' loaded into SQLite as 'kaggle_table'")
                st.dataframe(df.head())
            else:
                st.error("❌ No CSV file found in Kaggle dataset.")
        except Exception as e:
            st.error(f"❌ Kaggle Load Error: {e}")

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
st.subheader("🆘 Need Help? (Gemma-3-270m)")
help_input = st.text_area("Type your question (about SQL, errors, or dataset):", height=100)
if st.button("Get Help from AI"):
    with st.spinner("Contacting Hugging Face Gemma-3-270m..."):
        help_response = ask_huggingface(help_input)
        st.info(help_response)

