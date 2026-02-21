from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService


router = APIRouter()
chat_service = ChatService()


@router.post("/message", response_model=ChatResponse)
async def send_message(payload: ChatRequest) -> ChatResponse:
    result = await chat_service.send_message(message=payload.message, session_id=payload.session_id)
    return ChatResponse(**result)
