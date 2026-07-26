import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def _sqlite_url() -> str:
    url = settings.DATABASE_URL
    if url.startswith("sqlite:///"):
        path = url.replace("sqlite:///", "")
        if path.startswith("/"):
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        else:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    return url


# SQLite + default QueuePool exhausts under concurrent/long-lived SSE chat streams
# (request-scoped sessions stay checked out until the stream finishes). NullPool
# avoids "QueuePool limit ... connection timed out" (sqlalchemy.exc.TimeoutError).
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if _is_sqlite else {}
engine = create_engine(
    _sqlite_url(),
    connect_args=connect_args,
    poolclass=NullPool if _is_sqlite else None,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    from app.database import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def check_db_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
