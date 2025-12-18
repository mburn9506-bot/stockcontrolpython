import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash

DB_PATH = Path("stock.db")

app = Flask(__name__)
app.secret_key = "change-me"  # For flash messages

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not DB_PATH.exists():
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                quantity INTEGER NOT NULL DEFAULT 0,
                min_quantity INTEGER NOT NULL DEFAULT 0
            );
        """)
        # Seed sample data
        cur.executemany("""
            INSERT INTO items (name, quantity, min_quantity)
            VALUES (?, ?, ?)
        """, [
            ("Apples", 12, 10),
            ("Bananas", 5, 8),
            ("Oranges", 0, 6),
            ("Grapes", 30, 15),
        ])
        conn.commit()
        conn.close()

@app.route("/", methods=["GET"])
def index():
    conn = get_conn()
    items = conn.execute("SELECT * FROM items ORDER BY name").fetchall()
    low_count = conn.execute(
        "SELECT COUNT(*) AS c FROM items WHERE quantity < min_quantity"
    ).fetchone()["c"]
    conn.close()
    return render_template("index.html", items=items, low_count=low_count)

@app.route("/add", methods=["POST"])
def add_item():
    name = request.form.get("name", "").strip()
    qty = request.form.get("quantity", "0").strip()
    min_qty = request.form.get("min_quantity", "0").strip()
    if not name:
        flash("Name is required", "error")
        return redirect(url_for("index"))
    try:
        qty = int(qty)
        min_qty = int(min_qty)
    except ValueError:
        flash("Quantity and minimum must be integers", "error")
        return redirect(url_for("index"))

    try:
        conn = get_conn()
        conn.execute(
            "INSERT INTO items (name, quantity, min_quantity) VALUES (?, ?, ?)",
            (name, qty, min_qty),
        )
        conn.commit()
        conn.close()
        flash(f"Added item: {name}", "success")
    except sqlite3.IntegrityError:
        flash("Item name must be unique", "error")
    return redirect(url_for("index"))

@app.route("/update/<int:item_id>", methods=["POST"])
def update_item(item_id):
    qty = request.form.get("quantity", "").strip()
    min_qty = request.form.get("min_quantity", "").strip()
    try:
        qty = int(qty)
        min_qty = int(min_qty)
    except ValueError:
        flash("Quantity and minimum must be integers", "error")
        return redirect(url_for("index"))

    conn = get_conn()
    conn.execute(
        "UPDATE items SET quantity = ?, min_quantity = ? WHERE id = ?",
        (qty, min_qty, item_id),
    )
    conn.commit()
    conn.close()
    flash("Item updated", "success")
    return redirect(url_for("index"))

@app.route("/delete/<int:item_id>", methods=["POST"])
def delete_item(item_id):
    conn = get_conn()
    conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    flash("Item deleted", "success")
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)