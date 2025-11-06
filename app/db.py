
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

from app.core.config import settings  

Base = declarative_base()

def _make_engine():
    url = settings.DATABASE_URL

    # Defaults
    engine_kwargs: dict = {
        "echo": getattr(settings, "ECHO_SQL", False),
        "future": True,
        "pool_pre_ping": True,  
    }


    if url.startswith("sqlite:"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        engine_kwargs["poolclass"] = NullPool  


    return create_engine(url, **engine_kwargs)

engine = _make_engine()


# Session factory

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    from app.models import Base  
    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope():
    """Gebruik als:
    with session_scope() as db:
        db.add(...)
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
