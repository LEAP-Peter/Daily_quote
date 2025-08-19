import sqlite3
import os

DB_PATH = "quotes.db"


CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_date TEXT NOT NULL,
    author TEXT NOT NULL,
    quote TEXT NOT NULL
);
"""


# Triggers to enforce quote length <= 25 on INSERT/UPDATE
CREATE_LENGTH_CHECK_TRIGGER_INSERT = """
CREATE TRIGGER IF NOT EXISTS trg_quotes_len_ins
BEFORE INSERT ON quotes
FOR EACH ROW
WHEN length(NEW.quote) > 25
BEGIN
SELECT RAISE(ABORT, 'quote too long (max 25)');
END;
"""


CREATE_LENGTH_CHECK_TRIGGER_UPDATE = """
CREATE TRIGGER IF NOT EXISTS trg_quotes_len_upd
BEFORE UPDATE OF quote ON quotes
FOR EACH ROW
WHEN length(NEW.quote) > 25
BEGIN
SELECT RAISE(ABORT, 'quote too long (max 25)');
END;
"""


def initialize_database(db_path: str = DB_PATH):
    """Create DB/table and ensure length triggers are present."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.executescript(CREATE_TABLE_QUERY)
        cur.executescript(CREATE_LENGTH_CHECK_TRIGGER_INSERT)
        cur.executescript(CREATE_LENGTH_CHECK_TRIGGER_UPDATE)
        conn.commit()
    finally:
        conn.close()


def get_connection(db_path: str = DB_PATH):
    initialize_database(db_path)
    return sqlite3.connect(db_path)


def get_all_quotes(conn):
# Get all quotes from the database.
    cursor = conn.cursor()
    cursor.execute("SELECT quote_date, author, quote FROM quotes ORDER BY quote_date DESC")
    rows = cursor.fetchall()
    return rows


def add_quotes(conn, quote_date, author, quote):
# Add a new quote to the database with a defensive length check.
    if quote is None:
        raise ValueError("quote cannot be None")
    if len(quote) > 25:
        raise ValueError(f"quote too long (len={len(quote)}), max 25")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO quotes (quote_date, author, quote) VALUES (?, ?, ?)", (quote_date, author, quote))
    conn.commit()
    print(f"Quote added: {quote_date} - {author}: {quote}")


def find_violations(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, quote FROM quotes WHERE length(quote) > 25")
    return cur.fetchall()