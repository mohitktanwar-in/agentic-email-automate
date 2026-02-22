from pydantic import BaseModel, Field
from typing import Literal, Optional


class ClassificationResult(BaseModel):
    intent: str = Field(description="Choose only one from these four: sales | support | spam | human")
    confidence: float = Field(description="How confident are you in your classification?" ,ge=0.0, le=1.0)


class AgentDecision(BaseModel):
    action: Literal["auto_reply", "escalate", "ignore"]
    intent: Optional[str] 
    confidence: Optional[float] 
    reason: str = Field(description="What is the reason behind chosen decision?")
    # reply_sent: bool = False

class DraftReply(BaseModel):
    subject: Optional[str]   # allow None → reuse original subject
    body: str                # plain text only for now
    confidence: float        # how confident the agent is in this draft
