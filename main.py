import sqlite3
from datetime import datetime
import re
import importlib.util
import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import scraper  # 你的专用爬虫（已支持 quotes.toscrape.com）

# === 强制从本地 generator.py 加载 QuoteGenerator ===
gen_path = os.path.join(os.path.dirname(__file__), "generator.py")
spec = importlib.util.spec_from_file_location("generator", gen_path)
generator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator_module)
QuoteGenerator = generator_module.QuoteGenerator
# === 结束 ===

DB_PATH = "quotes.db"
MAX_PAGES = 50         # 默认最多翻 50 页，按需可调
REQUEST_DELAY = 0.8    # 礼貌等待，避免请求过快

# ---------- 公共工具 ----------
def _list_columns(conn):
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(quotes)")
    return [r[1] for r in cur.fetchall()]

def _detect_date_column(conn):
    cols = _list_columns(conn)
    if "date" in cols:
        return "date"
    if "quote_date" in cols:
        return "quote_date"
    return None

# ---------- 功能 1：Manual input ----------
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

    date_str = dt.strftime("%Y.%m.%d")

    author = input("Please enter author name: ").strip()
    quote = input("Please enter quotes: ").strip()

    gen = QuoteGenerator()
    gen.generate(date=date_str, author=author, quote=quote, output_format="jpeg")

    save_quote(conn, date_str, author, quote)
    print("✅ Quote saved and image generated!\n")

# ---------- 功能 2：From database（支持按 n 换一批） ----------
def from_db_mode(conn):
    date_col = _detect_date_column(conn)
    cur = conn.cursor()

    def fetch_batch(limit=5):
        if date_col:
            cur.execute(f"SELECT id, {date_col}, author, quote FROM quotes ORDER BY RANDOM() LIMIT {limit}")
        else:
            cur.execute(f"SELECT id, author, quote FROM quotes ORDER BY RANDOM() LIMIT {limit}")
        return cur.fetchall()

    while True:
        rows = fetch_batch(5)
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

        user_in = input("\nEnter ID to generate image, or press 'n' to refresh, 'q' to cancel: ").strip().lower()

        if user_in == "q":
            print("Canceled.")
            return
        if user_in == "n":
            continue

        try:
            selected_id = int(user_in)
        except ValueError:
            print("❌ Invalid input. Please enter a valid ID, 'n', or 'q'.")
            continue

        if date_col:
            cur.execute(f"SELECT {date_col}, author, quote FROM quotes WHERE id=?", (selected_id,))
            result = cur.fetchone()
            if not result:
                print("❌ ID not found.")
                continue
            date, author, quote = result
            if not date:
                date = datetime.today().strftime("%Y.%m.%d")
        else:
            cur.execute("SELECT author, quote FROM quotes WHERE id=?", (selected_id,))
            result = cur.fetchone()
            if not result:
                print("❌ ID not found.")
                continue
            author, quote = result
            date = datetime.today().strftime("%Y.%m.%d")

        gen = QuoteGenerator()
        gen.generate(date, author, quote)
        print("✅ Image generated!\n")
        return

# ---------- 保存到数据库（兼容旧列名） ----------
def save_quote(conn, date, author, quote):
    cols = _list_columns(conn)

    insert_cols, params = [], []
    if "date" in cols:
        insert_cols.append("date"); params.append(date)
    if "quote_date" in cols:
        insert_cols.append("quote_date"); params.append(date)

    insert_cols.extend(["author", "quote"])
    params.extend([author, quote])

    placeholders = ",".join(["?"] * len(insert_cols))
    sql = f"INSERT INTO quotes ({', '.join(insert_cols)}) VALUES ({placeholders})"

    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()

# ---------- 初始化数据库（保持兼容旧库） ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            author TEXT,
            quote TEXT
        )
    """)
    conn.commit()

    cur.execute("PRAGMA table_info(quotes)")
    cols = [r[1] for r in cur.fetchall()]
    if "date" not in cols:
        try:
            cur.execute("ALTER TABLE quotes ADD COLUMN date TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass

    return conn

# ---------- 通用解析：抽取页面上的 quotes ----------
def _extract_quotes_from_soup(soup):
    extracted = []

    # .quote 结构
    for q in soup.select(".quote"):
        t = q.select_one(".text")
        a = q.select_one(".author")
        if t and a:
            text = " ".join(t.stripped_strings).strip('“”"')
            author = " ".join(a.stripped_strings)
            if text:
                extracted.append((author, text))

    # blockquote + cite / 或 “— Author”
    for bq in soup.find_all("blockquote"):
        text = " ".join(bq.stripped_strings)
        if not text:
            continue
        author = None
        cite = bq.find("cite")
        if cite:
            author = " ".join(cite.stripped_strings)
        if not author:
            m = re.search(r"[—\-–]\s*([^—\-–]{2,})$", text)
            if m:
                author = m.group(1).strip()
                text = text[:m.start()].strip()
        if text:
            extracted.append((author or "Unknown", text.strip('“”"')))

    # Goodreads 风格 .quoteText
    for div in soup.select(".quoteText"):
        full = " ".join(div.stripped_strings)
        m = re.match(r"[“\"](.+?)[”\"]\s*[―\-–]\s*(.+)$", full)
        if m:
            text = m.group(1).strip()
            author = m.group(2).strip()
            extracted.append((author, text))

    # 清洗与页面内去重
    seen, cleaned = set(), []
    for author, text in extracted:
        key = (author.strip().lower(), text.strip().lower())
        if key not in seen and len(text) >= 5:
            seen.add(key)
            cleaned.append((author.strip(), text.strip()))
    return cleaned

# ---------- 通用解析：发现“下一页”链接 ----------
def _find_next_url(soup, base_url):
    # 1) <link rel="next" href="...">
    link = soup.find("link", attrs={"rel": re.compile(r"\bnext\b", re.I)})
    if link and link.get("href"):
        return urljoin(base_url, link["href"])

    # 2) <a rel="next">、class 含 next
    a = soup.find("a", attrs={"rel": re.compile(r"\bnext\b", re.I)})
    if a and a.get("href"):
        return urljoin(base_url, a["href"])
    a = soup.find("a", class_=re.compile("next", re.I))
    if a and a.get("href"):
        return urljoin(base_url, a["href"])

    # 3) 文本是“next / 下一页 / › / »”
    a = soup.find("a", string=re.compile(r"^\s*(next|下一页|›|»)\s*$", re.I))
    if a and a.get("href"):
        return urljoin(base_url, a["href"])

    # 4) 常见分页 li.next > a
    li = soup.find("li", class_=re.compile("next", re.I))
    if li:
        a = li.find("a")
        if a and a.get("href"):
            return urljoin(base_url, a["href"])

    return None

# ---------- 功能 3：Scrape from website（自动翻页） ----------
def scrape_from_website(conn):
    print("\nScrape from website")
    url = input("Enter a URL that contains quotes: ").strip()
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url

    # 限定在同一域名内抓取
    start_host = urlparse(url).netloc.lower()

    # 专用：quotes.toscrape.com 用你的爬虫（它自己会翻页、去重、入库）
    if re.search(r"(^|\.)quotes\.toscrape\.com", start_host, re.I):
        print("Using built-in scraper for quotes.toscrape.com ...")
        try:
            scraper.scrape_quotes()
            print("✅ Scraping finished via custom scraper.")
        except Exception as e:
            print(f"❌ Custom scraper failed: {e}")
        return

    visited = set()
    page_count = 0
    total_new, total_skipped = 0, 0
    next_url = url

    while next_url and page_count < MAX_PAGES:
        # 域名保护
        if urlparse(next_url).netloc.lower() != start_host:
            break
        if next_url in visited:
            break

        print(f"Fetching: {next_url}")
        visited.add(next_url)
        page_count += 1

        try:
            resp = requests.get(next_url, timeout=15, headers={"User-Agent": "quote-generator/1.0"})
        except Exception as e:
            print(f"❌ 请求失败：{e}")
            break

        if resp.status_code != 200 or not resp.text:
            print(f"❌ 拉取失败，HTTP {resp.status_code}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        cleaned = _extract_quotes_from_soup(soup)

        if page_count == 1 and not cleaned:
            print("⚠️ 未检测到可识别的 quote 结构，或该网站不可爬取。")
            return

        # 与数据库去重后入库
        cur = conn.cursor()
        today = datetime.today().strftime("%Y.%m.%d")
        new_count, skipped = 0, 0
        for author, text in cleaned:
            cur.execute("SELECT COUNT(*) FROM quotes WHERE quote=? AND author=?", (text, author))
            if cur.fetchone()[0]:
                skipped += 1
                continue
            save_quote(conn, today, author, text)
            new_count += 1

        total_new += new_count
        total_skipped += skipped
        print(f"Page {page_count}: 新增 {new_count} 条，跳过 {skipped} 条")

        # 找下一页
        nxt = _find_next_url(soup, next_url)
        next_url = None if not nxt or nxt in visited else nxt

        time.sleep(REQUEST_DELAY)

    print(f"✅ 爬取完成：共处理 {page_count} 页，新增 {total_new} 条，跳过 {total_skipped} 条。")

# ---------- 主菜单 ----------
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
        scrape_from_website(conn)
    else:
        print("❌ Invalid choice.")

    conn.close()

if __name__ == "__main__":
    main()
