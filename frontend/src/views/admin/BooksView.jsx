import { useEffect, useRef, useState } from 'react';
import { api } from '../../api.js';
import {
  EmptyView,
  ErrorView,
  Icons,
  Modal,
  categoryName,
  debounce,
  money,
  toast,
} from '../../ui.jsx';
import { StockPill, Thumb, fetchAllBooks } from './common.jsx';

const PAGE_SIZE = 10;

export function AdminBooksView() {
  const [books, setBooks] = useState(null);
  const [categories, setCategories] = useState([]);
  const [error, setError] = useState(null);
  const [q, setQ] = useState('');
  const [category, setCategory] = useState('');
  const [page, setPage] = useState(1);
  const [modal, setModal] = useState(null); // {book: X | null} when open

  const load = () => {
    setError(null);
    setBooks(null);
    Promise.all([fetchAllBooks(), api.categories()])
      .then(([allBooks, allCategories]) => {
        setBooks(allBooks);
        setCategories(allCategories);
      })
      .catch((loadError) => setError(loadError.message));
  };

  useEffect(load, []);

  const debouncedSearch = useRef(debounce((value) => {
    setQ(value.trim());
    setPage(1);
  })).current;

  const filtered = (books || []).filter((book) => {
    const query = q.toLowerCase();
    return (
      (!category || book.category === category) &&
      (!query ||
        book.title.toLowerCase().includes(query) ||
        book.author.toLowerCase().includes(query) ||
        String(book.id) === query)
    );
  });

  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, pages);
  const visible = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  async function remove(book) {
    if (!window.confirm(`Delete “${book.title}” from the catalog?`)) return;
    try {
      await api.admin.deleteBook(book.id);
      toast('Book deleted', 'success');
      load();
    } catch (deleteError) {
      toast(deleteError.message, 'error');
    }
  }

  if (error) {
    return (
      <div className="admin-page">
        <ErrorView message={error} onRetry={load} />
      </div>
    );
  }

  return (
    <div className="admin-page">
      <div className="admin-toolbar">
        <label className="field search-field">
          <span className="sr-only">Search books</span>
          <input
            type="search"
            placeholder="Search by title or author…"
            onChange={(event) => debouncedSearch(event.target.value)}
          />
        </label>
        <label className="field">
          <span className="sr-only">Category</span>
          <select
            value={category}
            onChange={(event) => {
              setCategory(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All categories</option>
            {categories.map((entry) => (
              <option value={entry.code} key={entry.code}>
                {entry.name}
              </option>
            ))}
          </select>
        </label>
        <button
          className="btn"
          type="button"
          disabled={!categories.length}
          onClick={() => setModal({ book: null })}
        >
          {Icons.plus}
          <span>Add book</span>
        </button>
      </div>
      <div className="panel">
        {!books ? (
          <>
            <div className="skeleton skeleton-line" />
            <div className="skeleton skeleton-line" />
          </>
        ) : visible.length ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Author</th>
                  <th>Category</th>
                  <th>Stock</th>
                  <th>Price</th>
                  <th>Status</th>
                  <th className="actions-col">Actions</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((book) => (
                  <tr key={book.id}>
                    <td>
                      <div className="cell-product">
                        <Thumb book={book} />
                        <div>
                          <strong>{book.title}</strong>
                          <span className="muted">#{book.id}</span>
                        </div>
                      </div>
                    </td>
                    <td>{book.author}</td>
                    <td>{categoryName(book.category)}</td>
                    <td>{book.stock}</td>
                    <td>{money(book.price)}</td>
                    <td>
                      <StockPill stock={book.stock} />
                    </td>
                    <td className="actions-col">
                      <button
                        className="icon-btn"
                        type="button"
                        aria-label={`Edit ${book.title}`}
                        onClick={() => setModal({ book })}
                      >
                        {Icons.edit}
                      </button>
                      <button
                        className="icon-btn danger"
                        type="button"
                        aria-label={`Delete ${book.title}`}
                        onClick={() => remove(book)}
                      >
                        {Icons.trash}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyView title="No books match" message="Adjust the search or category filter." />
        )}
        {books && (
          <nav className="pagination">
            {pages > 1 ? (
              <>
                <span className="muted">
                  Page {currentPage} of {pages} · {filtered.length} books
                </span>
                <button
                  className="page-btn"
                  type="button"
                  disabled={currentPage === 1}
                  onClick={() => setPage(currentPage - 1)}
                >
                  Previous
                </button>
                <button
                  className="page-btn"
                  type="button"
                  disabled={currentPage === pages}
                  onClick={() => setPage(currentPage + 1)}
                >
                  Next
                </button>
              </>
            ) : (
              <span className="muted">
                {filtered.length} book{filtered.length === 1 ? '' : 's'}
              </span>
            )}
          </nav>
        )}
      </div>
      {modal && (
        <BookModal
          book={modal.book}
          categories={categories}
          onClose={() => setModal(null)}
          onSaved={load}
        />
      )}
    </div>
  );
}

function BookModal({ book, categories, onClose, onSaved }) {
  const isEdit = Boolean(book);
  const [form, setForm] = useState({
    title: book?.title || '',
    author: book?.author || '',
    category: book?.category || categories[0]?.code || '',
    price: book ? Number(book.price).toFixed(2) : '19.99',
    stock: book ? String(book.stock) : '12',
    cover: book?.cover || '/static/covers/book-001.svg',
    description: book?.description || '',
  });
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const set = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }));

  async function submit(event) {
    event.preventDefault();
    setError(null);
    setSaving(true);
    const payload = {
      title: form.title.trim(),
      author: form.author.trim(),
      category: form.category,
      description: form.description.trim(),
      price: Number(form.price),
      stock: Number(form.stock),
      cover: form.cover.trim(),
    };
    try {
      if (isEdit) await api.admin.updateBook(book.id, payload);
      else await api.admin.createBook(payload);
      onClose();
      toast(isEdit ? 'Book updated' : 'Book created', 'success');
      onSaved();
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title={isEdit ? `Edit book #${book.id}` : 'Add a book'} onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <div className="form-grid">
          <label className="span-2">
            Title
            <input name="title" required maxLength="255" value={form.title} onChange={set('title')} />
          </label>
          <label>
            Author
            <input name="author" required maxLength="150" value={form.author} onChange={set('author')} />
          </label>
          <label>
            Category
            <select name="category" required value={form.category} onChange={set('category')}>
              {categories.map((entry) => (
                <option value={entry.code} key={entry.code}>
                  {entry.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Price (USD)
            <input
              name="price"
              type="number"
              min="0.01"
              step="0.01"
              required
              value={form.price}
              onChange={set('price')}
            />
          </label>
          <label>
            Stock
            <input name="stock" type="number" min="0" step="1" required value={form.stock} onChange={set('stock')} />
          </label>
          <label className="span-2">
            Cover path
            <input
              name="cover"
              maxLength="255"
              placeholder="/static/covers/book-001.svg"
              value={form.cover}
              onChange={set('cover')}
            />
          </label>
          <label className="span-2">
            Description
            <textarea name="description" rows="4" maxLength="2000" value={form.description} onChange={set('description')} />
          </label>
          {error && <p className="form-error span-2">{error}</p>}
          <div className="modal-actions span-2">
            <button className="btn ghost" type="button" onClick={onClose}>
              Cancel
            </button>
            <button className="btn" type="submit" disabled={saving}>
              {isEdit ? 'Save changes' : 'Create book'}
            </button>
          </div>
        </div>
      </form>
    </Modal>
  );
}
