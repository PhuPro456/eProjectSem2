import { useEffect, useState } from 'react';
import { api } from '../../api.js';
import { ErrorView, formatDate, toast } from '../../ui.jsx';

export function AdminCustomersView() {
  const [users, setUsers] = useState(null);
  const [error, setError] = useState(null);
  const [busyUser, setBusyUser] = useState(null);

  const load = () => {
    setError(null);
    setUsers(null);
    api.admin
      .users()
      .then(setUsers)
      .catch((loadError) => setError(loadError.message));
  };

  useEffect(load, []);

  async function updateRole(userId, role) {
    setBusyUser(userId);
    try {
      await api.admin.updateRole(Number(userId), role);
      toast('Role updated', 'success');
    } catch (updateError) {
      toast(updateError.message, 'error');
    } finally {
      load();
    }
  }

  return (
    <div className="admin-page">
      <div className="panel">
        <header className="panel-head">
          <h2>Customers &amp; users</h2>
          <span className="muted">{users ? `${users.length} accounts` : ''}</span>
        </header>
        {error ? (
          <ErrorView message={error} onRetry={load} />
        ) : !users ? (
          <>
            <div className="skeleton skeleton-line" />
            <div className="skeleton skeleton-line" />
          </>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Joined</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id}>
                    <td>
                      <strong>{user.name}</strong>
                    </td>
                    <td>{user.email}</td>
                    <td>
                      <select
                        className="role-select"
                        defaultValue={user.role}
                        disabled={busyUser === user.id}
                        onChange={(event) => updateRole(user.id, event.target.value)}
                      >
                        <option value="customer">customer</option>
                        <option value="admin">admin</option>
                      </select>
                    </td>
                    <td>
                      {user.is_active ? (
                        <span className="pill status-completed">Active</span>
                      ) : (
                        <span className="pill status-cancelled">Inactive</span>
                      )}
                    </td>
                    <td>{formatDate(user.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
