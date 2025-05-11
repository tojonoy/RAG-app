from fastapi import FastAPI, File, UploadFile
from langchain.chat_models import init_chat_model
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from langchain.chains import RetrievalQA
from pprint import pprint
import os
from extract import extract_text_from_pdf
import tempfile
from dotenv import load_dotenv
import getpass
import sys 
import time
import threading
from io import BytesIO
load_dotenv()
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("try2")

embeddings = OllamaEmbeddings(model="llama3")
vector_store = PineconeVectorStore(embedding=embeddings, index=index)

app = FastAPI()

def spinner(stop_event):
    while not stop_event.is_set():
        for c in "|/-\\":
            sys.stdout.write(f"\rAdding to vector store... {c}")
            sys.stdout.flush()
            time.sleep(0.1)
    sys.stdout.write("\rDone adding to vector store.     \n")

def chunk_documents(docs, batch_size=20):
    for i in range(0, len(docs), batch_size):
        yield docs[i:i + batch_size]
@app.get("/")
async def root():
    return {"message": "Welcome to the PDF Upload API"}
@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    pdf_file = await file.read()
    raw_text = extract_text_from_pdf(pdf_file)
    if raw_text is None:
        return {"error": "Failed to extract text from the PDF file."}
    document=Document(page_content=raw_text)
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    splits = splitter.split_documents([document])
    #print(f"doocument lenght: {len(docs)}")
    print(f"Split into {len(splits)} chunks.,")
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=spinner, args=(stop_event,))
    spinner_thread.start()
    #for chunk in chunk_documents(splits, batch_size=20):  # Adjust batch_size as needed
    vector_store.add_documents(splits)
    stop_event.set()
    spinner_thread.join()
    return {"message": "PDF uploaded and processed successfully", "splits_count": len(splits)}

@app.get("/query")
async def query_vector_store(query: str):
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 4})

    rag_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )

    response = rag_chain.invoke(query)

    pprint(response)

    answer = response["result"]
    sources = [doc.metadata.get("source", "N/A") for doc in response["source_documents"]]

    return {"answer": answer}
