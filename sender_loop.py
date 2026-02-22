import time
from db.drafts import fetch_approved_drafts
from db.db_outgoing import persist_outgoing_email
from send_email_tool import send_email
from db.db import get_conn
from datetime import datetime, timezone
import json


# Interval in seconds to poll for approved drafts.
POLL_INTERVAL = 5

def get_last_message_ids(thread_id: str):
 # Connect to the database.
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT message_id, references_ids
            FROM email_events
            WHERE thread_id = ?
              AND direction = 'incoming'
            ORDER BY received_at DESC
            LIMIT 1
            """,
            (thread_id,),
        ).fetchone()

 # If no row is found, return None for message_id and an empty list for references.
    if not row:
        return None, []

 # Extract message_id and references_ids, then parse references_ids from JSON.
    message_id, refs = row
    return message_id, json.loads(refs or "[]")
 

def get_reply_to_email(thread_id: str) -> str:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT from_email
            FROM email_events
            WHERE thread_id = ?
              AND direction = 'incoming'
            ORDER BY received_at DESC
            LIMIT 1
            """,
            (thread_id,),
        ).fetchone()

 # Raise an error if no incoming sender is found for the thread.
    if not row or not row[0]:
        raise RuntimeError(f"No incoming sender found for thread {thread_id}")

    return row[0]

def get_reply_subject(thread_id: str) -> str:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT subject
            FROM email_events
            WHERE thread_id = ?
              AND direction = 'incoming'
            ORDER BY received_at DESC
            LIMIT 1
            """,
            (thread_id,),
        ).fetchone()

    if not row or not row[0]:
        return "Re: Your message"

 # Prepend "Re:" if the subject doesn't already start with it.
    subj = row[0]
    return subj if subj.lower().startswith("re:") else f"Re: {subj}"


def sender_loop():
    print("📤 Sender loop started")
 # Loop indefinitely to continuously check for approved drafts.
    while True:
 # Fetch all approved drafts from the database.
        drafts = fetch_approved_drafts()
 # Iterate through each approved draft.
        for draft_id, thread_id, subject, body in drafts:
            try:
 # Determine the recipient email for the reply.
                to_email = get_reply_to_email(thread_id)
 # Get the last message ID and existing references for the thread to maintain conversation context.
                last_msg_id, existing_refs = get_last_message_ids(thread_id)
 # Build the 'References' header for the outgoing email.
                references = []
                if existing_refs:
                    references.extend(existing_refs)
                if last_msg_id:
                    references.append(last_msg_id)
 # Send the email using the send_email tool.
                result = send_email(
                    to_email=to_email,  # later derive dynamically
                    subject=subject or get_reply_subject(thread_id),
                    body=body,
                    in_reply_to=last_msg_id,
                    references=references,
                )
 # Persist the record of the outgoing email in the database.
                persist_outgoing_email(
                    draft_id=draft_id,
                    thread_id=thread_id,
                    to_email=to_email,
                    subject=subject,
                    body=body,
                    provider="sendgrid",
                    provider_message_id=result.get("provider_message_id"),
                    status="sent",
                )
                print(f"📨 Replying to {to_email} for thread {thread_id}")
 # Update the status of the draft to 'sent' and record the outgoing email as an event.
                print(f"✅ Sent draft {draft_id}")
                with get_conn() as conn:
                    conn.execute(
                        """
                        UPDATE email_drafts
                        SET status = 'sent'
                        WHERE id = ?
                        AND status = 'approved'
                        """,
                        (draft_id,)
                    )
 # Insert the outgoing email as a new event in the email_events table.
                    conn.execute(
                        """
                        INSERT INTO email_events (
                            message_id,
                            in_reply_to,
                            references_ids,
                            thread_id,
                            direction,
                            from_email,
                            to_email,
                            subject,
                            body,
                            raw_headers,
                            received_at,
                            created_at,
                            processed
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                        """,
                        (
                            result["provider_message_id"],
                            last_msg_id,
                            json.dumps(references),
                            thread_id,
                            "outgoing",
                            "support@aiguru360.in",
                            to_email,
                            subject,
                            body,
                            None,
                            datetime.now(timezone.utc).isoformat(),
                            datetime.now(timezone.utc).isoformat(),
                        ),
                    )

 # Handle exceptions during email sending or persistence.

            except Exception as e:
                persist_outgoing_email(
                    draft_id=draft_id,
                    thread_id=thread_id,
                    to_email="mohit@aiguru360.in",
                    subject=subject,
                    body=body,
                    provider="sendgrid",
                    provider_message_id=None,
                    status="failed",
                )
                print(f"❌ Failed to send draft {draft_id}: {e}")
 # Wait for the specified poll interval before checking for new drafts again.
        time.sleep(POLL_INTERVAL)
if __name__ == "__main__":
    sender_loop()