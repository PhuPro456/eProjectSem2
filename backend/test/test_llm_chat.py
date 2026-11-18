from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from sqlalchemy.orm import Session

from app.crud import chat as chat_crud
from app.models.book import Book
from app.models.chat import ChatMessage
from app.models.user import User
from app.services import ai_tools
from app.services import llm_chat


def _response(message: dict[str, Any]) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": message}]})


def test_generate_chat_response_uses_db_history_and_executes_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = [
        _response(
            {
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {
                            "name": "get_order_status",
                            "arguments": '{"order_id": 42}',
                        },
                    },
                    {
                        "id": "call-2",
                        "type": "function",
                        "function": {
                            "name": "get_order_status",
                            "arguments": "not-json",
                        },
                    },
                ],
            }
        ),
        _response(
            {
                "content": '{"reply":"Your order is being shipped.","book_ids":[],"suggestions":[]}',
                "tool_calls": [],
            }
        ),
    ]
    requests: list[dict[str, Any]] = []
    tool_context: list[tuple[str, dict[str, Any], Session, User | None]] = []
    saved_messages: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    db = Session()
    user = User(name="Reader", email="reader@example.com", hashed_password="unused")
    session_id = "00000000-0000-0000-0000-000000000001"
    books: list[Book] = []
    categories: dict[str, str] = {}
    history = [
        ChatMessage(role="user", content="I placed order 42."),
        ChatMessage(role="model", content="I can check that."),
        ChatMessage(role="user", content="Where is it?"),
    ]

    def fake_post(url: str, **kwargs: Any) -> httpx.Response:
        requests.append(
            {
                **kwargs,
                "json": {
                    **kwargs["json"],
                    "messages": list(kwargs["json"]["messages"]),
                },
            }
        )
        return responses.pop(0)

    def fake_execute_tool(
        name: str,
        arguments: dict[str, Any],
        session: Session,
        current_user: User | None,
    ) -> dict[str, str]:
        tool_context.append((name, arguments, session, current_user))
        return {"status": "shipped"}

    def fake_create_message(*args: Any, **kwargs: Any) -> None:
        saved_messages.append((args, kwargs))

    monkeypatch.setattr(llm_chat.httpx, "post", fake_post)
    monkeypatch.setattr(llm_chat, "execute_tool", fake_execute_tool)
    monkeypatch.setattr(chat_crud, "create_message", fake_create_message)

    answer = llm_chat.generate_chat_response(
        provider="gemini",
        api_key="test-key",
        history=history,
        session_id=session_id,
        books=books,
        categories=categories,
        db=db,
        current_user=user,
    )

    assert answer.reply == "Your order is being shipped."
    assert len(requests) == 2
    assert requests[0]["json"]["tools"] == llm_chat.CHATBOT_TOOLS
    assert requests[0]["json"]["messages"][1:] == [
        {"role": "user", "content": "I placed order 42."},
        {"role": "assistant", "content": "I can check that."},
        {"role": "user", "content": "Where is it?"},
    ]
    assert tool_context == [("get_order_status", {"order_id": 42}, db, user)]
    tool_messages = requests[1]["json"]["messages"][-2:]
    assert tool_messages == [
        {
            "role": "tool",
            "tool_call_id": "call-1",
            "content": '{"status": "shipped"}',
        },
        {
            "role": "tool",
            "tool_call_id": "call-2",
            "content": '{"error": "The tool arguments must be a JSON object."}',
        },
    ]
    assert saved_messages == [
        (
            (db, session_id),
            {"role": "model", "content": "Your order is being shipped."},
        )
    ]
    db.close()


def test_generate_chat_response_stops_after_tool_round_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests = 0

    def fake_post(url: str, **kwargs: Any) -> httpx.Response:
        nonlocal requests
        requests += 1
        return _response(
            {
                "content": None,
                "tool_calls": [
                    {
                        "id": f"call-{requests}",
                        "type": "function",
                        "function": {
                            "name": "get_order_status",
                            "arguments": '{"order_id": 42}',
                        },
                    }
                ],
            }
        )

    monkeypatch.setattr(llm_chat.httpx, "post", fake_post)
    monkeypatch.setattr(
        llm_chat,
        "execute_tool",
        lambda name, arguments, db, current_user: {"status": "shipped"},
    )
    books: list[Book] = []
    categories: dict[str, str] = {}

    with pytest.raises(llm_chat.LLMError, match="tool-call limit"):
        llm_chat.generate_chat_response(
            provider="gemini",
            api_key="test-key",
            history=[ChatMessage(role="user", content="Where is order 42?")],
            session_id="00000000-0000-0000-0000-000000000001",
            books=books,
            categories=categories,
            db=Session(),
            current_user=None,
        )

    assert requests == llm_chat.MAX_TOOL_ROUNDS + 1


@pytest.mark.parametrize("order_id", [True, 0, -1, "42", None])
def test_order_tool_rejects_invalid_order_ids(
    monkeypatch: pytest.MonkeyPatch, order_id: Any
) -> None:
    def unexpected_lookup(_db: Session, _order_id: int) -> None:
        pytest.fail("Invalid order IDs must not trigger a database lookup")

    monkeypatch.setattr(ai_tools.crud_order, "get_order", unexpected_lookup)
    user = User(name="Reader", email="reader@example.com", hashed_password="unused")

    result = ai_tools.execute_tool(
        "get_order_status", {"order_id": order_id}, Session(), user
    )

    assert "error" in result


def test_order_tool_does_not_disclose_another_users_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    order = SimpleNamespace(
        id=42,
        user_id=8,
        status="shipped",
        total=10,
    )
    monkeypatch.setattr(ai_tools.crud_order, "get_order", lambda db, order_id: order)
    user = User(name="Reader", email="reader@example.com", hashed_password="unused")
    user.id = 7

    result = ai_tools.execute_tool(
        "get_order_status", {"order_id": 42}, Session(), user
    )

    assert set(result) == {"error"}
