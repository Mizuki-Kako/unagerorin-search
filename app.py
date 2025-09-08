from flask import Flask, request, render_template
import sqlite3

DB_NAME = "unagerorin.db"
app = Flask(__name__)

def search_db(keyword, order):
    conn = sqlite3.connect('unagero.db')
    cur = conn.cursor()

    if order == "relevance":
        query = """
            SELECT e.title, e.description, e.pub_date, e.link, bm25(episodes_fts) as score
            FROM episodes_fts
            JOIN episodes e ON episodes_fts.rowid = e.id
            WHERE episodes_fts MATCH ?
            ORDER BY score ASC
        """
        params = (keyword,)
    else:
        # 並び順
        order_by = "DESC" if order == "newest" else "ASC"
        query = """
            SELECT title, description, pub_date, link, NULL as score
            FROM episodes
            WHERE title LIKE ? OR description LIKE ?
            ORDER BY pub_date {}
        """.format(order_by)
        params = (f"%{keyword}%", f"%{keyword}%")

    cur.execute(query, params)
    results = cur.fetchall()
    conn.close()
    return results

@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    keyword = ""
    order = "relevance"

    if request.method == "POST":
        keyword = request.form.get("keyword", "")
        order = request.form.get("order", "relevance")
        if keyword:
            results = search_db(keyword, order)

    return render_template("index.html", keyword=keyword, order=order, results=results)

if __name__ == "__main__":
    app.run(debug=True)
