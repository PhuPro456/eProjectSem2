from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.chat import ChatMessage, ChatSession


def _parse_session_id(session_id: str) -> UUID | None:
    try:
        return UUID(session_id)
    except (AttributeError, TypeError, ValueError):
        return None


def create_session(
    db: Session, user_id: int | None, anon_id: str | None
) -> ChatSession:
    chat_session = ChatSession(user_id=user_id, anon_id=anon_id)
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)
    return chat_session


def get_user_sessions(
    db: Session,
    user_id: int | None,
    anon_id: str | None,
    skip: int = 0,
    limit: int = 20,
) -> list[ChatSession]:
    if user_id is not None:
        stmt = select(ChatSession).where(ChatSession.user_id == user_id)
    elif anon_id:
        stmt = select(ChatSession).where(
            ChatSession.user_id.is_(None),
            ChatSession.anon_id == anon_id,
        )
    else:
        return []

    stmt = (
        stmt.order_by(ChatSession.started_at.desc(), ChatSession.id.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def get_session_with_messages(db: Session, session_id: str) -> ChatSession | None:
    parsed_id = _parse_session_id(session_id)
    if parsed_id is None:
        return None

    stmt = (
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.id == parsed_id)
    )
    return db.execute(stmt).scalars().first()


def delete_session(db: Session, session_id: str) -> bool:
    parsed_id = _parse_session_id(session_id)
    if parsed_id is None:
        return False

    exists = db.execute(
        select(ChatSession.id).where(ChatSession.id == parsed_id)
    ).scalar_one_or_none()
    if exists is None:
        return False

    db.execute(delete(ChatMessage).where(ChatMessage.session_id == parsed_id))
    result = db.execute(delete(ChatSession).where(ChatSession.id == parsed_id))
    db.commit()
    return bool(result.rowcount)


def create_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    tool_calls: dict[str, Any] | None = None,
) -> ChatMessage:
    parsed_id = _parse_session_id(session_id)
    if parsed_id is None:
        raise ValueError("Invalid chat session ID.")
    chat_session = db.get(ChatSession, parsed_id)
    if chat_session is None:
        raise LookupError("Chat session not found.")

    message = ChatMessage(
        session=chat_session,
        role=role,
        content=content,
        tool_calls=tool_calls if tool_calls is not None else {},
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message