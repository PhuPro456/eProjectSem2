# Paper & Pine — Flask Bookstore

A complete responsive bookstore demo with **100 book records**, **100 locally stored SVG covers**, title/author/description search, category filtering, stock and price display, and a JSON API.

## Run on Windows

```powershell
cd FrontEnd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Run on macOS / Linux

```bash
cd FrontEnd
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Files
- `app.py` — Flask backend and `/api/books` endpoint.
- `database/books.json` — 100 real published titles and authors with **demo** prices, stock, and descriptions.
- `static/covers/book-001.svg` through `book-100.svg` — locally generated decorative cover illustrations, **not original published cover photographs**.
- `templates/index.html` — storefront HTML.
- `static/css/styles.css` — responsive styling.
- `static/js/app.js` — search, category filtering, and book display.

## API
`GET /api/books` — all books.
`GET /api/books?q=python` — search title, author, and description.
`GET /api/books?category=Fiction` — category filter.

This is a demo catalog. Prices and stock are fictional. The bookstore does not process purchases or payments.
