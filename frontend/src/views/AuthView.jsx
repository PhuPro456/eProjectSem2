import { useState } from 'react';
import { api } from '../api.js';
import { loadUser, setToken } from '../store.js';
import { toast } from '../ui.jsx';

const DEMO_ACCOUNTS = [
  {
    label: 'Admin console',
    email: 'admin@bookstorepro.com',
    password: 'admin-password-123',
    next: '#/admin',
  },
  {
    label: 'Shopper',
    email: 'maya.chen@example.com',
    password: 'reader-password-1',
    next: '#/',
  },
];

function afterAuth() {
  const next = sessionStorage.getItem('bookstore.next') || '#/';
  sessionStorage.removeItem('bookstore.next');
  const reopenCart = sessionStorage.getItem('bookstore.reopenCart') === '1';
  sessionStorage.removeItem('bookstore.reopenCart');
  location.hash = next;
  if (reopenCart) {
    setTimeout(() => document.dispatchEvent(new Event('open-cart')), 80);
  }
}

export function LoginView() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [pending, setPending] = useState(false);

  async function submitLogin(loginEmail, loginPassword) {
    setError(null);
    if (!loginEmail || !loginPassword) {
      setError('Enter your email and password.');
      return;
    }
    setPending(true);
    try {
      const token = await api.login(loginEmail, loginPassword);
      setToken(token.access_token);
      await loadUser();
      toast('Signed in', 'success');
      afterAuth();
    } catch (loginError) {
      setError(loginError.message);
      setPending(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <p className="eyebrow">Welcome back</p>
        <h1>Sign in</h1>
        <p className="auth-sub">
          Track your orders, check out faster, and keep your cart between visits.
        </p>
        <form
          className="form"
          noValidate
          onSubmit={(event) => {
            event.preventDefault();
            submitLogin(email.trim(), password);
          }}
        >
          <label>
            Email
            <input
              type="email"
              required
              autoComplete="email"
              placeholder="you@example.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label>
            Password
            <input
              type="password"
              required
              autoComplete="current-password"
              placeholder="Your password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          {error && <p className="form-error">{error}</p>}
          <button className="btn full" type="submit" disabled={pending}>
            {pending ? 'Please wait…' : 'Sign in'}
          </button>
        </form>
        <div className="auth-demo">
          <p className="auth-demo-title">Demo accounts</p>
          <div className="auth-demo-actions">
            {DEMO_ACCOUNTS.map((account) => (
              <button
                className="auth-demo-btn"
                type="button"
                key={account.email}
                onClick={() => {
                  setEmail(account.email);
                  setPassword(account.password);
                  sessionStorage.setItem('bookstore.next', account.next);
                  submitLogin(account.email, account.password);
                }}
              >
                <span className="auth-demo-role">{account.label}</span>
                <span className="auth-demo-mail">{account.email}</span>
              </button>
            ))}
          </div>
          <p className="auth-demo-hint">Pick one to fill the form and sign straight in.</p>
        </div>
        <p className="auth-alt">
          New here? <a href="#/register">Create an account</a>
        </p>
      </div>
    </div>
  );
}

export function RegisterView() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [pending, setPending] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setError(null);
    const trimmedName = name.trim();
    const trimmedEmail = email.trim();
    if (trimmedName.length < 1 || !trimmedEmail || password.length < 8) {
      setError('Name, a valid email, and a password of at least 8 characters are required.');
      return;
    }
    setPending(true);
    try {
      await api.register({ name: trimmedName, email: trimmedEmail, password });
      const token = await api.login(trimmedEmail, password);
      setToken(token.access_token);
      await loadUser();
      toast('Account created — welcome aboard', 'success');
      afterAuth();
    } catch (registerError) {
      setError(registerError.message);
      setPending(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <p className="eyebrow">Join the club</p>
        <h1>Create account</h1>
        <p className="auth-sub">One account for orders, faster checkout, and your reading history.</p>
        <form className="form" noValidate onSubmit={submit}>
          <label>
            Name
            <input
              type="text"
              required
              maxLength="100"
              autoComplete="name"
              placeholder="Ada Lovelace"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </label>
          <label>
            Email
            <input
              type="email"
              required
              autoComplete="email"
              placeholder="you@example.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label>
            Password
            <input
              type="password"
              required
              minLength="8"
              maxLength="128"
              autoComplete="new-password"
              placeholder="At least 8 characters"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          {error && <p className="form-error">{error}</p>}
          <button className="btn full" type="submit" disabled={pending}>
            {pending ? 'Please wait…' : 'Create account'}
          </button>
        </form>
        <p className="auth-alt">
          Already have an account? <a href="#/login">Sign in</a>
        </p>
      </div>
    </div>
  );
}
