import hashlib

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book import Book, BookEmbedding
from app.services.llm_chat import ssl_context

EMBEDDING_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-embedding-001:embedContent"
)
EMBEDDING_DIMENSION = 768
EMBEDDING_BATCH_SIZE = 20


def get_gemini_embedding(text: str, api_key: str) -> list[float]:
    response = httpx.post(
        EMBEDDING_URL,
        headers={"x-goog-api-key": api_key},
        json={
            "model": "models/gemini-embedding-001",
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": EMBEDDING_DIMENSION,
        },
        timeout=30.0,
        verify=ssl_context(),
    )
    response.raise_for_status()

    try:
        values = response.json()["embedding"]["values"]
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("Gemini returned an invalid embedding response.") from exc
    if not isinstance(values, list) or len(values) != EMBEDDING_DIMENSION:
        raise RuntimeError("Gemini returned an invalid embedding response.")

    try:
        return [float(value) for value in values]
    except (TypeError, ValueError) as exc:
        raise RuntimeError("Gemini returned non-numeric embedding values.") from exc


def reindex_catalog_task(db: Session, api_key: str) -> None:
    books = db.execute(select(Book).order_by(Book.id)).scalars().all()
    embeddings = {
        item.book_id: item
        for item in db.execute(select(BookEmbedding)).scalars().all()
    }

    updated_count = 0
    for book in books:
        content = (
            f"Title: {book.title}. Author: {book.author}. "
            f"Category: {book.category}. Description: {book.description}"
        )
        content_hash = hashlib.md5(
            content.encode("utf-8"), usedforsecurity=False
        ).hexdigest()

        embedding_record = embeddings.get(book.id)
        if (
            embedding_record is not None
            and embedding_record.content_hash == content_hash
        ):
            continue

        vector = get_gemini_embedding(content, api_key)
        if embedding_record is None:
            embedding_record = BookEmbedding(
                book_id=book.id,
                embedding=vector,
                content_hash=content_hash,
            )
            db.add(embedding_record)
            embeddings[book.id] = embedding_record
        else:
            embedding_record.embedding = vector
            embedding_record.content_hash = content_hash

        updated_count += 1
        if updated_count % EMBEDDING_BATCH_SIZE == 0:
            db.commit()

    db.commit()