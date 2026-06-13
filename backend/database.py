import os
from datetime import datetime, timezone

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
IS_PG = DATABASE_URL.startswith("postgres")

if IS_PG:
    import psycopg2
    import psycopg2.extras
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    import sqlite3
    DB_PATH = os.path.join(os.path.dirname(__file__), "pato.db")

PH = "%s" if IS_PG else "?"
PK = "SERIAL PRIMARY KEY" if IS_PG else "INTEGER PRIMARY KEY AUTOINCREMENT"

ROLE_CHECK = "CHECK (role IN ('cliente','N1','N2','N3'))"
LEVEL_CHECK = "CHECK (level IN ('N1','N2','N3'))"
STATUS_CHECK = "CHECK (status IN ('Aberto','Em análise','Em atendimento','Aguardando cliente','Aguardando terceiro','Resolvido','Encerrado'))"
PRIORITY_CHECK = "CHECK (priority IN ('Baixa','Média','Alta','Crítica') OR priority IS NULL)"


def get_conn():
    if IS_PG:
        return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def q(sql: str) -> str:
    return sql.replace("?", "%s") if IS_PG else sql


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"""
    CREATE TABLE IF NOT EXISTS users (
        id {PK},
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'cliente' {ROLE_CHECK},
        created_at TEXT NOT NULL
    )""")
    c.execute(f"""
    CREATE TABLE IF NOT EXISTS tickets (
        id {PK},
        code TEXT UNIQUE NOT NULL,
        client_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT,
        priority TEXT {PRIORITY_CHECK},
        ai_summary TEXT,
        status TEXT NOT NULL DEFAULT 'Aberto' {STATUS_CHECK},
        level TEXT NOT NULL DEFAULT 'N1' {LEVEL_CHECK},
        channel TEXT DEFAULT 'Chat',
        frequency TEXT DEFAULT 'Apenas atualizações importantes',
        eta TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""")
    c.execute(f"""
    CREATE TABLE IF NOT EXISTS events (
        id {PK},
        ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
        kind TEXT NOT NULL,
        author TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    c.execute(f"""
    CREATE TABLE IF NOT EXISTS attachments (
        id {PK},
        ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
        filename TEXT NOT NULL,
        mimetype TEXT,
        size INTEGER,
        data TEXT NOT NULL,
        uploaded_by TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    c.execute(f"""
    CREATE TABLE IF NOT EXISTS reset_tokens (
        id {PK},
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        token TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        used INTEGER DEFAULT 0
    )""")
    c.execute(f"""
    CREATE TABLE IF NOT EXISTS kb_articles (
        id {PK},
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'Geral',
        tags TEXT NOT NULL DEFAULT '',
        author TEXT NOT NULL,
        views INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""")
    c.execute("UPDATE tickets SET channel='Chat' WHERE channel != 'Chat'")
    for idx in (
        "CREATE INDEX IF NOT EXISTS idx_tickets_client ON tickets(client_id)",
        "CREATE INDEX IF NOT EXISTS idx_tickets_level_status ON tickets(level,status)",
        "CREATE INDEX IF NOT EXISTS idx_events_ticket ON events(ticket_id)",
        "CREATE INDEX IF NOT EXISTS idx_attachments_ticket ON attachments(ticket_id)",
        "CREATE INDEX IF NOT EXISTS idx_reset_tokens_token ON reset_tokens(token)",
        "CREATE INDEX IF NOT EXISTS idx_kb_category ON kb_articles(category)",
    ):
        c.execute(idx)
    conn.commit()
    conn.close()


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


def fetchone(conn, sql, params=()):
    cur = conn.cursor()
    cur.execute(q(sql), params)
    row = cur.fetchone()
    return dict(row) if row else None


def fetchall(conn, sql, params=()):
    cur = conn.cursor()
    cur.execute(q(sql), params)
    return [dict(r) for r in cur.fetchall()]


def execute(conn, sql, params=()):
    cur = conn.cursor()
    cur.execute(q(sql), params)
    return cur


def insert_returning_id(conn, sql, params=()):
    cur = conn.cursor()
    if IS_PG:
        cur.execute(q(sql) + " RETURNING id", params)
        return cur.fetchone()["id"]
    cur.execute(q(sql), params)
    return cur.lastrowid
