import { useEffect, useState } from 'react';
import { api } from '../../api.js';
import { EmptyView, ErrorView, Icons, StatusPill, categoryName, formatDate, money } from '../../ui.jsx';
import { Kpi, KpiSkeletons, ProductCell, StockPill, fetchAllBooks } from './common.jsx';

export function AdminOverviewView() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    (async () => {
      try {
        const [stats, books, orders] = await Promise.all([
          api.stats(),
          fetchAllBooks(),
          api.admin.orders({ limit: 5 }),
        ]);
        if (!cancelled) setData({ stats, books, orders });
      } catch (loadError) {
        if (!cancelled) setError(loadError.message);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [version]);

  if (error) {
    return (
      <div className="admin-page">
        <div className="kpi-grid" />
        <div className="admin-columns">
          <section className="panel">
            <ErrorView message={error} onRetry={() => setVersion((value) => value + 1)} />
          </section>
        </div>
      </div>
    );
  }

  const low = data
    ? data.books.filter((book) => book.stock <= 10).sort((a, b) => a.stock - b.stock)
    : null;
  const out = data ? data.books.filter((book) => book.stock === 0).length : 0;

  return (
    <div className="admin-page">
      <div className="kpi-grid" id="adminKpis">
        {data ? (
          <>
            <Kpi icon={Icons.book} label="Total titles" value={String(data.stats.total_books)} hint="in the catalog" />
            <Kpi icon={Icons.box} label="Units in stock" value={String(data.stats.total_stock)} hint="across all titles" />
            <Kpi icon={Icons.chart} label="Low stock" value={String(low.length)} hint="10 units or fewer" />
            <Kpi icon={Icons.close} label="Out of stock" value={String(out)} hint="needs restocking" />
            <Kpi
              icon={Icons.receipt}
              label="Inventory value"
              value={money(data.stats.inventory_value)}
              hint="retail value on hand"
            />
          </>
        ) : (
          <KpiSkeletons count={5} />
        )}
      </div>
      <div className="admin-columns">
        <section className="panel">
          <header className="panel-head">
            <h2>Needs attention</h2>
            <a className="link-arrow" href="#/admin/books">
              Manage books →
            </a>
          </header>
          {!low ? (
            <>
              <div className="skeleton skeleton-line" />
              <div className="skeleton skeleton-line" />
            </>
          ) : low.length ? (
            <div className="table-wrap">
              <table className="data-table compact">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Category</th>
                    <th>Stock</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {low.slice(0, 6).map((book) => (
                    <tr key={book.id}>
                      <td>
                        <ProductCell book={book} />
                      </td>
                      <td>{categoryName(book.category)}</td>
                      <td>{book.stock}</td>
                      <td>
                        <StockPill stock={book.stock} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyView
              title="Everything is stocked"
              message="No title is below the low-stock threshold."
            />
          )}
        </section>
        <section className="panel">
          <header className="panel-head">
            <h2>Recent orders</h2>
            <a className="link-arrow" href="#/admin/orders">
              All orders →
            </a>
          </header>
          {!data ? (
            <>
              <div className="skeleton skeleton-line" />
              <div className="skeleton skeleton-line" />
            </>
          ) : data.orders.length ? (
            <div className="table-wrap">
              <table className="data-table compact">
                <thead>
                  <tr>
                    <th>Order</th>
                    <th>Customer</th>
                    <th>Total</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.orders.map((order) => (
                    <tr key={order.id}>
                      <td>
                        <strong>#{order.id}</strong>
                        <span className="muted block">{formatDate(order.created_at)}</span>
                      </td>
                      <td>{order.customer_name}</td>
                      <td>{money(order.total)}</td>
                      <td>
                        <StatusPill status={order.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyView title="No orders yet" message="Orders placed in the store will appear here." />
          )}
        </section>
      </div>
    </div>
  );
}
