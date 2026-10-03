"""Access to data/campus_customs.db.

get_db() is read-only (catalogue, inventory; used by the API and every agent tool).
get_write_db() is read-write and only used for accounts, sessions and chat history.
"""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "campus_customs.db"
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    # Opened read-only: nothing in the shop or the chatbot can change the data.
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def to_product(row: sqlite3.Row) -> dict:
    return {
        "id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "tags": json.loads(row["search_tags"]),
        # image_file_path is "products/<file>.jpg"; served from /images/<product_id>
        "image_url": f"/images/{row['product_id']}",
        "price": row["price"],
    }


def fetch_sizes(conn: sqlite3.Connection, product_id: str) -> list[dict]:
    """Sizes and stock for one product, straight from the inventory table, XS→XXL."""
    rows = conn.execute(
        "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
    ).fetchall()
    return sorted(
        ({"size": r["size"], "quantity": r["quantity"]} for r in rows),
        key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else 99,
    )


def all_sizes(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    """Sizes and stock for every product in one query: {product_id: [{size, quantity}, ...]}."""
    out: dict[str, list[dict]] = {}
    for r in conn.execute("SELECT product_id, size, quantity FROM inventory"):
        out.setdefault(r["product_id"], []).append({"size": r["size"], "quantity": r["quantity"]})
    for sizes in out.values():
        sizes.sort(key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else 99)
    return out


PRODUCTS_WITH_STOCK = """
    SELECT c.*, COALESCE(SUM(i.quantity), 0) AS total_stock
    FROM catalogue c LEFT JOIN inventory i ON i.product_id = c.product_id
"""


@contextmanager
def get_write_db() -> Iterator[sqlite3.Connection]:
    """Read-write connection, used ONLY for accounts, sessions and chat history.
    The agent's tools never get this; they stay on the read-only get_db()."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


SCHEMA = """
-- Logged-in customers' chat with Buddy (Problem 8). Guests are never stored.
CREATE TABLE IF NOT EXISTS customer_chat_history (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role              TEXT    NOT NULL CHECK (role IN ('user', 'assistant')),
    content           TEXT    NOT NULL,
    product_ids_json  TEXT,   -- chat mini cards: ["basic-hoodie-big-yale", ...]
    page_results_json TEXT,   -- {"heading", "query", "product_ids"} when Buddy filled the page
    page_json         TEXT,   -- where the shopper was: {"path", "product_id"}
    created_at        TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_customer_chat_history_user ON customer_chat_history (user_id, id);

-- Login sessions. Only a SHA-256 of the token is stored, never the token itself.
CREATE TABLE IF NOT EXISTS user_sessions (
    token_hash TEXT    PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    expires_at TEXT    NOT NULL
);
"""


def init_db() -> None:
    """Create the Problem 8 tables if they don't exist yet (safe to run on every start)."""
    with get_write_db() as conn:
        conn.executescript(SCHEMA)
