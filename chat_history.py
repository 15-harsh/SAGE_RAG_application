from flask import session
from user_auth import get_db_connection


def update_history(email, session_id, question, answer, sources, confidence, cache_id, accepted, edited_answer):
    
    with get_db_connection() as conn:
        
        cursor = conn.cursor()
    
        cursor.execute("""
            INSERT INTO chat_history 
            (user_email, session_id, question, answer, confidence, sources, cache_id, accepted, edited_answer)
            OUTPUT INSERTED.question_id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            email,
            session_id,
            question,
            answer,
            confidence,
            sources,
            cache_id,
            accepted, 
            edited_answer
        ))
        
        question_id = cursor.fetchone()[0] 
        conn.commit()
        return question_id

def update_final_answer(question_id, answer, sources, confidence, cache_id, accepted, edited_answer):
    
        with get_db_connection() as conn:
        
            cursor = conn.cursor()
    
            cursor.execute("""
                UPDATE chat_history
                SET answer = ?,
                    sources = ?,
                    confidence = ?,
                    cache_id = ?,
                    accepted = ?,
                    edited_answer = ?
                WHERE question_id = ?
            """, (
                answer,
                sources,
                confidence,
                cache_id,
                accepted,
                edited_answer,
                question_id,
            ))
            
            conn.commit()

    
def get_user_history(session_id):

    with get_db_connection() as conn:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT question_id, question, answer, confidence, sources, accepted, edited_answer
            FROM chat_history
            WHERE session_id = ?
        """, session_id)
        
        rows = cursor.fetchall()

        history = []
        for row in rows:
            history.append({
                'question_id': row[0],
                'question': row[1],
                'answer': row[2],
                'confidence': row[3], 
                'sources' : row[4],
                'accepted': row[5],
                'edited_answer': row[6]
            })
        
        return history


def accept_answer(question_id):
    
    with get_db_connection() as conn:

        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE chat_history
            SET accepted = 1
            WHERE cache_id = (
                SELECT cache_id
                FROM chat_history
                WHERE question_id = ?
            )
        """, (question_id,))
        
        conn.commit()
    
    
def edit_answer(question_id, new_answer):
    
    with get_db_connection() as conn:

        cursor = conn.cursor()
       
        cursor.execute("""
            UPDATE chat_history
            SET edited_answer = ?
            WHERE cache_id = (
                SELECT cache_id
                FROM chat_history
                WHERE question_id = ?
            )
        """, (new_answer, question_id))
        
        conn.commit()
    
    
def save_chat ( question, answer, sources, confidence,):

    with get_db_connection() as conn:

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO chat_history
            (user_email, session_id, question, answer, sources, confidence)

            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session['user_email'],
            session['session_id'],
            question,
            answer,
            sources,
            confidence
        ))

        conn.commit()


    
    
def update_excell_history(email, session_id, question, answer, confidence, sources):
    
    with get_db_connection() as conn:
        
        cursor = conn.cursor()
    
        cursor.execute("""
                INSERT INTO chat_history (user_email, session_id, question, answer, confidence, sources)
                VALUES (?, ?, ?, ?, ?)
                """, email, session_id, question, answer, confidence, sources)
        
        conn.commit()
    
    
def get_global_history():

    with get_db_connection() as conn:
        
        cursor = conn.cursor()

        cursor.execute("""
            SELECT question_id, question, answer, confidence, sources, edited_answer, accepted
            FROM (
                SELECT question_id, question, answer, confidence, sources, edited_answer, accepted,  -- Added comma here
                    ROW_NUMBER() OVER (PARTITION BY cache_id ORDER BY question_id) as rn
                FROM chat_history
                WHERE cache_id IS NOT NULL
            ) t
            WHERE rn = 1
            ORDER BY question_id DESC;
        """)
        
        rows = cursor.fetchall()

        global_history = []
        for row in rows:
            global_history.append({
                'question_id' : row[0],
                'question': row[1],
                'answer': row[2],
                'confidence': row[3], 
                'sources' : row[4],
                'edited_answer': row[5],
                'accepted' : row[6]
            })
        
        return global_history