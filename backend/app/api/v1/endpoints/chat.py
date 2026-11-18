from typing import Annotated

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    Header,
    HTTPException,
    Query,
    Response,
    status,
)

from app.api.deps import DatabaseSession, get_optional_user
from app.crud import chat as chat_crud
from app.models.chat import ChatSession
from app.models.user import User
from app.schemas.chat import ChatSessionRead, ChatSessionWithMessagesRead

router = APIRouter(prefix="/ai/chat/sessions", tags=["chat-history"])


def _anonymous_id(header_id: str | None, cookie_id: str | None) -> str | None:
    for candidate in (header_id, cookie_id):
        if candidate and candidate.strip():
            return candidate.strip()
    return None


def _ensure_session_owner(
    chat_session: ChatSession,
    current_user: User | None,
    anon_id: str | None,
) -> None:
    if current_user is not None and chat_session.user_id == current_user.id:
        return
    if (
        current_user is None
        and anon_id is not None
        and chat_session.user_id is None
        and chat_session.anon_id == anon_id
    ):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have access to this chat session.",
    )


@router.get("", response_model=list[ChatSessionRead])
def list_chat_sessions(
    db: DatabaseSession,
    current_user: Annotated[User | None, Depends(get_optional_user)],
    anon_id_header: Annotated[str | None, Header(alias="X-Anonymous-ID")] = None,
    anon_id_cookie: Annotated[str | None, Cookie(alias="anon_id")] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[ChatSessionRead]:
    anon_id = _anonymous_id(anon_id_header, anon_id_cookie)
    sessions = chat_crud.get_user_sessions(
        db,
        user_id=current_user.id if current_user is not None else None,
        anon_id=anon_id,
        skip=skip,
        limit=limit,
    )
    return [ChatSessionRead.model_validate(session) for session in sessions]


@router.get("/{session_id}", response_model=ChatSessionWithMessagesRead)
def get_chat_session(
    session_id: str,
    db: DatabaseSession,
    current_user: Annotated[User | None, Depends(get_optional_user)],
    anon_id_header: Annotated[str | None, Header(alias="X-Anonymous-ID")] = None,
    anon_id_cookie: Annotated[str | None, Cookie(alias="anon_id")] = None,
) -> ChatSessionWithMessagesRead:
    chat_session = chat_crud.get_session_with_messages(db, session_id)
    if chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )
    _ensure_session_owner(
        chat_session,
        current_user,
        _anonymous_id(anon_id_header, anon_id_cookie),
    )
    return ChatSessionWithMessagesRead.model_validate(chat_session)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_chat_session(
    session_id: str,
    db: DatabaseSession,
    current_user: Annotated[User | None, Depends(get_optional_user)],
    anon_id_header: Annotated[str | None, Header(alias="X-Anonymous-ID")] = None,
    anon_id_cookie: Annotated[str | None, Cookie(alias="anon_id")] = None,
) -> Response:
    chat_session = chat_crud.get_session_with_messages(db, session_id)
    if chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )
    _ensure_session_owner(
        chat_session,
        current_user,
        _anonymous_id(anon_id_header, anon_id_cookie),
    )
    if not chat_crud.delete_session(db, session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)