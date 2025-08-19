import sqlite3
from utils import get_connection, find_violations


def main():
    conn = get_connection("quotes.db")
    bad = find_violations(conn)
    if not bad:
        print("All quotes satisfy length <= 25.")
    return
    print(f"{len(bad)} violating row(s):")
    for _id, q in bad:
        print(f"- id={_id}, len={len(q)}: {q!r}")


if __name__ == "__main__":
    main()