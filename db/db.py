import sqlite3
from pathlib import Path
from datetime import datetime, timezone

# Define the path to the SQLite database file.
# It's located in the same directory as this script and named "email.db".
DB_PATH = Path(__file__).parent / "email.db"


def get_conn():
 # Ensure the parent directory for the database exists.
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
 # Establish a connection to the database.
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS email_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- SMTP identifiers
            message_id TEXT NOT NULL UNIQUE,
            in_reply_to TEXT,
            references_ids TEXT,          -- JSON array or space-separated list

            -- Our internal grouping
            thread_id TEXT NOT NULL,

            -- Metadata
            direction TEXT NOT NULL,
            from_email TEXT,
            to_email TEXT,
            subject TEXT,
            body TEXT,
            raw_headers TEXT,

            received_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            processed INTEGER DEFAULT 0,
            processed_at TEXT
        );
        """)

 # Create the email_decisions table if it doesn't already exist.
        conn.execute("""
        CREATE TABLE IF NOT EXISTS email_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            message_id TEXT NOT NULL,
            thread_id TEXT NOT NULL,

            action TEXT NOT NULL,
            intent TEXT,
            confidence REAL,
            reason TEXT,

            created_at TEXT NOT NULL
        )
        """)

 # Create the email_drafts table if it doesn't already exist.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS email_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                message_id TEXT NOT NULL UNIQUE,
                thread_id TEXT NOT NULL,

                subject TEXT,
                body TEXT NOT NULL,
                confidence REAL,

                agent_name TEXT NOT NULL,
                model TEXT NOT NULL,

                status TEXT DEFAULT 'pending',
                reviewed_by TEXT,
                reviewed_at TEXT,
                reviewer_note TEXT,

                created_at TEXT NOT NULL
            );
        """)

 # Create the outgoing_emails table if it doesn't already exist.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS outgoing_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                draft_id INTEGER NOT NULL UNIQUE,
                thread_id TEXT NOT NULL,

                to_email TEXT NOT NULL,
                subject TEXT,
                body TEXT NOT NULL,

                sent_at TEXT NOT NULL,

                provider TEXT NOT NULL,
                provider_message_id TEXT,

                status TEXT NOT NULL
            );
        """)

        
        

        
