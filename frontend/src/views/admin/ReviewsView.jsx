import { useEffect, useState } from 'react';
import { api } from '../../api.js';
import { EmptyView, Icons, Stars, formatDate } from '../../ui.jsx';
import { Kpi, KpiSkeletons } from './common.jsx';

function KeywordCloud({ keywords, kind }) {
  if (!keywords.length) {
    return <p className="muted">No {kind} themes detected in the current reviews.</p>;
  }
  return (
    <div className="keyword-cloud">
      {keywords.map((keyword) => (
        <span className={`keyword-chip ${kind}`} key={keyword.keyword}>
          {keyword.keyword}
          <em>{keyword.count}</em>
        </span>
      ))}
    </div>
  );
}

export function ReviewsView() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    api.admin
      .reviews(60)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((loadError) => {
        if (!cancelled) setError(loadError.message);
      });
    return () => {
      cancelled = true;
    };
  }, [version]);

  const summary = data ? data.summary : null;
  const positiveShare = summary && summary.total ? Math.round((summary.positive / summary.total) * 100) : 0;

  return (
    <div className="admin-page">
      <div className="analytics-banner">
        <div>
          <p className="eyebrow">Voice of the reader</p>
          <h2>Review sentiment</h2>
          <p className="muted">
            Every review is classified locally into positive, neutral or negative with keyword
            extraction.
          </p>
        </div>
        <span className="live-chip">
          <i />
          Lexicon model
        </span>
      </div>
      {error ? (
        <div className="analytics-grid">
          <div className="state-card">
            <h3>Could not load reviews</h3>
            <p>{error}</p>
            <button className="btn" type="button" onClick={() => setVersion((value) => value + 1)}>
              Try again
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="kpi-grid">
            {summary ? (
              <>
                <Kpi
                  icon={Icons.spark}
                  label="Reviews"
                  value={String(summary.total)}
                  hint="across the catalog"
                />
                <Kpi
                  icon={Icons.chart}
                  label="Average rating"
                  value={`${summary.average_rating.toFixed(2)} / 5`}
                  hint={'★'.repeat(Math.round(summary.average_rating)) || 'No ratings'}
                />
                <Kpi
                  icon={Icons.book}
                  label="Positive share"
                  value={`${positiveShare}%`}
                  hint={`${summary.positive} positive reviews`}
                />
                <Kpi
                  icon={Icons.close}
                  label="Negative reviews"
                  value={String(summary.negative)}
                  hint={`${summary.neutral} neutral`}
                />
              </>
            ) : (
              <KpiSkeletons count={4} />
            )}
          </div>
          {data && (
            <div className="analytics-grid">
              <section className="panel">
                <header className="panel-head">
                  <h2>Positive themes</h2>
                  <span className="muted">Most mentioned</span>
                </header>
                <KeywordCloud keywords={data.positive_keywords} kind="positive" />
              </section>
              <section className="panel">
                <header className="panel-head">
                  <h2>Negative themes</h2>
                  <span className="muted">Most mentioned</span>
                </header>
                <KeywordCloud keywords={data.negative_keywords} kind="negative" />
              </section>
              <section className="panel wide">
                <header className="panel-head">
                  <h2>Latest reviews</h2>
                  <span className="muted">{data.items.length} shown</span>
                </header>
                {data.items.length ? (
                  <div className="table-wrap">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Book</th>
                          <th>Reader</th>
                          <th>Rating</th>
                          <th>Sentiment</th>
                          <th>Review</th>
                          <th>Date</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.items.map((review) => (
                          <tr key={review.id}>
                            <td>
                              <a href={`#/book/${review.book_id}`}>{review.book_title}</a>
                            </td>
                            <td>{review.author_name}</td>
                            <td>
                              <Stars rating={review.rating} />
                            </td>
                            <td>
                              <span className={`sentiment-pill ${review.sentiment}`}>
                                {review.sentiment}
                              </span>
                            </td>
                            <td className="review-quote">{review.text}</td>
                            <td className="muted">{formatDate(review.created_at)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <EmptyView
                    title="No reviews yet"
                    message="Reader reviews will appear here once they are submitted."
                  />
                )}
              </section>
            </div>
          )}
        </>
      )}
    </div>
  );
}
