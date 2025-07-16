from utils import initialize_database, add_quotes
from generator import QuoteGenerator
from datetime import datetime
import sqlite3


def main():
    print("Welcome to the Quote Generator!")
    print("Initializing database... Please wait.")
    initialize_database("quotes.db")
    print("Database initialized successfully.")

    conn = sqlite3.connect("quotes.db")

    while True:
        quote_date = input("Please enter quote date (YYYY/MM/DD): ").strip()
        author = input("Please enter author name: ").strip()
        quote = input("Please enter quote: ").strip()
        
        if not quote_date or not author or not quote:
            print("All fields are required. Please try again.")
        else:
            break

    raw_date = quote_date
    formats = ["%Y%m%d", "%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d"]

    for fmt in formats:
        try:
            dt = datetime.strptime(raw_date, fmt)
            quote_date = dt.strftime("%Y.%m.%d")
            break
        except ValueError:
            continue
    else:
        print("Invalid date format. Please use YYYY/MM/DD, YYYY-MM-DD or YYYY.MM.DD.")
        conn.close()
        return

    add_quotes(conn, quote_date, author, quote)

    generator = QuoteGenerator()
    generator.generate(
        date = quote_date,
        author = author,
        quote = quote,
        output_format = "jpeg"
    )
    print("Quote generated successfully! Check output folder for image.")

    conn.close()

if __name__ == "__main__":
    main()




