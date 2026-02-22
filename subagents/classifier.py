from subagents.schemas import ClassificationResult
from agents import Agent, Runner
import asyncio
from dotenv import load_dotenv

load_dotenv(override=True)

classifier_agent = Agent(
    name="ClassifierAgent",
    model="gpt-5-nano",
    instructions="""
    Classify the email intent.
    Return JSON matching Classification.
    """,
    output_type=ClassificationResult
)


async def classify(thread_messages: list[str]) -> ClassificationResult:
    result = await Runner.run(
        classifier_agent,
        input={"thread_messages": thread_messages}
    )
    return result.final_output_as(ClassificationResult)
