import sqlite3
from datetime import datetime
import re
import importlib.util
import os
from scraper import scrape_quotes
from scraper_goodreads import scrape_goodreads

# === 强制从本地 generator.py 加载 QuoteGenerator ===
gen_path = os.path.join(os.path.dirname(__file__), "generator.py")
spec = importlib.util.spec_from_file_location("generator", gen_path)
generator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator_module)
QuoteGenerator = generator_module.QuoteGenerator
# === 结束 ===

DB_PATH = "quotes.db"

def _list_columns(conn):
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(quotes)")
    return [r[1] for r in cur.fetchall()]

def manual_mode(conn):
    print("\nManual input Mode")
    raw_date = input("Please enter date (支持: 20250811 / 2025/08/11 / 2025.08.11): ").strip()

    if re.fullmatch(r"\d{8}", raw_date):
        raw_date = f"{raw_date[0:4]}.{raw_date[4:6]}.{raw_date[6:8]}"

    dt = None
    for pat in ("%Y/%m/%d", "%Y.%m.%d", "%Y%m%d"):
        try:
            dt = datetime.strptime(raw_date, pat)
            break
        except ValueError:
            pass

    if dt is None:
        print("❌ 日期格式不正确，请用 2025/08/11 或 20250811 或 2025.08.11")
        return

    date_str = dt.strftime("%Y.%m.%d")  # 统一成 YYYY.MM.DD

    author = input("Please enter author name: ").strip()
    quote = input("Please enter quotes: ").strip()

    gen = QuoteGenerator()
    gen.generate(date=date_str, author=author, quote=quote, output_format="jpeg")

    save_quote(conn, date_str, author, quote)
    print("✅ Quote saved and image generated!\n")

def from_db_mode(conn):
    cols = _list_columns(conn)
    date_col = "date" if "date" in cols else ("quote_date" if "quote_date" in cols else None)

    cur = conn.cursor()
    if date_col:
        cur.execute(f"SELECT id, {date_col}, author, quote FROM quotes ORDER BY RANDOM() LIMIT 5")
    else:
        cur.execute("SELECT id, author, quote FROM quotes ORDER BY RANDOM() LIMIT 5")
    rows = cur.fetchall()

    if not rows:
        print("⚠️ No quotes in database.")
        return

    print("\nAvailable Quotes:")
    if date_col:
        for row in rows:
            print(f"{row[0]}: [{row[1]}] {row[2]} - {row[3][:50]}...")
    else:
        for row in rows:
            print(f"{row[0]}: {row[1]} - {row[2][:50]}...")

    try:
        selected_id = int(input("Enter ID to generate image: ").strip())
    except ValueError:
        print("❌ Invalid ID.")
        return

    if date_col:
        cur.execute(f"SELECT {date_col}, author, quote FROM quotes WHERE id=?", (selected_id,))
        result = cur.fetchone()
        if result:
            date, author, quote = result
        else:
            print("❌ ID not found.")
            return
    else:
        cur.execute("SELECT author, quote FROM quotes WHERE id=?", (selected_id,))
        result = cur.fetchone()
        if result:
            author, quote = result
            date = datetime.today().strftime("%Y.%m.%d")
        else:
            print("❌ ID not found.")
            return

    gen = QuoteGenerator()
    gen.generate(date, author, quote)
    print("✅ Image generated!\n")

def save_quote(conn, date, author, quote):
    cols = _list_columns(conn)

    # 构造要写入的列与参数：有哪个写哪个
    insert_cols = []
    params = []

    if "date" in cols:
        insert_cols.append("date")
        params.append(date)
    if "quote_date" in cols:                # 兼容旧库
        insert_cols.append("quote_date")
        params.append(date)

    insert_cols.extend(["author", "quote"])
    params.extend([author, quote])

    placeholders = ",".join(["?"] * len(insert_cols))
    sql = f"INSERT INTO quotes ({', '.join(insert_cols)}) VALUES ({placeholders})"

    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 若不存在则按新结构创建
    cur.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            author TEXT,
            quote TEXT
        )
    """)
    conn.commit()

    # 如果是非常老的库没有 date 列，补上（不影响已有 NOT NULL 约束的 quote_date）
    cur.execute("PRAGMA table_info(quotes)")
    cols = [r[1] for r in cur.fetchall()]
    if "date" not in cols:
        try:
            cur.execute("ALTER TABLE quotes ADD COLUMN date TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass

    return conn

def main():
    conn = init_db()

    print("Select an option:")
    print("1. Manual input")
    print("2. From database")
    print("3. Scrape from website")

    choice = input("Please enter 1, 2, or 3: ").strip()

    if choice == "1":
        manual_mode(conn)
    elif choice == "2":
        from_db_mode(conn)
    elif choice == "3":
        scrape_quotes(conn)
        scrape_goodreads(conn)
    else:
        print("❌ Invalid choice.")

    conn.close()

if __name__ == "__main__":
    main()
