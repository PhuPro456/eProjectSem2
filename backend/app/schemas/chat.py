from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ChatRole = Literal["user", "model", "system", "tool"]


class ChatSessionBase(BaseModel):
    anon_id: str | None = None


class ChatSessionCreate(ChatSessionBase):
    pass


class ChatSessionRead(ChatSessionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: int | None
    started_at: datetime


class ChatMessageBase(BaseModel):
    role: ChatRole
    content: str
    tool_calls: dict[str, Any] | list[dict[str, Any]] | None = Field(
        default_factory=dict
    )


class ChatMessageCreate(ChatMessageBase):
    session_id: UUID


class ChatMessageRead(ChatMessageBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: UUID
    created_at: datetime


class ChatSessionWithMessagesRead(ChatSessionRead):
    messages: list[ChatMessageRead]