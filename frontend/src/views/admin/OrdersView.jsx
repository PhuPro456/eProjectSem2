import { useEffect, useState } from 'react';
import { api } from '../../api.js';
import { EmptyView, ErrorView, StatusPill, formatDate, money, toast } from '../../ui.jsx';
import { NEXT_STATUS, STATUSES } from './common.jsx';

export function AdminOrdersView() {
  const [status, setStatus] = useState('');
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState(null);
  const [busyOrder, setBusyOrder] = useState(null);

  const load = () => {
    setError(null);
    setOrders(null);
    api.admin
      .orders({ status: status || undefined, limit: 100 })
      .then(setOrders)
      .catch((loadError) => setError(loadError.message));
  };

  // reload whenever the filter changes (initial mount included)
  useEffect(load, [status]);

  async function move(orderId, nextStatus) {
    if (!nextStatus) return;
    setBusyOrder(orderId);
    try {
      await api.admin.updateOrderStatus(Number(orderId), nextStatus);
      toast(`Order #${orderId} marked ${nextStatus}`, 'success');
      load();
    } catch (updateError) {
      toast(updateError.message, 'error');
    } finally {
      setBusyOrder(null);
    }
  }

  return (
    <div className="admin-page">
      <div className="admin-toolbar">
        <label className="field">
          <span className="sr-only">Status</span>
          <select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">All statuses</option>
            {STATUSES.map((entry) => (
              <option value={entry} key={entry}>
                {entry}
              </option>
            ))}
          </select>
        </label>
        <button className="btn ghost" type="button" onClick={load}>
          Refresh
        </button>
      </div>
      <div className="panel">
        {error ? (
          <ErrorView message={error} onRetry={load} />
        ) : !orders ? (
          <div className="skeleton skeleton-line" />
        ) : !orders.length ? (
          <EmptyView title="No orders" message="Orders will appear here after customers check out." />
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Order</th>
                  <th>Customer</th>
                  <th>Items</th>
                  <th>Total</th>
                  <th>Placed</th>
                  <th>Status</th>
                  <th>Update</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => {
                  const next = NEXT_STATUS[order.status] || [];
                  return (
                    <tr key={order.id}>
                      <td>
                        <strong>#{order.id}</strong>
                      </td>
                      <td>
                        <div>
                          <strong>{order.customer_name}</strong>
                          <span className="muted block">{order.customer_email}</span>
                        </div>
                      </td>
                      <td>{order.item_count}</td>
                      <td>{money(order.total)}</td>
                      <td>{formatDate(order.created_at)}</td>
                      <td>
                        <StatusPill status={order.status} />
                      </td>
                      <td>
                        {next.length ? (
                          <select
                            className="status-select"
                            defaultValue=""
                            disabled={busyOrder === order.id}
                            onChange={(event) => move(order.id, event.target.value)}
                          >
                            <option value="">Move to…</option>
                            {next.map((entry) => (
                              <option value={entry} key={entry}>
                                {entry}
                              </option>
                            ))}
                          </select>
                        ) : (
                          <span className="muted">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
