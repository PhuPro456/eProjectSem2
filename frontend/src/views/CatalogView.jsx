import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../api.js';
import { rewriteUrl } from '../router.js';
import { BookCard, EmptyView, ErrorView, SkeletonGrid, categoryName, debounce } from '../ui.jsx';

const PAGE_SIZE = 12;
const SORTS = {
  id_asc: { sort_by: 'id', order: 'asc' },
  price_asc: { sort_by: 'price', order: 'asc' },
  price_desc: { sort_by: 'price', order: 'desc' },
  title_asc: { sort_by: 'title', order: 'asc' },
  stock_desc: { sort_by: 'stock', order: 'desc' },
};

function readQuery() {
  const raw = (location.hash || '').split('?')[1] || '';
  const params = new URLSearchParams(raw);
  return {
    q: params.get('q') || '',
    category: params.get('category') || '',
    sort: SORTS[params.get('sort')] ? params.get('sort') : 'id_asc',
    availability: params.get('availability') || '',
    page: Math.max(1, Number(params.get('page')) || 1),
  };
}

function buildQuery(filters) {
  const params = new URLSearchParams();
  if (filters.q) params.set('q', filters.q);
  if (filters.category) params.set('category', filters.category);
  if (filters.sort !== 'id_asc') params.set('sort', filters.sort);
  if (filters.availability) params.set('availability', filters.availability);
  if (filters.page > 1) params.set('page', String(filters.page));
  const query = params.toString();
  return `#/catalog${query ? `?${query}` : ''}`;
}

export function CatalogView() {
  const [filters, setFilters] = useState(readQuery);
  const [categories, setCategories] = useState([]);
  const [status, setStatus] = useState({ state: 'loading' });
  const headRef = useRef(null);
  const filtersRef = useRef(filters);
  filtersRef.current = filters;

  const load = useCallback(async (next) => {
    rewriteUrl(buildQuery(next));
    setStatus({ state: 'loading' });
    const sort = SORTS[next.sort] || SORTS.id_asc;
    try {
      const data = await api.listBooks({
        skip: (next.page - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
        keyword: next.q || undefined,
        category: next.category || undefined,
        is_available: next.availability === '' ? undefined : next.availability === 'true',
        sort_by: sort.sort_by,
        order: sort.order,
      });
      setStatus({ state: 'ready', data });
    } catch (error) {
      setStatus({ state: 'error', message: error.message });
    }
  }, []);

  useEffect(() => {
    api.categories().then(setCategories).catch(() => setCategories([]));
    load(filtersRef.current);
  }, [load]);

  const change = useCallback(
    (patch) => {
      const next = { ...filtersRef.current, page: 1, ...patch };
      setFilters(next);
      load(next);
    },
    [load],
  );

  const goPage = useCallback(
    (page) => {
      const next = { ...filtersRef.current, page };
      setFilters(next);
      load(next);
      headRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    },
    [load],
  );

  const debouncedSearch = useRef(
    debounce((value) => change({ q: value.trim() })),
  ).current;

  function clearFilters() {
    const next = { q: '', category: '', availability: '', sort: 'id_asc', page: 1 };
    setFilters(next);
    load(next);
  }

  return (
    <div className="page catalog-page">
      <header className="catalog-head" ref={headRef}>
        <div>
          <p className="eyebrow">The collection</p>
          <h1>{filters.category ? categoryName(filters.category) : 'All books'}</h1>
        </div>
        <p className="results-count" aria-live="polite">
          {status.state === 'loading'
            ? 'Loading…'
            : status.state === 'error'
              ? 'Unavailable'
              : `${status.data.total} book${status.data.total === 1 ? '' : 's'}`}
        </p>
      </header>
      <div className="catalog-controls">
        <label className="field search-field">
          <span className="sr-only">Search books</span>
          <input
            type="search"
            defaultValue={filters.q}
            placeholder="Search titles or authors…"
            autoComplete="off"
            onChange={(event) => debouncedSearch(event.target.value)}
          />
        </label>
        <label className="field">
          <span className="sr-only">Category</span>
          <select
            value={filters.category}
            onChange={(event) => change({ category: event.target.value })}
          >
            <option value="">All categories</option>
            {categories.map((category) => (
              <option value={category.code} key={category.code}>
                {category.name} ({category.book_count})
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span className="sr-only">Availability</span>
          <select
            value={filters.availability}
            onChange={(event) => change({ availability: event.target.value })}
          >
            <option value="">Any availability</option>
            <option value="true">In stock</option>
            <option value="false">Out of stock</option>
          </select>
        </label>
        <label className="field">
          <span className="sr-only">Sort</span>
          <select value={filters.sort} onChange={(event) => change({ sort: event.target.value })}>
            <option value="id_asc">Featured</option>
            <option value="price_asc">Price: low to high</option>
            <option value="price_desc">Price: high to low</option>
            <option value="title_asc">Title: A–Z</option>
            <option value="stock_desc">Stock: high to low</option>
          </select>
        </label>
        <button className="btn ghost" type="button" onClick={clearFilters}>
          Clear
        </button>
      </div>
      {status.state === 'error' ? (
        <ErrorView message={status.message} onRetry={() => load(filtersRef.current)} />
      ) : status.state === 'loading' ? (
        <SkeletonGrid count={PAGE_SIZE} />
      ) : status.data.items.length ? (
        <div className="book-grid">
          {status.data.items.map((book) => (
            <BookCard book={book} key={book.id} />
          ))}
        </div>
      ) : (
        <EmptyView
          title="No books found"
          message="Try a different search, category, or availability filter."
          action={
            <button className="btn ghost" type="button" onClick={clearFilters}>
              Clear filters
            </button>
          }
        />
      )}
      {status.state === 'ready' && (
        <Pagination total={status.data.total} page={filters.page} onPage={goPage} />
      )}
    </div>
  );
}

function Pagination({ total, page, onPage }) {
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  if (pages <= 1) return null;
  const current = Math.min(page, pages);
  const start = Math.max(1, current - 2);
  const end = Math.min(pages, start + 4);
  const numbers = [];
  for (let index = start; index <= end; index += 1) numbers.push(index);

  return (
    <nav className="pagination" aria-label="Pagination">
      <button type="button" className="page-btn" disabled={current === 1} onClick={() => onPage(current - 1)}>
        Previous
      </button>
      {start > 1 && (
        <>
          <button type="button" className="page-btn" onClick={() => onPage(1)}>
            1
          </button>
          {start > 2 && <span className="page-ellipsis">…</span>}
        </>
      )}
      {numbers.map((number) => (
        <button
          type="button"
          className={`page-btn${number === current ? ' active' : ''}`}
          onClick={() => onPage(number)}
          key={number}
        >
          {number}
        </button>
      ))}
      {end < pages && (
        <>
          {end < pages - 1 && <span className="page-ellipsis">…</span>}
          <button type="button" className="page-btn" onClick={() => onPage(pages)}>
            {pages}
          </button>
        </>
      )}
      <button type="button" className="page-btn" disabled={current === pages} onClick={() => onPage(current + 1)}>
        Next
      </button>
    </nav>
  );
}
