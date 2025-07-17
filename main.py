from utils import initialize_database, add_quotes
from generator import QuoteGenerator
from datetime import datetime
import sqlite3

def manual_mode(conn):
    print("\n Manual input Mode")
    while True:
        quote_date = input("Please enter date:(YYYY/MM/DD): ").strip()
        author = input("Please enter author name: ").strip()
        quote = input("Please enter quotes: ").strip()
        
        if not quote_date or not author or not quote:
            print("All fields are required.")
        else:
            break

    raw_date = quote_date
    formats = ["%Y%m%d, %Y%m%d", "%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d"]

    for fmt in formats:
        try:
            dt = datetime.strptime(raw_date, fmt)
            quote_date = dt.strftime("%Y.%m.%d")
            break
        except ValueError:
            continue
    else:
        print("Date format wrong, Please use YYYYMMDD, YYYY/MM/DD, YYYY-MM-DD or YYYY.MM.DD")
        return

    add_quotes(conn, quote_date, author, quote)

    today = datetime.now().strftime("%Y.%m.%d")
    generator = QuoteGenerator()
    generator.generate(
        date=today,
        author=author,
        quote=quote,
        output_format="jpeg"
    )
    print(f"Quote generated. Date：{today}")

def select_from_database(conn):
    print("\n Database Mode")

    offset = 0
    page_size = 10

    while True:
        cursor = conn.cursor()
        cursor.execute("SELECT quote_date, author, quote FROM quotes ORDER BY id DESC LIMIT ? OFFSET ?", (page_size, offset))
        rows = cursor.fetchall()

        if not rows:
            print("No more quotes found.")
            return

        for i, (qdate, author, quote) in enumerate(rows, 1):
            print(f"{i}. [{qdate}] {author}:\n   “{quote[:60]}...”\n")

        choice = input(" Choose from 1-10 to generate，n for next page，q for exit").strip().lower()

        if choice == "q":
            return
        elif choice == "n":
            offset += page_size
        elif choice.isdigit() and 1 <= int(choice) <= len(rows):
            qdate, author, quote = rows[int(choice) - 1]
            today = datetime.now().strftime("%Y.%m.%d")
            generator = QuoteGenerator()
            generator.generate(date=today, author=author, quote=quote, output_format="jpeg")
            print("Image generated successfully.")
            return
        else:
            print("Invalid Input, please try again.")


def main():
    print("📸 Welcome to the Quote Generator!")
    initialize_database("quotes.db")
    conn = sqlite3.connect("quotes.db")

    print("\n Choose a mode:")
    print("1 - manually input quote")
    print("2 - choose quote from database")

    mode = input("Please enter 1 or 2").strip()

    if mode == "1":
        manual_mode(conn)
    elif mode == "2":
        select_from_database(conn)
    else:
        print("Invalid input. Please enter 1 or 2.")

    conn.close()

if __name__ == "__main__":
    main()




