
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings
from pathlib import Path

def _prepare_sqlite(url: str) -> tuple[str, dict]:
    connect_args = {"check_same_thread": False}
    if url.startswith("sqlite:///"):
        db_file = url.replace("sqlite:///", "", 1)
        Path(db_file).parent.mkdir(parents=True, exist_ok=True)
    return url, connect_args


if settings.DATABASE_URL.startswith("sqlite"):
    db_url, connect_args = _prepare_sqlite(settings.DATABASE_URL)
    engine = create_engine(db_url, connect_args=connect_args, echo=False, future=True)
else:
    
    engine = create_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True, future=True)


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
