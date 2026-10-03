"""Customer memory: save and load logged-in customers' chats (customer_chat_history table).

Guests are never written here. Product cards are stored as product ids only and rebuilt
from the catalogue when history is loaded, so reloaded cards show today's price and stock.
"""

import json

from db import get_write_db
from models import ChatTurn, HistoryMessage, PageInfo, PageResults
from tools import product_cards

AGENT_HISTORY_TURNS = 10  # how many saved messages the agent gets as context
RELOAD_LIMIT = 50  # how many messages the chat box shows after logging back in


def save_turn(user_id: int, message: str, page: PageInfo, reply: str, product_ids: list[str], page_results: PageResults | None) -> None:
    page_json = json.dumps(page.model_dump())
    results_json = (
        json.dumps({"heading": page_results.heading, "query": page_results.query, "product_ids": [p.id for p in page_results.products]})
        if page_results
        else None
    )
    with get_write_db() as conn:
        conn.execute(
            "INSERT INTO customer_chat_history (user_id, role, content, page_json) VALUES (?, 'user', ?, ?)",
            (user_id, message, page_json),
        )
        conn.execute(
            """INSERT INTO customer_chat_history (user_id, role, content, product_ids_json, page_results_json, page_json)
               VALUES (?, 'assistant', ?, ?, ?, ?)""",
            (user_id, reply, json.dumps(product_ids), results_json, page_json),
        )


def _recent_rows(user_id: int, limit: int):
    with get_write_db() as conn:
        rows = conn.execute(
            "SELECT * FROM customer_chat_history WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)
        ).fetchall()
    return list(reversed(rows))


def agent_history(user_id: int) -> list[ChatTurn]:
    """The customer's last few messages, for the agent's context."""
    return [ChatTurn(role=r["role"], content=r["content"][:4000]) for r in _recent_rows(user_id, AGENT_HISTORY_TURNS)]


def load_history(user_id: int) -> list[HistoryMessage]:
    """The customer's saved chat, with cards rebuilt from the catalogue, for the chat box."""
    out = []
    for r in _recent_rows(user_id, RELOAD_LIMIT):
        page_results = None
        if r["page_results_json"]:
            pr = json.loads(r["page_results_json"])
            cards = product_cards(pr["product_ids"], limit=12)
            if cards:
                page_results = PageResults(heading=pr["heading"], query=pr["query"], products=cards)
        out.append(
            HistoryMessage(
                role=r["role"],
                content=r["content"],
                products=product_cards(json.loads(r["product_ids_json"] or "[]")),
                page_results=page_results,
                created_at=r["created_at"],
            )
        )
    return out


def clear_history(user_id: int) -> None:
    with get_write_db() as conn:
        conn.execute("DELETE FROM customer_chat_history WHERE user_id = ?", (user_id,))
