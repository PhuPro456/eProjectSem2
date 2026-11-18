from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models.book import Book, BookEmbedding, Category
from app.models.review import Review
from app.models.user import User
from app.services import recommender


@pytest.fixture
def recommendation_db() -> Generator[Session, None, None]:
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


def _book(book_id: int, title: str) -> Book:
    return Book(
        id=book_id,
        title=title,
        author="Author",
        category_code="python",
        description="",
        price=10,
        stock=1,
    )


def _persist_book(db: Session, title: str, category_code: str = "python") -> Book:
    book = Book(
        title=title,
        author="Author",
        category_code=category_code,
        description="",
        price=10,
        stock=1,
    )
    db.add(book)
    db.flush()
    return book


def _review(
    book: Book, user_id: int, rating: int, created_at: datetime
) -> Review:
    return Review(
        book_id=book.id,
        user_id=user_id,
        author_name="Reader",
        rating=rating,
        text="Review",
        sentiment="positive",
        created_at=created_at,
    )


def _prepare_keyword_search(
    monkeypatch: pytest.MonkeyPatch, keyword_book: Book
) -> None:
    monkeypatch.setattr(recommender, "category_names", lambda db: {})
    monkeypatch.setattr(recommender, "book_popularity", lambda db: {})
    monkeypatch.setattr(recommender, "_detect_topics", lambda text: ("python",))
    monkeypatch.setattr(recommender, "_detect_level", lambda text: None)
    monkeypatch.setattr(recommender, "_detect_price", lambda text: None)
    monkeypatch.setattr(recommender, "_terms", lambda text: [])
    monkeypatch.setattr(recommender, "_available_books", lambda db: [keyword_book])
    monkeypatch.setattr(recommender, "_rank", lambda books, popularity: list(books))
    monkeypatch.setattr(recommender, "_score", lambda book, terms, level: 0)


def test_semantic_search_orders_by_cosine_distance_and_applies_limit() -> None:
    import_module("app.models.chat")
    db = Mock()
    db.bind = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))
    expected_books = [object(), object()]
    db.scalars.return_value.all.return_value = expected_books

    books = recommender.semantic_search_books(db, [0.1] * 768, limit=2)

    statement = db.scalars.call_args.args[0]
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert books == expected_books
    assert "book_embeddings.embedding <=> " in sql
    assert statement._limit_clause.value == 2
    assert statement.column_descriptions[0]["entity"] is Book


def test_answer_chat_prioritizes_semantic_results_and_deduplicates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import_module("app.models.chat")
    keyword_book = _book(2, "Keyword result")
    semantic_book = _book(1, "Semantic result")
    semantic_duplicate = _book(2, "Keyword result")
    _prepare_keyword_search(monkeypatch, keyword_book)
    monkeypatch.setattr(
        recommender,
        "get_active_admin_key",
        lambda db: SimpleNamespace(encrypted_key="encrypted"),
    )
    monkeypatch.setattr(recommender, "decrypt_secret", lambda value: "api-key")
    monkeypatch.setattr(
        recommender,
        "get_gemini_embedding",
        lambda message, api_key: [0.1] * 768,
    )
    search_calls: list[tuple[list[float], int]] = []

    def fake_semantic_search(db, query_vector: list[float], limit: int) -> list[Book]:
        search_calls.append((query_vector, limit))
        return [semantic_book, semantic_duplicate]

    monkeypatch.setattr(recommender, "semantic_search_books", fake_semantic_search)

    reply, suggestions, books = recommender.answer_chat(Mock(), "python", limit=2)

    assert reply.startswith("python it is.")
    assert suggestions
    assert [book.id for book in books] == [1, 2]
    assert books == [semantic_book, semantic_duplicate]
    assert search_calls == [([0.1] * 768, 2)]


def test_answer_chat_keeps_topic_when_semantic_results_are_off_topic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import_module("app.models.chat")
    manga_book = Book(
        id=2,
        title="Naruto Vol. 1",
        author="Author",
        category_code="manga",
        description="",
        price=10,
        stock=1,
    )
    tech_book = _book(1, "Head First Java")
    _prepare_keyword_search(monkeypatch, manga_book)
    monkeypatch.setattr(recommender, "_detect_topics", lambda text: ("manga",))
    monkeypatch.setattr(
        recommender,
        "get_active_admin_key",
        lambda db: SimpleNamespace(encrypted_key="encrypted"),
    )
    monkeypatch.setattr(recommender, "decrypt_secret", lambda value: "api-key")
    monkeypatch.setattr(
        recommender,
        "get_gemini_embedding",
        lambda message, api_key: [0.1] * 768,
    )
    monkeypatch.setattr(
        recommender,
        "semantic_search_books",
        lambda db, query_vector, limit: [tech_book],
    )

    _, _, books = recommender.answer_chat(Mock(), "manga like Naruto", limit=2)

    assert books == [manga_book]


def test_anonymous_recommendations_are_highest_rated(
    recommendation_db: Session,
) -> None:
    recommendation_db.add_all(
        [Category(code="python", name="Python"), Category(code="ai", name="AI")]
    )
    best = _persist_book(recommendation_db, "Best", "python")
    next_best = _persist_book(recommendation_db, "Next best", "ai")
    unrated = _persist_book(recommendation_db, "Unrated", "python")
    reader = User(
        name="Reader",
        email="ratings@example.com",
        hashed_password="unused",
    )
    recommendation_db.add(reader)
    recommendation_db.flush()
    now = datetime.now(timezone.utc)
    recommendation_db.add_all(
        [
            _review(best, reader.id, 5, now),
            _review(best, reader.id, 4, now + timedelta(seconds=1)),
            _review(next_best, reader.id, 4, now),
        ]
    )
    recommendation_db.commit()

    books, reason = recommender.build_recommendations(
        recommendation_db, limit=3
    )

    assert [book.id for book in books] == [best.id, next_best.id, unrated.id]
    assert reason == "Trending books you might like."


def test_user_without_high_rated_reviews_gets_generic_recommendations(
    recommendation_db: Session,
) -> None:
    recommendation_db.add(Category(code="python", name="Python"))
    current_user = User(
        name="Reader",
        email="reader@example.com",
        hashed_password="unused",
    )
    other_user = User(
        name="Other reader",
        email="other@example.com",
        hashed_password="unused",
    )
    recommendation_db.add_all([current_user, other_user])
    book = _persist_book(recommendation_db, "Highly rated")
    low_rated = _persist_book(recommendation_db, "Low rated")
    recommendation_db.flush()
    now = datetime.now(timezone.utc)
    recommendation_db.add_all(
        [
            _review(book, other_user.id, 5, now),
            _review(low_rated, current_user.id, 3, now),
        ]
    )
    recommendation_db.commit()

    books, reason = recommender.build_recommendations(
        recommendation_db, current_user, limit=1
    )

    assert books == [book]
    assert reason == "Popular choices for you."


def test_user_embedding_recommendations_exclude_favorite(
    recommendation_db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    recommendation_db.add(Category(code="python", name="Python"))
    current_user = User(
        name="Reader",
        email="favorite@example.com",
        hashed_password="unused",
    )
    recommendation_db.add(current_user)
    favorite = _persist_book(recommendation_db, "Favorite")
    older_favorite = _persist_book(recommendation_db, "Older favorite")
    first_match = _persist_book(recommendation_db, "First match")
    second_match = _persist_book(recommendation_db, "Second match")
    recommendation_db.flush()
    now = datetime.now(timezone.utc)
    recommendation_db.add_all(
        [
            _review(favorite, current_user.id, 4, now),
            _review(older_favorite, current_user.id, 5, now - timedelta(days=1)),
            BookEmbedding(
                book_id=favorite.id,
                embedding=[0.1] * 768,
                content_hash="a" * 64,
            ),
        ]
    )
    recommendation_db.commit()
    search_calls: list[tuple[list[float], int]] = []

    def fake_semantic_search(
        db: Session, query_vector: list[float], limit: int
    ) -> list[Book]:
        search_calls.append((query_vector, limit))
        return [favorite, first_match, second_match]

    monkeypatch.setattr(
        recommender, "semantic_search_books", fake_semantic_search
    )

    books, reason = recommender.build_recommendations(
        recommendation_db, current_user, limit=2
    )

    assert books == [first_match, second_match]
    assert reason == "Because you loved 'Favorite' (AI Matched)."
    assert search_calls == [([0.1] * 768, 3)]


def test_user_without_embedding_gets_same_category_recommendations(
    recommendation_db: Session,
) -> None:
    recommendation_db.add_all(
        [
            Category(code="python", name="Python"),
            Category(code="ai", name="AI"),
        ]
    )
    current_user = User(
        name="Reader",
        email="category@example.com",
        hashed_password="unused",
    )
    recommendation_db.add(current_user)
    favorite = _persist_book(recommendation_db, "Favorite")
    same_category = _persist_book(recommendation_db, "Same category")
    other_category = _persist_book(recommendation_db, "Other category", "ai")
    recommendation_db.flush()
    recommendation_db.add(
        _review(
            favorite,
            current_user.id,
            5,
            datetime.now(timezone.utc),
        )
    )
    recommendation_db.commit()

    books, reason = recommender.build_recommendations(
        recommendation_db, current_user, limit=4
    )

    assert books == [same_category]
    assert other_category not in books
    assert reason == "Because you loved 'Favorite' (Category Match)."


def test_answer_chat_uses_keyword_results_when_embedding_request_fails(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    import_module("app.models.chat")
    keyword_book = _book(2, "Keyword result")
    _prepare_keyword_search(monkeypatch, keyword_book)
    monkeypatch.setattr(
        recommender,
        "get_active_admin_key",
        lambda db: SimpleNamespace(encrypted_key="encrypted"),
    )
    monkeypatch.setattr(recommender, "decrypt_secret", lambda value: "api-key")

    def fail_embedding(message: str, api_key: str) -> list[float]:
        raise httpx.TimeoutException(
            "Embedding request timed out",
            request=httpx.Request(
                "POST", "https://generativelanguage.googleapis.com"
            ),
        )

    monkeypatch.setattr(recommender, "get_gemini_embedding", fail_embedding)
    monkeypatch.setattr(
        recommender,
        "semantic_search_books",
        lambda *args: pytest.fail("Semantic search should be skipped after embedding failure"),
    )

    _, _, books = recommender.answer_chat(Mock(), "python")

    assert books == [keyword_book]
    assert "Semantic query embedding failed" in caplog.text
