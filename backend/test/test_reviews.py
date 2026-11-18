from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.crud import review as review_crud
from app.db.session import Base
from app.models.book import Book, Category
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate


@pytest.fixture
def db() -> Generator[Session, None, None]:
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


def test_create_review_persists_analyzed_aspects(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected_aspects = {
        "content": "positive",
        "understandability": "neutral",
        "examples_code": "positive",
        "print_quality": "neutral",
        "price": "negative",
    }

    def analyze_sentiment(text: str, rating: int) -> dict:
        assert text == "A clear and useful book"
        assert rating == 5
        return {
            "sentiment": "positive",
            "keywords": ["clear"],
            "aspects": expected_aspects,
        }

    monkeypatch.setattr(review_crud, "analyze_sentiment", analyze_sentiment)
    db.add(Category(code="programming", name="Programming"))
    book = Book(
        title="Python Basics",
        author="A. Author",
        category_code="programming",
        price=10,
    )
    user = User(
        name="Reader",
        email="reader@example.com",
        hashed_password="not-used",
    )
    db.add_all([book, user])
    db.flush()

    review = review_crud.create_review(
        db, book.id, user, ReviewCreate(rating=5, text="A clear and useful book")
    )
    persisted_review = db.get(Review, review.id)

    assert persisted_review is not None
    assert persisted_review.aspects == expected_aspects
