"""Подключение к БД через SQLAlchemy."""
import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/bookstore",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

if engine.dialect.name == "sqlite":
    # Режим для быстрой проверки без PostgreSQL: включаем внешние ключи
    # и учим lower() работать с кириллицей (нужно для ILIKE).
    @event.listens_for(engine, "connect")
    def _sqlite_setup(conn, _record):
        conn.execute("PRAGMA foreign_keys = ON")
        conn.create_function("lower", 1, lambda s: s.lower() if isinstance(s, str) else s)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
