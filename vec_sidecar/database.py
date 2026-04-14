"""sqlite-vec database initialization and management."""

import logging
import os
import sqlite3

import sqlite_vec

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("VEC_DB_PATH", "/app/data/vectors.db")

_conn: sqlite3.Connection | None = None


def get_db() -> sqlite3.Connection:
    """Get the sqlite-vec database connection (singleton)."""
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.enable_load_extension(True)
        sqlite_vec.load(_conn)
        _conn.enable_load_extension(False)
        _init_schema(_conn)
        logger.info("sqlite-vec database initialized at %s", DB_PATH)
    return _conn


def close_db() -> None:
    """Close the database connection."""
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None


def _init_schema(conn: sqlite3.Connection) -> None:
    """Create tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS vec_metadata (
            id TEXT PRIMARY KEY,
            collection TEXT NOT NULL,
            title TEXT DEFAULT '',
            content_preview TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_vec_metadata_collection
        ON vec_metadata(collection);
    """)

    # Check if vec_embeddings exists
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='vec_embeddings'"
    )
    if cursor.fetchone() is None:
        conn.execute("""
            CREATE VIRTUAL TABLE vec_embeddings USING vec0(
                id TEXT PRIMARY KEY,
                embedding float[1536]
            )
        """)

    conn.commit()
