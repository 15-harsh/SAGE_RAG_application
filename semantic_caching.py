# semantic_cache.py

import uuid
from langchain_core.documents import Document

from user_auth import get_db_connection
from chunking_embedding import semantic_retriever


# Load Chroma once
semantic_vector_store = semantic_retriever()


# ===============================
# Utility DB helpers
# ===============================

def execute_query(query, params=None):
    """Execute INSERT, UPDATE, DELETE queries"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()


def fetch_one(query, params=None):
    """Fetch a single row from database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        return cursor.fetchone()


# ===============================
# Cache ↔ Chat History
# ===============================

def save_cache_to_chat_history(cache_id, question_id):
    query = """
        UPDATE chat_history
        SET cache_id = ?
        WHERE question_id = ?
    """
    execute_query(query, (cache_id, question_id))


def get_from_chat_history(cache_id):
    if not cache_id:
        return None

    query = """
        SELECT answer, sources, confidence, cache_id, accepted, edited_answer
        FROM chat_history
        WHERE cache_id = ?
    """

    result = fetch_one(query, (cache_id,))

    if not result:
        return None

    return {
        "answer": result[0],
        "sources": result[1],
        "confidence": result[2],
        "cache_id": result[3],
        "accepted": result[4],
        "edited_answer": result[5]
    }


# ===============================
# Chroma: Store
# ===============================

def store_in_chroma(question, cache_id):
    doc = Document(
        page_content=question,
        metadata={"cache_id": cache_id}
    )
    semantic_vector_store.add_documents([doc])


# ===============================
# Chroma: Search
# ===============================

def search_cache(question, threshold=0.60):
    results = semantic_vector_store.similarity_search_with_score(
        question, k=1
    )

    if not results:
        return None

    doc, score = results[0]
    similarity = 1 - score

    if similarity < threshold:
        return None

    return str(doc.metadata.get("cache_id"))


# ===============================
# Cache ID
# ===============================

def generate_cache_id():
    return str(uuid.uuid4())