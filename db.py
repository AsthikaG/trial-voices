"""SQLite schema + helpers. Resume-safe: every doc keyed by reddit id."""
import sqlite3
from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id            TEXT PRIMARY KEY,   -- reddit fullname (t1_xxx / t3_xxx)
    kind          TEXT,               -- 'post' | 'comment'
    subreddit     TEXT,
    permalink     TEXT,
    author        TEXT,
    created_utc   REAL,
    title         TEXT,               -- post title (null for comments)
    body          TEXT,
    score         INTEGER,
    fetched_at    REAL,
    extracted     INTEGER DEFAULT 0   -- 0=pending, 1=done, -1=not relevant
);

CREATE TABLE IF NOT EXISTS extractions (
    doc_id            TEXT PRIMARY KEY REFERENCES documents(id),
    is_patient_voice  INTEGER,        -- 1 if first-hand trial experience
    drug_name         TEXT,
    condition         TEXT,
    trial_phase       TEXT,
    duration_on_drug  TEXT,           -- free text as stated, e.g. "8 months"
    duration_days     INTEGER,        -- normalized estimate, null if unknown
    sentiment         TEXT,           -- positive|neutral|negative|mixed
    adverse_events    TEXT,           -- JSON array of strings
    summary           TEXT,
    raw_json          TEXT,
    extracted_at      REAL
);

CREATE INDEX IF NOT EXISTS idx_docs_pending ON documents(extracted);
"""


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init():
    conn = connect()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def upsert_document(conn, doc):
    conn.execute(
        """INSERT INTO documents
           (id, kind, subreddit, permalink, author, created_utc, title, body, score, fetched_at, extracted)
           VALUES (:id,:kind,:subreddit,:permalink,:author,:created_utc,:title,:body,:score,:fetched_at,
                   COALESCE((SELECT extracted FROM documents WHERE id=:id), 0))
           ON CONFLICT(id) DO UPDATE SET score=excluded.score, fetched_at=excluded.fetched_at""",
        doc,
    )


if __name__ == "__main__":
    init()
    print(f"Initialized {DB_PATH}")
