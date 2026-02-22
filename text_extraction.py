from langchain_community.document_loaders import PyMuPDFLoader
import hashlib
from flask_login import current_user
from user_auth import get_db_connection
import re
import os


def clean_extraction(text):
    text = re.sub(r'-\s+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def text_extraction(file_path):
    pdf_name = os.path.basename(file_path)

    loader = PyMuPDFLoader(file_path)
    docs = loader.load()

    for doc in docs:
        doc.page_content = clean_extraction(doc.page_content)
    
    return pdf_name, docs


def save_to_db(pdf_name, docs):
    
    hasher = hashlib.sha256()
    for doc in docs:
        hasher.update(doc.page_content.encode("utf-8"))

    metadata_hash = hasher.hexdigest()

    with get_db_connection() as conn:
        
        cursor = conn.cursor()

        cursor.execute("""
            SELECT pdf_id FROM pdf_main
            WHERE metadata_hash = ?
        """, (metadata_hash,))

        row = cursor.fetchone()

        if row:
            status = "already_exists"

        else:
            # 2. Insert only if not exists
            cursor.execute("""
                INSERT INTO pdf_main (pdf_name, metadata_hash, uploaded_by)
                VALUES (?, ?, ?)
            """, (pdf_name, metadata_hash, current_user.email))

            status = "Uploaded"

        conn.commit()
        cursor.close()
        
        return status




