from user_auth import get_db_connection

def create_user_session(email, chat_type="chat", session_name="New Chat"):
    
    with get_db_connection() as conn:
        
        cursor = conn.cursor()
    
        cursor.execute("""
            INSERT INTO chat_sessions (user_email, session_name, chat_type)
            OUTPUT INSERTED.session_id
            VALUES (?, ?, ?)
        """, (email, session_name, chat_type))
        
        session_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        
        return session_id


def get_all_sessions(chat_type):

    with get_db_connection() as conn:
        
        cursor = conn.cursor()

        cursor.execute("""
            SELECT session_id, user_email, session_name
            FROM chat_sessions
            WHERE chat_type = ?
            ORDER BY created_at DESC
        """, (chat_type,))

        rows = cursor.fetchall()

        return rows


def get_session_history(session_id):

    with get_db_connection() as conn:
        
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM chat_history
            WHERE session_id = ?
            ORDER BY question_id
        """, (session_id,))

        return cursor.fetchall()



def rename_session_if_new(session_id, first_question):

    if not session_id:
        return

    with get_db_connection() as conn:
        
        cursor = conn.cursor()

        cursor.execute("""
            SELECT session_name
            FROM chat_sessions
            WHERE session_id = ?
        """, (session_id,))


        row = cursor.fetchone()

        if not row:
            cursor.close()
            return

        current_name = row[0]

        if current_name == "New Chat":

            new_name = first_question[:40]

            cursor.execute("""
                UPDATE chat_sessions
                SET session_name = ?
                WHERE session_id = ?
            """, (new_name, session_id))

            conn.commit()

        cursor.close()
