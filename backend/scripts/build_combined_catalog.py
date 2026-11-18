"""Merge the Cover_Remake catalogs into one sequential catalog.

Ids are assigned in SOURCES order: Programming 1-100, AI 101-200, Computer
Science 201-300, then Humor, Light Reads, Magazines, Manga, Mystical and
Romance. Each book's cover path is rewritten to the new sequential id and the
matching source JPEG is copied into the frontend static folder, so a book's
cover always lines up with the title the seed will store for it.

Writes backend/app/db/books_catalog.json and frontend/static/covers/*.jpg,
and removes the placeholder SVGs that no longer map to any book.
"""

from __future__ import annotations

import json
import shutil
import textwrap
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COVER_REMAKE = PROJECT_ROOT / "Cover_Remake"
CATALOG_OUT = PROJECT_ROOT / "backend" / "app" / "db" / "books_catalog.json"
COVERS_OUT = PROJECT_ROOT / "frontend" / "static" / "covers"

# (folder, catalog_label) in the order the ids are assigned.
SOURCES = (
    ("Programming_Book_Covers", "Programming"),
    ("AI_Book_Covers", "Artificial Intelligence"),
    ("Computer_Science_Book_Covers", "Computer Science"),
    ("Humor_Books_and_Covers", "Humor"),
    ("Light_Reads_Catalog", "Light Reads"),
    ("Magazine_Catalog", "Magazines"),
    ("Manga_1000_Covers", "Manga"),
    ("Mystical_Books_and_Covers", "Mystical"),
    ("Romance_Books_and_Covers", "Romance"),
)


def build() -> list[dict]:
    combined: list[dict] = []
    new_id = 0
    for folder, label in SOURCES:
        root = COVER_REMAKE / folder
        # Older packs nest everything under FrontEnd/; newer packs keep the
        # catalog JSON at the folder root and covers under static/covers.
        frontend = root / "FrontEnd"
        if frontend.is_dir():
            catalog_path = frontend / "database" / "books.json"
            src_covers = frontend / "static" / "covers"
        else:
            catalog_path = next(root.glob("*.json"))
            src_covers = root / "static" / "covers"
        data = json.loads(catalog_path.read_text(encoding="utf-8"))
        for entry in data:
            new_id += 1
            source_image = src_covers / Path(entry["cover"]).name
            if not source_image.is_file():
                raise FileNotFoundError(f"missing cover {source_image}")
            shutil.copyfile(source_image, COVERS_OUT / f"book-{new_id:03d}.jpg")
            # DB column and API schema cap author at 150 chars; Open Library
            # contributor lists can run much longer.
            author = textwrap.shorten(entry["author"], width=150, placeholder="…")
            record = {
                "id": new_id,
                "title": entry["title"],
                "author": author,
                "category": entry["category"],
                "description": entry.get("description", ""),
                "price": entry["price"],
                "stock": entry["stock"],
                "cover": f"/static/covers/book-{new_id:03d}.jpg",
                "isbn": entry.get("isbn") or "",
                "collection": label,
            }
            combined.append(record)
    return combined


def report(books: list[dict]) -> None:
    seen: dict[str, int] = {}
    for book in books:
        seen[book["category"]] = seen.get(book["category"], 0) + 1
    print(f"total books: {len(books)}")
    print(f"distinct categories: {len(seen)}")
    for name, count in seen.items():
        code = "-".join(name.casefold().split())
        print(f"  {count:>3}  {code}  ({name})")


def main() -> None:
    COVERS_OUT.mkdir(parents=True, exist_ok=True)
    for stale in COVERS_OUT.glob("*.svg"):
        stale.unlink()
    books = build()
    CATALOG_OUT.write_text(json.dumps(books, indent=2, ensure_ascii=False), encoding="utf-8")
    report(books)
    print(f"wrote {CATALOG_OUT}")


if __name__ == "__main__":
    main()
