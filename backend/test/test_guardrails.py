import httpx
import pytest

from app.services import guardrails


@pytest.mark.parametrize(
    ("response_text", "expected"),
    [
        ("PASS", (True, "")),
        ("BLOCK: Nội dung không liên quan.", (False, "Nội dung không liên quan.")),
    ],
)
def test_verify_prompt_safety_parses_gemini_verdict(
    monkeypatch: pytest.MonkeyPatch,
    response_text: str,
    expected: tuple[bool, str],
) -> None:
    request_data: dict[str, object] = {}

    def fake_post(url: str, **kwargs: object) -> httpx.Response:
        request_data["url"] = url
        request_data.update(kwargs)
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"parts": [{"text": response_text}]}}
                ]
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(guardrails.httpx, "post", fake_post)

    result = guardrails.verify_prompt_safety("Find a book", "test-key")

    assert result == expected
    assert request_data["url"].endswith("?key=test-key")
    assert "Find a book" in request_data["json"]["contents"][0]["parts"][0]["text"]


def test_verify_prompt_safety_blocks_long_messages_without_api_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        guardrails.httpx,
        "post",
        lambda *args, **kwargs: pytest.fail("Long messages must not call Gemini"),
    )

    result = guardrails.verify_prompt_safety("x" * 1001, "test-key")

    assert result == (False, "Tin nhắn quá dài, vui lòng rút gọn lại.")


def test_verify_prompt_safety_fails_open_on_network_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_post(url: str, **kwargs: object) -> httpx.Response:
        raise httpx.TimeoutException(
            "Request timed out",
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(guardrails.httpx, "post", fail_post)

    assert guardrails.verify_prompt_safety("Find a book", "test-key") == (True, "")
