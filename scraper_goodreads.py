import requests
from bs4 import BeautifulSoup
import sqlite3
from utils import initialize_database, add_quotes
import time

def get_next_index(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM quotes")
    result = cursor.fetchone()[0]
    return result + 1 if result is not None else 1

def quote_exists(conn, quote_text):
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM quotes WHERE quote = ?", (quote_text,))
    return cursor.fetchone() is not None

def scrape_goodreads():
    print("Initializing database...")
    initialize_database("quotes.db")
    conn = sqlite3.connect("quotes.db")
    current_day = get_next_index(conn)

    page = 1
    MAX_PAGES = 100 

    while page <= MAX_PAGES:
        url = f"https://www.goodreads.com/quotes?page={page}"
        print(f"\nFetching page {page} ...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print(f"Error fetching page {page}, status: {res.status_code}")
            break

        soup = BeautifulSoup(res.text, "html.parser")
        quote_blocks = soup.find_all("div", class_="quoteText")

        if not quote_blocks:
            print("No more quotes found. Stopping.")
            break

        for block in quote_blocks:
            full_text = block.get_text(separator="\n", strip=True)
            parts = full_text.split("―")
            if len(parts) < 2:
                continue

            quote = parts[0].strip('“”"\n ')
            author = parts[1].strip().split(",")[0]

            date = f"2025.{(current_day - 1)//30 + 1:02d}.{(current_day - 1)%30 + 1:02d}"
            current_day += 1

            if quote_exists(conn, quote):
                print("Already exists:", quote[:60])
                continue

            add_quotes(conn, date, author, quote)
            print("✅ Added:", quote[:60])

        page += 1
        time.sleep(1)  

    conn.close()
    print("\nScraping complete.")

if __name__ == "__main__":
    scrape_goodreads()