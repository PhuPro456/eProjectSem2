from collections.abc import Generator
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db, get_optional_user
from app.api.v1.endpoints import ai as ai_endpoint
from app.api.v1.endpoints.chat import router
from app.crud import chat as chat_crud
from app.db.session import Base
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User
from app.schemas.chat import ChatMessageRead, ChatSessionRead


def _client(db: Session, user: User | None) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_optional_user] = lambda: user
    return TestClient(app)


def _ai_client(db: Session, user: User | None) -> TestClient:
    app = FastAPI()
    app.include_router(ai_endpoint.router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_optional_user] = lambda: user
    return TestClient(app)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        yield session
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_chat_models_persist_and_serialize_relationships(db: Session) -> None:
    user = User(
        name="Reader",
        email="reader@example.com",
        hashed_password="not-used",
    )
    chat_session = ChatSession(user=user, anon_id="anonymous-session")
    chat_session.messages.append(ChatMessage(role="user", content="Hello"))
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)

    session_read = ChatSessionRead.model_validate(chat_session)
    message_read = ChatMessageRead.model_validate(chat_session.messages[0])

    assert isinstance(session_read.id, UUID)
    assert session_read.user_id == user.id
    assert session_read.anon_id == "anonymous-session"
    assert message_read.session_id == session_read.id
    assert message_read.role == "user"
    assert message_read.tool_calls == {}


def test_chat_history_routes_enforce_user_and_anonymous_ownership(
    db: Session,
) -> None:
    user = User(
        name="Reader",
        email="reader@example.com",
        hashed_password="not-used",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user_session = chat_crud.create_session(db, user.id, None)

    anon_session = chat_crud.create_session(db, None, "anon-123")
    chat_crud.create_message(db, str(anon_session.id), "user", "Hello")

    with _client(db, user) as client:
        user_sessions = client.get("/ai/chat/sessions")
        assert user_sessions.status_code == 200
        assert [item["id"] for item in user_sessions.json()] == [
            str(user_session.id)
        ]
        denied_anon_session = client.get(
            f"/ai/chat/sessions/{anon_session.id}",
            headers={"X-Anonymous-ID": "anon-123"},
        )
        assert denied_anon_session.status_code == 403

    with _client(db, None) as client:
        anon_sessions = client.get(
            "/ai/chat/sessions", headers={"X-Anonymous-ID": "anon-123"}
        )
        assert anon_sessions.status_code == 200
        assert [item["id"] for item in anon_sessions.json()] == [
            str(anon_session.id)
        ]

        client.cookies.set("anon_id", "anon-123")
        details = client.get(f"/ai/chat/sessions/{anon_session.id}")
        assert details.status_code == 200
        assert details.json()["messages"][0]["content"] == "Hello"

        denied_delete = client.delete(
            f"/ai/chat/sessions/{anon_session.id}",
            headers={"X-Anonymous-ID": "another-anon"},
        )
        assert denied_delete.status_code == 403

        deleted = client.delete(
            f"/ai/chat/sessions/{anon_session.id}",
            headers={"X-Anonymous-ID": "anon-123"},
        )
        assert deleted.status_code == 204

    assert chat_crud.get_session_with_messages(db, str(anon_session.id)) is None


def test_ai_chat_persists_turns_and_returns_session_id(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        ai_endpoint,
        "answer_chat",
        lambda db, message, user: ("Local reply", ["Ask another question"], []),
    )
    monkeypatch.setattr(ai_endpoint, "get_active_admin_key", lambda db: None)

    with _ai_client(db, None) as client:
        first = client.post(
            "/ai/chat",
            headers={"X-Anonymous-ID": "anon-chat"},
            json={"message": "Hello"},
        )
        assert first.status_code == 200
        session_id = first.json()["session_id"]

        forbidden = client.post(
            "/ai/chat",
            headers={"X-Anonymous-ID": "other-anon"},
            json={"message": "Do not save me", "session_id": session_id},
        )
        assert forbidden.status_code == 403

        second = client.post(
            "/ai/chat",
            headers={"X-Anonymous-ID": "anon-chat"},
            json={"message": "How are you?", "session_id": session_id},
        )
        assert second.status_code == 200
        assert second.json()["session_id"] == session_id

    saved_session = chat_crud.get_session_with_messages(db, session_id)
    assert saved_session is not None
    assert [(message.role, message.content) for message in saved_session.messages] == [
        ("user", "Hello"),
        ("model", "Local reply"),
        ("user", "How are you?"),
        ("model", "Local reply"),
    ]


def test_ai_chat_blocks_unsafe_prompt_and_persists_refusal(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unexpected_local_search(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Blocked prompts must not start local recommendation search")

    monkeypatch.setattr(ai_endpoint, "answer_chat", unexpected_local_search)
    monkeypatch.setattr(
        ai_endpoint,
        "get_active_admin_key",
        lambda db: SimpleNamespace(
            provider="gemini",
            encrypted_key="encrypted-key",
        ),
    )
    monkeypatch.setattr(ai_endpoint, "decrypt_secret", lambda value: "api-key")
    safety_calls: list[tuple[str, str]] = []

    def block_prompt(message: str, api_key: str) -> tuple[bool, str]:
        safety_calls.append((message, api_key))
        return False, "Tin nhắn không phù hợp."

    monkeypatch.setattr(ai_endpoint, "verify_prompt_safety", block_prompt)

    with _ai_client(db, None) as client:
        response = client.post(
            "/ai/chat",
            headers={"X-Anonymous-ID": "guardrail-test"},
            json={"message": "An unsafe prompt"},
        )

    assert response.status_code == 200
    result = response.json()
    assert result["reply"] == "Tin nhắn không phù hợp."
    assert result["suggestions"] == []
    assert result["books"] == []
    assert result["source"] == "guardrail"
    assert safety_calls == [("An unsafe prompt", "api-key")]

    session = chat_crud.get_session_with_messages(db, result["session_id"])
    assert session is not None
    assert [(message.role, message.content) for message in session.messages] == [
        ("user", "An unsafe prompt"),
        ("model", "Tin nhắn không phù hợp."),
    ]
