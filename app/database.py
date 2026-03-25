from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = None
SessionLocal = None

LOCAL_SQLITE_URL = "sqlite:///./soundverse.db"


def _make_engine(url: str):
    is_sqlite = url.startswith("sqlite")
    kwargs: dict = {"pool_pre_ping": True}
    if not is_sqlite:
        kwargs.update({"pool_size": 5, "max_overflow": 10})
    else:
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


def init_db(url: str | None = None) -> str:
    """Bind engine and SessionLocal to the given URL (default: settings.database_url)."""
    global engine, SessionLocal
    resolved = (url if url is not None else settings.database_url).strip()
    engine = _make_engine(resolved)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return resolved


init_db()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
