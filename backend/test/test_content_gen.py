from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException

from app.api.v1.endpoints import admin
from app.schemas.ai import GenerateDescRequest
from app.services import content_gen


def test_generate_book_description_sends_gemini_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_data: dict[str, object] = {}

    def fake_post(url: str, **kwargs: object) -> httpx.Response:
        request_data["url"] = url
        request_data.update(kwargs)
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"parts": [{"text": "  Mô tả sách.  "}]}}
                ]
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(content_gen.httpx, "post", fake_post)

    description = content_gen.generate_book_description(
        "Python cơ bản", "Tác giả", "Lập trình", "test-key"
    )

    assert description == "Mô tả sách."
    assert request_data["url"].endswith("?key=test-key")
    assert request_data["timeout"] == 30.0
    assert "Python cơ bản" in request_data["json"]["contents"][0]["parts"][0]["text"]


def test_generate_book_description_returns_fallback_on_api_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(
            503,
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(content_gen.httpx, "post", fake_post)

    description = content_gen.generate_book_description(
        "Title", "Author", "Category", "test-key"
    )

    assert description == "Không thể tạo mô tả sách lúc này. Vui lòng thử lại sau."


def test_admin_description_uses_active_key_and_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        admin,
        "get_active_admin_key",
        lambda _db: SimpleNamespace(
            encrypted_key="encrypted-key",
            provider="gemini",
        ),
    )
    monkeypatch.setattr(admin, "decrypt_secret", lambda _value: "api-key")
    generated: dict[str, str] = {}

    def fake_generate_book_description(**kwargs: str) -> str:
        generated.update(kwargs)
        return "Generated description"

    monkeypatch.setattr(
        admin, "generate_book_description", fake_generate_book_description
    )

    result = admin.generate_description(
        GenerateDescRequest(title="Title", author="Author", category="Category"),
        None,
    )

    assert result.description == "Generated description"
    assert generated == {
        "title": "Title",
        "author": "Author",
        "category": "Category",
        "api_key": "api-key",
        "provider": "gemini",
    }


def test_admin_description_requires_active_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(admin, "get_active_admin_key", lambda _db: None)

    with pytest.raises(HTTPException) as exc_info:
        admin.generate_description(
            GenerateDescRequest(title="Title", author="Author", category="Category"),
            None,
        )

    assert exc_info.value.status_code == 400
