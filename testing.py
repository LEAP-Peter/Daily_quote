# testing.py

# from generator import QuoteGenerator

# g = QuoteGenerator()

# g.generate(
#     date="2025.07.02",
#     author="Einstein",
#     quote="Imagination is more important than knowledge.",
#     output_format="jpeg"
# )


# import sqlite3

# conn = sqlite3.connect("quotes.db")
# cursor = conn.cursor()
# cursor.execute("SELECT COUNT(*) FROM quotes")
# count = cursor.fetchone()[0]
# print(f"Total quotes: {count}")
# conn.close()

# import sqlite3

# conn = sqlite3.connect("quotes.db")
# cursor = conn.cursor()

# cursor.execute("SELECT quote_date, author, quote FROM quotes ORDER BY id DESC LIMIT 10")
# rows = cursor.fetchall()

# for row in rows:
#     print(f"{row[0]} - {row[1]}:\n  {row[2]}\n")

# conn.close()


import sqlite3

def view_quotes(limit=20):
    conn = sqlite3.connect("quotes.db")
    cursor = conn.cursor()

    cursor.execute("SELECT quote_date, author, quote FROM quotes ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()

    print(f"--- Showing latest {limit} quotes ---\n")
    for i, (date, author, quote) in enumerate(rows, 1):
        print(f"{i}. {date} - {author}\n   “{quote}”\n")

    conn.close()

if __name__ == "__main__":
    view_quotes(limit=20)  
