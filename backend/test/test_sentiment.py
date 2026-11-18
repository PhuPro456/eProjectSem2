import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-only-secret-key-with-at-least-32-characters")

import pytest

from app.services import sentiment as mod


@pytest.fixture
def no_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mod, "_load_model", lambda: None)


class FakeModel:
    def __init__(self, row=None, error=None) -> None:
        self._row = row
        self._error = error

    def predict(self, texts):
        if self._error is not None:
            raise self._error
        return [self._row]


def test_lexicon_labels_and_shape(no_model) -> None:
    result = mod.analyze_sentiment("Absolutely loved it, a gripping plot.", 5)
    assert result["sentiment"] == "positive"
    assert "gripping" in result["keywords"]
    assert set(result["aspects"]) == set(mod.ASPECTS)
    assert all(value in mod.VALID_SENTIMENTS for value in result["aspects"].values())

    assert mod.analyze_sentiment("Boring and predictable.", 2)["sentiment"] == "negative"
    assert mod.analyze_sentiment("The book has 300 pages.", 3)["sentiment"] == "neutral"


def test_lexicon_negation_still_works(no_model) -> None:
    result = mod.analyze_sentiment("This was not great at all.", 3)
    assert result["sentiment"] == "negative"


def test_vietnamese_lexicon(no_model) -> None:
    result = mod.analyze_sentiment("Sách rất hay và đáng đọc.", 5)
    assert result["sentiment"] == "positive"
    assert "hay" in result["keywords"]


def test_rule_aspects_follow_clause_polarity(no_model) -> None:
    result = mod.analyze_sentiment(
        "The code examples are full of bugs, but the paper quality is great.", 3
    )
    assert result["aspects"]["examples_code"] == "negative"
    assert result["aspects"]["print_quality"] == "positive"
    assert result["aspects"]["price"] == "neutral"


def test_model_prediction_is_used(monkeypatch: pytest.MonkeyPatch) -> None:
    row = ["positive", "positive", "neutral", "negative", "neutral", "positive"]
    monkeypatch.setattr(mod, "_load_model", lambda: FakeModel(row=row))
    result = mod.analyze_sentiment("Some review text.", 5)
    assert result["sentiment"] == "positive"
    assert result["aspects"] == {
        "content": "positive",
        "understandability": "neutral",
        "examples_code": "negative",
        "print_quality": "neutral",
        "price": "positive",
    }


def test_model_failure_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        mod, "_load_model", lambda: FakeModel(error=RuntimeError("bad artifact"))
    )
    result = mod.analyze_sentiment("Absolutely loved it, gripping.", 5)
    assert result["sentiment"] == "positive"
    assert "gripping" in result["keywords"]


def test_model_invalid_labels_fall_back(monkeypatch: pytest.MonkeyPatch) -> None:
    row = ["mixed", "positive", "neutral", "neutral", "neutral", "neutral"]
    monkeypatch.setattr(mod, "_load_model", lambda: FakeModel(row=row))
    result = mod.analyze_sentiment("Boring and dull.", 2)
    assert result["sentiment"] == "negative"


def test_missing_model_file_uses_lexicon(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(mod, "MODEL_PATH", tmp_path / "absent.joblib")
    mod._load_model.cache_clear()
    try:
        assert mod._load_model() is None
    finally:
        mod._load_model.cache_clear()