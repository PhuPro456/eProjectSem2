import { api } from '../../api.js';
import { money } from '../../ui.jsx';

export const STATUSES = ['pending', 'paid', 'shipped', 'completed', 'cancelled'];
export const NEXT_STATUS = {
  pending: ['paid', 'cancelled'],
  paid: ['shipped', 'cancelled'],
  shipped: ['completed'],
  completed: [],
  cancelled: [],
};

export async function fetchAllBooks() {
  const books = [];
  let skip = 0;
  for (;;) {
    const page = await api.listBooks({ limit: 50, skip, sort_by: 'id', order: 'asc' });
    books.push(...page.items);
    skip += 50;
    if (skip >= page.total) break;
  }
  return books;
}

export function StockPill({ stock }) {
  if (stock <= 0) return <span className="pill status-cancelled">Out of stock</span>;
  if (stock <= 10) return <span className="pill status-pending">Low stock</span>;
  return <span className="pill status-completed">In stock</span>;
}

export function Thumb({ book }) {
  return book.cover ? (
    <img className="thumb" src={book.cover} alt="" loading="lazy" />
  ) : (
    <span className="thumb thumb-empty">—</span>
  );
}

export function Kpi({ icon, label, value, hint }) {
  return (
    <article className="kpi">
      <span className="kpi-icon">{icon}</span>
      <div>
        <span className="kpi-label">{label}</span>
        <strong>{value}</strong>
        <span className="kpi-hint">{hint}</span>
      </div>
    </article>
  );
}

export function KpiSkeletons({ count }) {
  return (
    <>
      {Array.from({ length: count }, (_, index) => (
        <div className="kpi skeleton" style={{ height: 104 }} key={index} />
      ))}
    </>
  );
}

export function ProductCell({ book }) {
  return (
    <div className="cell-product">
      <Thumb book={book} />
      <div>
        <strong>{book.title}</strong>
        <span className="muted">
          #{book.id} · {book.author}
        </span>
      </div>
    </div>
  );
}

export { money };
