# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings
from pathlib import Path

def _prepare_sqlite(url: str) -> tuple[str, dict]:
    # Alleen voor sqlite: maak directory aan en zet connect_args
    connect_args = {"check_same_thread": False}
    # Alleen paden die beginnen met sqlite:///
    if url.startswith("sqlite:///"):
        # Strip alleen de scheme prefix; resultaat is een bestandsnaam (kan relatief zijn)
        db_file = url.replace("sqlite:///", "", 1)
        # Zorg dat de map bestaat ('.' is ok)
        Path(db_file).parent.mkdir(parents=True, exist_ok=True)
    return url, connect_args

if settings.DATABASE_URL.startswith("sqlite"):
    db_url, connect_args = _prepare_sqlite(settings.DATABASE_URL)
    engine = create_engine(db_url, connect_args=connect_args, echo=False)
else:
    engine = create_engine(settings.DATABASE_URL, echo=False)

SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass
