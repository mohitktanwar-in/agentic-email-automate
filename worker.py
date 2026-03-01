import re
import uuid
import json
import time
from google.cloud import pubsub_v1
from db.db import init_db, get_conn
from sqlite3 import IntegrityError
from datetime import datetime, timezone
from email.parser import Parser
from email.header import decode_header


# Google Cloud Project ID and Pub/Sub subscription ID.
PROJECT_ID = "ai-agents-483504"
SUBSCRIPTION_ID = "email-ingestion-worker"

# Initialize a Pub/Sub subscriber client.
subscriber = pubsub_v1.SubscriberClient()
# Construct the full subscription path.
subscription_path = subscriber.subscription_path(
    PROJECT_ID, SUBSCRIPTION_ID
)

def parse_headers(raw_headers):
    parser = Parser()
    msg = parser.parsestr(raw_headers)

    print("HEADERS FOUND:")
    for key in msg.keys():
        print(f" - {key}")

    print("References value:", msg.get("References"))
    print("In-Reply-To value:", msg.get("In-Reply-To"))

    in_reply_to = msg.get("In-Reply-To")
    references = []
    for header_value in msg.get_all("References", []):
        # Split on whitespace
        parts = header_value.strip().split()
        references.extend(parts)
    return in_reply_to, references

def extract_in_reply_to(headers: str | None):
 # If no headers are provided, return None.
    if not headers:
        print("⚠️ No headers provided, skipping")
        return None
 # Use regex to find the 'In-Reply-To' header and extract its value.
    match = re.search(
        r"In-Reply-To:\s*(<[^>]+>)",
        headers,
        re.IGNORECASE
    )
    return match.group(1) if match else None


def extract_references(headers: str | None):
 # If no headers are provided, return an empty list.
    if not headers:
        print("⚠️ No headers provided, skipping")
        return []
 # Use regex to find the 'References' header.
    match = re.search(
        r"References:\s*(.+)", # In Email Header Structure: Email headers are typically structured as one field per line.
                               # This regex is designed to grab everything on the "References" line but ignore subsequent headers (like "Subject:" or "Date:")
                               # that start on the next line.
        headers,
        re.IGNORECASE
    )
    if not match:
        print("⚠️ No references provided, skipping")
        return []
    # split on whitespace, keep <...>
 # Extract all message IDs enclosed in angle brackets from the references string.
    references = re.findall(r"<[^>]+>", match.group(1))
    print("References found:", references)
    return references


def resolve_thread_id(conn, in_reply_to, references):
    # 1️⃣ In-Reply-To (strongest signal)
 # If an 'In-Reply-To' header exists, try to find a matching thread_id in the database.
    if in_reply_to:
        row = conn.execute(
            "SELECT thread_id FROM email_events WHERE message_id = ?",
            (in_reply_to,)
        ).fetchone()
        if row:
            return row[0] # Return the found thread_id.

    # 2️⃣ References (fallback)
 # If 'In-Reply-To' didn't yield a thread, check 'References' IDs.
    for ref in references:
        row = conn.execute(
            "SELECT thread_id FROM email_events WHERE message_id = ?",
            (ref,)
        ).fetchone()
        if row:
            return row[0]

    # 3️⃣ New conversation
    return str(uuid.uuid4())


def callback(message: pubsub_v1.subscriber.message.Message):
    try:
        payload = json.loads(message.data.decode("utf-8"))
        message_id = payload.get("message_id")
        raw_headers = payload.get("raw_headers")

        in_reply_to, references = parse_headers(raw_headers)
        if not in_reply_to:
            print("⚠️ No In-Reply-To found, fallback to extract_in_reply_to")
            in_reply_to = extract_in_reply_to(raw_headers)
        if not references:
            print("⚠️ No References found, fallback to extract_references")
            references = extract_references(raw_headers)

        if not message_id:
            print("⚠️ Missing message_id, skipping")
            message.ack()
            return
            

        # in_reply_to = extract_in_reply_to(raw_headers)
        # references = extract_references(raw_headers)

        with get_conn() as conn:
            thread_id = resolve_thread_id(conn, in_reply_to, references)

            conn.execute("""
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
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message_id,
                in_reply_to,
                json.dumps(references),
                thread_id,
                "incoming",
                payload.get("from"),
                payload.get("to"),
                payload.get("subject"),
                payload.get("text"),
                raw_headers,
                payload.get("received_at"),
                datetime.now(timezone.utc).isoformat()
            ))

 # Log the stored email details and acknowledge the message.
        print("📩 Stored email:")
        print("  Message-ID:", message_id)
        print("  Thread-ID :", thread_id)
        print("  From      :", payload.get("from"))
        print("  To        :", payload.get("to"))
        print("  Received at:", payload.get("received_at"))
        print("  Subject   :", payload.get("subject"))
        message.ack()

    except IntegrityError:
 # If an IntegrityError occurs (e.g., duplicate message_id), ignore it and acknowledge the message.
        print("⚠️ Duplicate email ignored:", message_id)
        message.ack()

    except Exception as e:
 # For any other exception, log the error but do NOT acknowledge the message, allowing it to be redelivered.
        print("❌ Error:", e)
        # do NOT ack


def main():
 # Initialize the database (create tables if they don't exist).
    init_db()
    print("🗄️ SQLite initialized")

 # Subscribe to the Pub/Sub topic and register the callback function.
    streaming_pull_future = subscriber.subscribe(
        subscription_path, callback=callback
    )

    print("🚀 Ingestion worker started. Waiting for messages...")

 # Keep the main thread alive to listen for messages.
    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        streaming_pull_future.cancel()


if __name__ == "__main__":
    main()
