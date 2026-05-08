import sqlite3
import os
from datetime import datetime, timezone, timedelta

# Get absolute path to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "documents.db")
MALAYSIA_TZ = timezone(timedelta(hours=8))

DEFAULT_DOMAINS = [
    (
        "Macroeconomics",
        "Inflation, GDP, CPI, PPI, unemployment, economic growth, recession, interest rates.",
    ),
    (
        "Central Banks",
        "Federal Reserve, ECB, BOJ, PBOC, monetary policy, reserve announcements, rate decisions.",
    ),
    (
        "Geopolitics",
        "Wars, sanctions, trade conflicts, political instability, global tensions, safe-haven demand.",
    ),
]


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
        document_id TEXT,
        field TEXT,
        value TEXT,
        FOREIGN KEY (document_id) REFERENCES documents(id)
    )
    """)

    cursor.execute("PRAGMA table_info(document_metadata)")
    metadata_columns = [row["name"] for row in cursor.fetchall()]

    if "id" in metadata_columns:
        cursor.execute("""
        ALTER TABLE document_metadata RENAME TO document_metadata_old
        """)
        cursor.execute("""
        CREATE TABLE document_metadata (
            document_id TEXT,
            field TEXT,
            value TEXT,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
        """)
        cursor.execute("""
        INSERT INTO document_metadata (document_id, field, value)
        SELECT document_id, field, value FROM document_metadata_old
        """)
        cursor.execute("DROP TABLE document_metadata_old")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS domains (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        created_date TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_domains (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id TEXT,
        domain_id INTEGER,
        confidence REAL,
        created_date TEXT,
        FOREIGN KEY (document_id) REFERENCES documents(id),
        FOREIGN KEY (domain_id) REFERENCES domains(id)
    )
    """)

    cursor.execute("SELECT COUNT(*) AS total FROM domains")
    if cursor.fetchone()["total"] == 0:
        created_date = datetime.now(MALAYSIA_TZ).isoformat(timespec="seconds")
        cursor.executemany(
            "INSERT INTO domains (name, description, created_date) VALUES (?, ?, ?)",
            [
                (name, description, created_date)
                for name, description in DEFAULT_DOMAINS
            ]
        )

    conn.commit()
    conn.close()
