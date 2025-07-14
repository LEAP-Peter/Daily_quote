import sqlite3
import os

DB_PATH = "quotes.db"

CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_date TEXT NOT NULL,
    author TEXT NOT NULL,
    quote TEXT NOT NULL
)
"""

def initialize_database(DB_PATH):
    conn = None
    try:
      if not os.path.exists(DB_PATH):
          print(f"Creating database at {DB_PATH}")
      else:
          print(f"Database already exists at {DB_PATH}")

      conn = sqlite3.connect(DB_PATH)
      cursor = conn.cursor()
      cursor.execute(CREATE_TABLE_QUERY)
      conn.commit()  
      print(f"table created in {DB_PATH}")    
    except sqlite3.Error as e:
        print(f"Error in {DB_PATH}",e)  
    finally: 
            if conn:
                conn.close()  


def get_all_quotes(conn):
    #Get all quotes from the database.
    cursor = conn.cursor()
    cursor.execute("SELECT quote_date, author, quote FROM quotes ORDER BY quote_date DESC")
    rows = cursor.fetchall()
    return rows

def add_quotes(conn, quote_date, author, quote):
    #Add a new quote to the database.
    cursor = conn.cursor()
    cursor.execute("INSERT INTO quotes (quote_date, author, quote) VALUES (?, ?, ?)", (quote_date, author, quote))
    conn.commit()
    print(f"Quote added: {quote_date} - {author}: {quote}")