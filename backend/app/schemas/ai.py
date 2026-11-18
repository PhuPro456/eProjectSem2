from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.book import BookRead


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    history: list[ChatTurn] = Field(default_factory=list, max_length=12)
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    suggestions: list[str]
    books: list[BookRead]
    source: str = "local"
    notice: str | None = None
    session_id: str | None = None


class GenerateDescRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    author: str = Field(min_length=1, max_length=150)
    category: str = Field(min_length=1, max_length=100)


class GenerateDescResponse(BaseModel):
    description: str


class CopilotSummaryResponse(BaseModel):
    summary: str


class AiStatus(BaseModel):
    provider: str | None = None


class RecommendationResponse(BaseModel):
    reason: str
    items: list[BookRead]
