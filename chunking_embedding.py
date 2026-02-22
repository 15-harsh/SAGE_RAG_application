from langchain_text_splitters import RecursiveCharacterTextSplitter
from transformers import AutoTokenizer
from langchain_chroma import Chroma 
from langchain_huggingface import HuggingFaceEmbeddings
import os 


CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR")
CHROMA_PERSIST_DIR_FOR_CACHE = os.getenv("CHROMA_PERSIST_DIR_FOR_CACHE")

tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-small-en-v1.5')
embedding_model = HuggingFaceEmbeddings(model_name='BAAI/bge-small-en-v1.5') 

def chunking(docs):
    text_splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
            tokenizer = tokenizer,
            chunk_size = 500,
            chunk_overlap = 50,
        )
        
    chunks = text_splitter.split_documents(docs)
    
    return chunks


def create_vector_store(chunks):
    vector_store = Chroma.from_documents(
        documents = chunks,
        embedding = embedding_model,
        persist_directory="vector_db",
        collection_metadata={"hnsw:space": "cosine"} 
    )
    
    return vector_store


def retriever_function():
    
    vector_store = Chroma(
        persist_directory= CHROMA_PERSIST_DIR,
        embedding_function=embedding_model,
        collection_metadata={"hnsw:space": "cosine"}  
    )
    
    return vector_store


def semantic_retriever():
    
    semantic_vector_store = Chroma(
    persist_directory=CHROMA_PERSIST_DIR_FOR_CACHE,
    embedding_function = embedding_model
    )
    
    return semantic_vector_store

