import json
import re
import ssl
import time
from dataclasses import dataclass
from functools import lru_cache

import httpx
import truststore
from sqlalchemy.orm import Session

from app.crud import chat as chat_crud
from app.models.book import Book
from app.models.chat import ChatMessage
from app.models.user import User
from app.services.ai_tools import CHATBOT_TOOLS, execute_tool


@dataclass(frozen=True)
class Endpoint:
    base_url: str
    model: str


# Gemini exposes an OpenAI-compatible /chat/completions route.
# Model must be a valid GA ID; "gemini-3.5-flash" does not exist (only -lite does).
ENDPOINTS: dict[str, Endpoint] = {
    "gemini": Endpoint("https://generativelanguage.googleapis.com/v1beta/openai", "gemini-3.6-flash"),
}

SYSTEM_PROMPT = """You are the friendly bookseller assistant of "Bookstore Pro", an online shop
with books of every kind — programming, computer science and AI, plus manga, romance, humor,
light reads, magazines and fantasy. Answer in the user's language, in 1-4 short sentences.
Only recommend books from the CATALOG list below — never invent titles, prices or stock.
If nothing in the list fits, say so and suggest how to rephrase. You may answer short general
questions about the topics, but keep the focus on helping the reader choose a book.

Reply with JSON only, no markdown:
{"reply": "<text>", "book_ids": [<up to 3 ids from CATALOG, best first>],
 "suggestions": ["<up to 4 short follow-up prompts the user could click>"]}

CATALOG:
"""


class LLMError(Exception):
    pass


MAX_TOOL_ROUNDS = 3


@lru_cache(maxsize=1)
def ssl_context() -> ssl.SSLContext:
    # OS trust store, so TLS-inspecting proxies/antivirus with a local root CA still verify.
    return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)


@dataclass
class LLMAnswer:
    reply: str
    book_ids: list[int]
    suggestions: list[str]


def _catalog_lines(books: list[Book], categories: dict[str, str]) -> str:
    lines = []
    for book in books:
        description = " ".join((book.description or "").split())[:220]
        lines.append(
            f"- id={book.id} | {book.title} | {book.author} | "
            f"{categories.get(book.category_code, book.category_code)} | ${book.price} | "
            f"stock {book.stock} | {description}"
        )
    return "\n".join(lines)


def _parse(content: str, allowed_ids: set[int]) -> LLMAnswer:
    match = re.search(r"\{.*\}", content, re.DOTALL)
    try:
        data = json.loads(match.group(0)) if match else {}
    except json.JSONDecodeError:
        data = {}
    if not isinstance(data, dict) or not str(data.get("reply", "")).strip():
        # Model ignored the JSON format: still show its text.
        return LLMAnswer(reply=content.strip()[:1500], book_ids=[], suggestions=[])

    ids: list[int] = []
    for value in data.get("book_ids") or []:
        try:
            book_id = int(value)
        except (TypeError, ValueError):
            continue
        if book_id in allowed_ids and book_id not in ids:
            ids.append(book_id)
    suggestions = [str(s).strip()[:60] for s in (data.get("suggestions") or []) if str(s).strip()]
    return LLMAnswer(reply=str(data["reply"]).strip()[:1500], book_ids=ids[:3], suggestions=suggestions[:4])


def _error_message(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return ""
    if isinstance(data, list) and data:
        data = data[0]
    error = data.get("error") if isinstance(data, dict) else None
    message = error.get("message") if isinstance(error, dict) else error
    return str(message or "")[:200]


def _check_response(response: httpx.Response) -> None:
    if response.status_code in (401, 403):
        raise LLMError("The AI provider rejected the saved API key.")
    if response.status_code == 429:
        raise LLMError("The AI provider rate limit or quota was reached.")
    if response.status_code >= 400:
        detail = _error_message(response)
        if "api key" in detail.casefold():
            raise LLMError("The AI provider rejected the saved API key.")
        raise LLMError(f"The AI provider returned an error ({response.status_code}). {detail}".strip())


CHAT_MAX_ATTEMPTS = 3


def _post_chat(
    endpoint: Endpoint,
    api_key: str,
    messages: list[dict],
    timeout: float,
    tools: list[dict] | None = None,
) -> dict:
    payload: dict = {"model": endpoint.model, "messages": messages, "temperature": 0.4}
    if tools is not None:
        payload["tools"] = tools
    for attempt in range(CHAT_MAX_ATTEMPTS):
        try:
            response = httpx.post(
                f"{endpoint.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
                timeout=timeout,
                verify=ssl_context(),
            )
        except httpx.HTTPError as exc:
            raise LLMError("Could not reach the AI provider.") from exc

        # 503 is transient Google-side capacity, not our quota; a short backoff usually recovers.
        if response.status_code == 503 and attempt < CHAT_MAX_ATTEMPTS - 1:
            time.sleep(0.5 * (2**attempt))
            continue

        _check_response(response)

        try:
            return response.json()["choices"][0]["message"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMError("The AI provider sent an unexpected response.") from exc
    raise LLMError("The AI provider is busy (503). Please try again shortly.")


def ask_llm(
    provider: str,
    api_key: str,
    message: str,
    history: list[tuple[str, str]],
    books: list[Book],
    categories: dict[str, str],
    timeout: float = 25.0,
) -> LLMAnswer:
    endpoint = ENDPOINTS.get(provider)
    if endpoint is None:
        raise LLMError("Unsupported AI provider.")

    messages = [{"role": "system", "content": SYSTEM_PROMPT + _catalog_lines(books, categories)}]
    messages += [{"role": role, "content": content} for role, content in history]
    messages.append({"role": "user", "content": message})

    reply_message = _post_chat(endpoint, api_key, messages, timeout)
    return _parse(reply_message.get("content") or "", {book.id for book in books})


def generate_chat_response(
    provider: str,
    api_key: str,
    history: list[ChatMessage],
    session_id: str,
    books: list[Book],
    categories: dict[str, str],
    db: Session,
    current_user: User | None,
    timeout: float = 25.0,
) -> LLMAnswer:
    """Chat with persisted history and safe tool calling; saves the final reply."""
    endpoint = ENDPOINTS.get(provider)
    if endpoint is None:
        raise LLMError("Unsupported AI provider.")

    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT + _catalog_lines(books, categories)}
    ]
    messages += [
        {
            "role": "assistant" if item.role == "model" else item.role,
            "content": item.content,
        }
        for item in history
    ]
    allowed_ids = {book.id for book in books}

    for round_index in range(MAX_TOOL_ROUNDS + 1):
        reply_message = _post_chat(endpoint, api_key, messages, timeout, tools=CHATBOT_TOOLS)
        tool_calls = reply_message.get("tool_calls") or []
        if not tool_calls:
            answer = _parse(reply_message.get("content") or "", allowed_ids)
            chat_crud.create_message(db, session_id, role="model", content=answer.reply)
            return answer
        if round_index == MAX_TOOL_ROUNDS:
            raise LLMError("The assistant reached the tool-call limit.")

        messages.append(
            {
                "role": "assistant",
                "content": reply_message.get("content"),
                "tool_calls": tool_calls,
            }
        )
        for call in tool_calls:
            function = call.get("function") or {}
            try:
                arguments = json.loads(function.get("arguments") or "{}")
            except json.JSONDecodeError:
                arguments = None
            if isinstance(arguments, dict):
                result = execute_tool(function.get("name", ""), arguments, db, current_user)
            else:
                result = {"error": "The tool arguments must be a JSON object."}
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id"),
                    "content": json.dumps(result),
                }
            )

    raise LLMError("The assistant reached the tool-call limit.")
