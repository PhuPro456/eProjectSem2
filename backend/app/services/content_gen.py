import logging

import httpx

from app.services.llm_chat import ssl_context

logger = logging.getLogger(__name__)


def generate_book_description(
    title: str,
    author: str,
    category: str,
    api_key: str,
    provider: str = "gemini",
) -> str:
    if provider != "gemini":
        raise ValueError(f"Unsupported AI provider for description generation: {provider}")

    prompt = (
        "Write a compelling, SEO-friendly book description in Vietnamese for the "
        f"book '{title}' by '{author}' in the '{category}' category. The description "
        "should be engaging, around 3-4 paragraphs. Return ONLY the description text "
        "without any markdown formatting or prefix."
    )
    fallback = "Không thể tạo mô tả sách lúc này. Vui lòng thử lại sau."

    try:
        response = httpx.post(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-3.6-flash:generateContent?key={api_key}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30.0,
            verify=ssl_context(),
        )
        response.raise_for_status()
        description = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        if not isinstance(description, str) or not description.strip():
            raise ValueError("Gemini returned an empty description.")
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        logger.warning(
            "Gemini book-description generation failed (%s).",
            type(exc).__name__,
        )
        return fallback

    return description.strip()