from typing import Annotated

from cryptography.fernet import InvalidToken
from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Query, status

from app.api.deps import DatabaseSession, get_optional_user
from app.api.v1.endpoints.chat import _anonymous_id, _ensure_session_owner
from app.core.ai_providers import PROVIDERS
from app.core.security import decrypt_secret
from app.crud import chat as chat_crud
from app.crud.ai_key import get_active_admin_key
from app.models.book import Book
from app.models.user import User
from app.schemas.ai import AiStatus, ChatRequest, ChatResponse, RecommendationResponse
from app.schemas.ai_key import AIProviderRead
from app.services.guardrails import verify_prompt_safety
from app.services.llm_chat import LLMError, generate_chat_response
from app.services.recommender import (
    answer_chat,
    build_recommendations,
    category_names,
)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/providers", response_model=list[AIProviderRead])
def list_providers() -> list[AIProviderRead]:
    return [
        AIProviderRead(
            slug=provider.slug,
            name=provider.name,
            key_prefix=provider.key_prefix,
            console_url=provider.console_url,
            description=provider.description,
        )
        for provider in PROVIDERS.values()
    ]


@router.get("/status", response_model=AiStatus)
def ai_status(db: DatabaseSession) -> AiStatus:
    key = get_active_admin_key(db)
    return AiStatus(provider=key.provider if key else None)


@router.get("/recommendations", response_model=RecommendationResponse)
def recommendations(
    db: DatabaseSession,
    current_user: Annotated[User | None, Depends(get_optional_user)],
    limit: Annotated[int, Query(ge=1, le=8)] = 4,
) -> RecommendationResponse:
    books, reason = build_recommendations(db, current_user, limit=limit)
    return RecommendationResponse(reason=reason, items=books)


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: DatabaseSession,
    current_user: Annotated[User | None, Depends(get_optional_user)],
    anon_id_header: Annotated[str | None, Header(alias="X-Anonymous-ID")] = None,
    anon_id_cookie: Annotated[str | None, Cookie(alias="anon_id")] = None,
) -> ChatResponse:
    anon_id = _anonymous_id(anon_id_header, anon_id_cookie)
    if payload.session_id:
        chat_session = chat_crud.get_session_with_messages(db, payload.session_id)
        if chat_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found.",
            )
        _ensure_session_owner(chat_session, current_user, anon_id)
    else:
        chat_session = chat_crud.create_session(
            db,
            user_id=current_user.id if current_user is not None else None,
            anon_id=anon_id if current_user is None else None,
        )
    session_id = str(chat_session.id)

    key = get_active_admin_key(db)
    api_key: str | None = None
    if key is not None:
        try:
            api_key = decrypt_secret(key.encrypted_key)
        except InvalidToken:
            api_key = None

    chat_crud.create_message(db, session_id, role="user", content=payload.message)

    if api_key is not None:
        is_safe, refusal = verify_prompt_safety(payload.message, api_key)
        if not is_safe:
            chat_crud.create_message(db, session_id, role="model", content=refusal)
            return ChatResponse(
                reply=refusal,
                suggestions=[],
                books=[],
                source="guardrail",
                session_id=session_id,
            )

    reply, suggestions, books = answer_chat(db, payload.message, current_user)
    local = ChatResponse(
        reply=reply, suggestions=suggestions, books=books, session_id=session_id
    )

    if api_key is None:
        if key is not None:
            local.notice = (
                f"Could not unlock the administrator's {PROVIDERS[key.provider].name} "
                "key — showing local picks."
            )
        chat_crud.create_message(db, session_id, role="model", content=local.reply)
        return local

    # Ground the model in real catalog rows: this message's matches plus
    # personal favourites, so it can never invent titles.
    pool: dict[int, Book] = {}
    for group in (books, build_recommendations(db, current_user, limit=4)[0]):
        for book in group:
            pool.setdefault(book.id, book)
    candidates = list(pool.values())[:16]

    history = chat_crud.get_session_with_messages(db, session_id).messages[-20:]
    try:
        answer = generate_chat_response(
            provider=key.provider,
            api_key=api_key,
            history=history,
            session_id=session_id,
            books=candidates,
            categories=category_names(db),
            db=db,
            current_user=current_user,
        )
    except LLMError as exc:
        local.notice = f"{PROVIDERS[key.provider].name}: {exc} Showing local picks instead."
        chat_crud.create_message(db, session_id, role="model", content=local.reply)
        return local

    return ChatResponse(
        reply=answer.reply,
        suggestions=answer.suggestions or suggestions,
        books=[pool[book_id] for book_id in answer.book_ids if book_id in pool],
        source=key.provider,
        session_id=session_id,
    )
