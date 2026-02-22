from subagents.schemas import AgentDecision
from subagents.classifier import classify
from subagents.reply import DraftReply
from agents import Agent, Runner
import asyncio
from dotenv import load_dotenv
import json
from pydantic import ValidationError


load_dotenv(override=True)


main_agent = Agent(
    name="MainEmailAgent",
    instructions="""
You are an AI email automation agent.

You will receive:
- thread_messages: a chronological list of messages.

Each message has:
- role: "user" or "assistant"
- from: email address of the sender
- body: plain text message content

Rules:
- Decide ONE action: auto_reply, escalate, or ignore
- Be conservative with auto_reply
- If unsure, escalate
- Never hallucinate facts

Return your decision STRICTLY as JSON
matching this schema:

{
  "action": "auto_reply | escalate | ignore",
  "intent": string | null,
  "confidence": number | null,
  "reason": string
}
""",
model = "gpt-5-nano",
output_type=AgentDecision
)

async def run_main_agent(thread_messages: list[str]) -> AgentDecision:
    payload = {
        "thread_messages": thread_messages
    }

    content = json.dumps(payload, ensure_ascii=False)
    result = await Runner.run(main_agent, input=content)
    # classification = classify(thread_messages)

    # if classification.intent == "spam":
    #     return AgentDecision(
    #         action="ignore",
    #         intent=classification.intent,
    #         confidence=classification.confidence,
    #         reason="Classified as spam"``
    #     )

    # if classification.confidence < 0.8:
    #     return AgentDecision(
    #         action="escalate",
    #         intent=classification.intent,
    #         confidence=classification.confidence,
    #         reason="Low confidence"
    #     )

    # # auto-reply path (no send yet)
    # _reply = draft_reply(thread_messages)

    # return AgentDecision(
    #     action="auto_reply",
    #     intent=classification.intent,
    #     confidence=classification.confidence,
    #     reason="High confidence support request",
    #     reply_sent=False  # IMPORTANT: no side effects yet
    # )
    return result.final_output_as(AgentDecision)
