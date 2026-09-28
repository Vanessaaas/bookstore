"""Создаёт базу bookstore и выполняет database/create_db.sql.

Удобно, если psql нет в PATH. Строка подключения берётся из DATABASE_URL.
Запуск: python tools/init_db.py
"""
import re
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.database import DATABASE_URL, Base, engine  # noqa: E402
from app import models  # noqa: E402,F401

SQL_FILE = ROOT / "database" / "create_db.sql"


def init_postgres(script: str) -> None:
    url = make_url(DATABASE_URL)
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": url.database})
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{url.database}" ENCODING \'UTF8\' TEMPLATE template0'))
            print(f"База {url.database} создана")
    admin.dispose()
    raw = engine.raw_connection()
    try:
        with raw.cursor() as cur:
            cur.execute(script)
        raw.commit()
    finally:
        raw.close()


def init_sqlite(script: str) -> None:
    """Проверочный режим: схема из ORM, данные из того же SQL-скрипта."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    data = re.search(r"-- @data-begin\n(.*)-- @data-end", script, re.S).group(1)
    raw = engine.raw_connection()
    try:
        raw.executescript(data)
        raw.commit()
    finally:
        raw.close()


def main() -> None:
    script = SQL_FILE.read_text(encoding="utf-8")
    if engine.dialect.name == "sqlite":
        init_sqlite(script)
    else:
        init_postgres(script)
    print("Схема и данные загружены")


if __name__ == "__main__":
    main()
