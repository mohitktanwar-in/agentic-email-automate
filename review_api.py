from fastapi import FastAPI
from db.drafts import (
    fetch_pending_drafts,
    approve_draft,
    reject_draft,
    edit_and_approve_draft,
)

# Initialize FastAPI application with a title.
app = FastAPI(title="Email Draft Review API")


# Define a GET endpoint to list all pending email drafts.
@app.get("/drafts/pending")
def list_pending():
    rows = fetch_pending_drafts()
    return [
        {
            "id": r[0],
            "message_id": r[1],
            "thread_id": r[2],
            "subject": r[3],
            "body": r[4],
            "confidence": r[5],
            "agent_name": r[6],
            "model": r[7],
            "created_at": r[8],
        }
        for r in rows
    ]

# Define a POST endpoint to approve a specific draft.
@app.post("/drafts/{draft_id}/approve")
def approve(draft_id: int, reviewed_by: str):
    approve_draft(draft_id, reviewed_by)
    return {"status": "approved"}


# Define a POST endpoint to reject a specific draft, optionally with a note.
@app.post("/drafts/{draft_id}/reject")
def reject(draft_id: int, reviewed_by: str, note: str | None = None):
    reject_draft(draft_id, reviewed_by, note)
    return {"status": "rejected"}


# Define a POST endpoint to edit and then approve a specific draft.
@app.post("/drafts/{draft_id}/edit")
def edit(
    draft_id: int,
    subject: str | None,
    body: str,
    reviewed_by: str,
):
    edit_and_approve_draft(draft_id, subject, body, reviewed_by)
    return {"status": "edited_and_approved"}

# Define a GET endpoint for health checking the API.
@app.get("/")
def health():
    return {"status": "review api running"}
