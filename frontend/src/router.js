import { useEffect, useState } from 'react';

export function parseHash() {
  const raw = (location.hash || '').replace(/^#/, '');
  const [rawPath, rawQuery = ''] = raw.split('?');
  let pathname = rawPath || '/';
  if (!pathname.startsWith('/')) pathname = `/${pathname}`;
  if (pathname.length > 1) pathname = pathname.replace(/\/+$/, '');
  return { pathname, search: rawQuery ? `?${rawQuery}` : '' };
}

export function useHashLocation() {
  const [locationState, setLocationState] = useState(parseHash);
  useEffect(() => {
    const onChange = () => setLocationState(parseHash());
    window.addEventListener('hashchange', onChange);
    return () => window.removeEventListener('hashchange', onChange);
  }, []);
  return locationState;
}

export function navigate(to) {
  location.hash = to.startsWith('#') ? to : `#${to}`;
}

export function rewriteUrl(to) {
  history.replaceState(null, '', to.startsWith('#') ? to : `#${to}`);
}
