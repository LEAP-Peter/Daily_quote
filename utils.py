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

def initialize_database():
    if os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} exists.")
        return
    conn = None 
    # If database file does not exist, create 
    try:
        print(f"Database file {DB_PATH} does not exist. Creating a new database.")  
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(CREATE_TABLE_QUERY)
        conn.commit()
        print(f"Database file {DB_PATH} created")
    except sqlite3.Error as e:
        print(f"Error in {DB_PATH}",e)  
    finally: 
            conn.close()  


def get_all_quotes():
    #Get all quotes from the database.
    conn = sqlite3. connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT quote_date, author, quote FROM quotes ORDER BY quote_date DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_quotes(quote_date, author,quote):
    #Add a new quote to the database.
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO quotes (quote_date, author, quote) VALUES (?, ?, ?)", (quote_date, author, quote))
    conn.commit()
    conn.close()
    print(f"Quote added: {quote_date} - {author}: {quote}")