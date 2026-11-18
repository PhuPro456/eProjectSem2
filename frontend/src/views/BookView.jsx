import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { cartAdd, useStore } from '../store.js';
import {
  BookCard,
  Icons,
  Stars,
  StockLabel,
  categoryName,
  formatDate,
  initials,
  money,
  toast,
} from '../ui.jsx';

export function BookView({ bookId }) {
  const { user } = useStore();
  const [book, setBook] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [related, setRelated] = useState([]);
  const [quantity, setQuantity] = useState(1);
  const [reviews, setReviews] = useState(null);
  const [reviewsError, setReviewsError] = useState(null);
  const [reviewVersion, setReviewVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setBook(null);
    setLoadError(null);
    setReviews(null);
    (async () => {
      try {
        const data = await api.getBook(bookId);
        if (cancelled) return;
        setBook(data);
        setQuantity(Math.max(0, data.stock) > 0 ? 1 : 0);
        try {
          const sameCategory = await api.listBooks({ category: data.category, limit: 5 });
          if (!cancelled) {
            setRelated(sameCategory.items.filter((item) => item.id !== data.id).slice(0, 4));
          }
        } catch {
          /* related books are optional */
        }
      } catch (error) {
        if (!cancelled) setLoadError(error);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [bookId]);

  useEffect(() => {
    if (!book) return;
    let cancelled = false;
    setReviewsError(null);
    api
      .bookReviews(book.id)
      .then((data) => {
        if (!cancelled) setReviews(data);
      })
      .catch((error) => {
        if (!cancelled) setReviewsError(error.message);
      });
    return () => {
      cancelled = true;
    };
  }, [book, reviewVersion]);

  if (loadError) {
    const notFound = loadError.status === 404;
    return (
      <div className="page">
        <div className="state-card">
          <h3>{notFound ? 'Book not found' : 'Could not load this book'}</h3>
          <p>{notFound ? 'That title may have been removed from the catalog.' : loadError.message}</p>
          <a className="btn" href="#/catalog">
            Back to the catalog
          </a>
        </div>
      </div>
    );
  }

  if (!book) {
    return (
      <div className="page">
        <div className="detail-skeleton">
          <div className="skeleton skeleton-cover tall" />
          <div>
            <div className="skeleton skeleton-line" />
            <div className="skeleton skeleton-line" />
            <div className="skeleton skeleton-line tiny" />
          </div>
        </div>
      </div>
    );
  }

  const maxQuantity = Math.max(0, book.stock);

  function addToCart() {
    const result = cartAdd(book, quantity);
    if (!result.added) {
      toast('This title is out of stock', 'error');
      return;
    }
    toast(
      result.limited
        ? `Added ${quantity} — only ${maxQuantity} available`
        : `${quantity} × ${book.title} added to cart`,
      'success',
    );
  }

  return (
    <div className="page detail-page">
      <a className="back-link" href="#/catalog">
        {Icons.arrowLeft} Back to catalog
      </a>
      <div className="detail">
        <div className="detail-cover">
          {book.cover ? (
            <img src={book.cover} alt={`Cover of ${book.title}`} />
          ) : (
            <div className="cover-fallback">No cover</div>
          )}
        </div>
        <div className="detail-info">
          <a
            className="book-cat"
            href={`#/catalog?category=${encodeURIComponent(book.category)}`}
          >
            {categoryName(book.category)}
          </a>
          <h1>{book.title}</h1>
          <p className="detail-author">by {book.author}</p>
          <p className="detail-desc">{book.description}</p>
          <div className="detail-buy">
            <span className="detail-price">{money(book.price)}</span>
            <StockLabel stock={book.stock} />
          </div>
          <div className="detail-actions">
            <div className="qty" role="group" aria-label="Quantity">
              <button
                type="button"
                aria-label="Decrease quantity"
                onClick={() => setQuantity((value) => Math.max(1, value - 1))}
              >
                {Icons.minus}
              </button>
              <span>{quantity}</span>
              <button
                type="button"
                aria-label="Increase quantity"
                onClick={() => setQuantity((value) => Math.min(maxQuantity, value + 1))}
              >
                {Icons.plus}
              </button>
            </div>
            <button className="btn" type="button" disabled={maxQuantity === 0} onClick={addToCart}>
              {maxQuantity === 0 ? 'Out of stock' : 'Add to cart'}
            </button>
          </div>
          <ul className="detail-facts">
            <li>Free standard shipping over $35</li>
            <li>30-day returns on every order</li>
            <li>Orders are stored in PostgreSQL</li>
          </ul>
        </div>
      </div>
      <section className="reviews">
        <div className="section-head">
          <div>
            <p className="eyebrow">Reader voices</p>
            <h2>Reviews</h2>
          </div>
          <span className="muted">
            {reviews
              ? reviews.summary.total
                ? `${reviews.summary.average_rating.toFixed(1)} average from ${reviews.summary.total} review${
                    reviews.summary.total === 1 ? '' : 's'
                  }`
                : 'No reviews yet'
              : ''}
          </span>
        </div>
        {reviewsError ? (
          <p className="muted">Reviews are unavailable right now: {reviewsError}</p>
        ) : !reviews ? (
          <div id="reviewBody">
            <div className="skeleton skeleton-line" />
            <div className="skeleton skeleton-line short" />
          </div>
        ) : (
          <Reviews
            book={book}
            user={user}
            data={reviews}
            onPosted={() => setReviewVersion((value) => value + 1)}
          />
        )}
      </section>
      {related.length > 0 && (
        <section className="related">
          <div className="section-head">
            <div>
              <p className="eyebrow">Keep browsing</p>
              <h2>More in {categoryName(book.category)}</h2>
            </div>
          </div>
          <div className="book-grid">
            {related.map((item) => (
              <BookCard book={item} key={item.id} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function ReviewBar({ kind, count, total }) {
  const percent = total ? (count / total) * 100 : 0;
  return (
    <div className="review-bar-row">
      <span className="review-bar-label">{kind}</span>
      <div className="review-bar-track">
        <span className={`review-bar-fill ${kind}`} style={{ width: `${percent.toFixed(1)}%` }} />
      </div>
      <span className="review-bar-count">{count}</span>
    </div>
  );
}

function Reviews({ book, user, data, onPosted }) {
  const { summary, items } = data;
  const [rating, setRating] = useState('5');
  const [text, setText] = useState('');
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function submitForm(event) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.addReview(book.id, { rating: Number(rating), text: text.trim() });
      toast('Review posted', 'success');
      setText('');
      onPosted();
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div id="reviewBody">
      <div className="review-summary">
        <div className="review-score">
          <strong>{summary.total ? summary.average_rating.toFixed(1) : '—'}</strong>
          <Stars rating={Math.round(summary.average_rating)} />
          <span className="muted">
            {summary.total} review{summary.total === 1 ? '' : 's'}
          </span>
        </div>
        <div className="review-bars">
          <ReviewBar kind="positive" count={summary.positive} total={summary.total} />
          <ReviewBar kind="neutral" count={summary.neutral} total={summary.total} />
          <ReviewBar kind="negative" count={summary.negative} total={summary.total} />
        </div>
      </div>
      <div className="review-list">
        {items.length ? (
          items.map((review) => (
            <article className="review-item" key={review.id}>
              <header className="review-item-head">
                <div className="reviewer">
                  <span className="avatar small">{initials(review.author_name)}</span>
                  <div>
                    <strong>{review.author_name}</strong>
                    <span className="muted">{formatDate(review.created_at)}</span>
                  </div>
                </div>
                <div className="review-rating">
                  <Stars rating={review.rating} />
                  <span className={`sentiment-pill ${review.sentiment}`}>{review.sentiment}</span>
                </div>
              </header>
              <p className="review-text">{review.text}</p>
              {review.keywords.length > 0 && (
                <div className="review-keywords">
                  {review.keywords.map((keyword, index) => (
                    <span className={`keyword-chip ${review.sentiment}`} key={index}>
                      {keyword}
                    </span>
                  ))}
                </div>
              )}
            </article>
          ))
        ) : (
          <p className="muted review-empty">No one has reviewed this title yet.</p>
        )}
      </div>
      {user ? (
        <form className="review-form" onSubmit={submitForm}>
          <header>
            <h3>Share your thoughts</h3>
            <p className="muted">Signed in as {user.name}</p>
          </header>
          <div className="form-grid review-form-grid">
            <label>
              Rating
              <select value={rating} onChange={(event) => setRating(event.target.value)}>
                {[5, 4, 3, 2, 1].map((value) => (
                  <option value={value} key={value}>
                    {value} star{value === 1 ? '' : 's'}
                  </option>
                ))}
              </select>
            </label>
            <label className="span-2">
              Your review
              <textarea
                rows="3"
                minLength="3"
                maxLength="2000"
                required
                value={text}
                onChange={(event) => setText(event.target.value)}
                placeholder="What worked, what didn't?"
              />
            </label>
          </div>
          {error && <p className="form-error">{error}</p>}
          <button className="btn" type="submit" disabled={submitting}>
            Post review
          </button>
        </form>
      ) : (
        <p className="review-signin">
          <a
            href="#/login"
            onClick={() => sessionStorage.setItem('bookstore.next', location.hash || '#/')}
          >
            Sign in
          </a>{' '}
          to leave a review.
        </p>
      )}
    </div>
  );
}
