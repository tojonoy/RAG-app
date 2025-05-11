import streamlit as st
import requests

UPLOAD_URL = "http://127.0.0.1:8000/upload_pdf"
QUERY_URL = "http://127.0.0.1:8000/query"
st.title("PDF Upload and Query API")
st.header("Upload PDF")
uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
if uploaded_file is not None:
    st.write(f"Uploaded file: {uploaded_file.name}")
    if st.button("Upload and Process PDF"):
        files = {"file": uploaded_file.getvalue()}
        response = requests.post(UPLOAD_URL, files=files)
        if response.status_code == 200:
            st.success("PDF uploaded and processed successfully!")
            splits_count = response.json().get("splits_count", 0)
            st.write(f"PDF split into {splits_count} chunks.")
        else:
            st.error("Error uploading PDF: " + response.text)

st.header("Query Vector Store")
query = st.text_input("Enter your query:")
if query:
    if st.button("Submit Query"):
        params = {"query": query}
        response = requests.get(QUERY_URL, params=params)
        if response.status_code == 200:
            result = response.json()
            answer = result.get("answer", "No answer found.")
            sources = result.get("sources", [])
            st.subheader("Answer")
            st.write(answer)
        else:
            st.error("Error querying vector store: " + response.text)
