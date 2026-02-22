from datetime import datetime, timezone
from subagents.schemas import AgentDecision
from db.db import get_conn

# Function to persist an agent's decision into the email_decisions table.

def persist_decision(
    message_id: str,
    thread_id: str,
    decision: AgentDecision,
):
    with get_conn() as conn:
 # Insert the decision details, including action, intent, confidence, and reason.
        conn.execute("""
            INSERT INTO email_decisions (
                message_id,
                thread_id,
                action,
                intent,
                confidence,
                reason,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            message_id,
            thread_id,
            decision.action,
            decision.intent,
            decision.confidence,
            decision.reason,
            datetime.now(timezone.utc).isoformat()
        ))
