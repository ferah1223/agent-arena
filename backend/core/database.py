import sqlite3
import os
from contextlib import contextmanager
from .config import settings

DB_PATH = settings.DATABASE_URL


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                model TEXT NOT NULL,
                owner TEXT NOT NULL,
                description TEXT DEFAULT '',
                api_key TEXT NOT NULL UNIQUE,
                elo INTEGER NOT NULL DEFAULT 1200,
                wins INTEGER NOT NULL DEFAULT 0,
                losses INTEGER NOT NULL DEFAULT 0,
                streak INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_a_id INTEGER NOT NULL REFERENCES agents(id),
                agent_b_id INTEGER NOT NULL REFERENCES agents(id),
                game_mode TEXT NOT NULL,
                difficulty TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','running','completed')),
                winner_id INTEGER REFERENCES agents(id),
                agent_a_score REAL DEFAULT 0,
                agent_b_score REAL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS match_rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
                round_num INTEGER NOT NULL,
                agent_id INTEGER NOT NULL REFERENCES agents(id),
                input_prompt TEXT NOT NULL,
                output_response TEXT DEFAULT '',
                score REAL DEFAULT 0,
                timestamp TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS challenge_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                content_json TEXT NOT NULL DEFAULT '{}',
                time_limit INTEGER DEFAULT 60,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);
            CREATE INDEX IF NOT EXISTS idx_agents_elo ON agents(elo DESC);
            CREATE INDEX IF NOT EXISTS idx_match_rounds_match ON match_rounds(match_id);
        """)
