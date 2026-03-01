import os
import sendgrid
from sendgrid.helpers.mail import (
    Mail,
    Email,
    To,
    Content,
    Header
)
from dotenv import load_dotenv
import uuid

load_dotenv(override=True)
# Function to send an email

def generate_message_id(domain: str = "aiguru360.in") -> str:
    return f"<{uuid.uuid4().hex}@{domain}>"

def send_email(
    *,
    to_email: str,
    subject: str,
    body: str,
    in_reply_to: str | None,
    references: list[str] | None
):
    sg = sendgrid.SendGridAPIClient(
        api_key=os.environ.get("SENDGRID_API_KEY")
    )

    mail = Mail(
        from_email=Email("support@aiguru360.in"),
        to_emails=To(to_email),
        subject=subject,
        plain_text_content=Content("text/plain", body),
    )

    # ---- Threading headers ----
    message_id = generate_message_id()
    mail.add_header(Header("Message-ID", message_id))

    if in_reply_to:
        mail.add_header(Header("In-Reply-To", in_reply_to))

    if references:
        mail.add_header(Header("References", " ".join(references)))


    response = sg.client.mail.send.post(
        request_body=mail.get()
    )

    return {
        "status": "success",
        "provider_message_id": message_id,
    }
