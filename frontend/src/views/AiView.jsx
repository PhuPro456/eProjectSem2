import { useEffect, useRef, useState } from 'react';
import { api } from '../api.js';
import { BookCard, ErrorView, Icons, money } from '../ui.jsx';

const GREETING =
  "Hello! I'm the Bookstore Pro assistant. Tell me a topic, a language, your level, or a budget and I'll pull a few titles from the shelf.";
const DEFAULT_CHIPS = [
  'Python for beginners',
  'Deep learning books',
  'LLMs and NLP under $40',
  'Surprise me',
];
const PROVIDER_NAMES = { gemini: 'Gemini' };

let messageSeq = 0;

export function AiView() {
  return (
    <div className="page ai-page">
      <header className="ai-head">
        <div>
          <p className="eyebrow">{Icons.spark} AI reading room</p>
          <h1>
            Your next read,
            <br />
            <em>in conversation.</em>
          </h1>
          <p className="muted">
            A bookseller assistant with the catalog, stock levels and reader history at hand. An
            administrator-managed provider key powers conversational replies when one is configured.
          </p>
        </div>
        <div className="ai-badges">
          <span className="ai-badge">Catalogue-aware</span>
          <span className="ai-badge">Sentiment-labelled reviews</span>
          <span className="ai-badge">Admin-managed AI key</span>
        </div>
      </header>

      <div className="ai-layout">
        <ChatCard />

        <aside className="ai-side">
          <section className="panel ai-about">
            <header className="panel-head">
              <h2>How it works</h2>
            </header>
            <ul className="ai-steps">
              <li>
                <span>01</span> Reads the live catalog, stock and your order history.
              </li>
              <li>
                <span>02</span> Matches topics, budgets and reader favourites.
              </li>
              <li>
                <span>03</span> Suggests three titles you can add to your cart.
              </li>
            </ul>
          </section>
        </aside>
      </div>

      <RecsSection />
    </div>
  );
}

function ChatCard() {
  const [messages, setMessages] = useState([{ id: ++messageSeq, role: 'assistant', text: GREETING }]);
  const [chips, setChips] = useState(DEFAULT_CHIPS);
  const [draft, setDraft] = useState('');
  const [status, setStatus] = useState({ provider: null });
  const [busy, setBusy] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);
  const providerName = status.provider ? PROVIDER_NAMES[status.provider] : null;

  useEffect(() => {
    api.ai
      .status()
      .then(setStatus)
      .catch(() => setStatus({ provider: null }));
  }, []);

  useEffect(() => {
    const node = scrollRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [messages]);

  async function send(text) {
    const message = text.trim();
    if (!message || busy) return;
    const history = messages
      .filter((item) => item.id !== messages[0].id && !item.typing && item.text)
      .slice(-10)
      .map((item) => ({ role: item.role, content: item.text.slice(0, 2000) }));
    const typingId = ++messageSeq;
    setMessages((current) => [
      ...current,
      { id: ++messageSeq, role: 'user', text: message },
      { id: typingId, role: 'assistant', text: 'Checking the shelves…', typing: true },
    ]);
    setDraft('');
    setBusy(true);

    try {
      const data = await api.ai.chat(message, { history, sessionId });
      if (data.session_id) setSessionId(data.session_id);
      setMessages((current) =>
        current.map((item) =>
          item.id === typingId
            ? {
                ...item,
                typing: false,
                text: data.reply,
                books: data.books,
                source: data.source,
                notice: data.notice,
              }
            : item,
        ),
      );
      setChips(data.suggestions.length ? data.suggestions : DEFAULT_CHIPS);
    } catch (error) {
      setMessages((current) =>
        current.map((item) =>
          item.id === typingId ? { ...item, typing: false, text: error.message } : item,
        ),
      );
    } finally {
      setBusy(false);
    }
  }

  function pick(chip) {
    send(chip);
    inputRef.current?.focus();
  }

  return (
    <section className="chat-card">
      <header className="chat-head">
        <div className="chat-avatar">{Icons.spark}</div>
        <div>
          <strong>Bookstore assistant</strong>
          <span className="muted">{providerName ? `Powered by ${providerName}` : 'Local recommender'}</span>
        </div>
      </header>
      <div className="chat-messages" ref={scrollRef}>
        {messages.map((message) => (
          <div className={`chat-msg ${message.role}${message.typing ? ' typing' : ''}`} key={message.id}>
            <div className="chat-bubble">
              <p>{message.text}</p>
              {message.notice && <p className="chat-notice">{message.notice}</p>}
              {message.books && message.books.length > 0 && (
                <div className="chat-books">
                  {message.books.map((book) => (
                    <a className="chat-book" href={`#/book/${book.id}`} key={book.id}>
                      <img src={book.cover} alt="" loading="lazy" />
                      <span>
                        <strong>{book.title}</strong>
                        <small>
                          {book.author} · {money(book.price)}
                        </small>
                      </span>
                    </a>
                  ))}
                </div>
              )}
              {message.source && message.source !== 'local' && (
                <small className="chat-source">via {PROVIDER_NAMES[message.source] || message.source}</small>
              )}
            </div>
          </div>
        ))}
      </div>
      <div className="chat-chips">
        {chips.map((chip) => (
          <button className="chip" type="button" onClick={() => pick(chip)} key={chip}>
            {chip}
          </button>
        ))}
      </div>
      <form
        className="ai-composer"
        onSubmit={(event) => {
          event.preventDefault();
          send(draft);
        }}
      >
        <label className="sr-only" htmlFor="aiInput">
          Ask for a recommendation
        </label>
        <input
          id="aiInput"
          name="message"
          maxLength="500"
          autoComplete="off"
          placeholder="e.g. beginner Python under $30"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          ref={inputRef}
        />
        <button className="btn" type="submit" disabled={busy}>
          Send
        </button>
      </form>
      <p className="ai-note">
        {providerName
          ? `Your message, recent chat and matching catalog entries are sent to ${providerName} using the administrator-managed key.`
          : 'Local recommender — no messages leave this server.'}
      </p>
    </section>
  );
}

function RecsSection() {
  const [status, setStatus] = useState({ state: 'loading' });
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setStatus({ state: 'loading' });
    api
      .ai.recommendations(4)
      .then((data) => {
        if (!cancelled) setStatus({ state: 'ready', data });
      })
      .catch((error) => {
        if (!cancelled) setStatus({ state: 'error', message: error.message });
      });
    return () => {
      cancelled = true;
    };
  }, [version]);

  return (
    <section className="ai-recs" id="aiRecs">
      {status.state === 'error' ? (
        <ErrorView message={status.message} onRetry={() => setVersion((value) => value + 1)} />
      ) : (
        <>
          <div className="section-head">
            <div>
              <p className="eyebrow">Picked for you</p>
              <h2>{status.state === 'ready' ? status.data.reason : 'Fresh from the shelves'}</h2>
            </div>
            {status.state === 'ready' && (
              <a className="link-arrow" href="#/catalog">
                Browse everything <span aria-hidden="true">→</span>
              </a>
            )}
          </div>
          {status.state === 'ready' ? (
            <div className="book-grid">
              {status.data.items.map((book) => (
                <BookCard book={book} key={book.id} />
              ))}
            </div>
          ) : (
            <div className="book-grid">
              {Array.from({ length: 4 }, (_, index) => (
                <div className="book-card skeleton-card" key={index}>
                  <div className="skeleton skeleton-cover" />
                  <div className="skeleton skeleton-line" />
                  <div className="skeleton skeleton-line short" />
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}
