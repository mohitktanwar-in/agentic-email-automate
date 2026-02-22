# agents/reply.py
from agents import Agent, Runner
import asyncio
from dotenv import load_dotenv
from subagents.schemas import DraftReply
import json

load_dotenv(override=True)

reply_agent = Agent(
    name="ReplyAgent",
    instructions="""
You draft email replies.

Input:
- Full thread context
- Last incoming message is what you reply to

Rules:
- Be concise and professional
- Do NOT invent facts
- Do NOT promise actions unless explicitly stated
- Plain text only (no HTML)
- No emojis

Return STRICT JSON matching this schema:

{
  "subject": string | null,
  "body": string,
  "confidence": number
}
""",
    model="gpt-5-nano",
    output_type=DraftReply
)


async def run_reply_agent(thread_messages: list[str]) -> DraftReply:
    payload = {"thread_messages": thread_messages}

    result = await Runner.run(
        reply_agent,
        input=json.dumps(payload, ensure_ascii=False)
    )

    draft = result.final_output
    assert isinstance(draft, DraftReply)

    return draft