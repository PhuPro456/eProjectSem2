from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
from fastapi import HTTPException


def test_generate_admin_summary_uses_current_database_metrics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import admin_copilot

    db = Mock()
    db.scalar.side_effect = [7, 4, Decimal("125.50"), 4.5]
    request_data: dict[str, object] = {}

    def fake_post(url: str, **kwargs: object) -> httpx.Response:
        request_data["url"] = url
        request_data.update(kwargs)
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"parts": [{"text": "Báo cáo kinh doanh."}]}}
                ]
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(admin_copilot.httpx, "post", fake_post)

    summary = admin_copilot.generate_admin_summary(db, "test-key")

    prompt = request_data["json"]["contents"][0]["parts"][0]["text"]
    assert summary == "Báo cáo kinh doanh."
    assert request_data["url"].endswith("?key=test-key")
    assert "Tổng người dùng (7)" in prompt
    assert "Tổng đơn hàng (4)" in prompt
    assert "Tổng doanh thu (125.50 VNĐ)" in prompt
    assert "Điểm đánh giá trung bình (4.5/5)" in prompt


def test_generate_admin_summary_defaults_empty_metrics_and_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import admin_copilot

    db = Mock()
    db.scalar.side_effect = [None, None, None, None]
    request_data: dict[str, object] = {}

    def fake_post(url: str, **kwargs: object) -> httpx.Response:
        request_data.update(kwargs)
        return httpx.Response(503, request=httpx.Request("POST", url))

    monkeypatch.setattr(admin_copilot.httpx, "post", fake_post)

    summary = admin_copilot.generate_admin_summary(db, "test-key")

    prompt = request_data["json"]["contents"][0]["parts"][0]["text"]
    assert summary == "Không thể tạo báo cáo lúc này."
    assert "Tổng người dùng (0)" in prompt
    assert "Tổng đơn hàng (0)" in prompt
    assert "Tổng doanh thu (0 VNĐ)" in prompt
    assert "Điểm đánh giá trung bình (0/5)" in prompt


def test_copilot_summary_endpoint_uses_active_decrypted_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.api.v1.endpoints import admin

    monkeypatch.setattr(
        admin,
        "get_active_admin_key",
        lambda _db: SimpleNamespace(encrypted_key="encrypted-key"),
    )
    monkeypatch.setattr(admin, "decrypt_secret", lambda _value: "api-key")
    calls: list[tuple[object, str]] = []

    def fake_generate_summary(db: object, api_key: str) -> str:
        calls.append((db, api_key))
        return "Summary"

    monkeypatch.setattr(admin, "generate_admin_summary", fake_generate_summary)
    db = object()

    response = admin.copilot_summary(db)

    assert response.summary == "Summary"
    assert calls == [(db, "api-key")]


def test_copilot_summary_endpoint_requires_active_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.api.v1.endpoints import admin

    monkeypatch.setattr(admin, "get_active_admin_key", lambda _db: None)

    with pytest.raises(HTTPException) as exc_info:
        admin.copilot_summary(object())

    assert exc_info.value.status_code == 400
