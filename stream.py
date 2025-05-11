import streamlit as st
import requests

# FastAPI URLs for PDF upload and querying
UPLOAD_URL = "http://127.0.0.1:8000/upload_pdf"
QUERY_URL = "http://127.0.0.1:8000/query"

# Title of the Streamlit app
st.title("PDF Upload and Query API")

# File upload section
st.header("Upload PDF")
uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

# If the user uploads a file
if uploaded_file is not None:
    # Show the filename of the uploaded PDF
    st.write(f"Uploaded file: {uploaded_file.name}")

    # Upload PDF to FastAPI backend
    if st.button("Upload and Process PDF"):
        files = {"file": uploaded_file.getvalue()}
        
        # Call FastAPI's PDF upload endpoint
        response = requests.post(UPLOAD_URL, files=files)
        
        if response.status_code == 200:
            st.success("PDF uploaded and processed successfully!")
            splits_count = response.json().get("splits_count", 0)
            st.write(f"PDF split into {splits_count} chunks.")
        else:
            st.error("Error uploading PDF: " + response.text)

# Query section
st.header("Query Vector Store")
query = st.text_input("Enter your query:")

# If the user submits a query
if query:
    if st.button("Submit Query"):
        # Send the query to FastAPI's query endpoint
        params = {"query": query}
        response = requests.get(QUERY_URL, params=params)
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("answer", "No answer found.")
            sources = result.get("sources", [])

            # Display answer and sources
            st.subheader("Answer")
            st.write(answer)
        else:
            st.error("Error querying vector store: " + response.text)
