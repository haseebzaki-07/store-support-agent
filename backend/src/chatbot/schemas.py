"""API schemas.

The JSON contract is camelCase and is consumed by web/app/page.tsx. Do not change field
names or shapes without updating the UI.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from chatbot.models import MessageSender


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ChatMessageRequest(CamelModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None


class ChatMessageResponse(CamelModel):
    reply: str
    session_id: str
    message_id: str
    timestamp: datetime


class MessageOut(CamelModel):
    id: str
    sender: MessageSender
    text: str
    timestamp: datetime


class ConversationHistoryResponse(CamelModel):
    session_id: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageOut]


class ErrorDetail(CamelModel):
    path: list[str | int]
    message: str


class ErrorResponse(CamelModel):
    error: str
    message: str | None = None
    details: list[ErrorDetail] | None = None
