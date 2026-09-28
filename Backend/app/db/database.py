from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings


engine = create_engine(
    settings.DATABASE_URL,
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
    # Ensure tables exist for this engine (useful for in‑memory test DBs)
    Base.metadata.create_all(bind=db.get_bind())
    try:
        yield db
    finally:
        db.close()