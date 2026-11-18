from collections.abc import Generator
from hashlib import md5
from importlib import import_module
from types import SimpleNamespace

import httpx
import pytest
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.endpoints import admin
from app.db.session import Base
from app.models.book import Book, BookEmbedding, Category
from app.services import embedding


@pytest.fixture
def db() -> Generator[Session, None, None]:
    import_module("app.models.chat")
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


def _book_text(book: Book) -> str:
    return (
        f"Title: {book.title}. Author: {book.author}. "
        f"Category: {book.category}. Description: {book.description}"
    )


def test_get_gemini_embedding_uses_embed_content_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_data: dict[str, object] = {}

    def fake_post(url: str, **kwargs: object) -> httpx.Response:
        request_data["url"] = url
        request_data.update(kwargs)
        request = httpx.Request("POST", url)
        return httpx.Response(
            200,
            json={"embedding": {"values": [0.1] * 768}},
            request=request,
        )

    monkeypatch.setattr(embedding.httpx, "post", fake_post)

    result = embedding.get_gemini_embedding("book description", "test-key")

    assert result == [0.1] * 768
    assert request_data["url"] == embedding.EMBEDDING_URL
    assert request_data["headers"] == {"x-goog-api-key": "test-key"}
    assert request_data["json"] == {
        "model": "models/gemini-embedding-001",
        "content": {"parts": [{"text": "book description"}]},
        "outputDimensionality": 768,
    }


def test_get_gemini_embedding_rejects_unexpected_dimensions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(
            200,
            json={"embedding": {"values": [0.1, 0.2]}},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(embedding.httpx, "post", fake_post)

    with pytest.raises(RuntimeError, match="invalid embedding response"):
        embedding.get_gemini_embedding("book description", "test-key")


def test_reindex_catalog_skips_matching_hash_and_updates_changed_books(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    db.add(Category(code="programming", name="Programming"))
    unchanged = Book(
        title="Unchanged",
        author="Author",
        category_code="programming",
        description="Same description",
        price=10,
    )
    changed = Book(
        title="Changed",
        author="Author",
        category_code="programming",
        description="New description",
        price=10,
    )
    missing = Book(
        title="Missing",
        author="Author",
        category_code="programming",
        description="New book",
        price=10,
    )
    db.add_all([unchanged, changed, missing])
    db.flush()
    unchanged_hash = md5(
        _book_text(unchanged).encode("utf-8"), usedforsecurity=False
    ).hexdigest()
    db.add_all(
        [
            BookEmbedding(
                book_id=unchanged.id,
                embedding=[0.9],
                content_hash=unchanged_hash,
            ),
            BookEmbedding(
                book_id=changed.id,
                embedding=[0.8],
                content_hash="old-hash",
            ),
        ]
    )
    db.commit()

    requested_texts: list[str] = []

    def fake_embedding(text: str, api_key: str) -> list[float]:
        requested_texts.append(text)
        return [0.1, 0.2]

    monkeypatch.setattr(embedding, "get_gemini_embedding", fake_embedding)

    embedding.reindex_catalog_task(db, "test-key")

    records = {
        record.book_id: record
        for record in db.execute(select(BookEmbedding)).scalars().all()
    }
    assert requested_texts == [_book_text(changed), _book_text(missing)]
    assert records[unchanged.id].embedding == [0.9]
    assert records[changed.id].embedding == [0.1, 0.2]
    assert records[missing.id].embedding == [0.1, 0.2]
    assert records[changed.id].content_hash == md5(
        _book_text(changed).encode("utf-8"), usedforsecurity=False
    ).hexdigest()


def test_admin_reindex_requires_active_key(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(admin, "get_active_admin_key", lambda session: None)

    with pytest.raises(HTTPException) as exc_info:
        admin.reindex_books(BackgroundTasks(), db)

    assert exc_info.value.status_code == 400


def test_admin_reindex_schedules_catalog_task(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        admin,
        "get_active_admin_key",
        lambda session: SimpleNamespace(encrypted_key="encrypted-key"),
    )
    monkeypatch.setattr(admin, "decrypt_secret", lambda value: "api-key")
    background_tasks = BackgroundTasks()

    result = admin.reindex_books(background_tasks, db)

    assert result == {"message": "Reindexing started in background"}
    assert len(background_tasks.tasks) == 1
    assert background_tasks.tasks[0].func is embedding.reindex_catalog_task
    assert background_tasks.tasks[0].args == (db, "api-key")
