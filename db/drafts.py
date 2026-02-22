from datetime import datetime, timezone
from db.db import get_conn

# Function to persist a new email draft into the database.
def persist_draft(
    *,
    message_id: str,
    thread_id: str,
    subject: str | None,
    body: str,
    confidence: float,
    agent_name: str,
    model: str,
):
    with get_conn() as conn:
 # Insert the draft details. 'INSERT OR IGNORE' prevents duplicates based on UNIQUE constraints.
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO email_drafts (
                message_id,
                thread_id,
                subject,
                body,
                confidence,
                agent_name,
                model,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                thread_id,
                subject,
                body,
                confidence,
                agent_name,
                model,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
 # Return the ID of the newly inserted row.
        return cursor.lastrowid


def fetch_pending_drafts():
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT
                id,
                message_id,
                thread_id,
                subject,
                body,
                confidence,
                agent_name,
                model,
                created_at
            FROM email_drafts
            WHERE status = 'pending'
            ORDER BY created_at
            """
        ).fetchall()


# Function to approve a pending email draft.
def approve_draft(draft_id: int, reviewed_by: str):
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE email_drafts
            SET
                status = 'approved',
                reviewed_by = ?,
                reviewed_at = ?
            WHERE id = ?
              AND status = 'pending'
            """,
            (reviewed_by, datetime.now(timezone.utc).isoformat(), draft_id),
        )

# Function to reject a pending email draft.
def reject_draft(
    draft_id: int,
    reviewed_by: str,
    note: str | None = None,
):
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE email_drafts
            SET
                status = 'rejected',
                reviewed_by = ?,
                reviewed_at = ?,
                reviewer_note = ?
            WHERE id = ?
              AND status = 'pending'
            """,
            (
                reviewed_by,
                datetime.now(timezone.utc).isoformat(),
                note,
                draft_id,
            ),
        )


# Function to edit and then approve a pending email draft.
def edit_and_approve_draft(
    draft_id: int,
    subject: str | None,
    body: str,
    reviewed_by: str,
):
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE email_drafts
            SET
                subject = ?,
                body = ?,
                status = 'approved',
                reviewed_by = ?,
                reviewed_at = ?
            WHERE id = ?
              AND status = 'pending'
            """,
            (
                subject,
                body,
                reviewed_by,
                datetime.now(timezone.utc).isoformat(),
                draft_id,
            ),
        )


# Function to fetch all approved email drafts.
def fetch_approved_drafts():
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT
                id,
                thread_id,
                subject,
                body
            FROM email_drafts
            WHERE status = 'approved'
            """
        ).fetchall()


# db/drafts.py

# Function to automatically approve a draft, typically based on confidence scores.
def auto_approve_draft(conn, draft_id: int):
    conn.execute(
        """
        UPDATE email_drafts
        SET
            status = 'approved',
            reviewed_by = 'system:auto_confidence_gate',
            reviewed_at = CURRENT_TIMESTAMP,
            reviewer_note = 'Auto-approved by confidence gate'
        WHERE id = ?
          AND status = 'pending'
        """,
        (draft_id,)
    )
