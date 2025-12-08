from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import uuid

class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    summary: str = ""  # The "Rolling Summary" of the conversation so far
    recent_messages: List[Message] = []  # The last N messages (raw)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatRequest(BaseModel):
    session_id: Optional[str] = None  # If None, create new session
    message: str

class ChatResponse(BaseModel):
    session_id: str
    response: str
    history_summary: str  # return summary for debugging
