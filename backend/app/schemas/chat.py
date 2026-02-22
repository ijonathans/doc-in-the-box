from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    state: dict[str, Any]
    needs_emergency: bool
    handoff_ready: bool
    outbound_call_started: bool = False
    outbound_call_error: str = ""
