from typing import List, Optional
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the speaker: 'user' or 'assistant'")
    content: str = Field(..., description="The textual content of the message")

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The incoming user query")
    history: List[ChatMessage] = Field(default=[], description="Previous chat logs")