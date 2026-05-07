import sqlite3
import os

# Get absolute path to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "documents.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(BASE_DIR, exist_ok=True)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        created_date TEXT,
        file_path TEXT,
        meta_json TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_metadata (
        field TEXT,
        value TEXT,
        document_id TEXT,
        FOREIGN KEY (document_id) REFERENCES documents(id)
    )
    """)

    conn.commit()
    conn.close()
