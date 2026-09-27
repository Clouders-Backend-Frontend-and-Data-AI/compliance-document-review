from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from data_engineering.config import get_settings

_engine: Optional[Engine] = None
SessionLocal: Optional[sessionmaker] = None


def _ensure_engine() -> Engine:
    global _engine, SessionLocal
    if _engine is None:
        settings = get_settings()
        kwargs = {"pool_pre_ping": True, "echo": False}
        if settings.database_url.startswith("postgresql"):
            kwargs.update({"pool_size": 10, "max_overflow": 20, "pool_recycle": 3600})
        _engine = create_engine(settings.database_url, **kwargs)
        SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    return _engine


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Context manager yielding a database session. Rolls back on exception."""
    _ensure_engine()
    assert SessionLocal is not None
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def set_ivfflat_probes(db: Session, probes: int = 10) -> None:
    """Set ivfflat.probes for the session (Postgres/pgvector only)."""
    settings = get_settings()
    if not settings.uses_pgvector:
        return
    db.execute(text(f"SET ivfflat.probes = {probes}"))
