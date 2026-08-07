import sqlite3
from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

_IS_SQLITE = settings.database_url.startswith("sqlite")

if _IS_SQLITE:
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=1800,
    )

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@event.listens_for(Engine, "connect")
def _apply_sqlite_pragmas(dbapi_connection: object, _record: object) -> None:
    """SQLite ulanishlari uchun PRAGMA'lar (test enginelariga ham tegishli)."""
    if not isinstance(dbapi_connection, sqlite3.Connection):
        return
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        # WAL faqat fayl bazasida ma'noga ega; in-memory bazada "main" fayli bo'sh qatorda.
        cursor.execute("SELECT file FROM pragma_database_list WHERE name = 'main'")
        row = cursor.fetchone()
        if row and row[0]:
            cursor.execute("PRAGMA journal_mode=WAL")
    finally:
        cursor.close()


class Base(DeclarativeBase):
    pass


def session_scope(session_factory: sessionmaker) -> Generator[Session, None, None]:
    """Unit-of-work: muvaffaqiyatda bitta commit, xatoda rollback."""
    db: Session = session_factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    yield from session_scope(SessionLocal)
