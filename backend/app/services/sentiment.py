import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

POSITIVE = {
    "love",
    "loved",
    "loving",
    "brilliant",
    "wonderful",
    "great",
    "excellent",
    "enjoyed",
    "enjoy",
    "beautiful",
    "compelling",
    "satisfying",
    "favourite",
    "favorite",
    "delightful",
    "gripping",
    "perfect",
    "recommend",
    "recommended",
    "amazing",
    "charming",
    "vivid",
    "superb",
    "moving",
    "best",
    "masterful",
    "unputdownable",
    "refreshing",
    "thoughtful",
    "heartwarming",
    "thrilling",
    "immersive",
    "memorable",
    "gorgeous",
    "clever",
    "riveting",
    "outstanding",
    "cozy",
    "fun",
    "fast-paced",
    "page-turner",
    "clear",
    "cheap",
    "worth",
    "helpful",
    "informative",
    "practical",
    "crisp",
    "sturdy",
    "hay",
    "tốt",
    "rẻ",
    "đáng",
    "mượt",
    "dễ hiểu",
}

NEGATIVE = {
    "boring",
    "dull",
    "slow",
    "disappointing",
    "disappointed",
    "bad",
    "terrible",
    "awful",
    "hate",
    "hated",
    "predictable",
    "flat",
    "tedious",
    "confusing",
    "weak",
    "poor",
    "waste",
    "worst",
    "annoying",
    "frustrating",
    "overrated",
    "bland",
    "forgettable",
    "clunky",
    "messy",
    "repetitive",
    "shallow",
    "unconvincing",
    "mediocre",
    "tiresome",
    "dragged",
    "slow-paced",
    "outdated",
    "overpriced",
    "expensive",
    "bugs",
    "buggy",
    "blurry",
    "smudged",
    "faded",
    "flimsy",
    "khó hiểu",
    "mờ",
    "đắt",
    "phí",
    "lỗi",
    "cũ",
    "dở",
}

NEGATIONS = {
    "not",
    "no",
    "never",
    "hardly",
    "barely",
    "scarcely",
    "isn't",
    "wasn't",
    "aren't",
    "weren't",
    "don't",
    "didn't",
    "doesn't",
    "couldn't",
    "wouldn't",
    "can't",
    "cannot",
    "without",
    "không",
    "chẳng",
}

INTENSIFIERS = {"very", "really", "absolutely", "totally", "so", "quite", "extremely", "truly", "rất", "quá"}

WORD_RE = re.compile(r"[^\W\d_]+(?:['-][^\W\d_]+)*", re.UNICODE)

Sentiment = Literal["positive", "neutral", "negative"]

VALID_SENTIMENTS = {"positive", "neutral", "negative"}

ASPECTS = ("content", "understandability", "examples_code", "print_quality", "price")

ASPECT_CUES: dict[str, tuple[str, ...]] = {
    "content": (
        "content", "nội dung", "story", "plot", "kiến thức", "theory",
        "outdated", "chapter", "chương", "cũ",
    ),
    "understandability": (
        "understand", "dễ hiểu", "khó hiểu", "clear", "confusing",
        "explanation", "giải thích", "easy to follow", "basic", "cơ bản",
    ),
    "examples_code": (
        "code", "example", "ví dụ", "snippet", "bug", "lỗi",
        "exercise", "bài tập",
    ),
    "print_quality": (
        "print", "paper", "giấy", "binding", "mờ", "trang",
    ),
    "price": (
        "price", "giá", "cheap", "expensive", "rẻ", "đắt",
        "worth", "penny", "tiền", "cost",
    ),
}

MODEL_PATH = Path(__file__).resolve().parent.parent / "ml_models" / "sentiment_pipeline.joblib"


@lru_cache(maxsize=1)
def _load_model():
    if not MODEL_PATH.is_file():
        return None
    try:
        import joblib

        return joblib.load(MODEL_PATH)
    except Exception as exc:
        logger.warning(
            "Sentiment model could not be loaded (%s); using lexicon fallback.",
            type(exc).__name__,
        )
        return None


def analyze_sentiment(text: str, rating: int | None = None) -> dict:
    """Classify a review and its aspects with the trained pipeline when available.

    Any model failure (missing file, incompatible artifact, bad prediction) falls
    back to the offline lexicon, so posting a review never depends on ML deps.
    """
    keywords = _lexicon_keywords(text)
    model = _load_model()
    if model is not None:
        try:
            prediction = model.predict([text])[0]
            label = str(prediction[0]).strip().casefold()
            aspects = {
                aspect: str(value).strip().casefold()
                for aspect, value in zip(ASPECTS, prediction[1:])
            }
            if label in VALID_SENTIMENTS and all(
                value in VALID_SENTIMENTS for value in aspects.values()
            ):
                return {"sentiment": label, "keywords": keywords, "aspects": aspects}
            logger.warning("Sentiment model returned invalid labels; using lexicon fallback.")
        except Exception as exc:
            logger.warning(
                "Sentiment model prediction failed (%s); using lexicon fallback.",
                type(exc).__name__,
            )

    sentiment, _ = _lexicon_sentiment(text, rating)
    return {
        "sentiment": sentiment,
        "keywords": keywords,
        "aspects": _rule_aspects(text),
    }


def _score_words(words: list[str]) -> tuple[int, list[str]]:
    score = 0
    keywords: list[str] = []
    for index, word in enumerate(words):
        polarity = 1 if word in POSITIVE else -1 if word in NEGATIVE else 0
        if polarity == 0:
            continue
        if any(token in NEGATIONS for token in words[max(0, index - 3) : index]):
            polarity *= -1
        if index > 0 and words[index - 1] in INTENSIFIERS:
            score += polarity * 2
        else:
            score += polarity
        if word not in keywords:
            keywords.append(word)
    return score, keywords


def _lexicon_keywords(text: str) -> list[str]:
    _, keywords = _score_words(WORD_RE.findall(text.casefold()))
    return keywords[:6]


def _lexicon_sentiment(text: str, rating: int | None = None) -> tuple[Sentiment, list[str]]:
    """Offline fallback: score review text with a small sentiment lexicon."""
    score, keywords = _score_words(WORD_RE.findall(text.casefold()))

    if rating is not None:
        if rating >= 4:
            score += 1
        elif rating <= 2:
            score -= 1

    if score > 0:
        sentiment: Sentiment = "positive"
    elif score < 0:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return sentiment, keywords[:6]


def _rule_aspects(text: str) -> dict[str, str]:
    """Assign aspect labels from clause-level lexicon scores when no model exists."""
    lowered = text.casefold()
    clauses = re.split(r"[.,;!?]|\bnhưng\b|\bbut\b", lowered)
    aspects: dict[str, str] = {aspect: "neutral" for aspect in ASPECTS}
    for aspect, cues in ASPECT_CUES.items():
        pattern = re.compile(
            r"(?<!\w)(?:" + "|".join(re.escape(cue) for cue in cues) + r")(?!\w)"
        )
        score = 0
        for clause in clauses:
            if pattern.search(clause):
                clause_score, _ = _score_words(WORD_RE.findall(clause))
                score += clause_score
        if score > 0:
            aspects[aspect] = "positive"
        elif score < 0:
            aspects[aspect] = "negative"
    return aspects