# SAGE: A Medical RAG Application

SAGE is a Retrieval-Augmented Generation (RAG) application designed for the medical domain. It provides a robust platform for users to ask questions against a knowledge base of medical documents (PDFs) and receive accurate, context-aware answers. The application features an interactive chat interface, bulk question processing from Excel files, and a comprehensive user feedback loop for answer validation and editing.

## Key Features

*   **RAG Pipeline:** Leverages a local Large Language Model (LLM) and a vector database (ChromaDB) to provide answers based on uploaded documents.
*   **Document Ingestion:** Easily upload and process PDF documents to build a custom knowledge base.
*   **Interactive Chat:** A real-time chat interface for asking questions and receiving answers with source citations and confidence scores.
*   **Bulk QA with Excel:** Upload an Excel file containing a list of questions and receive a downloadable Excel sheet with the corresponding answers.
*   **Semantic Caching:** Reduces latency and computational cost by caching answers to semantically similar questions.
*   **User Feedback Loop:** Users can "Approve" correct answers or "Edit" generated answers, which helps refine the system's knowledge and flags answers for review.
*   **Session Management:** Conversations are organized into sessions, allowing users to revisit past chats.
*   **User Authentication:** Secure login and registration system to manage user access and history.
*   **Global History:** A centralized view of all unique questions asked across the system, enabling review and quality control.
*   **Knowledge Base Browser:** View and access all the PDF documents that form the application's knowledge base.

## Technology Stack

*   **Backend:** Python, Flask
*   **Frontend:** HTML, CSS, JavaScript
*   **Database:** Microsoft SQL Server (connected via `pyodbc`)
*   **LLM:** 'Llama 3.2 3B'
*   **RAG Framework:** LangChain
*   **Vector Database:** ChromaDB
*   **Embedding Model:** `BAAI/bge-small-en-v1.5`
*   **Authentication:** Flask-Login, Flask-Bcrypt
*   **Document Loaders:** PyMuPDF, UnstructuredExcel

## Project Structure and Core Components

The application is organized into several key modules that handle specific functionalities:

| File/Directory        | Description                                                                                                                               |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `app.py`              | The main Flask application. Defines all routes, handles user requests, and integrates the different components.                            |
| `answer_generation.py`| The core RAG logic. Loads the LLM, performs similarity search, calculates confidence, formats prompts, and generates answers.             |
| `semantic_caching.py` | Implements the caching mechanism. Searches for similar questions in the cache and stores new Q&A pairs.                                     |
| `chunking_embedding.py`| Responsible for splitting documents into chunks, generating embeddings using Hugging Face models, and managing the Chroma vector store.    |
| `text_extraction.py`  | Extracts text from uploaded PDF files using `PyMuPDFLoader` and stores metadata in the database.                                          |
| `upload_excell.py`    | Handles the processing of Excel files for bulk question answering, generating answers for each question, and creating a results file.     |
| `user_auth.py`        | Manages user authentication, including creating, retrieving, and verifying users against the database.                                     |
| `chat_history.py`     | Handles all database interactions related to storing, retrieving, and updating user chat history, including edits and approvals.           |
| `sessions.py`         | Manages user chat sessions, allowing for the creation and retrieval of distinct conversation threads.                                      |
| `templates/`          | Contains all Jinja2 HTML templates for rendering the user interface.                                                                      |
| `static/`             | Holds all static assets like CSS stylesheets and images.                                                                                  |

## Usage

1.  **Register and Login:** Navigate to the homepage and create a new account or log in with existing credentials.
2.  **Dashboard:** After logging in, you will be directed to the dashboard, which serves as the central hub.
3.  **Build Your Knowledge Base:**
    - From the dashboard, click "Upload PDF".
    - Select a PDF file from your local machine. The file will be processed, chunked, embedded, and added to the Chroma vector store.
4.  **Ask Questions:**
    - **Interactive Chat:** Click "Chat Directly". You can now ask questions related to the content of your uploaded PDFs. The system will provide an answer, confidence score, and the source documents.
    - **Bulk Questions:** Click "Upload Excel". You can upload an `.xlsx` file with a list of questions. The application will process them and present the results in a table, which can also be downloaded.
5.  **Review and Refine:**
    - In both the chat and Excel results views, you can interact with the generated answers.
    - Click **Approve** to validate a correct answer. This feedback helps track model performance.
    - Click **Edit** to modify an incorrect or incomplete answer. The edited answer will be saved and displayed for future reference.
6.  **Explore History and Knowledge:**
    - **My Chats:** The sidebar in the chat and Excel views lists your past sessions, allowing you to revisit conversations.
    - **Global History:** View a log of all unique questions and their approved/edited answers across the platform.
    - **Knowledge Base:** See a list of all PDFs currently in the system and open them directly.

## Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/15-harsh/sage_rag_application.git
    cd sage_rag_application
    ```

2.  **Create and Activate a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirement.txt
    ```

4.  **Set Up Environment Variables:**
    Create a `.env` file in the root directory and add the following configuration. Update the values to match your local setup.
    ```
    SECRET_KEY='your_strong_secret_key'

    # Database Connection
    DB_DRIVER='ODBC Driver 17 for SQL Server'
    DB_SERVER='your_server_name'
    DB_NAME='your_database_name'

    # File Paths
    UPLOAD_FOLDER='PDFs'
    BASE_EXCELL_FOLDER='EXCELL'
    CHROMA_PERSIST_DIR='vector_db'
    CHROMA_PERSIST_DIR_FOR_CACHE='cache_db'
    ```

5.  **Download a GGUF Language Model:**
    The application is configured to use a local LLM in GGUF format.
    - Download a model like [Llama-3.2-3B-Instruct-Q4_K_M.gguf](https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF).
    - Create a `models` directory in the project root.
    - Place the downloaded `.gguf` file inside the `models` directory.
    - Ensure the path in `answer_generation.py` matches your model file name:
      ```python
      # in answer_generation.py
      model_path=r"models\Llama-3.2-3B-Instruct-Q4_K_M.gguf",
      ```

6.  **Set Up the Database:**
    - Ensure you have a running instance of Microsoft SQL Server.
    - Create a new database with the name you specified in your `.env` file.
    - You will need to create the necessary tables. The schemas can be inferred from the SQL queries in `user_auth.py`, `chat_history.py`, `sessions.py`, and `text_extraction.py`.
  
    - Create the following tables before running the application:

        - **`user_table`**  
          `user_id`, `user_name`, `email`, `password`
        
        - **`chat_sessions`**  
          `session_id`, `user_email`, `session_name`, `created_at`, `chat_type`
        
        - **`chat_history`**  
          `question_id`, `user_email`, `question`, `answer`, `confidence`, `sources`,  
          `accepted`, `edited_answer`, `session_id`, `cache_id`
        
        - **`pdf_main`**  
          `pdf_id`, `pdf_name`, `metadata_hash`, `uploaded_at`, `uploaded_by`

7.  **Run the Application:**


    
