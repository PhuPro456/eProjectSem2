import { useEffect, useRef, useState } from 'react';
import { api } from './api.js';
import {
  cartCount,
  cartClear,
  cartRemove,
  cartSetQuantity,
  cartTotal,
  getState,
  isAdmin,
  logout,
  useStore,
} from './store.js';
import { navigate } from './router.js';
import { Icons, initials, money, toast } from './ui.jsx';

function Wordmark({ light = false }) {
  return (
    <a className={light ? 'wordmark light' : 'wordmark'} href="#/">
      Bookstore<span>Pro</span>
    </a>
  );
}

function AccountMenu({ user, open, onToggle, onClose, onLogout }) {
  return (
    <div className="account">
      <button
        className="account-btn"
        type="button"
        aria-haspopup="true"
        aria-expanded={open}
        onClick={onToggle}
      >
        {Icons.user}
        <span className="account-name">{user?.name?.split(/\s+/)[0] || 'Sign in'}</span>
      </button>
      <div className="account-menu" hidden={!open}>
        {user ? (
          <>
            <div className="account-head">
              <strong>{user.name}</strong>
              <span>{user.email}</span>
            </div>
            <a href="#/orders" onClick={onClose}>
              {Icons.receipt}
              <span>Your orders</span>
            </a>
            <a href="#/ai" onClick={onClose}>
              {Icons.spark}
              <span>AI reading room</span>
            </a>
            {isAdmin(user) && (
              <a href="#/admin" onClick={onClose}>
                {Icons.chart}
                <span>Admin console</span>
              </a>
            )}
            <button
              type="button"
              onClick={() => {
                onClose();
                onLogout();
              }}
            >
              {Icons.logout}
              <span>Sign out</span>
            </button>
          </>
        ) : (
          <>
            <div className="account-head">
              <strong>Welcome</strong>
              <span>Sign in to check out faster and keep track of your orders.</span>
            </div>
            <a href="#/login" onClick={onClose}>
              {Icons.user}
              <span>Sign in</span>
            </a>
            <a href="#/register" onClick={onClose}>
              {Icons.plus}
              <span>Create account</span>
            </a>
          </>
        )}
      </div>
    </div>
  );
}

function CartDrawer({ user, open, onClose, onOrderPlaced }) {
  const [placing, setPlacing] = useState(false);
  const closeRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    closeRef.current?.focus();
    const onKey = (event) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  async function checkout() {
    const cart = getState().cart;
    if (!cart.length) return;
    if (!user) {
      sessionStorage.setItem('bookstore.next', '#/orders');
      sessionStorage.setItem('bookstore.reopenCart', '1');
      onClose();
      navigate('#/login');
      toast('Sign in to place your order', 'info');
      return;
    }
    setPlacing(true);
    try {
      const order = await api.checkout(cart.map(({ book_id, quantity }) => ({ book_id, quantity })));
      cartClear();
      onClose();
      toast(`Order #${order.id} placed`, 'success');
      if (location.hash === '#/orders') onOrderPlaced();
      else navigate('#/orders');
    } catch (error) {
      toast(error.message, 'error');
    } finally {
      setPlacing(false);
    }
  }

  return (
    <div className="cart-layer" hidden={!open}>
      <div className="cart-backdrop" onClick={onClose} />
      <aside className="cart-drawer" role="dialog" aria-modal="true" aria-label="Shopping cart">
        <header className="cart-head">
          <div>
            <p className="eyebrow">Your bag</p>
            <h2>Cart</h2>
          </div>
          <button className="icon-btn" type="button" aria-label="Close cart" onClick={onClose} ref={closeRef}>
            {Icons.close}
          </button>
        </header>
        <CartBody onClose={onClose} />
        <CartFoot user={user} placing={placing} onCheckout={checkout} />
      </aside>
    </div>
  );
}

function CartBody({ onClose }) {
  const { cart } = useStore();
  if (!cart.length) {
    return (
      <div className="cart-body">
        <div className="cart-empty">
          {Icons.cart}
          <h3>Your cart is empty</h3>
          <p>Add a few titles and they will show up here.</p>
          <a className="btn" href="#/catalog" onClick={onClose}>
            Browse books
          </a>
        </div>
      </div>
    );
  }
  return (
    <div className="cart-body">
      <ul className="cart-items">
        {cart.map((item) => (
          <li className="cart-item" key={item.book_id}>
            <img className="cart-thumb" src={item.cover || ''} alt="" loading="lazy" />
            <div className="cart-item-main">
              <a className="cart-title" href={`#/book/${item.book_id}`} onClick={onClose}>
                {item.title}
              </a>
              <span className="muted cart-author">{item.author}</span>
              <div className="cart-item-row">
                <div className="cart-qty" role="group" aria-label={`Quantity for ${item.title}`}>
                  <button
                    type="button"
                    aria-label="Decrease quantity"
                    onClick={() => cartSetQuantity(item.book_id, item.quantity - 1)}
                  >
                    {Icons.minus}
                  </button>
                  <span>{item.quantity}</span>
                  <button
                    type="button"
                    aria-label="Increase quantity"
                    onClick={() => cartSetQuantity(item.book_id, item.quantity + 1)}
                  >
                    {Icons.plus}
                  </button>
                </div>
                <strong>{money(item.price * item.quantity)}</strong>
              </div>
            </div>
            <button
              className="icon-btn danger"
              type="button"
              aria-label={`Remove ${item.title}`}
              onClick={() => cartRemove(item.book_id)}
            >
              {Icons.trash}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function CartFoot({ user, placing, onCheckout }) {
  const { cart } = useStore();
  const total = cartTotal(cart);
  return (
    <footer className="cart-foot">
      <div className="cart-subtotal">
        <span>Subtotal</span>
        <strong>{money(total)}</strong>
      </div>
      <p className="cart-note">
        {total >= 35
          ? 'Free shipping is included in this order.'
          : `Add ${money(35 - total)} more for free shipping.`}
      </p>
      <button className="btn full" type="button" disabled={placing} onClick={onCheckout}>
        {placing ? 'Placing order…' : user ? 'Checkout' : 'Sign in & checkout'}
      </button>
      <p className="cart-fine">Demo store — no payment is taken.</p>
    </footer>
  );
}

export function StoreShell({ user, locationState, refresh, onOrderPlaced, children }) {
  const [cartOpen, setCartOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [navOpen, setNavOpen] = useState(false);
  const accountRef = useRef(null);
  const { cart } = useStore();
  const count = cartCount(cart);

  useEffect(() => {
    const onOpenCart = () => {
      setMenuOpen(false);
      setCartOpen(true);
    };
    document.addEventListener('open-cart', onOpenCart);
    return () => document.removeEventListener('open-cart', onOpenCart);
  }, []);

  useEffect(() => {
    document.body.classList.toggle('cart-open', cartOpen);
    return () => document.body.classList.remove('cart-open');
  }, [cartOpen]);

  useEffect(() => {
    if (!menuOpen) return;
    const onClick = (event) => {
      if (!accountRef.current?.contains(event.target)) setMenuOpen(false);
    };
    const onKey = (event) => {
      if (event.key === 'Escape') setMenuOpen(false);
    };
    document.addEventListener('click', onClick);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('click', onClick);
      document.removeEventListener('keydown', onKey);
    };
  }, [menuOpen]);

  useEffect(() => {
    // close transient UI on every navigation, like the original renderRoute
    setCartOpen(false);
    setMenuOpen(false);
    setNavOpen(false);
  }, [locationState.pathname, locationState.search]);

  function onSearchSubmit(event) {
    event.preventDefault();
    const query = event.currentTarget.q.value.trim();
    const next = query ? `#/catalog?q=${encodeURIComponent(query)}` : '#/catalog';
    event.currentTarget.reset();
    if (location.hash === next) refresh();
    else navigate(next);
  }

  function onLogout() {
    if (location.hash.startsWith('#/admin')) navigate('#/');
    logout();
    toast('Signed out', 'info');
  }

  const adminLink = isAdmin(user) && <a href="#/admin" data-nav="admin">Admin</a>;

  return (
    <div className={`store-shell${navOpen ? ' nav-open' : ''}`}>
      <div className="announce">
        <span>Free shipping on orders over $35</span>
        <span className="announce-dot" aria-hidden="true">
          ·
        </span>
        <span>30-day returns</span>
      </div>
      <header className="site-header">
        <div className="header-inner">
          <Wordmark />
          <nav className="main-nav" aria-label="Primary">
            <NavLink id="home" href="#/" activeKey={navKey(locationState)}>
              Home
            </NavLink>
            <NavLink id="catalog" href="#/catalog" activeKey={navKey(locationState)}>
              All books
            </NavLink>
            <NavLink id="programming" href="#/catalog?category=software-engineering" activeKey={navKey(locationState)}>
              Programming
            </NavLink>
            <NavLink id="ai-cat" href="#/catalog?category=ai-foundations" activeKey={navKey(locationState)}>
              AI
            </NavLink>
            <NavLink id="ai" href="#/ai" activeKey={navKey(locationState)}>
              AI assistant
            </NavLink>
            <NavLink id="orders" href="#/orders" activeKey={navKey(locationState)}>
              Orders
            </NavLink>
            {adminLink}
          </nav>
          <div className="header-actions">
            <form className="header-search" role="search" onSubmit={onSearchSubmit}>
              {Icons.search}
              <input
                name="q"
                type="search"
                placeholder="Search books"
                aria-label="Search books"
                autoComplete="off"
              />
            </form>
            <a className="icon-btn orders-link" href="#/orders" aria-label="Your orders">
              {Icons.receipt}
            </a>
            <div ref={accountRef}>
              <AccountMenu
                user={user}
                open={menuOpen}
                onToggle={() => setMenuOpen((v) => !v)}
                onClose={() => setMenuOpen(false)}
                onLogout={onLogout}
              />
            </div>
            <button
              className="cart-btn"
              type="button"
              aria-label="Open cart"
              onClick={() => {
                setMenuOpen(false);
                setCartOpen(true);
              }}
            >
              {Icons.cart}
              <span className="badge" hidden={count === 0}>
                {count}
              </span>
            </button>
            <button
              className="icon-btn nav-toggle"
              type="button"
              aria-label="Toggle navigation"
              aria-expanded={navOpen}
              onClick={() => setNavOpen((v) => !v)}
            >
              {Icons.menu}
            </button>
          </div>
        </div>
      </header>
      <main id="main" className="site-main">
        {children}
      </main>
      <footer className="site-footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <Wordmark light />
            <p>
              A full catalog of real technical titles with a demo checkout built on FastAPI,
              PostgreSQL and React.
            </p>
          </div>
          <div className="footer-col">
            <h4>Shop</h4>
            <a href="#/catalog">All books</a>
            <a href="#/catalog?category=software-engineering">Programming</a>
            <a href="#/catalog?category=ai-foundations">AI</a>
            <a href="#/catalog?category=systems-programming">Systems</a>
          </div>
          <div className="footer-col">
            <h4>Account</h4>
            <a href="#/orders">Your orders</a>
            <a href="#/login">Sign in</a>
            <a href="#/register">Create account</a>
          </div>
          <div className="footer-col">
            <h4>Under the hood</h4>
            <span>FastAPI · SQLAlchemy</span>
            <span>PostgreSQL · JWT auth</span>
            <span>React · Vite</span>
          </div>
        </div>
        <p className="footer-fine">
          © 2026 Bookstore Pro — an FPT e-project demo. Prices, inventory and orders are fictional.
        </p>
      </footer>
      <CartDrawer
        user={user}
        open={cartOpen}
        onClose={() => setCartOpen(false)}
        onOrderPlaced={onOrderPlaced}
      />
    </div>
  );
}

function NavLink({ id, href, activeKey, children }) {
  return (
    <a href={href} data-nav={id} className={activeKey === id ? 'active' : undefined}>
      {children}
    </a>
  );
}

function navKey({ pathname, search }) {
  const category = new URLSearchParams(search.slice(1)).get('category');
  if (pathname === '/') return 'home';
  if (pathname === '/catalog') {
    if (category === 'software-engineering') return 'programming';
    if (category === 'ai-foundations') return 'ai-cat';
    return 'catalog';
  }
  if (pathname === '/orders') return 'orders';
  if (pathname === '/ai') return 'ai';
  if (pathname.startsWith('/admin')) return 'admin';
  return null;
}

export function AdminShell({ user, locationState, onLogout, children }) {
  const adminKey =
    locationState.pathname === '/admin'
      ? 'overview'
      : locationState.pathname.startsWith('/admin/')
        ? locationState.pathname.split('/')[2]
        : null;
  const [navOpen, setNavOpen] = useState(false);

  useEffect(() => {
    setNavOpen(false);
  }, [locationState.pathname]);

  const link = (id, href, icon, label) => (
    <a
      href={href}
      data-admin-nav={id}
      className={adminKey === id ? 'active' : undefined}
      onClick={() => setNavOpen(false)}
    >
      {icon}
      <span>{label}</span>
    </a>
  );

  return (
    <div className={`admin-shell${navOpen ? ' admin-nav-open' : ''}`}>
      <aside className="admin-sidebar">
        <div className="sidebar-brand">
          <Wordmark light />
          <span className="admin-chip">Admin</span>
        </div>
        <nav className="admin-nav" aria-label="Administration">
          {link('overview', '#/admin', Icons.chart, 'Overview')}
          {link('books', '#/admin/books', Icons.book, 'Books')}
          {link('orders', '#/admin/orders', Icons.receipt, 'Orders')}
          {link('customers', '#/admin/customers', Icons.users, 'Customers')}
          {link('analytics', '#/admin/analytics', Icons.chart, 'Analytics')}
          {link('reviews', '#/admin/reviews', Icons.spark, 'Reviews')}
          {link('ai-keys', '#/admin/ai-keys', Icons.spark, 'AI keys')}
        </nav>
        <div className="sidebar-foot">
          <a className="sidebar-link" href="#/">
            {Icons.arrowLeft}
            <span>Storefront</span>
          </a>
          <button className="sidebar-link" type="button" onClick={onLogout}>
            {Icons.logout}
            <span>Sign out</span>
          </button>
        </div>
      </aside>
      <div className="admin-frame">
        <header className="admin-topbar">
          <button
            className="icon-btn admin-nav-toggle"
            type="button"
            aria-label="Toggle sidebar"
            onClick={() => setNavOpen((v) => !v)}
          >
            {Icons.menu}
          </button>
          <div className="admin-title">
            <p className="eyebrow">Administration</p>
            <h1>
              {adminKey === 'ai-keys'
                ? 'AI keys'
                : adminKey
                  ? adminKey[0].toUpperCase() + adminKey.slice(1)
                  : 'Overview'}
            </h1>
          </div>
          <div className="admin-user">
            <span className="avatar">{initials(user?.name)}</span>
            <div>
              <strong>{user?.name || 'Admin'}</strong>
              <span className="muted">{user?.email || ''}</span>
            </div>
          </div>
        </header>
        <main id="main" className="admin-main">
          {children}
        </main>
      </div>
    </div>
  );
}

export function AuthShell({ children }) {
  return (
    <div className="auth-shell">
      <header className="auth-top">
        <Wordmark />
        <a className="link-arrow" href="#/">
          Back to the store <span aria-hidden="true">→</span>
        </a>
      </header>
      <main id="main" className="auth-main">
        {children}
      </main>
    </div>
  );
}

