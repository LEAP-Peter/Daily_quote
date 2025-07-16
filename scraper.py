import requests 
import sqlite3
from bs4 import BeautifulSoup
from utils import initialize_database, add_quotes


DB_path = "quotes.db"

def quote_exists(conn, quote_text):
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM quotes WHERE quote = ?", (quote_text,))
    return cursor.fetchone() is not None

def scrape_quotes():
    initialize_database("quotes.db")
    conn = sqlite3.connect("quotes.db")

    page = 1
    current_day = 1

    while True:
        url = f"https://quotes.toscrape.com/page/{page}/"
        res = requests.get(url)
        if res.status_code != 200:
            print(f"Status code {res.status_code}, fetching stopped.")
            break

        soup = BeautifulSoup(res.text, "html.parser")
        quotes = soup.find_all("div", class_="quote")

        if not quotes:
            break 

        for q in quotes:
            text = q.find("span", class_="text").text.strip()
            author = q.find("small", class_="author").text.strip()

            date = f"2025.{(current_day - 1)//30 + 1:02d}.{(current_day - 1) % 30 + 1:02d}"
            current_day += 1

            if quote_exists(conn, text):
                print(f"Quote already exists: {text}")
                continue

            add_quotes(conn,date, author, text)
            print(f"Quote added: {text} by {author} on {date}")

        page += 1
    
    conn.close()
    print("Scraping completed.")

if __name__ == "__main__":
    scrape_quotes()
    


            

