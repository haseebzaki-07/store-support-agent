from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from chatbot.agent import AgentGraph, run_agent
from chatbot.config import Settings
from chatbot.llm import LLMMessage
from chatbot.models import Conversation, Message, MessageSender
from chatbot.prompts import SYSTEM_PROMPT


class ConversationNotFoundError(Exception):
    pass


class ChatService:
    def __init__(self, session: AsyncSession, graph: AgentGraph, settings: Settings) -> None:
        self._session = session
        self._graph = graph
        self._settings = settings

    async def handle_message(self, text: str, session_id: str | None) -> Message:
        """Store the user's message, run the agent, store and return the AI reply."""
        conversation = await self._load_or_create(session_id)
        history = await self._recent_messages(conversation.id)

        self._session.add(
            Message(conversation_id=conversation.id, sender=MessageSender.USER, text=text)
        )
        # Commit before calling the agent so the user's message is kept if generation fails.
        await self._session.commit()

        llm_messages = [
            LLMMessage("system", SYSTEM_PROMPT),
            *(
                LLMMessage("user" if m.sender == MessageSender.USER else "assistant", m.text)
                for m in history
            ),
            LLMMessage("user", text),
        ]
        reply = await run_agent(self._graph, llm_messages)

        ai_message = Message(conversation_id=conversation.id, sender=MessageSender.AI, text=reply)
        self._session.add(ai_message)
        conversation.updated_at = datetime.now(UTC)
        await self._session.commit()
        return ai_message

    async def get_history(self, session_id: str) -> Conversation:
        conversation = await self._session.get(
            Conversation, session_id, options=[selectinload(Conversation.messages)]
        )
        if conversation is None:
            raise ConversationNotFoundError(session_id)
        return conversation

    async def _load_or_create(self, session_id: str | None) -> Conversation:
        if session_id is None:
            conversation = Conversation(meta={"startedAt": datetime.now(UTC).isoformat()})
            self._session.add(conversation)
            await self._session.flush()  # assigns the id
            return conversation
        conversation = await self._session.get(Conversation, session_id)
        if conversation is None:
            raise ConversationNotFoundError(session_id)
        return conversation

    async def _recent_messages(self, conversation_id: str) -> list[Message]:
        rows = await self._session.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp.desc())
            .limit(self._settings.history_window)
        )
        return list(reversed(rows.all()))
