"""Camada de banco de dados.

- Na Render: usa PostgreSQL (variável DATABASE_URL, criada pelo render.yaml).
- No seu PC: usa SQLite (arquivo data/ely.db), sem precisar instalar nada.

Importante: o disco da Render (plano grátis) é apagado a cada deploy,
por isso os usuários ficam no PostgreSQL e não em arquivo.
"""
import os
import sqlite3
from datetime import datetime, timezone

DATABASE_URL = os.getenv("DATABASE_URL", "")
USE_PG = DATABASE_URL.startswith("postgres")
SQLITE_PATH = os.path.join(os.path.dirname(__file__), "data", "ely.db")

if USE_PG:
    import psycopg
    from psycopg.rows import dict_row


def _connect():
    if USE_PG:
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _sql(query: str) -> str:
    """Escreve as queries com '?' e converte para '%s' no PostgreSQL."""
    return query.replace("?", "%s") if USE_PG else query


def execute(query: str, params: tuple = ()):
    """Roda INSERT/UPDATE/CREATE."""
    conn = _connect()
    try:
        conn.execute(_sql(query), params)
        conn.commit()
    finally:
        conn.close()


def fetch_one(query: str, params: tuple = ()):
    """Retorna uma linha (dict) ou None."""
    conn = _connect()
    try:
        row = conn.execute(_sql(query), params).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def init_db():
    execute(
        """CREATE TABLE IF NOT EXISTS users (
            username   TEXT PRIMARY KEY,
            email      TEXT UNIQUE NOT NULL,
            name       TEXT NOT NULL,
            pass_hash  TEXT NOT NULL,
            created_at TEXT NOT NULL
        )"""
    )


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_user(identifier: str):
    """Busca por usuário OU e-mail."""
    return fetch_one("SELECT * FROM users WHERE username = ? OR email = ?", (identifier, identifier))


def create_user(username, email, name, pass_hash):
    execute(
        "INSERT INTO users (username, email, name, pass_hash, created_at) VALUES (?, ?, ?, ?, ?)",
        (username, email, name, pass_hash, now()),
    )
