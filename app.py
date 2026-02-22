from flask import Flask, render_template, url_for, redirect, request, send_file, send_from_directory
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, length, ValidationError
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os
from flask import jsonify

from user_auth import  get_user_by_id, get_user_by_email, create_user, get_existing_user_email
from answer_generation import chat_pipeline
from chat_history import update_history, get_user_history, accept_answer, edit_answer, get_global_history, update_final_answer
from text_extraction import text_extraction, save_to_db
from chunking_embedding import chunking, create_vector_store
from upload_excell import extract_text_from_excell, excell_answer, save_answers_to_excel
from sessions import rename_session_if_new, get_all_sessions, create_user_session

#=========================================================================================================#

app = Flask(__name__)

# Get project base directory
basedir = os.path.abspath(os.path.dirname(__file__))

load_dotenv()

# Set secret key for sessions/security
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

# Initialize password hashing
bcrypt = Bcrypt(app)


# Setup login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# Folder to store uploaded PDFs
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Base folder for Excel data
BASE_EXCELL_FOLDER = os.getenv("BASE_EXCELL_FOLDER")

# Folder for excell questions and answers 
QUESTION_FOLDER = os.path.join(BASE_EXCELL_FOLDER)
ANSWER_FOLDER = os.path.join(BASE_EXCELL_FOLDER)
os.makedirs(QUESTION_FOLDER, exist_ok=True)
os.makedirs(ANSWER_FOLDER, exist_ok=True)


# Store folder paths in app config
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["QUESTION_FOLDER"] = QUESTION_FOLDER
app.config["ANSWER_FOLDER"] = ANSWER_FOLDER

# Initialize RAG pipeline
rag_chain = chat_pipeline()


###======================================= Load user for Flask-Login  ========================================###

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)

###=========================================  Signup form  ===================================================###

class SignupForm(FlaskForm):
    
     # Username input
    user_name = StringField(
        validators=[InputRequired(),
                    length(min = 4, max = 20)],
                    render_kw= {"placeholder": "Name"}
    )
    
    # Email input
    email = StringField(
        validators=[InputRequired(),
                    length(min = 4, max = 20)],
                    render_kw= {"placeholder": "Email"}
    )
    
     # Password input
    password = PasswordField(
        validators=[InputRequired(),
                    length(min = 4, max = 20)],
                    render_kw= {"placeholder": "Password"}
    )
    
    submit = SubmitField("Sign Up")
    
     # Check if email already exists
    def validate_email(self,email):
        existing_user_email = get_existing_user_email(email.data)
        
        if existing_user_email:
            raise ValidationError("This User Already Exists, try logging in")

###=========================================  Login form  ====================================================###

class LoginForm(FlaskForm):
    
    # Email input
    email = StringField(
        validators=[InputRequired(),
                    length(min = 4, max = 20)],
                    render_kw= {"placeholder": "Email"}
    )
    
    # Password input
    password = PasswordField(
        validators=[InputRequired(),
                    length(min = 4, max = 20)],
                    render_kw= {"placeholder": "Password"}
    )
    
    submit = SubmitField("Login")


###=============================================  Home Route  =================================================###


@app.route('/')
def home():
    return render_template("index.html")


###=========================================  Login Route  ====================================================###


@app.route('/login', methods =['GET', 'POST'])
def login():
    
    form = LoginForm()

    if form.validate_on_submit():
        
        email = request.form['email']
        password = request.form['password']
        
        user = get_user_by_email(email)
        
        if user:
            if bcrypt.check_password_hash(user.password, password):
                
                login_user(user)
                
                return redirect(url_for("dashboard"))

    
    return render_template("login.html", form=form)


###==========================================  Sign-Up Route  ================================================###


@app.route('/register', methods =['GET', 'POST'])
def register():
    
    form = SignupForm()
    
    if form.validate_on_submit():
        
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        
        create_user(user_name = form.user_name.data, email = form.email.data, password= hashed_password)
        
        return redirect(url_for('login'))
        
    return render_template("register.html", form=form)


###===========================================  Dashboard Route  ==============================================###


@app.route('/dashboard', methods = ["GET", "POST"])
@login_required
def dashboard():
    return render_template("dashboard.html")


###=============================================  Logout Route ================================================###


@app.route('/logout', methods = ["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


###========================================  PDF upload route  ================================================###


@app.route("/upload", methods=["GET","POST"])
def upload_pdf():

    if "filename" not in request.files:
        return "No file uploaded", 400

    # Get uploaded file
    file = request.files["filename"]

    if not file.filename.lower().endswith(".pdf"):
        return "Only PDF files allowed", 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Extract text from PDF
    pdf_name, docs = text_extraction(file_path)
    
    # Save extracted data to database
    status = save_to_db(pdf_name, docs)

     # If new PDF, process and store vectors
    if status == "already_exists":
        pass
    else:
        chunks = chunking(docs)
        create_vector_store(chunks)

    return render_template("upload_questions.html")


###==========================================  Direct Chat route  =============================================###


@app.route('/chat', methods=["GET", "POST"])
@login_required
def chat_directly():
    
    email = current_user.email

    # Get session ID from URL
    session_id = request.args.get("session_id")
    
    # Get all chat sessions
    chat_sessions = get_all_sessions("chat")
    
    
    if request.method == "POST":

        question = request.form.get("question")

        if question:
            
             # Create new session if none exists
            if not session_id:
                session_id = create_user_session(email, chat_type="chat")
            
            rename_session_if_new(session_id, question)
            
            
            # Save only the question to history db
            question_id = update_history(
                email=current_user.email,
                session_id=session_id,
                question=question,
                answer=None,
                sources=None,
                confidence=None,
                cache_id = None,
                accepted = None,
                edited_answer = None
            )
            
            
            # Get answer from RAG model
            answer = rag_chain.invoke({
                "question": question,
                "question_id": question_id
            })


            # Update database with final answer
            update_final_answer(
                question_id,
                answer["answer"],
                answer["sources"],
                answer["confidence"],
                answer["cache_id"],
                answer["accepted"],
                answer["edited_answer"]
            )

    
    # Get chat history if session exists
    if session_id:
        chat_history = get_user_history(session_id)
    else:
        chat_history = []


    # Display answer on UI
    messages = []

    for entry in chat_history:

        messages.append({
            "text": entry["question"],
            "is_user": True,
            "question_id": entry["question_id"] 
        })
        
        # Determine which answer to show
        display_answer = entry['edited_answer'] if entry['edited_answer'] is not None else entry['answer']
        display_confidence = entry['confidence']
        
        messages.append({
            "text": f"""Answer:
                        {display_answer}

                        Sources:
                        {entry['sources']}

                        Confidence:
                        {display_confidence} %""",
                        
                        "is_user": False,
                        
                        "question_id": entry["question_id"],  # ADDED
                        
                        "accepted": entry["accepted"],  # ADDED
                        
                        "is_edited": entry['edited_answer'] is not None,  # ADDED
                        
                        "original_answer": entry['answer'],
                        
                        "sources": entry['sources']  # ADDED
        })

    return render_template("chat.html", messages=messages, chat_sessions= chat_sessions, active_session=session_id)

###=======================================  Route to accept answer  ===========================================###

@app.route('/accept_answer/<int:question_id>', methods=["POST"])
def accept_answer_route(question_id):
    
    try:
        
        accept_answer(question_id)
        return jsonify({"success": True})
    
    except Exception as e:
        
        print(f"Error accepting answer: {e}")  # Debug print
        return jsonify({"success": False, "error": str(e)}), 500


###=======================================  Route to edit answer  =============================================###


@app.route('/edit_answer/<int:question_id>', methods=["POST"])
def edit_answer_route(question_id):

    try:

        # Get JSON data from request
        data = request.get_json()

        new_answer = data.get("edited_answer")
        session_id = data.get("session_id")

        if not new_answer or not session_id:
            return jsonify({"success": False}), 400

        # Update answer in database
        edit_answer(question_id, new_answer)

        return jsonify({"success": True})

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500



###=========================================  Excel upload page  ==============================================###


@app.route('/excell', methods = ["GET", "POST"])
@login_required
def excell():    
    return render_template("upload_excell.html")


###===================================  Excel upload and processing route  ====================================###


@app.route('/upload_excell', methods=["GET", "POST"])
@login_required
def upload_excell():

    email = current_user.email

    raw_session_id = request.args.get("session_id")
    answer_file = None
    

    if not raw_session_id or raw_session_id == "None":
        session_id = None
    else:
        session_id = int(raw_session_id)


    # Get all Excel chat sessions
    chat_sessions = get_all_sessions("excel")
    
    
     # Handle file upload
    if request.method == "POST":

        # Create new session if needed
        if not session_id:
            session_id = create_user_session(email, chat_type="excel")


         # Prevent re-upload in same session
        existing = get_user_history(session_id)

        if existing:
            return redirect(url_for("upload_excell", session_id=session_id))


        if "excell_file" not in request.files:
            return "No file uploaded", 400


        # Get the file and save it to question folder
        excell_file = request.files["excell_file"]

        file_path = os.path.join(QUESTION_FOLDER, excell_file.filename)
        excell_file.save(file_path)

        
        # Extract questions from Excel
        questions_list = extract_text_from_excell(file_path)

        
         # Generate answers using RAG
        final_answer = excell_answer(
            questions_list,
            session_id,
            email,
            rag_chain
        )


        if final_answer:
            rename_session_if_new(session_id, final_answer[0]["question"])


        return redirect(
            url_for("upload_excell", session_id=session_id, file=answer_file)
        )

    
    # Load history and output file if session exists
    if session_id:
        history = get_user_history(session_id)
        answer_file = f"EXCELL/Excell_answers/rag_answers_{session_id}.xlsx"
    else:
        history = []


    return render_template(
        "upload_excell.html",
        chat_sessions=chat_sessions,
        active_session=session_id,
        history=history,
        excel_file = answer_file
    )


###==================================  Download generated Excel file =========================================###


@app.route('/download_excel/<int:session_id>')
@login_required
def download_excel(session_id):

    history = get_user_history(session_id)

    file_path = f"EXCELL/Excell_answers/rag_answers_{session_id}.xlsx"

    # Save answers to Excel file
    save_answers_to_excel(history, file_path)

    return send_file(file_path, as_attachment=True)


###=======================================  Approve an Excel answer  ==========================================###


@app.route("/excel/accept", methods=["POST"])
@login_required
def excel_accept():

    question_id = request.form.get("question_id")

    if not question_id:
        return {"status": "error"}, 400

     # Mark answer as accepted in database
    accept_answer(question_id)

    return {"status": "success"}


###============================================  Edit an Excel answer =========================================###


@app.route("/excel/edit", methods=["POST"])
@login_required
def excel_edit():

    question_id = request.form.get("question_id")
    new_answer = request.form.get("new_answer")

    if not question_id or not new_answer:
        return {"status": "error"}, 400

    # Update answer in database
    edit_answer(question_id, new_answer)

    return jsonify({"status": "success"})


###=========================================  Knowledge Base Route  ===========================================###


@app.route("/pdfs")
def list_pdfs():
    files = os.listdir(UPLOAD_FOLDER)

    # Filter only PDF files
    pdf_files = [f for f in files if f.lower().endswith(".pdf")]

    return render_template("knowledge_base.html", pdfs=pdf_files)


###=========================================  Download PDF Route  ===========================================###


@app.route("/pdfs/<filename>")
def serve_pdf(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


###=========================================  Global History Route  ===========================================###


@app.route('/global_history', methods = ["GET", "POST"])
@login_required
def global_history():    
    
    results = get_global_history()
    
    return render_template("global_history.html", global_history=results)


###============================================  Run the Flask app  ===========================================###

if  __name__ == "__main__":
    app.run(debug=True)

