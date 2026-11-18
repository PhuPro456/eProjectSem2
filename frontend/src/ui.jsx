import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';

function svg(paths, { width = 1.7, filled = false } = {}) {
  return (
    <svg viewBox="0 0 24 24" fill={filled ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth={width}>
      {paths}
    </svg>
  );
}

export const Icons = {
  search: svg(<><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></>),
  cart: svg(
    <>
      <circle cx="9" cy="20" r="1.4" />
      <circle cx="18" cy="20" r="1.4" />
      <path d="M3 4h2l2.4 12.1a2 2 0 0 0 2 1.9h7.7a2 2 0 0 0 2-1.6L21 8H6" />
    </>,
  ),
  user: svg(<><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 3.6-6 8-6s8 2 8 6" /></>),
  receipt: svg(<><path d="M6 3h12v18l-3-2-3 2-3-2-3 2z" /><path d="M9 8h6M9 12h6" /></>),
  close: svg(<path d="M6 6l12 12M18 6 6 18" />, { width: 1.8 }),
  arrowLeft: svg(<path d="M15 5l-7 7 7 7" />, { width: 1.8 }),
  spark: svg(<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z" />, { width: 1.5 }),
  box: svg(<><path d="M21 8l-9-5-9 5v8l9 5 9-5z" /><path d="M3 8l9 5 9-5M12 13v8" /></>, { width: 1.6 }),
  users: svg(
    <>
      <circle cx="9" cy="8" r="4" />
      <path d="M2 21c0-4 3-6 7-6s7 2 7 6" />
      <circle cx="17" cy="9" r="3" />
      <path d="M17 15c3 0 5 2 5 5" />
    </>,
    { width: 1.6 },
  ),
  chart: svg(<><path d="M4 20V4M4 20h16" /><path d="M8 17v-5M12.5 17V8M17 17v-7" /></>, { width: 1.6 }),
  book: svg(
    <>
      <path d="M4 5a2 2 0 0 1 2-2h5v18H6a2 2 0 0 1-2-2z" />
      <path d="M20 5a2 2 0 0 0-2-2h-5v18h5a2 2 0 0 0 2-2z" />
    </>,
    { width: 1.6 },
  ),
  logout: svg(<><path d="M9 4H5v16h4" /><path d="M14 8l4 4-4 4M18 12H9" /></>),
  trash: svg(<path d="M4 7h16M9 7V4h6v3M6 7l1 14h10l1-14" />, { width: 1.6 }),
  edit: svg(<path d="M4 20h4L19 9a2.8 2.8 0 0 0-4-4L4 16z" />, { width: 1.6 }),
  plus: svg(<path d="M12 5v14M5 12h14" />, { width: 1.8 }),
  minus: svg(<path d="M5 12h14" />, { width: 1.8 }),
  menu: svg(<path d="M4 7h16M4 12h16M4 17h16" />, { width: 1.8 }),
};

export function money(value) {
  return '$' + Number(value || 0).toFixed(2);
}

export function categoryName(code) {
  return String(code || '')
    .split('-')
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export function formatDate(value, { omitYear = false } = {}) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value ?? '');
  const options = { year: 'numeric', month: 'short', day: 'numeric' };
  if (omitYear) delete options.year;
  return date.toLocaleDateString(undefined, options);
}

export function initials(name) {
  return String(name || '?')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join('');
}

export function debounce(fn, wait = 260) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), wait);
  };
}

export function StockLabel({ stock }) {
  if (stock <= 0) return <span className="stock out">Out of stock</span>;
  if (stock <= 10) return <span className="stock low">Only {stock} left</span>;
  return <span className="stock">In stock</span>;
}

export function StatusPill({ status }) {
  return <span className={`pill status-${status}`}>{status}</span>;
}

export function Stars({ rating }) {
  const filled = Math.max(0, Math.min(5, Number(rating) || 0));
  return (
    <span className="stars" aria-label={`${filled} out of 5`}>
      {'★'.repeat(filled)}
      {'☆'.repeat(5 - filled)}
    </span>
  );
}

export function BookCard({ book }) {
  return (
    <article className="book-card">
      <a className="book-cover" href={`#/book/${book.id}`} aria-label={book.title}>
        <img src={book.cover} alt={`Cover of ${book.title}`} loading="lazy" />
      </a>
      <a className="book-cat" href={`#/catalog?category=${encodeURIComponent(book.category)}`}>
        {categoryName(book.category)}
      </a>
      <h3 className="book-title">
        <a href={`#/book/${book.id}`}>{book.title}</a>
      </h3>
      <p className="book-author">{book.author}</p>
      <div className="book-meta">
        <span className="price">{money(book.price)}</span>
        <StockLabel stock={book.stock} />
      </div>
    </article>
  );
}

export function SkeletonGrid({ count = 12 }) {
  return (
    <div className="book-grid">
      {Array.from({ length: count }, (_, index) => (
        <div className="book-card skeleton-card" key={index}>
          <div className="skeleton skeleton-cover" />
          <div className="skeleton skeleton-line short" />
          <div className="skeleton skeleton-line" />
          <div className="skeleton skeleton-line tiny" />
        </div>
      ))}
    </div>
  );
}

export function ErrorView({ message, retry, onRetry }) {
  return (
    <div className="state-card">
      <h3>Something went wrong</h3>
      <p>{message}</p>
      {retry !== false && (
        <button className="btn" type="button" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

export function EmptyView({ title, message, action }) {
  return (
    <div className="state-card">
      <h3>{title}</h3>
      <p>{message}</p>
      {action}
    </div>
  );
}

/* ------------------------------------------------------------------ toasts */

const toastListeners = new Set();
let toastSeq = 0;

export function toast(message, kind = 'info') {
  toastListeners.forEach((listener) => listener({ id: ++toastSeq, message, kind }));
}

export function ToastHost() {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    const onToast = (item) => {
      setToasts((current) => [...current, item]);
      setTimeout(() => {
        setToasts((current) => current.map((t) => (t.id === item.id ? { ...t, leaving: true } : t)));
        setTimeout(() => setToasts((current) => current.filter((t) => t.id !== item.id)), 260);
      }, 3400);
    };
    toastListeners.add(onToast);
    return () => toastListeners.delete(onToast);
  }, []);

  return (
    <div className="toast-root" aria-live="polite" aria-atomic="false">
      {toasts.map((item) => (
        <div key={item.id} className={`toast toast-${item.kind}${item.leaving ? ' leaving' : ''}`}>
          {item.message}
        </div>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ modal */

export function Modal({ title, onClose, children, footer }) {
  useEffect(() => {
    document.body.classList.add('modal-open');
    const onKey = (event) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => {
      document.body.classList.remove('modal-open');
      document.removeEventListener('keydown', onKey);
    };
  }, [onClose]);

  return createPortal(
    <div
      className="modal-backdrop"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section className="modal" role="dialog" aria-modal="true">
        <header className="modal-head">
          <h2>{title}</h2>
          <button className="icon-btn" type="button" aria-label="Close" onClick={onClose}>
            {Icons.close}
          </button>
        </header>
        <div className="modal-body">{children}</div>
        {footer ? <footer className="modal-foot">{footer}</footer> : null}
      </section>
    </div>,
    document.body,
  );
}
