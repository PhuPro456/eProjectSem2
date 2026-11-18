import { useEffect, useState } from 'react';
import { api } from '../../api.js';
import { EmptyView, Icons, categoryName, money } from '../../ui.jsx';
import { Kpi, KpiSkeletons } from './common.jsx';

export function AnalyticsView() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    api.admin
      .analytics()
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

  return (
    <div className="admin-page analytics-page">
      <div className="analytics-banner">
        <div>
          <p className="eyebrow">Business intelligence</p>
          <h2>Sales &amp; customer overview</h2>
          <p className="muted">Live from non-cancelled orders, inventory and reader accounts.</p>
        </div>
        <span className="live-chip">
          <i />
          Live data
        </span>
      </div>
      {error ? (
        <div className="analytics-grid">
          <div className="state-card">
            <h3>Could not load analytics</h3>
            <p>{error}</p>
            <button className="btn" type="button" onClick={() => setVersion((value) => value + 1)}>
              Try again
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="kpi-grid">
            {data ? (
              <>
                <Kpi
                  icon={Icons.chart}
                  label="Total revenue"
                  value={money(data.total_revenue)}
                  hint={`${data.total_orders} orders counted`}
                />
                <Kpi
                  icon={Icons.receipt}
                  label="Orders"
                  value={String(data.total_orders)}
                  hint={`${data.units_sold} units sold`}
                />
                <Kpi
                  icon={Icons.box}
                  label="Average order"
                  value={money(data.average_order_value)}
                  hint="per non-cancelled order"
                />
                <Kpi
                  icon={Icons.users}
                  label="Customers"
                  value={String(data.total_customers)}
                  hint={`${data.repeat_customers} repeat readers`}
                />
                <Kpi
                  icon={Icons.spark}
                  label="Monthly growth"
                  value={`${Number(data.growth_rate) >= 0 ? '+' : ''}${(Number(data.growth_rate) || 0).toFixed(1)}%`}
                  hint={`${data.low_stock_books} low-stock titles`}
                />
              </>
            ) : (
              <KpiSkeletons count={5} />
            )}
          </div>
          {data && (
            <div className="analytics-grid">
              <section className="panel wide">
                <header className="panel-head">
                  <h2>Revenue by month</h2>
                  <span className="muted">Last 8 months</span>
                </header>
                <RevenueChart points={data.sales_by_month} />
              </section>
              <section className="panel">
                <header className="panel-head">
                  <h2>Order status mix</h2>
                  <span className="muted">All orders</span>
                </header>
                <StatusMix points={data.order_statuses} />
              </section>
              <section className="panel">
                <header className="panel-head">
                  <h2>Revenue by category</h2>
                  <span className="muted">Non-cancelled</span>
                </header>
                <CategoryBars points={data.sales_by_category} />
              </section>
              <section className="panel">
                <header className="panel-head">
                  <h2>New customers</h2>
                  <span className="muted">Monthly sign-ups</span>
                </header>
                <NewCustomers points={data.new_customers_by_month} />
              </section>
              <section className="panel">
                <header className="panel-head">
                  <h2>Top products</h2>
                  <span className="muted">By revenue</span>
                </header>
                {data.top_products.length ? (
                  <div className="table-wrap">
                    <table className="data-table compact">
                      <thead>
                        <tr>
                          <th>Title</th>
                          <th>Units</th>
                          <th>Revenue</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.top_products.map((product) => (
                          <tr key={product.book_id}>
                            <td>
                              <a href={`#/book/${product.book_id}`}>{product.title}</a>
                            </td>
                            <td>{product.units}</td>
                            <td>{money(product.revenue)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <EmptyView
                    title="No product sales yet"
                    message="Top titles appear once orders are placed."
                  />
                )}
              </section>
              <section className="panel wide">
                <header className="panel-head">
                  <h2>Top customers</h2>
                  <span className="muted">By lifetime spend</span>
                </header>
                {data.top_customers.length ? (
                  <div className="table-wrap">
                    <table className="data-table compact">
                      <thead>
                        <tr>
                          <th>Customer</th>
                          <th>Orders</th>
                          <th>Spend</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.top_customers.map((customer) => (
                          <tr key={customer.email}>
                            <td>
                              <div>
                                <strong>{customer.name}</strong>
                                <span className="muted block">{customer.email}</span>
                              </div>
                            </td>
                            <td>{customer.orders}</td>
                            <td>{money(customer.spend)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <EmptyView title="No customers yet" message="Registered readers will appear here." />
                )}
              </section>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function shortMoney(value) {
  const number = Number(value) || 0;
  if (number >= 1000) return `$${(number / 1000).toFixed(1)}k`;
  return `$${Math.round(number)}`;
}

function RevenueChart({ points }) {
  const width = 760;
  const height = 260;
  const left = 48;
  const right = 18;
  const top = 18;
  const bottom = 34;
  const innerW = width - left - right;
  const innerH = height - top - bottom;
  const max = Math.max(...points.map((point) => point.revenue), 1);
  const step = points.length > 1 ? innerW / (points.length - 1) : innerW;
  const x = (index) => left + index * step;
  const y = (value) => top + innerH - (value / max) * innerH;
  const coords = points.map((point, index) => [x(index), y(point.revenue)]);
  const line = coords
    .map(([cx, cy], index) => `${index ? 'L' : 'M'}${cx.toFixed(1)} ${cy.toFixed(1)}`)
    .join(' ');
  const area = `${line} L${x(points.length - 1).toFixed(1)} ${top + innerH} L${left} ${top + innerH} Z`;

  return (
    <svg className="chart-svg" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Revenue by month">
      <defs>
        <linearGradient id="revenueFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(31,77,59,0.28)" />
          <stop offset="100%" stopColor="rgba(31,77,59,0.02)" />
        </linearGradient>
      </defs>
      {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
        const gy = top + innerH - ratio * innerH;
        return (
          <g key={ratio}>
            <line x1={left} y1={gy.toFixed(1)} x2={width - right} y2={gy.toFixed(1)} className="chart-grid" />
            <text x={left - 8} y={gy + 4} textAnchor="end" className="chart-axis">
              {shortMoney(max * ratio)}
            </text>
          </g>
        );
      })}
      <path d={area} fill="url(#revenueFill)" />
      <path d={line} className="chart-line" />
      {coords.map(([cx, cy], index) => (
        <circle cx={cx.toFixed(1)} cy={cy.toFixed(1)} r="4" className="chart-dot" key={index}>
          <title>
            {points[index].label}: {money(points[index].revenue)} · {points[index].orders} orders
          </title>
        </circle>
      ))}
      {points.map((point, index) => (
        <text x={x(index).toFixed(1)} y={height - 10} textAnchor="middle" className="chart-axis" key={index}>
          {point.label}
        </text>
      ))}
    </svg>
  );
}

function StatusMix({ points }) {
  const total = points.reduce((sum, point) => sum + point.count, 0);
  if (!total) {
    return <EmptyView title="No orders yet" message="Status distribution appears after checkout." />;
  }
  return (
    <>
      <div className="mix-bar">
        {points
          .filter((point) => point.count > 0)
          .map((point) => (
            <span
              className={`mix-seg seg-${point.status}`}
              style={{ width: `${((point.count / total) * 100).toFixed(1)}%` }}
              title={`${point.status}: ${point.count}`}
              key={point.status}
            />
          ))}
      </div>
      <ul className="mix-legend">
        {points.map((point) => (
          <li key={point.status}>
            <span className={`legend-dot seg-${point.status}`} />
            <span>{point.status}</span>
            <strong>{point.count}</strong>
          </li>
        ))}
      </ul>
    </>
  );
}

function CategoryBars({ points }) {
  if (!points.length) {
    return (
      <EmptyView title="No sales yet" message="Category revenue appears after the first order." />
    );
  }
  const max = Math.max(...points.map((point) => point.revenue), 1);
  return (
    <ul className="bar-list">
      {points.map((point) => (
        <li className="bar-row" key={point.category}>
          <div className="bar-label">
            <span>{categoryName(point.category)}</span>
            <strong>{money(point.revenue)}</strong>
          </div>
          <div className="bar-track">
            <span className="bar-fill" style={{ width: `${((point.revenue / max) * 100).toFixed(1)}%` }} />
          </div>
          <span className="bar-note">{point.units} units sold</span>
        </li>
      ))}
    </ul>
  );
}

function NewCustomers({ points }) {
  const max = Math.max(...points.map((point) => point.new_customers), 1);
  return (
    <div className="mini-chart">
      {points.map((point) => {
        const barHeight = point.new_customers ? Math.max(8, (point.new_customers / max) * 100) : 2;
        return (
          <div
            className="mini-col"
            title={`${point.label}: ${point.new_customers} new customers`}
            key={point.label}
          >
            <span className="mini-bar" style={{ height: `${barHeight.toFixed(1)}%` }}>
              <em>{point.new_customers}</em>
            </span>
            <small>{point.label}</small>
          </div>
        );
      })}
    </div>
  );
}
