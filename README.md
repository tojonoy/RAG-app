
# PDF-based RAG System using FastAPI and Streamlit

This project implements a Retrieval-Augmented Generation (RAG) system where users can upload PDFs, process them, and query content using a user-friendly interface powered by Streamlit and FastAPI.

## 🚀 Getting Started

### Note to use llama3 model locally for the working of the app
### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
````

### 2. Install Dependencies

First check for the virtual environment is activated or not, then run:

```bash
pip install -r requirements.txt
```

### 3. Start the FastAPI Backend

```bash
uvicorn app:app --reload
```

FastAPI will be available at:
[http://127.0.0.1:8000](http://127.0.0.1:8000)
Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 4. Start the Streamlit Frontend

In a new terminal window/tab (but same environment):

```bash
streamlit run stream.py
```



### 5. Access the Streamlit App

Streamlit will display the running app's URL in the terminal, typically:

[http://localhost:8501](http://localhost:8501)

