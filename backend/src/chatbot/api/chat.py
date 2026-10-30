from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from chatbot.db import get_session
from chatbot.errors import ApiError
from chatbot.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationHistoryResponse,
    MessageOut,
)
from chatbot.services import ChatService, ConversationNotFoundError

router = APIRouter(prefix="/api/chat", tags=["chat"])


def get_chat_service(
    request: Request, session: Annotated[AsyncSession, Depends(get_session)]
) -> ChatService:
    return ChatService(session, request.app.state.graph, request.app.state.settings)


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]


@router.post("/message")
async def post_message(body: ChatMessageRequest, service: ChatServiceDep) -> ChatMessageResponse:
    try:
        ai_message = await service.handle_message(body.message, body.session_id)
    except ConversationNotFoundError as exc:
        raise ApiError(404, "Session not found") from exc
    return ChatMessageResponse(
        reply=ai_message.text,
        session_id=ai_message.conversation_id,
        message_id=ai_message.id,
        timestamp=ai_message.timestamp,
    )


@router.get("/message")
async def get_history(
    service: ChatServiceDep,
    session_id: Annotated[str | None, Query(alias="sessionId")] = None,
) -> ConversationHistoryResponse:
    if not session_id:
        raise ApiError(400, "sessionId is required")
    try:
        conversation = await service.get_history(session_id)
    except ConversationNotFoundError as exc:
        raise ApiError(404, "Session not found") from exc
    return ConversationHistoryResponse(
        session_id=conversation.id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            MessageOut(id=m.id, sender=m.sender, text=m.text, timestamp=m.timestamp)
            for m in conversation.messages
        ],
    )
