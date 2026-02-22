import os
import pyodbc
from flask_login import UserMixin

def get_db_connection():

    driver = os.getenv("DB_DRIVER")
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")

    return pyodbc.connect(
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        "Trusted_Connection=yes;"
    )


class User(UserMixin):

    def __init__(self, user_id, name, email, password):

        self.id = user_id      
        self.name = name
        self.email = email
        self.password = password
    


def get_user_by_email(email):

    with get_db_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT user_id, user_name, email, password
            FROM user_table
            WHERE email = ?
            """,
            email
        )

        row = cursor.fetchone()

        if row:
            return User(*row)   

def get_user_by_id(user_id):

    with get_db_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT user_id, user_name, email, password
            FROM user_table
            WHERE user_id = ?
            """,
            user_id
        )

        row = cursor.fetchone()

        if row:
            return User(*row)



def create_user(user_name, email, password):

    with get_db_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO user_table (user_name, email, password)
            VALUES (?, ?, ?)
            """,
            user_name,
            email,
            password
        )

        conn.commit()
        
        
def get_existing_user_email(email):

    with get_db_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1 FROM user_table WHERE email = ?",
            email
        )

        existing_user_email = cursor.fetchone() 
        
        return existing_user_email


