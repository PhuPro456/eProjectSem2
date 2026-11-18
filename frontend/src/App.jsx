import { useEffect, useRef, useState } from 'react';
import { isAdmin, loadUser, logout, useStore } from './store.js';
import { navigate, useHashLocation } from './router.js';
import { AdminShell, AuthShell, StoreShell } from './shell.jsx';
import { toast, ToastHost } from './ui.jsx';
import { AiView } from './views/AiView.jsx';
import { AdminBooksView } from './views/admin/BooksView.jsx';
import { AdminCustomersView } from './views/admin/CustomersView.jsx';
import { AdminOrdersView } from './views/admin/OrdersView.jsx';
import { AdminAiKeysView } from './views/admin/AiKeysView.jsx';
import { AdminOverviewView } from './views/admin/OverviewView.jsx';
import { AnalyticsView } from './views/admin/AnalyticsView.jsx';
import { ReviewsView } from './views/admin/ReviewsView.jsx';
import { BookView } from './views/BookView.jsx';
import { CatalogView } from './views/CatalogView.jsx';
import { HomeView } from './views/HomeView.jsx';
import { LoginView, RegisterView } from './views/AuthView.jsx';
import { OrdersView } from './views/OrdersView.jsx';

const ROUTES = [
  { pattern: /^\/?$/, layout: 'store', title: 'Home', Comp: HomeView },
  { pattern: /^\/catalog$/, layout: 'store', title: 'Books', Comp: CatalogView },
  {
    pattern: /^\/book\/(\d+)$/,
    layout: 'store',
    title: 'Book',
    Comp: BookView,
    props: (match) => ({ bookId: match[1] }),
  },
  { pattern: /^\/ai$/, layout: 'store', title: 'AI assistant', Comp: AiView },
  { pattern: /^\/login$/, layout: 'auth', title: 'Sign in', Comp: LoginView },
  { pattern: /^\/register$/, layout: 'auth', title: 'Create account', Comp: RegisterView },
  { pattern: /^\/orders$/, layout: 'store', title: 'Your orders', requiresAuth: true, Comp: OrdersView },
  { pattern: /^\/admin$/, layout: 'admin', title: 'Overview', requiresAdmin: true, Comp: AdminOverviewView },
  { pattern: /^\/admin\/books$/, layout: 'admin', title: 'Books', requiresAdmin: true, Comp: AdminBooksView },
  { pattern: /^\/admin\/orders$/, layout: 'admin', title: 'Orders', requiresAdmin: true, Comp: AdminOrdersView },
  {
    pattern: /^\/admin\/customers$/,
    layout: 'admin',
    title: 'Customers',
    requiresAdmin: true,
    Comp: AdminCustomersView,
  },
  {
    pattern: /^\/admin\/analytics$/,
    layout: 'admin',
    title: 'Analytics',
    requiresAdmin: true,
    Comp: AnalyticsView,
  },
  { pattern: /^\/admin\/reviews$/, layout: 'admin', title: 'Reviews', requiresAdmin: true, Comp: ReviewsView },
  {
    pattern: /^\/admin\/ai-keys$/,
    layout: 'admin',
    title: 'AI keys',
    requiresAdmin: true,
    Comp: AdminAiKeysView,
  },
];

function NotFoundView() {
  return (
    <div className="page">
      <div className="state-card">
        <p className="eyebrow">404</p>
        <h3>Page not found</h3>
        <p>The page you were looking for does not exist or has moved.</p>
        <a className="btn" href="#/">
          Back to the store
        </a>
      </div>
    </div>
  );
}

export default function App() {
  const { user } = useStore();
  const locationState = useHashLocation();
  const [booted, setBooted] = useState(false);
  const [renderKey, setRenderKey] = useState(0);
  const firstAuthRender = useRef(true);

  useEffect(() => {
    loadUser().then(() => setBooted(true));
  }, []);

  useEffect(() => {
    const onError = (event) => {
      const image = event.target;
      if (!(image instanceof HTMLImageElement) || image.dataset.failed) return;
      image.dataset.failed = 'true';
      image.classList.add('is-broken');
      image.closest('.book-cover, .detail-cover, .cat-covers')?.classList.add('cover-missing');
    };
    document.addEventListener('error', onError, true);
    return () => document.removeEventListener('error', onError, true);
  }, []);

  const { pathname, search } = locationState;
  const entry = ROUTES.find((candidate) => candidate.pattern.test(pathname));
  const match = entry ? pathname.match(entry.pattern) : null;
  const layout = entry?.layout || 'store';
  const blocked =
    (entry?.requiresAuth && !user) || (entry?.requiresAdmin && !isAdmin(user));

  useEffect(() => {
    if (!booted || !blocked) return;
    if (!user) {
      sessionStorage.setItem('bookstore.next', location.hash || '#/');
      navigate('#/login');
    } else {
      toast('Administrator access is required', 'error');
      navigate('#/');
    }
  }, [booted, blocked, user]);

  useEffect(() => {
    if (!booted) return;
    if (firstAuthRender.current) {
      firstAuthRender.current = false;
      return;
    }
    if (user && (pathname === '/login' || pathname === '/register')) return;
    setRenderKey((key) => key + 1);
  }, [user, booted]);

  useEffect(() => {
    document.title = entry ? `${entry.title} · Bookstore Pro` : 'Page not found · Bookstore Pro';
  }, [entry]);

  useEffect(() => {
    document.body.classList.toggle('admin-body', booted && layout === 'admin');
  }, [booted, layout]);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname, search, renderKey]);

  if (!booted) return null;

  const viewKey = `${pathname}${search}#${renderKey}`;
  let body = null;
  if (!blocked) {
    if (entry) {
      const Comp = entry.Comp;
      body = <Comp key={viewKey} {...(entry.props ? entry.props(match) : {})} />;
    } else {
      body = <NotFoundView />;
    }
  }

  const refresh = () => setRenderKey((key) => key + 1);

  const onLogout = () => {
    if (location.hash.startsWith('#/admin')) navigate('#/');
    logout();
    toast('Signed out', 'info');
  };

  let shell;
  if (layout === 'admin') {
    shell = (
      <AdminShell user={user} locationState={locationState} onLogout={onLogout}>
        {body}
      </AdminShell>
    );
  } else if (layout === 'auth') {
    shell = <AuthShell>{body}</AuthShell>;
  } else {
    shell = (
      <StoreShell
        user={user}
        locationState={locationState}
        refresh={refresh}
        onOrderPlaced={refresh}
      >
        {body}
      </StoreShell>
    );
  }

  return (
    <>
      {shell}
      <ToastHost />
    </>
  );
}
