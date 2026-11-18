import { useSyncExternalStore } from 'react';
import { api } from './api.js';

const TOKEN_KEY = 'bookstore.token';
const CART_KEY = 'bookstore.cart';

function readCart() {
  try {
    const parsed = JSON.parse(localStorage.getItem(CART_KEY) || '[]');
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

let state = {
  token: localStorage.getItem(TOKEN_KEY),
  user: null,
  cart: readCart(),
};

const listeners = new Set();

export function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function getState() {
  return state;
}

function setState(patch) {
  state = { ...state, ...patch };
  listeners.forEach((listener) => listener(state));
}

function persistCart(cart) {
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
}

export function useStore() {
  return useSyncExternalStore(subscribe, getState);
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
  setState({ token });
}

export async function loadUser() {
  if (!state.token) {
    setState({ user: null });
    return null;
  }
  try {
    setState({ user: await api.me() });
  } catch {
    localStorage.removeItem(TOKEN_KEY);
    setState({ token: null, user: null });
  }
  return state.user;
}

export function logout() {
  localStorage.removeItem(TOKEN_KEY);
  setState({ token: null, user: null });
}

export function isAdmin(user) {
  return user?.role === 'admin';
}

export function cartCount(cart) {
  return cart.reduce((sum, item) => sum + item.quantity, 0);
}

export function cartTotal(cart) {
  return cart.reduce((sum, item) => sum + item.quantity * item.price, 0);
}

export function cartAdd(book, quantity = 1) {
  const stock = Number(book.stock) || 0;
  if (stock <= 0) return { added: false, limited: false };
  const existing = state.cart.find((item) => item.book_id === book.id);
  if (existing) {
    const next = Math.min(existing.quantity + quantity, stock);
    const limited = next < existing.quantity + quantity;
    const cart = state.cart.map((item) =>
      item.book_id === book.id ? { ...item, quantity: next, stock } : item,
    );
    persistCart(cart);
    setState({ cart });
    return { added: true, limited };
  }
  const next = Math.min(quantity, stock);
  const cart = [
    ...state.cart,
    {
      book_id: book.id,
      title: book.title,
      author: book.author,
      price: Number(book.price),
      cover: book.cover,
      stock,
      quantity: next,
    },
  ];
  persistCart(cart);
  setState({ cart });
  return { added: true, limited: next < quantity };
}

export function cartSetQuantity(bookId, quantity) {
  const item = state.cart.find((entry) => entry.book_id === bookId);
  if (!item) return;
  let cart;
  if (quantity <= 0) {
    cart = state.cart.filter((entry) => entry.book_id !== bookId);
  } else {
    cart = state.cart.map((entry) =>
      entry.book_id === bookId
        ? { ...entry, quantity: Math.min(quantity, entry.stock || quantity) }
        : entry,
    );
  }
  persistCart(cart);
  setState({ cart });
}

export function cartRemove(bookId) {
  const cart = state.cart.filter((item) => item.book_id !== bookId);
  persistCart(cart);
  setState({ cart });
}

export function cartClear() {
  persistCart([]);
  setState({ cart: [] });
}
