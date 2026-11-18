import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { useStore } from '../store.js';
import { EmptyView, ErrorView, StatusPill, formatDate, money } from '../ui.jsx';

export function OrdersView() {
  const { user } = useStore();
  const [status, setStatus] = useState({ state: 'loading' });
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setStatus({ state: 'loading' });
    api
      .myOrders()
      .then((orders) => {
        if (!cancelled) setStatus({ state: 'ready', orders });
      })
      .catch((error) => {
        if (!cancelled) setStatus({ state: 'error', message: error.message });
      });
    return () => {
      cancelled = true;
    };
  }, [version]);

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <p className="eyebrow">{user?.name || 'Your account'}</p>
          <h1>Your orders</h1>
        </div>
        <a className="btn ghost" href="#/catalog">
          Continue shopping
        </a>
      </header>
      {status.state === 'loading' && (
        <div id="ordersList">
          <div className="skeleton skeleton-line" />
          <div className="skeleton skeleton-line" />
        </div>
      )}
      {status.state === 'error' && (
        <ErrorView message={status.message} onRetry={() => setVersion((value) => value + 1)} />
      )}
      {status.state === 'ready' && !status.orders.length && (
        <EmptyView
          title="No orders yet"
          message="Your first order will appear here once you check out."
          action={
            <a className="btn" href="#/catalog">
              Browse books
            </a>
          }
        />
      )}
      {status.state === 'ready' && status.orders.length > 0 && (
        <div className="order-list">
          {status.orders.map((order) => (
            <article className="order-card" key={order.id}>
              <header>
                <div>
                  <p className="order-id">Order #{order.id}</p>
                  <p className="order-date">{formatDate(order.created_at)}</p>
                </div>
                <StatusPill status={order.status} />
              </header>
              <ul className="order-items">
                {order.items.map((item) => (
                  <li key={item.book_id ?? item.title}>
                    <span>{item.title}</span>
                    <span className="muted">× {item.quantity}</span>
                    <span>{money(item.unit_price * item.quantity)}</span>
                  </li>
                ))}
              </ul>
              <footer>
                <span className="muted">
                  {order.items.reduce((sum, item) => sum + item.quantity, 0)} item(s)
                </span>
                <strong>{money(order.total)}</strong>
              </footer>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
