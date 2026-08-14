import sqlite3
import bcrypt
import uuid
from datetime import datetime

DB_PATH = "jarvis_data.sqlite"

def init_db():
    """Initializes the database schema."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id TEXT PRIMARY KEY, email TEXT UNIQUE, password TEXT, verified INTEGER)''')
    # Threads table mapping a LangGraph thread_id to a specific user
    c.execute('''CREATE TABLE IF NOT EXISTS threads
                 (id TEXT PRIMARY KEY, user_id TEXT, title TEXT, created_at TIMESTAMP)''')
    conn.commit()
    conn.close()

def create_user(email, password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (id, email, password, verified) VALUES (?, ?, ?, 0)", 
                  (user_id, email, hashed))
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def verify_user_login(email, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, password FROM users WHERE email=?", (email,))
    user = c.fetchone()
    conn.close()
    if user and bcrypt.checkpw(password.encode('utf-8'), user[1]):
        return user[0]
    return None

def create_thread(user_id, title="New Chat"):
    thread_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO threads (id, user_id, title, created_at) VALUES (?, ?, ?, ?)",
              (thread_id, user_id, title, datetime.now()))
    conn.commit()
    conn.close()
    return thread_id

def get_user_threads(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title FROM threads WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    threads = c.fetchall()
    conn.close()
    return [{"id": t[0], "title": t[1]} for t in threads]

def update_thread_title(thread_id, new_title):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE threads SET title=? WHERE id=?", (new_title, thread_id))
    conn.commit()
    conn.close()

def delete_thread(thread_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM threads WHERE id=?", (thread_id,))
    conn.commit()
    conn.close()
    
def check_user_exists(email: str) -> bool:
    """Checks if an email is registered in the database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE email=?", (email,))
    user = c.fetchone()
    conn.close()
    return user is not None

def update_password(email: str, new_password: str):
    """Hashes the new password and updates the user's record."""
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET password=? WHERE email=?", (hashed, email))
    conn.commit()
    conn.close()