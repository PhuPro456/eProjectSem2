import logging
import re
from decimal import Decimal

import httpx
from cryptography.fernet import InvalidToken
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import decrypt_secret
from app.crud.ai_key import get_active_admin_key
from app.models.book import Book, BookEmbedding, Category
from app.models.order import Order, OrderItem
from app.models.review import Review
from app.models.user import User
from app.services.embedding import get_gemini_embedding

logger = logging.getLogger(__name__)


GRAPHICS_HCI = "graphics,-vision-&-human\u2013computer-interaction"

# Ordered: specific topics first so "deep learning" wins over generic "ai".
TOPIC_KEYWORDS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("llm", "llms", "gpt", "transformer", "transformers", "nlp", "language model", "chatbot", "rag", "prompt"),
     ("nlp-&-language-models", "generative-ai-&-applied-machine-learning")),
    (("generative", "genai", "diffusion", "gan"),
     ("generative-ai-&-applied-machine-learning",)),
    (("deep learning", "neural", "neural network", "neural networks", "pytorch", "tensorflow", "keras", "cnn"),
     ("deep-learning",)),
    (("computer vision", "image", "images", "opencv", "vision"),
     ("computer-vision", GRAPHICS_HCI)),
    (("reinforcement", "reinforcement learning", "robot", "robots", "robotics"),
     ("reinforcement-learning-&-robotics",)),
    (("mlops", "ml system", "ai system", "model deployment"),
     ("mlops-&-ai-systems",)),
    (("ethics", "ethical", "fairness", "bias", "society", "responsible ai"),
     ("ai-ethics-&-society",)),
    (("machine learning", "ml", "scikit", "sklearn", "data science"),
     ("machine-learning", "artificial-intelligence-&-machine-learning")),
    (("artificial intelligence", "ai"),
     ("ai-foundations", "artificial-intelligence-&-machine-learning")),
    (("math", "maths", "mathematics", "statistics", "stats", "probability", "linear algebra", "calculus"),
     ("mathematics-&-statistics",)),
    (("python", "django", "flask", "fastapi", "pandas"),
     ("python",)),
    (("javascript", "typescript", "node", "react", "js", "vue"),
     ("javascript-&-typescript",)),
    (("java", "kotlin", "jvm", "scala", "spring"),
     ("java-&-jvm",)),
    (("rust", "c++", "golang", "systems programming", "low level"),
     ("systems-programming",)),
    (("web", "html", "css", "frontend", "backend", "http", "api"),
     ("web-development",)),
    (("database", "databases", "sql", "postgres", "data engineering", "etl", "nosql", "information retrieval"),
     ("databases-&-data-engineering", "databases-&-information-retrieval")),
    (("devops", "cloud", "kubernetes", "docker", "microservice", "microservices", "architecture", "sre"),
     ("architecture-&-operations",)),
    (("security", "cryptography", "crypto", "hacking", "encryption", "pentest"),
     ("security-&-cryptography", "testing,-security-&-tools")),
    (("testing", "tdd", "git", "tooling", "debug"),
     ("testing,-security-&-tools",)),
    (("network", "networks", "networking", "distributed", "distributed systems", "tcp", "consensus"),
     ("networks-&-distributed-systems",)),
    (("operating system", "computer architecture", "kernel"),
     ("computer-architecture-&-operating-systems",)),
    (("compiler", "compilers", "programming language", "programming languages", "interpreter", "functional programming"),
     ("programming-languages-&-compilers",)),
    (("theory of computation", "discrete", "automata", "complexity"),
     ("theory-of-computation-&-discrete-mathematics",)),
    (("algorithm", "algorithms", "data structure", "data structures", "leetcode", "interview"),
     ("algorithms-&-data-structures", "algorithms-&-computer-science")),
    (("graphics", "hci", "user interface", "ux"),
     (GRAPHICS_HCI,)),
    (("software engineering", "clean code", "refactoring", "design pattern", "design patterns", "agile"),
     ("software-engineering",)),
    (("manga", "comic", "comics", "graphic novel", "graphic novels", "anime"),
     ("manga",)),
    (("romance", "romantic", "love story", "love stories"),
     ("romance",)),
    (("humor", "humour", "funny", "comedy", "jokes", "satire"),
     ("humor",)),
    (("light read", "light reads", "beach read", "beach reads", "easy read"),
     ("light-reads",)),
    (("magazine", "magazines", "byte magazine", "wired"),
     ("magazines",)),
    (("fantasy", "supernatural", "mystical", "ghost", "ghosts", "magic"),
     ("fantasy-&-supernatural",)),
)

LEVEL_CUES = {
    "beginner": ("beginner", "intro", "basics", "new to", "getting started", "first book", "easy"),
    "advanced": ("advanced", "expert", "deep dive", "in depth", "master", "senior", "internals"),
}
LEVEL_TEXT = {
    "beginner": ("introduc", "beginner", "first", "basics", "gentle", "practical", "hands-on", "crash course"),
    "advanced": ("advanced", "deep", "internals", "expert", "master", "research", "theory", "rigorous"),
}

STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "to", "of", "in", "on", "with", "about", "me",
    "i", "want", "need", "looking", "book", "books", "some", "something", "good", "best",
    "recommend", "please", "can", "you", "show", "find", "under", "below", "less", "than",
    "is", "are", "any", "that", "my", "like", "read", "reading", "how", "what", "by",
    "beginner", "beginners", "advanced", "cheap", "affordable", "learn", "learning",
    "only", "another", "other", "others", "different", "more", "else", "where", "which",
    "store", "shop", "have", "has", "got", "see", "there", "not", "but", "except",
    "besides", "excluding",
}

DEFAULT_SUGGESTIONS = [
    "Manga series like Naruto",
    "Romance novels",
    "Python for beginners",
    "Something under $30",
]

PRICE_RE = re.compile(
    r"(?:under|below|less than|cheaper than|budget of|max(?:imum)?|up to)\s*\$?\s*(\d+(?:\.\d+)?)"
)
DOLLAR_RE = re.compile(r"\$(\d+(?:\.\d+)?)")
CHEAP_WORDS = ("cheap", "affordable", "budget", "inexpensive")


def book_popularity(db: Session) -> dict[int, int]:
    rows = db.execute(
        select(OrderItem.book_id, func.sum(OrderItem.quantity))
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.status != "cancelled")
        .group_by(OrderItem.book_id)
    ).all()
    return {book_id: int(total or 0) for book_id, total in rows}


def _rank(books: list[Book], popularity: dict[int, int]) -> list[Book]:
    return sorted(
        books,
        key=lambda book: (
            -popularity.get(book.id, 0),
            -book.stock,
            Decimal(book.price),
            book.id,
        ),
    )


def _available_books(db: Session, categories: tuple[str, ...] | None = None) -> list[Book]:
    stmt = select(Book).where(Book.stock > 0)
    if categories:
        stmt = stmt.where(Book.category_code.in_(categories))
    return list(db.scalars(stmt).all())


def category_names(db: Session) -> dict[str, str]:
    return {code: name for code, name in db.execute(select(Category.code, Category.name)).all()}


def semantic_search_books(
    db: Session, query_vector: list[float], limit: int
) -> list[Book]:
    """Nearest-neighbour catalog search; requires pgvector (PostgreSQL only)."""
    if db.bind.dialect.name != "postgresql":
        return []
    stmt = (
        select(Book)
        .join(BookEmbedding, BookEmbedding.book_id == Book.id)
        .where(Book.stock > 0)
        .order_by(BookEmbedding.embedding.cosine_distance(query_vector))
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def _highest_rated(
    db: Session,
    limit: int,
    category_code: str | None = None,
    exclude_ids: tuple[int, ...] = (),
) -> list[Book]:
    average = func.avg(Review.rating)
    stmt = (
        select(Book)
        .outerjoin(Review, Review.book_id == Book.id)
        .where(Book.stock > 0)
        .group_by(Book.id)
        .order_by(average.desc().nulls_last(), func.count(Review.id).desc(), Book.id)
        .limit(limit)
    )
    if category_code is not None:
        stmt = stmt.where(Book.category_code == category_code)
    if exclude_ids:
        stmt = stmt.where(Book.id.not_in(exclude_ids))
    return list(db.scalars(stmt).all())


def build_recommendations(
    db: Session, user: User | None = None, limit: int = 4
) -> tuple[list[Book], str]:
    if user is not None:
        favorite = db.scalars(
            select(Book)
            .join(Review, Review.book_id == Book.id)
            .where(Review.user_id == user.id, Review.rating >= 4, Book.stock > 0)
            .order_by(Review.created_at.desc(), Review.id.desc())
        ).first()
        if favorite is not None:
            record = db.get(BookEmbedding, favorite.id)
            if record is not None:
                matches = semantic_search_books(db, record.embedding, limit + 1)
                picks = [book for book in matches if book.id != favorite.id][:limit]
                if picks:
                    return picks, f"Because you loved '{favorite.title}' (AI Matched)."
            picks = _highest_rated(
                db, limit, favorite.category_code, (favorite.id,)
            )
            if picks:
                return picks, f"Because you loved '{favorite.title}' (Category Match)."

    picks = _highest_rated(db, limit)
    reason = "Popular choices for you." if user is not None else "Trending books you might like."
    return picks, reason


def _has_word(text: str, keyword: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", text) is not None


def _detect_topics(text: str) -> tuple[str, ...]:
    codes: list[str] = []
    for keywords, categories in TOPIC_KEYWORDS:
        if any(_has_word(text, k) for k in keywords):
            codes.extend(c for c in categories if c not in codes)
            if len(codes) >= 3:
                break
    return tuple(codes)


def _detect_level(text: str) -> str | None:
    for level, cues in LEVEL_CUES.items():
        if any(cue in text for cue in cues):
            return level
    return None


def _detect_price(text: str) -> Decimal | None:
    match = PRICE_RE.search(text) or DOLLAR_RE.search(text)
    if not match:
        return None
    value = Decimal(match.group(1))
    if value <= 0 or value > 500:
        return None
    return value


def _terms(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9+#]+", text)
    return [w for w in words if w not in STOPWORDS and len(w) > 2 and not w.isdigit()]


def _score(book: Book, terms: list[str], level: str | None) -> int:
    title = book.title.casefold()
    author = book.author.casefold()
    description = (book.description or "").casefold()
    score = 0
    for term in terms:
        if term in title:
            score += 5
            # A leading word ("Naruto, Vol. 1") beats a mid-title mention
            # ("Boruto: Naruto Next Generations") for series queries.
            if title.startswith(term):
                score += 2
        if term in author:
            score += 6
        if term in description:
            score += 1
    if level:
        haystack = f"{title} {description}"
        score += 3 * sum(1 for cue in LEVEL_TEXT[level] if cue in haystack)
    return score


def _category_bonus(book: Book, terms: list[str], names: dict[str, str]) -> int:
    name = names.get(book.category_code, book.category_code).casefold()
    return 4 * sum(1 for term in terms if _has_word(name, term))


VOLUME_RE = re.compile(r"[,:\s]*(?:vol\.?|volume|book|part|#)\s*\d+.*$", re.IGNORECASE)


def _series_key(title: str) -> str:
    return VOLUME_RE.sub("", title).strip().casefold()


def _one_per_series(books: list[Book]) -> list[Book]:
    groups: dict[str, list[Book]] = {}
    for book in books:
        groups.setdefault(_series_key(book.title), []).append(book)
    position = {id(book): index for index, book in enumerate(books)}
    # Bigger series first: volume count is a proxy for how well-known it is.
    ordered = sorted(groups.values(), key=lambda g: (-len(g), position[id(g[0])]))
    return [group[0] for group in ordered]


EXCLUDE_RE = re.compile(
    r"\b(?:not only|anything but|other than|except(?: for)?|excluding|besides|not|no)\s+([^,.!?;]+)"
)


def _exclusions(text: str) -> list[list[str]]:
    groups = []
    for match in EXCLUDE_RE.finditer(text):
        terms = _terms(match.group(1))
        if terms:
            groups.append(terms)
    return groups


def _is_excluded(book: Book, exclusions: list[list[str]]) -> bool:
    title = book.title.casefold()
    author = book.author.casefold()
    return any(
        all(term in title or term in author for term in group)
        for group in exclusions
    )


def _suggestions_for(categories: tuple[str, ...], names: dict[str, str]) -> list[str]:
    if not categories:
        return list(DEFAULT_SUGGESTIONS)
    label = names.get(categories[0], categories[0])
    return [f"More {label}", f"{label} for beginners", f"Advanced {label}", "Something under $30"]


def answer_chat(
    db: Session, message: str, user: User | None = None, limit: int = 3
) -> tuple[str, list[str], list[Book]]:
    text = " ".join(message.casefold().split())
    names = category_names(db)
    popularity = book_popularity(db)
    topics = _detect_topics(text)

    if any(word in text for word in ("thank", "thanks", "cheers")):
        return "Anytime! Come back whenever you want your next read.", list(DEFAULT_SUGGESTIONS), []

    if text.strip("!. ") in {"hi", "hello", "hey", "good morning", "good evening"}:
        books, _ = build_recommendations(db, user, limit=3)
        return (
            "Hello! I can help you pick your next read — manga, romance, tech books and more. "
            "Tell me a topic, a series, your level or a budget — for example “manga like Naruto” "
            "or “beginner Python under $30”.",
            list(DEFAULT_SUGGESTIONS),
            books,
        )

    if "what can you do" in text or text == "help":
        sample = ", ".join(list(names.values())[:5])
        return (
            "I know the whole catalog, stock levels and what other readers buy. Ask for a "
            f"topic ({sample}…), an author, a level like beginner or advanced, or a budget, "
            "and I will pull three titles from the shelves.",
            list(DEFAULT_SUGGESTIONS),
            [],
        )

    if not topics and any(
        phrase in text for phrase in ("for me", "surprise", "staff pick", "popular", "bestseller", "trending")
    ):
        books, reason = build_recommendations(db, user, limit=3)
        return f"{reason} — here are three picks.", list(DEFAULT_SUGGESTIONS), books

    level = _detect_level(text)
    max_price = _detect_price(text)
    cheap = max_price is None and any(word in text for word in CHEAP_WORDS)
    terms = _terms(DOLLAR_RE.sub(" ", PRICE_RE.sub(" ", text)))
    exclusions = _exclusions(text)
    excluded_terms = {term for group in exclusions for term in group}
    terms = [term for term in terms if term not in excluded_terms]

    pool = _available_books(db)
    if max_price is not None:
        pool = [b for b in pool if Decimal(b.price) <= max_price]

    scored = {
        b.id: _score(b, terms, level) + _category_bonus(b, terms, names) for b in pool
    }

    def order(books: list[Book]) -> list[Book]:
        ranked = _rank(books, popularity)
        if cheap:
            return sorted(ranked, key=lambda b: (-scored[b.id], Decimal(b.price)))
        return sorted(ranked, key=lambda b: -scored[b.id])

    in_topic = [b for b in pool if b.category_code in topics]
    strong_hits = [b for b in pool if b not in in_topic and _score(b, terms, None) >= 5]
    if exclusions:
        in_topic = [b for b in in_topic if not _is_excluded(b, exclusions)]
        strong_hits = [b for b in strong_hits if not _is_excluded(b, exclusions)]
    in_topic = sorted(order(in_topic), key=lambda b: topics.index(b.category_code))
    # Broad category browse (no title/author hit beyond the category word itself):
    # one volume per series so the answer spans the shelf, not a single series.
    category_words = {
        term
        for term in terms
        if any(_has_word(names.get(code, "").casefold(), term) for code in topics)
    }
    specific_terms = [term for term in terms if term not in category_words]
    if in_topic and not any(_score(b, specific_terms, None) >= 5 for b in in_topic):
        in_topic = _one_per_series(in_topic)
    candidates = in_topic + order(strong_hits)
    if not candidates and not topics and terms:
        candidates = order(
            [b for b in pool if scored[b.id] > 0 and not _is_excluded(b, exclusions)]
        )
    if not candidates and not topics and not terms:
        candidates = order(pool)

    budget = f" under ${max_price:.0f}" if max_price is not None else ""
    level_text = {"beginner": " beginner-friendly", "advanced": " advanced"}.get(level or "", "")
    label = names.get(topics[0], topics[0]) if topics else ""

    if not candidates:
        fallback = _rank(_available_books(db, topics or None), popularity)[:3]
        where = f" in {label}" if label else ""
        reply = (
            f"I could not find an exact match{where}{budget}. Here are the closest titles — "
            "try widening the budget or rephrasing the topic."
        )
        return reply, _suggestions_for(topics, names), fallback

    books: list[Book] = []
    seen: set[str] = set()
    for book in candidates:
        if book.title.casefold() not in seen:
            seen.add(book.title.casefold())
            books.append(book)
        if len(books) == limit:
            break

    key = get_active_admin_key(db)
    if key is not None:
        semantic_books: list[Book] = []
        try:
            api_key = decrypt_secret(key.encrypted_key)
            query_vector = get_gemini_embedding(message, api_key)
            semantic_books = semantic_search_books(db, query_vector, limit)
        except InvalidToken:
            logger.warning("Semantic search skipped: the admin AI key could not be unlocked.")
        except (httpx.HTTPError, RuntimeError, SQLAlchemyError) as exc:
            logger.warning("Semantic query embedding failed (%s).", type(exc).__name__)
        if semantic_books:
            # Embeddings only cover part of the catalog, so nearest neighbours
            # can come from unrelated categories; an explicit topic wins.
            if topics:
                semantic_books = [b for b in semantic_books if b.category_code in topics]
            if exclusions:
                semantic_books = [b for b in semantic_books if not _is_excluded(b, exclusions)]
        if semantic_books:
            semantic_ids = {book.id for book in semantic_books}
            books = (semantic_books + [b for b in books if b.id not in semantic_ids])[:limit]

    if topics:
        reply = (
            f"{label} it is. Here are three{level_text} titles{budget} readers keep coming "
            "back for. Want something more advanced, cheaper, or a different topic?"
        )
    elif terms and any(scored.get(b.id, 0) >= 5 for b in books):
        reply = f"Here is what I found on the shelves{budget} for “{message.strip()}”."
    elif max_price is not None or cheap:
        reply = (
            f"Here are three good{level_text} reads{budget or ' at a friendly price'}. "
            "Tell me a topic to narrow it down."
        )
    else:
        reply = (
            "Here are three books our readers are talking about right now. "
            "Tell me a topic, a language or a budget and I will narrow it down."
        )

    return reply, _suggestions_for(topics, names), books
