import { useEffect, useState } from 'react';
import { api } from '../../api.js';
import { ErrorView, Icons, formatDate, toast } from '../../ui.jsx';

export function AdminAiKeysView() {
  const [providers, setProviders] = useState([]);
  const [keys, setKeys] = useState(null);
  const [error, setError] = useState(null);
  const [provider, setProvider] = useState('');
  const [label, setLabel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [formError, setFormError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [busyKey, setBusyKey] = useState(null);
  const [verifications, setVerifications] = useState({});

  useEffect(() => {
    api.ai.providers().then(setProviders).catch(() => setProviders([]));
  }, []);

  useEffect(() => {
    if (providers.length && !provider) setProvider(providers[0].slug);
  }, [providers, provider]);

  const load = () => {
    setError(null);
    setKeys(null);
    api.admin
      .aiKeys()
      .then(setKeys)
      .catch((loadError) => setError(loadError.message));
  };

  useEffect(load, []);

  const selected = providers.find((entry) => entry.slug === provider);
  const names = Object.fromEntries(providers.map((entry) => [entry.slug, entry.name]));

  async function save(event) {
    event.preventDefault();
    setFormError(null);
    setSaving(true);
    try {
      await api.admin.createAiKey({ provider, label: label.trim(), api_key: apiKey.trim() });
      toast('AI key saved', 'success');
      setLabel('');
      setApiKey('');
      load();
    } catch (saveError) {
      setFormError(saveError.message);
    } finally {
      setSaving(false);
    }
  }

  async function verify(id) {
    setBusyKey(id);
    try {
      const result = await api.admin.verifyAiKey(id);
      setVerifications((current) => ({
        ...current,
        [id]: { message: result.message, ok: result.status === 'format_ok' },
      }));
      toast(result.message, result.status === 'format_ok' ? 'success' : 'error');
    } catch (verifyError) {
      toast(verifyError.message, 'error');
    } finally {
      setBusyKey(null);
    }
  }

  async function activate(id, keyLabel) {
    setBusyKey(id);
    try {
      await api.admin.activateAiKey(id);
      toast(`${keyLabel} is now the active key`, 'success');
      load();
    } catch (activateError) {
      toast(activateError.message, 'error');
    } finally {
      setBusyKey(null);
    }
  }

  async function remove(id) {
    if (!window.confirm('Delete this AI key?')) return;
    setBusyKey(id);
    try {
      await api.admin.deleteAiKey(id);
      toast('AI key deleted', 'success');
      load();
    } catch (deleteError) {
      toast(deleteError.message, 'error');
    } finally {
      setBusyKey(null);
    }
  }

  return (
    <div className="admin-page">
      <div className="admin-columns">
        <section className="panel ai-keys">
          <header className="panel-head">
            <h2>Create new API key</h2>
            <span className="muted">{keys ? `${keys.length} stored` : ''}</span>
          </header>
          <p className="muted">
            The active administrator key powers the storefront assistant. New keys become active
            automatically; switch back at any time. Keys are encrypted with the server secret
            before storage.
          </p>
          <form className="key-form" id="adminAiKeyForm" onSubmit={save}>
            <label className="field">
              <span>Provider</span>
              <select value={provider} onChange={(event) => setProvider(event.target.value)}>
                {providers.map((entry) => (
                  <option value={entry.slug} key={entry.slug}>
                    {entry.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Label</span>
              <input
                maxLength="80"
                placeholder="Storefront Gemini key"
                required
                value={label}
                onChange={(event) => setLabel(event.target.value)}
              />
            </label>
            <label className="field">
              <span>API key</span>
              <input
                type="password"
                autoComplete="off"
                minLength="20"
                maxLength="512"
                placeholder={selected ? `${selected.key_prefix}…` : '…'}
                required
                value={apiKey}
                onChange={(event) => setApiKey(event.target.value)}
              />
            </label>
            <p className="key-hint">
              {selected ? `${selected.name} keys start with ${selected.key_prefix}` : 'Choose a provider'}
            </p>
            {formError && <p className="form-error">{formError}</p>}
            <button className="btn full" type="submit" disabled={saving}>
              Save encrypted key
            </button>
          </form>
        </section>

        <section className="panel">
          <header className="panel-head">
            <h2>Stored administrator keys</h2>
          </header>
          {error ? (
            <ErrorView message={error} onRetry={load} />
          ) : !keys ? (
            <>
              <div className="skeleton skeleton-line" />
              <div className="skeleton skeleton-line short" />
            </>
          ) : keys.length === 0 ? (
            <p className="key-empty muted">
              No keys yet. Add one to enable conversational AI on the storefront.
            </p>
          ) : (
            <>
              {!keys.some((key) => key.is_active) && (
                <p className="key-empty muted">
                  No key is active — the storefront assistant is using the local recommender.
                </p>
              )}
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Provider</th>
                      <th>Label</th>
                      <th>Stored key</th>
                      <th>Added</th>
                      <th>Status</th>
                      <th aria-label="Actions" />
                    </tr>
                  </thead>
                  <tbody>
                    {keys.map((key) => (
                      <tr key={key.id}>
                        <td>{names[key.provider] || key.provider}</td>
                        <td>
                          <strong>{key.label}</strong>
                        </td>
                        <td>
                          <code>{key.key_hint}</code>
                        </td>
                        <td>{formatDate(key.created_at)}</td>
                        <td>
                          {key.is_active ? (
                            <span className="pill status-completed">Active</span>
                          ) : (
                            <span className="pill">Inactive</span>
                          )}
                          {verifications[key.id] && (
                            <p className={`key-status ${verifications[key.id].ok ? 'ok' : 'bad'}`}>
                              {verifications[key.id].message}
                            </p>
                          )}
                        </td>
                        <td>
                          <div className="key-actions">
                            {!key.is_active && (
                              <button
                                className="btn ghost tiny"
                                type="button"
                                disabled={busyKey === key.id}
                                onClick={() => activate(key.id, key.label)}
                              >
                                Activate
                              </button>
                            )}
                            <button
                              className="btn ghost tiny"
                              type="button"
                              disabled={busyKey === key.id}
                              onClick={() => verify(key.id)}
                            >
                              Verify
                            </button>
                            <button
                              className="icon-btn danger"
                              type="button"
                              aria-label="Delete key"
                              disabled={busyKey === key.id}
                              onClick={() => remove(key.id)}
                            >
                              {Icons.trash}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
