import sqlite3
import feedparser
from datetime import datetime

# RSSフィードURL
RSS_URL = "https://feeds.megaphone.fm/unagerorin"
DB_FILE = "unagero.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    # テーブル作成
    cur.execute("""
        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            pub_date TEXT,
            link TEXT
        )
    """)
    # 既存テーブルにlinkカラムがなければ追加
    cur.execute("PRAGMA table_info(episodes)")
    columns = [row[1] for row in cur.fetchall()]
    if "link" not in columns:
        cur.execute("ALTER TABLE episodes ADD COLUMN link TEXT")

    # FTS5仮想テーブル作成
    cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS episodes_fts USING fts5(title, description, content='episodes', content_rowid='id')
    """)
    # episodes→episodes_ftsへ同期（差分のみ）
    cur.execute("SELECT id, title, description FROM episodes")
    for row in cur.fetchall():
        cur.execute("INSERT OR IGNORE INTO episodes_fts(rowid, title, description) VALUES (?, ?, ?)", (row[0], row[1], row[2]))

    conn.commit()
    conn.close()

def fetch_and_store():
    feed = feedparser.parse(RSS_URL)
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    count_inserted = 0
    for entry in feed.entries:
        title = entry.title if "title" in entry else ""
        description = entry.get("description", "")
        pub_date = entry.get("published", "")
        link = entry.get("link", "")

        # pubDate があるなら ISO 形式に整形
        if pub_date:
            try:
                pub_date = datetime(*entry.published_parsed[:6]).isoformat()
            except Exception:
                pass

        # 重複チェック（タイトルと日付で一意）
        cur.execute("SELECT id FROM episodes WHERE title=? AND pub_date=?", (title, pub_date))
        if cur.fetchone() is None:
            cur.execute("INSERT INTO episodes (title, description, pub_date, link) VALUES (?, ?, ?, ?)",
                        (title, description, pub_date, link))
            count_inserted += 1

    conn.commit()
    conn.close()
    print(f"{count_inserted} 件のエピソードを追加しました。")
    print("エントリー数:", len(feed.entries))
    for i, entry in enumerate(feed.entries[:5]):
        print(i, entry.title if "title" in entry else "No title")

if __name__ == "__main__":
    init_db()
    fetch_and_store()
