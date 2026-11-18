import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { BookCard, ErrorView, SkeletonGrid } from '../ui.jsx';

const TINTS = ['#e7edf7', '#f6ede1', '#e9f0e4', '#efe7f3', '#f8e8e6', '#e6eff0'];

export function HomeView() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    (async () => {
      try {
        const categories = await api.categories();
        // The list endpoint caps page size at 50, so walk the pages until a
        // short page arrives. Loading every book lets each category's tiles
        // show real covers regardless of how many categories the catalog has.
        const limit = 50;
        const items = [];
        for (let skip = 0; ; skip += limit) {
          const page = await api.listBooks({ limit, skip, sort_by: 'id', order: 'asc' });
          const batch = page?.items || [];
          items.push(...batch);
          if (batch.length < limit) break;
        }
        if (cancelled) return;
        setData({ categories, books: items });
      } catch (loadError) {
        if (!cancelled) setError(loadError.message);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [version]);

  const books = data ? data.books : [];

  const titlesCount = data
    ? data.categories.reduce((sum, category) => sum + (category.book_count || 0), 0)
    : null;
  const genresCount = data ? data.categories.length : null;
  const topSubjects = data && data.categories.length
    ? data.categories.slice(0, 3).map((category) => category.name).join(', ')
    : null;

  return (
    <>
      <section className="hero">
        <div className="hero-inner">
          <div className="hero-copy">
            <p className="eyebrow">The reading room</p>
            <h1>
              Find your
              <br />
              <em>next chapter.</em>
            </h1>
            <p className="hero-lede">
              {titlesCount != null
                ? `${titlesCount} titles across ${topSubjects ? `${topSubjects} and more` : `${genresCount} subjects`} — curated, in stock, and ready to ship.`
                : 'A growing catalog of real titles — curated, in stock, and ready to ship.'}
            </p>
            <div className="hero-actions">
              <a className="btn" href="#/catalog">
                Shop all books
              </a>
              <a className="btn ghost" href="#/catalog?sort=price_asc">
                Browse under $15
              </a>
            </div>
            <dl className="hero-stats">
              <div>
                <dt>{titlesCount != null ? titlesCount : '—'}</dt>
                <dd>curated titles</dd>
              </div>
              <div>
                <dt>{genresCount != null ? genresCount : '—'}</dt>
                <dd>subjects</dd>
              </div>
              <div>
                <dt>$35</dt>
                <dd>free shipping</dd>
              </div>
            </dl>
          </div>
          <div className="hero-tiles" id="homeTiles">
            {data
              ? data.categories.slice(0, 6).map((category, index) => {
                  const covers = books
                    .filter((book) => book.category === category.code)
                    .slice(0, 2);
                  return (
                    <a
                      className="cat-tile"
                      href={`#/catalog?category=${encodeURIComponent(category.code)}`}
                      style={{ '--tint': TINTS[index % TINTS.length] }}
                      key={category.code}
                    >
                      <div className="cat-covers">
                        {covers.map((book, position) => (
                          <img
                            className={`cover-${position}`}
                            src={book.cover}
                            alt=""
                            loading="lazy"
                            key={book.id}
                          />
                        ))}
                      </div>
                      <div className="cat-meta">
                        <span className="cat-name">{category.name}</span>
                        <span className="cat-count">{category.book_count} titles</span>
                      </div>
                    </a>
                  );
                })
              : !error && (
                  <>
                    {Array.from({ length: 6 }, (_, index) => (
                      <div className="cat-tile skeleton-tile" key={index} />
                    ))}
                  </>
                )}
            {data && !error && (
              <a className="link-arrow hero-tiles-more" href="#/catalog">
                All {genresCount} subjects <span aria-hidden="true">→</span>
              </a>
            )}
          </div>
        </div>
      </section>
      <section className="section">
        <div className="section-head">
          <div>
            <p className="eyebrow">Staff shelves</p>
            <h2>New &amp; noteworthy</h2>
          </div>
          <a className="link-arrow" href="#/catalog">
            View all books <span aria-hidden="true">→</span>
          </a>
        </div>
        <div id="homeGrid">
          {error ? (
            <ErrorView message={error} onRetry={() => setVersion((v) => v + 1)} />
          ) : data ? (
            <div className="book-grid">
              {books
                .slice(-8)
                .reverse()
                .map((book) => (
                  <BookCard book={book} key={book.id} />
                ))}
            </div>
          ) : (
            <SkeletonGrid count={8} />
          )}
        </div>
      </section>
      <section className="band">
        <div className="band-item">
          <strong>Free shipping</strong>
          <span>On every order over $35</span>
        </div>
        <div className="band-item">
          <strong>30-day returns</strong>
          <span>No questions asked</span>
        </div>
        <div className="band-item">
          <strong>Secure checkout</strong>
          <span>JWT-protected accounts</span>
        </div>
      </section>
      <section className="section split">
        <div className="split-copy">
          <p className="eyebrow">The collection</p>
          <h2>{genresCount != null ? `${genresCount} shelves, ${titlesCount} titles` : 'The full collection'}</h2>
          <p className="muted">
            {topSubjects
              ? `From ${topSubjects} to the far end of the catalog, every title is a real published work with a demo price and stock level.`
              : 'Every title is a real published work with a demo price and stock level.'}
          </p>
          <a className="btn ghost" href="#/catalog">
            Browse the catalog
          </a>
        </div>
        <div className="split-list" id="homeCategories">
          {data &&
            !error &&
            data.categories.map((category) => (
              <a
                className="split-row"
                href={`#/catalog?category=${encodeURIComponent(category.code)}`}
                key={category.code}
              >
                <span>{category.name}</span>
                <span className="muted">{category.book_count} books</span>
                <span aria-hidden="true">→</span>
              </a>
            ))}
        </div>
      </section>
    </>
  );
}
