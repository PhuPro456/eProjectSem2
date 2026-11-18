"""Rebuild the database from the current catalog and demo seed.

Drops every table, recreates the schema, and re-runs the normal startup
seeding (books + categories, admin, demo customers/orders/reviews) against the
database selected by DATABASE_URL. Use this after changing the book catalog so
the stored rows — and the covers they point at — match the new data.

    python scripts/reset_database.py            # uses .env DATABASE_URL
    DATABASE_URL=sqlite:///./dev.db python scripts/reset_database.py
"""

from app.db import init_db  # noqa: F401  (registers all model classes)
from app.db.session import Base, engine
from app.db.init_db import initialize_database


def main() -> None:
    print(f"Dropping all tables on: {engine.url}")
    Base.metadata.drop_all(bind=engine)
    initialize_database()
    print("Database reset and reseeded.")


if __name__ == "__main__":
    main()
