"""
SQLite migration helper for SereneMind backend.

Run from services/avatar-service:
    python scripts/migrate_db.py
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv()

from app.core.config import settings


def _sqlite_path() -> Path | None:
    url = settings.DATABASE_URL
    if not url.startswith("sqlite:///"):
        print("Migration script only supports SQLite.")
        return None
    path = url.replace("sqlite:///", "")
    return Path(path)


def migrate() -> None:
    db_path = _sqlite_path()
    if db_path is None:
        return

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone():
        cols = {row[1] for row in cursor.execute("PRAGMA table_info(users)")}
        if "password_hash" not in cols:
            cursor.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)")
            print("Added users.password_hash")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_summaries'")
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE user_summaries (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                summary_text TEXT NOT NULL,
                updated_at DATETIME,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        print("Created user_summaries table")

    conn.commit()
    conn.close()

    from app.database.session import init_db
    init_db()
    print(f"Migration complete: {db_path}")


if __name__ == "__main__":
    migrate()
