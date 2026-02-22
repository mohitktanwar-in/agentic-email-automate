import time
from datetime import datetime, timezone
from db.db import get_conn, init_db
from subagents.main_agent import run_main_agent
from subagents.reply import run_reply_agent
from subagents.schemas import AgentDecision
from db.decisions import persist_decision
from db.drafts import persist_draft
from db.drafts import auto_approve_draft
import asyncio
from dotenv import load_dotenv


# Load environment variables from .env file

load_dotenv(override=True)

# Define confidence thresholds for auto-decision and auto-draft approval.
AUTO_DECISION_THRESHOLD = 0.3
AUTO_DRAFT_THRESHOLD = 0.2

# Define the interval in seconds for polling for new emails.
POLL_INTERVAL = 2


# Function to fetch the next unprocessed email from the database.
def fetch_next_unprocessed_email(conn):
    return conn.execute("""
        SELECT *
        FROM email_events
        WHERE processed = 0
        ORDER BY received_at
        LIMIT 1
    """).fetchone()


# Function to fetch all emails belonging to a specific thread.
def fetch_thread(conn, thread_id):
    return conn.execute("""
        SELECT *
        FROM email_events
        WHERE thread_id = ?
        ORDER BY received_at
    """, (thread_id,)).fetchall()


# Function to mark an email as processed in the database.
def mark_processed(conn, message_id):
    conn.execute("""
        UPDATE email_events
        SET processed = 1,
            processed_at = ?
        WHERE message_id = ?
    """, (
        datetime.now(timezone.utc).isoformat(),
        message_id
    ))


async def main():
    init_db()
    print("🧠 Orchestrator started") # Log that the orchestrator has started.

 # Main loop for the orchestrator to continuously process emails.
    while True:
 # Get a database connection for the current iteration.
        with get_conn() as conn:
 # Fetch the next unprocessed email.
            row = fetch_next_unprocessed_email(conn)
 # If no unprocessed email is found, wait and continue to the next iteration.
            if not row:
                await asyncio.sleep(POLL_INTERVAL)
                continue

            (
                _id,
                message_id,
                in_reply_to,
                references,
                thread_id,
                direction,
                from_email,
                to_email,
                subject,
                body,
                raw_headers,
                received_at,
                created_at,
                processed,
                processed_at,
            ) = row

 # Fetch all messages in the current email's thread.
            thread = fetch_thread(conn, thread_id)
 # Log thread and email details.
            print("🧵 Thread:", thread_id)
            print("📩 New email:", subject)
            print("📚 Messages in thread:", len(thread))

            # Build thread messages (simple for now)
            # thread_messages = [row[9] for row in thread]  # body column
 # Construct a list of messages in the thread, formatted for agent processing.
            thread_messages = [
                {
                    "role": "user" if row[5] == "incoming" else "assistant",
                    "from": row[6],   # from_email
                    "body": row[9],   # body
                }
                for row in thread
            ]

            # Check if the email is an outgoing system email.
            if direction == "outgoing":
 # Create an 'ignore' decision for outgoing system emails.
                decision = AgentDecision(
                    action="ignore",
                    intent=None,
                    confidence=1.0,
                    reason="Skipping processing of system-sent outgoing email."
                )

                persist_decision(
                    message_id=message_id,
                    thread_id=thread_id,
                    decision=decision
                )

                mark_processed(conn, message_id)
                print("🛑 Ignored outgoing system email\n")
                continue




            decision = await run_main_agent(thread_messages)
            
            print(decision)

            # Hard validation (non-negotiable)
            assert isinstance(decision, AgentDecision)

            persist_decision(
                message_id=message_id,
                thread_id=thread_id,
                decision=decision
            )

 # Log the agent's decision.
            print("🤖 Agent decision persisted:")
            print(decision.model_dump())

 # If the agent decides to auto-reply.
            if decision.action == "auto_reply":
 # Run the reply agent to generate a draft.
                draft = await run_reply_agent(thread_messages)
                # persist_draft(
                #     message_id=message_id,
                #     thread_id=thread_id,
                #     subject=draft.subject,
                #     body=draft.body,
                #     confidence=draft.confidence,
                #     agent_name="ReplyAgent",
                #     model="gpt-5-nano",
                # )
 # Persist the generated draft.
                draft_id = persist_draft(
                                            message_id=message_id,
                                            thread_id=thread_id,
                                            subject=draft.subject,
                                            body=draft.body,
                                            confidence=draft.confidence,
                                            agent_name="ReplyAgent",
                                            model="gpt-5-nano",
                                        )
 # Check if both decision and draft confidence meet the auto-approval thresholds.
                if (
                    decision.confidence is not None
                    and draft.confidence is not None
                    and decision.confidence >= AUTO_DECISION_THRESHOLD
                    and draft.confidence >= AUTO_DRAFT_THRESHOLD
                ):
                    auto_approve_draft(conn, draft_id)
                    print(f"✅ Auto-approved draft {draft_id}") # Log auto-approval.
                else:
                    print(f"🕒 Draft {draft_id} pending human review") # Log pending review.

                # print("📝 Draft reply persisted")

 # Mark the current email as processed.
            mark_processed(conn, message_id)
            print("✅ Marked processed\n")

# Entry point for the script.
if __name__ == "__main__":
    asyncio.run(main())
