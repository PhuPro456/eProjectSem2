import logging

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.review import Review
from app.models.user import User
from app.services.llm_chat import ssl_context

logger = logging.getLogger(__name__)


def generate_admin_summary(db: Session, api_key: str) -> str:
    total_users = db.scalar(select(func.count(User.id))) or 0
    total_orders = db.scalar(select(func.count(Order.id))) or 0
    total_revenue = db.scalar(select(func.sum(Order.total))) or 0
    avg_rating = db.scalar(select(func.avg(Review.rating))) or 0

    prompt = (
        "Bạn là trợ lý AI Copilot của Bookstore Pro. Dựa vào các số liệu kinh doanh "
        f"hiện tại: Tổng người dùng ({total_users}), Tổng đơn hàng ({total_orders}), "
        f"Tổng doanh thu ({total_revenue} VNĐ), Điểm đánh giá trung bình "
        f"({avg_rating}/5). Hãy viết một đoạn tóm tắt ngắn gọn, chuyên nghiệp "
        "(khoảng 2 đoạn văn) báo cáo tình hình kinh doanh và đề xuất 1 hành động "
        "cải thiện. Trả về text thuần, không markdown."
    )
    fallback = "Không thể tạo báo cáo lúc này."

    try:
        response = httpx.post(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-3.6-flash:generateContent?key={api_key}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30.0,
            verify=ssl_context(),
        )
        response.raise_for_status()
        summary = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        if not isinstance(summary, str) or not summary.strip():
            raise ValueError("Gemini returned an empty summary.")
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        logger.warning(
            "Admin copilot summary generation failed (%s).",
            type(exc).__name__,
        )
        return fallback

    return summary.strip()