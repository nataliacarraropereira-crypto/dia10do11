from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from streamlit.errors import StreamlitSecretNotFoundError

load_dotenv()


class Base(DeclarativeBase):
    pass


def _secret_value(key: str) -> str | None:
    import streamlit as st

    try:
        value = st.secrets.get(key)
        if value:
            return str(value)
        database_secrets = st.secrets.get("database", {})
        nested_value = database_secrets.get(key) if hasattr(database_secrets, "get") else None
        return str(nested_value) if nested_value else None
    except StreamlitSecretNotFoundError:
        return None


def _setting(key: str, default: str | None = None) -> str | None:
    return os.getenv(key) or _secret_value(key) or default


def get_database_url() -> URL:
    mode = (_setting("APP_DB_MODE", "sqlite") or "sqlite").lower()

    if mode == "mysql":
        mysql_url = _setting("MYSQL_URL")
        if mysql_url:
            return make_url(mysql_url)

        host = _setting("MYSQL_HOST")
        port = _setting("MYSQL_PORT", "3306")
        database = _setting("MYSQL_DATABASE")
        user = _setting("MYSQL_USER")
        password = _setting("MYSQL_PASSWORD")
        if not all((host, port, database, user, password)):
            raise ValueError(
                "Configuração MySQL incompleta. Defina MYSQL_URL ou MYSQL_HOST, "
                "MYSQL_PORT, MYSQL_DATABASE, MYSQL_USER e MYSQL_PASSWORD."
            )
        return URL.create(
            "mysql+pymysql",
            username=user,
            password=password,
            host=host,
            port=int(port),
            database=database,
            query={"charset": "utf8mb4"},
        )

    if mode != "sqlite":
        raise ValueError("APP_DB_MODE deve ser 'sqlite' ou 'mysql'.")

    sqlite_path = Path(_setting("SQLITE_PATH", "data/cursinho_ufsc.db") or "")
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return URL.create("sqlite", database=str(sqlite_path.resolve()))


database_url = get_database_url()
engine = create_engine(
    database_url,
    echo=False,
    connect_args={"check_same_thread": False} if database_url.drivername == "sqlite" else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
