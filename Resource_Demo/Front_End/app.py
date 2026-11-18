from flask import Flask, render_template, jsonify, request
from pathlib import Path
import json

app = Flask(__name__)
DATA_FILE = Path(__file__).resolve().parent / "database" / "books.json"


def load_books():
    with DATA_FILE.open(encoding="utf-8") as f:
        return json.load(f)


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/books")
def books_api():
    books = load_books()
    query = request.args.get("q", "").strip().casefold()
    category = request.args.get("category", "").strip().casefold()
    results = [book for book in books if
               (not query or any(query in str(book.get(k, "")).casefold()
                                 for k in ("title", "author", "description")))
               and (not category or book["category"].casefold() == category)]
    return jsonify({"count": len(results), "books": results})


if __name__ == "__main__":
    app.run(debug=True)
