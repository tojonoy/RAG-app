
import os
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, ServiceContext
from llama_index.core.embeddings import resolve_embed_model
from llama_index.vector_stores.supabase import SupabaseVectorStore
from supabase import create_client
import uuid
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_API_KEY)

def process_and_store(text):
    doc_id = str(uuid.uuid4())
    filepath = f"temp_{doc_id}.txt"
    with open(filepath, "w") as f:
        f.write(text)

    documents = SimpleDirectoryReader(input_files=[filepath]).load_data()
    embed_model = resolve_embed_model("local:sentence-transformers/all-MiniLM-L6-v2")
    vector_store = SupabaseVectorStore.from_client(supabase, table_name="vectors")
    service_context = ServiceContext.from_defaults(embed_model=embed_model)

    index = VectorStoreIndex.from_documents(documents, service_context=service_context, vector_store=vector_store)
    os.remove(filepath)
    return doc_id

def query_and_respond(query_text, doc_id):
    embed_model = resolve_embed_model("local:sentence-transformers/all-MiniLM-L6-v2")
    vector_store = SupabaseVectorStore.from_client(supabase, table_name="vectors")
    index = VectorStoreIndex.from_vector_store(vector_store)
    retriever = index.as_retriever(similarity_top_k=3)
    context_nodes = retriever.retrieve(query_text)

    context = "\n".join([node.text for node in context_nodes])
    prompt = f"Context:\n{context}\n\nQuestion: {query_text}\nAnswer:"

    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    return response.text.strip()
