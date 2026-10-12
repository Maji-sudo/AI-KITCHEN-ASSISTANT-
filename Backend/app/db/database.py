from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings


_db_url = make_url(settings.DATABASE_URL)
if _db_url.database:
    _clean_db = _db_url.database.strip('"\'')
    _db_url = _db_url.set(database=_clean_db)

engine = create_engine(
    _db_url,
    echo=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


class Base(DeclarativeBase):
    pass

from app.models import *  # noqa: F401


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()