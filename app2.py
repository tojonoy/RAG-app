from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from pgvector.sqlalchemy import Vector
from flasgger import Swagger,swag_from
from llama_index.core import VectorStoreIndex, Document
from llama_index.vector_stores.supabase import SupabaseVectorStore
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response.pprint_utils import pprint_response
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core import Settings
from sqlalchemy import create_engine,text
import os
from extract import extract_text_from_pdf, extract_text_from_scanned_pdf
from dotenv import load_dotenv
from supabase import create_client, Client
import uuid

SUPABASE_URL = "https://spnkhaynovvwuxbreywk.supabase.co"
SUPABASE_serv_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNwbmtoYXlub3Z2d3V4YnJleXdrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Njk1MDU0MCwiZXhwIjoyMDYyNTI2NTQwfQ.oXC_2Wur3043cGpdm59EtGSnku-7fC1GMdl_IuxL8sU"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_serv_KEY)
load_dotenv()

db = SQLAlchemy()
app = Flask(__name__)
Swagger(app)  # Initialize Swagger

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SUPA_DBASE_URL")
SUPABASE_DB_URL = os.getenv("SUPA_DBASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

llm = GoogleGenAI(model="models/gemini-1.5-flash", api_key=GOOGLE_API_KEY)
embed_model = GoogleGenAIEmbedding(model_name="models/embedding-001",api_key=GOOGLE_API_KEY)

vector_store = SupabaseVectorStore(
    supabase_url=SUPABASE_URL,
    supabase_key=SUPABASE_KEY,
    postgres_connection_string="postgresql://postgres.spnkhaynovvwuxbreywk:thomasjohn@aws-0-ap-south-1.pooler.supabase.com:6543/postgres",  # New required param
    collection_name="vectors",
)
index= ''
Settings.llm = llm
Settings.embed_model = embed_model
text=""
@app.route("/upload", methods=["POST"])
@swag_from({
    'tags': ['PDF Upload'],
    'consumes': ['multipart/form-data'],
    'parameters': [
        {
            'name': 'pdf',
            'in': 'formData',
            'type': 'file',
            'required': True,
            'description': 'Upload a PDF file'
        }
    ],
    'responses': {
        200: {
            'description': 'Document processed and index created successfully'
        },
        400: {
            'description': 'Invalid PDF or no text found'
        },
        500: {
            'description': 'Server error while creating index'
        }
    }
})
def upload():
    global text
    file = request.files["pdf"]
    pdf_bytes = file.read()

    if not file.filename.endswith(".pdf"):
        return jsonify({"error": "File is not a PDF"}), 400

    # Extract text from PDF
    text = extract_text_from_pdf(pdf_bytes)
    if not text.strip():
        text = extract_text_from_scanned_pdf(pdf_bytes)

    if not text.strip():
        return jsonify({"error": "No text found in the PDF"}), 400
    print(text)
    print(f"vector_store: {vector_store}")
    print(f"embed_model: {embed_model}")

    # Create documents and index
    documents = [Document(text=text)]
    try:
        index = VectorStoreIndex.from_documents(
            documents, vector_store=vector_store, embed_model=embed_model, show_progress=True
        )
        print(f"Returned type of oindex: {type(index)}")
        print(index)
        data = {
          "text": text
        }
        response = supabase.table("just").insert(data).execute()
        print(response)
    except Exception as e:
        print(f"Error creating index: {e}")
        return jsonify({"error": "Error creating index"}), 500

    return jsonify({"message": "Document processed and index created successfully"}), 200

@app.route("/query", methods=["POST"])
@swag_from({
    'tags': ['Query'],
    'parameters': [
        {
            'name': 'query',
            'in': 'body',
            'schema': {
                'type': 'object',
                'properties': {
                    'query': {
                        'type': 'string',
                        'example': 'What is the summary of this document?'
                    }
                },
                'required': ['query']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Query successfully processed',
            'schema': {
                'type': 'object',
                'properties': {
                    'answer': {'type': 'string'}
                }
            }
        },
        500: {
            'description': 'Error processing query'
        }
    }
})
def query():
    data = request.json
    query_text = data.get("query")
    try:
        #index= VectorStoreIndex.from_vector_store( vector_store=vector_store, embed_model=embed_model)
        response = supabase.table("just").select("*").execute()
        documents = [Document(text=row["text"]) for row in response.data]

        index = VectorStoreIndex.from_documents(
            documents, vector_store=vector_store, embed_model=embed_model, show_progress=True
        )
        print(index)
        retriever = VectorIndexRetriever(index=index, similarity_top_k=4)
        postprocessor = SimilarityPostprocessor(similarity_cutoff=0.4)

        query_engine = RetrieverQueryEngine.from_args(retriever=retriever, node_postprocessors=[postprocessor],response_mode="tree_summarize")
        response = query_engine.query(query_text)

        pprint_response(response, show_source=True)
        print(dir(response))
        print(response.response) 
        answer = response.response
        return jsonify({"answer": answer}), 200
    except Exception as e:
        print(f"Error processing query: {e}")
        return jsonify({"error": "Error processing query"}), 500

if __name__ == "__main__":
    app.run(debug=True)
