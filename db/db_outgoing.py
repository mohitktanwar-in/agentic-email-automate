from datetime import datetime, timezone
from db.db import get_conn

# Function to persist a record of an outgoing email in the database.
def persist_outgoing_email(
    *,
    draft_id: int,
    thread_id: str,
    to_email: str,
    subject: str | None,
    body: str,
    provider: str,
    provider_message_id: str | None,
    status: str,
):
    with get_conn() as conn:
 # Insert the outgoing email details. 'INSERT OR IGNORE' prevents duplicates based on UNIQUE constraints.
        conn.execute(
            """
            INSERT OR IGNORE INTO outgoing_emails (
                draft_id,
                thread_id,
                to_email,
                subject,
                body,
                sent_at,
                provider,
                provider_message_id,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                draft_id,
                thread_id,
                to_email,
                subject,
                body,
                datetime.now(timezone.utc).isoformat(),
                provider,
                provider_message_id,
                status,
            ),
        )
