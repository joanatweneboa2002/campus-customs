"""Tools the Campus Customs agent can call.

Every tool is read-only, reads straight from data/campus_customs.db, and returns a
typed model from models.py. Each tool also records the prices and stock numbers it
returned in ctx.deps, so agent.py can reject any reply with a made-up number.

Only the catalogue and inventory tables are queried. Nothing here can read the users
table: the only customer info the agent can reach is the logged-in shopper's own name
and email, which the server puts in ctx.deps (see get_my_account).
"""

import json
import re
from typing import Literal

from pydantic_ai import RunContext

from db import PRODUCTS_WITH_STOCK, fetch_sizes, get_db, to_product
from models import (
    LOW_STOCK_MAX,
    AlternativeProduct,
    AlternativesReport,
    CategorySummary,
    ProductCard,
    ProductInfo,
    ProductSummary,
    SearchResults,
    ShopDeps,
    SizeStock,
    StockReport,
    ToolError,
)

MAX_RESULTS = 12  # enough to fill a page of cards on the website
STOPWORDS = {"a", "an", "the", "for", "and", "or", "with", "in", "of", "to", "me", "my", "some", "any", "yale", "shirt"}
# Shoppers say "large" or "2xl"; the inventory table says L / XXL.
SIZE_ALIASES = {
    "extra small": "XS", "x-small": "XS", "xsmall": "XS",
    "small": "S", "medium": "M", "med": "M", "large": "L",
    "extra large": "XL", "x-large": "XL", "xlarge": "XL",
    "xx-large": "XXL", "xxlarge": "XXL", "2xl": "XXL", "2x": "XXL",
}


# Sizes named in a shopper's message. Codes are matched as capital letters ("M", not the
# "m" in "I'm"); words in any case ("medium", "extra large", "2xl").
_SIZE_CODE = re.compile(r"\b(XXS|XS|S|M|L|XL|XXL|2XL)\b")
_SIZE_WORD = re.compile(r"\b(extra[ -]small|x-?small|small|medium|extra[ -]large|x-?large|xx-?large|2xl|large)\b", re.I)


def sizes_mentioned(text: str) -> list[str]:
    found = [normalize_size(m) for m in _SIZE_CODE.findall(text or "")]
    found += [normalize_size(m.replace("-", " ") if m.lower().startswith("extra") else m) for m in _SIZE_WORD.findall(text or "")]
    return list(dict.fromkeys(f for f in found if f in {"XS", "S", "M", "L", "XL", "XXL"}))


def normalize_size(size: str) -> str:
    s = size.strip().lower()
    return SIZE_ALIASES.get(s, s.upper())


def _status(quantity: int) -> str:
    if quantity == 0:
        return "sold_out"
    return "low_stock" if quantity <= LOW_STOCK_MAX else "in_stock"


def _garment_patterns(garment_type: str) -> list[str]:
    """Map a shopper's word to the catalogue's varied garment_type values
    (e.g. "hoodie" must also match "hooded sweatshirt")."""
    g = garment_type.lower()
    if "hood" in g:
        return ["hood"]
    if "zip" in g:
        return ["quarter-zip", "1-4-zip"]
    if "jacket" in g or "fleece" in g:
        return ["jacket", "fleece"]
    if "crew" in g or "sweatshirt" in g or "sweater" in g:
        return ["crew", "mockneck"]
    if "tee" in g or "shirt" in g:
        return ["t-shirt", "performance shirt"]  # not bare "shirt": it would match "sweatshirt"
    return [g]


def _not_found(product_id: str) -> ToolError:
    return ToolError(error=f"No product with id '{product_id}'. Use search_products to find the right product_id.")


# ------------------------------------------------------------------ tools


def search_products(
    ctx: RunContext[ShopDeps],
    query: str = "",
    garment_type: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    min_price: float | None = None,
    size: str | None = None,
    in_stock_only: bool = True,
    sort_by: Literal["relevance", "price_low_to_high", "price_high_to_low"] = "relevance",
) -> SearchResults:
    """Find products in the Campus Customs catalogue. Use this first whenever the shopper
    describes what they want, or names a product and you need its product_id.

    Args:
        query: Free-text keywords, e.g. "branford", "football", "dad", "bulldog". Can be empty.
        garment_type: Optional garment filter, e.g. "hoodie", "crewneck", "t-shirt", "quarter-zip", "jacket".
        color: Optional color filter, e.g. "navy", "gray", "cream".
        max_price: Optional maximum price in dollars.
        min_price: Optional minimum price in dollars.
        size: Optional size the shopper wants, e.g. "M", "large", "XXL". Products are NOT hidden
            when that size is sold out; each result reports requested_size_quantity (0 = sold out),
            and in-stock ones are listed first.
        in_stock_only: Skip products that are sold out in every size (default True).
        sort_by: "price_low_to_high" for cheapest / budget questions, "price_high_to_low" for
            fanciest / most expensive, otherwise "relevance".

    Returns total_matches (how many matched overall) and up to 12 products.
    """
    sql = PRODUCTS_WITH_STOCK
    where, params = [], []
    if garment_type:
        patterns = _garment_patterns(garment_type)
        where.append("(" + " OR ".join(["LOWER(c.garment_type) LIKE ? OR c.product_id LIKE ?"] * len(patterns)) + ")")
        for p in patterns:
            params += [f"%{p}%", f"%{p}%"]
    if color:
        where.append("LOWER(c.colors) LIKE ?")
        params.append(f"%{color.lower()}%")
    if max_price is not None:
        where.append("c.price <= ?")
        params.append(max_price)
    if min_price is not None:
        where.append("c.price >= ?")
        params.append(min_price)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " GROUP BY c.product_id"
    if in_stock_only:
        sql += " HAVING total_stock > 0"

    with get_db() as conn:
        rows = conn.execute(sql, params).fetchall()

    # One-letter words ("T Felt Y") would match every product, so they're skipped.
    terms = [t for t in re.findall(r"[a-z0-9]+", query.lower()) if len(t) > 1 and t not in STOPWORDS]

    def score(row) -> int:
        text = " ".join(
            [row["product_id"], row["name"], row["garment_type"], row["description"], row["colors"], row["search_tags"]]
        ).lower()
        return sum(1 for t in terms if t in text)

    scores = {r["product_id"]: score(r) for r in rows}
    if terms:
        rows = [r for r in rows if scores[r["product_id"]] > 0]

    size_qty: dict[str, int] = {}
    if size:
        with get_db() as conn:
            size_qty = {
                r["product_id"]: r["quantity"]
                for r in conn.execute("SELECT product_id, quantity FROM inventory WHERE UPPER(size) = ?", (normalize_size(size),))
            }

    def sort_key(r):
        size_sold_out = bool(size) and size_qty.get(r["product_id"], 0) == 0
        if sort_by == "price_low_to_high":
            return (size_sold_out, r["price"], r["name"])
        if sort_by == "price_high_to_low":
            return (size_sold_out, -r["price"], r["name"])
        # relevance: best keyword match first; among equals, in stock in the wanted size first
        return (-scores[r["product_id"]], size_sold_out, r["name"])

    rows = sorted(rows, key=sort_key)

    results = []
    for r in rows[:MAX_RESULTS]:
        p = to_product(r)
        results.append(
            ProductSummary(
                product_id=p["id"],
                name=p["name"],
                garment_type=p["garment_type"],
                price=p["price"],
                colors=p["colors"],
                total_stock=r["total_stock"],
                requested_size_quantity=size_qty.get(p["id"], 0) if size else None,
                short_description=p["description"][:160],
            )
        )
        ctx.deps.seen_ids.add(p["id"])
        ctx.deps.prices.add(p["price"])
        ctx.deps.quantities.add(r["total_stock"])
        if size:
            ctx.deps.quantities.add(size_qty.get(p["id"], 0))
    ctx.deps.quantities.add(len(rows))
    return SearchResults(total_matches=len(rows), sorted_by=sort_by, products=results)


def get_product_info(ctx: RunContext[ShopDeps], product_id: str) -> ProductInfo | ToolError:
    """Get a product's full description, price, colors and garment type.
    Use when the shopper asks what something is like, what it costs, or what colors it comes in.
    For sizes or stock, use check_stock instead.

    Args:
        product_id: The exact product_id from search_products, e.g. "basic-hoodie-big-yale".
    """
    with get_db() as conn:
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
    if row is None:
        return _not_found(product_id)
    p = to_product(row)
    ctx.deps.seen_ids.add(p["id"])
    ctx.deps.prices.add(p["price"])
    return ProductInfo(
        product_id=p["id"],
        name=p["name"],
        garment_type=p["garment_type"],
        description=p["description"],
        price=p["price"],
        colors=p["colors"],
    )


def check_stock(
    ctx: RunContext[ShopDeps], product_ids: list[str], size: str | None = None
) -> list[StockReport | ToolError]:
    """Check how many of one or more products are in stock, for every size, straight from the
    inventory table. Use whenever the shopper asks about sizes, availability, or "do you have it in M?".
    Pass every product you will mention or show in one call (up to 12).

    Args:
        product_ids: Exact product_ids from search_products, e.g. ["basic-hoodie-big-yale"].
        size: Optional size the shopper asked about, e.g. "M", "large", "XXL".
    """
    ids = list(dict.fromkeys(product_ids))[:12]
    with get_db() as conn:
        reports = [_stock_report(ctx, conn, pid, size) for pid in ids]
    # A shopper asking about ONE product in a size that's gone: we owe them alternatives.
    # Covers the size passed to this tool AND every size the shopper named in their message
    # ("L and XXL? And is it in M?"), since Buddy may check them all in one call without `size`.
    if len(ids) == 1 and isinstance(reports[0], StockReport):
        r = reports[0]
        wanted = set(sizes_mentioned(ctx.deps.shopper_message))
        if r.requested_size:
            wanted.add(r.requested_size)
        for s in r.sizes:
            if s.size in wanted and s.status == "sold_out":
                ctx.deps.sold_out_requests.add((r.product_id, s.size))
    return reports


def _stock_report(ctx: RunContext[ShopDeps], conn, product_id: str, size: str | None) -> StockReport | ToolError:
    row = conn.execute("SELECT product_id, name, price FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
    if row is None:
        return _not_found(product_id)
    sizes = [SizeStock(size=s["size"], quantity=s["quantity"], status=_status(s["quantity"])) for s in fetch_sizes(conn, product_id)]

    total = sum(s.quantity for s in sizes)
    sold_out = [s.size for s in sizes if s.status == "sold_out"]
    in_stock = [f"{s.size} ({s.quantity})" for s in sizes if s.quantity > 0]

    requested, req_status, lines = None, None, []
    if size:
        requested = normalize_size(size)
        match = next((s for s in sizes if s.size == requested), None)
        if match is None:
            req_status = "not_offered"
            lines.append(f"{row['name']} does not come in size {requested}.")
        else:
            req_status = match.status
            if match.status == "sold_out":
                lines.append(f"Size {requested} is SOLD OUT.")
            elif match.status == "low_stock":
                lines.append(f"Size {requested} is low: only {match.quantity} left.")
            else:
                lines.append(f"Size {requested} is in stock: {match.quantity} left.")
    if total == 0:
        lines.append("Sold out in every size.")
    else:
        lines.append("In stock: " + ", ".join(in_stock) + ".")
        if sold_out:
            lines.append("Sold out: " + ", ".join(sold_out) + ".")

    ctx.deps.stock_checked.add(row["product_id"])
    ctx.deps.seen_ids.add(row["product_id"])
    ctx.deps.prices.add(row["price"])
    ctx.deps.quantities.update(s.quantity for s in sizes)
    ctx.deps.quantities.add(total)
    return StockReport(
        product_id=row["product_id"],
        name=row["name"],
        price=row["price"],
        sizes=sizes,
        total_in_stock=total,
        sold_out_sizes=sold_out,
        requested_size=requested,
        requested_size_status=req_status,
        summary=" ".join(lines),
    )


def find_alternatives(ctx: RunContext[ShopDeps], product_id: str, size: str) -> AlternativesReport | ToolError:
    """When the shopper's size is SOLD OUT (or not offered), find what to offer instead:
    other sizes of the same product that are in stock, and up to 4 similar products that ARE
    in stock in their size. Always call this after check_stock reports a sold-out size.

    Args:
        product_id: The product whose size is sold out.
        size: The size the shopper wants, e.g. "M" or "large".
    """
    wanted = normalize_size(size)
    with get_db() as conn:
        base = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if base is None:
            return _not_found(product_id)
        sizes = fetch_sizes(conn, product_id)
        candidates = conn.execute(
            "SELECT c.*, i.quantity AS qty FROM catalogue c JOIN inventory i ON i.product_id = c.product_id "
            "WHERE UPPER(i.size) = ? AND i.quantity > 0 AND c.product_id != ?",
            (wanted, product_id),
        ).fetchall()

    b = to_product(base)
    b_kinds = set(_garment_patterns(b["garment_type"]))
    b_tags = {t.lower() for t in b["tags"]} - {"yale", "campus customs", "yale merch", "college merch"}
    b_colors = {c.lower() for c in b["colors"]}

    def score(row) -> tuple[float, str]:
        p = to_product(row)
        reasons, pts = [], 0.0
        if b_kinds & set(_garment_patterns(p["garment_type"])) or b_kinds & {k for k in b_kinds if k in p["id"]}:
            pts += 5; reasons.append("same kind of item")
        shared_colors = b_colors & {c.lower() for c in p["colors"]}
        if shared_colors:
            pts += 1.5 * len(shared_colors); reasons.append("also " + "/".join(sorted(shared_colors)[:2]))
        shared_tags = b_tags & {t.lower() for t in p["tags"]}
        if shared_tags:
            pts += min(len(shared_tags), 3); reasons.append("similar style (" + ", ".join(sorted(shared_tags)[:2]) + ")")
        gap = abs(p["price"] - b["price"])
        if gap <= 10:
            pts += 2; reasons.append("similar price")
        pts -= gap / 40  # gently prefer closer prices
        return pts, ", ".join(reasons) or "in stock in your size"

    ranked = sorted(((score(r), r) for r in candidates), key=lambda x: (-x[0][0], x[1]["name"]))
    similar = []
    for (pts, why), r in ranked[:4]:
        p = to_product(r)
        similar.append(
            AlternativeProduct(
                product_id=p["id"], name=p["name"], garment_type=p["garment_type"], price=p["price"],
                colors=p["colors"], quantity_in_size=r["qty"], why_similar=why,
            )
        )
    other_sizes = [SizeStock(size=s["size"], quantity=s["quantity"], status=_status(s["quantity"])) for s in sizes if s["quantity"] > 0]
    match = next((s for s in sizes if s["size"] == wanted), None)
    status = "not_offered" if match is None else _status(match["quantity"])

    lines = [f"{b['name']} in {wanted}: {status.replace('_', ' ')}."]
    if other_sizes:
        lines.append("Same item in stock in: " + ", ".join(f"{s.size} ({s.quantity})" for s in other_sizes) + ".")
    if similar:
        lines.append("Similar items in stock in " + wanted + ": " + "; ".join(f"{a.name} (${a.price:g}, {a.quantity_in_size} left)" for a in similar) + ".")
    else:
        lines.append(f"Nothing similar is in stock in {wanted} right now.")

    # record facts for the validators
    ctx.deps.alternatives[(product_id, wanted)] = [a.product_id for a in similar]
    for a in similar:
        ctx.deps.seen_ids.add(a.product_id); ctx.deps.prices.add(a.price); ctx.deps.quantities.add(a.quantity_in_size)
    ctx.deps.seen_ids.add(product_id); ctx.deps.prices.add(b["price"])
    ctx.deps.quantities.update(s.quantity for s in other_sizes)
    ctx.deps.stock_checked.update([product_id, *(a.product_id for a in similar)])  # stock came straight from inventory
    return AlternativesReport(
        product_id=product_id, name=b["name"], size=wanted, size_status=status,
        other_sizes_in_stock=other_sizes, similar_in_your_size=similar, summary=" ".join(lines),
    )


def get_my_account(ctx: RunContext[ShopDeps]) -> dict:
    """Get the logged-in shopper's OWN account details (name and email).
    Only use when they ask about their own account, e.g. "what email am I logged in with?".
    Never returns anyone else's info; there is no tool for that."""
    c = ctx.deps.customer
    if c is None:
        return {"logged_in": False, "note": "The shopper is a guest (not logged in). There are no account details to share."}
    return {"logged_in": True, "name": c.name, "first_name": c.first_name, "email": c.email}


def list_categories(ctx: RunContext[ShopDeps]) -> list[CategorySummary]:
    """List the garment types the shop carries, with how many products and the price range of each.
    Use when the shopper asks what we sell or wants to browse."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT garment_type, COUNT(*) AS n, MIN(price) AS lo, MAX(price) AS hi "
            "FROM catalogue GROUP BY LOWER(garment_type) ORDER BY n DESC"
        ).fetchall()
    out = [CategorySummary(garment_type=r["garment_type"], products=r["n"], min_price=r["lo"], max_price=r["hi"]) for r in rows]
    for c in out:
        ctx.deps.prices.update((c.min_price, c.max_price))
        ctx.deps.quantities.add(c.products)
    return out


AGENT_TOOLS = [search_products, get_product_info, check_stock, find_alternatives, list_categories, get_my_account]


# ------------------------------------------------- website (not an agent tool)


def product_cards(product_ids: list[str], limit: int = 4) -> list[ProductCard]:
    """Build product cards from the database for ids the agent picked, in the agent's order.

    Unknown ids are dropped, so the website only ever shows real products.
    """
    ids = list(dict.fromkeys(product_ids))[:limit]
    if not ids:
        return []
    marks = ",".join("?" * len(ids))
    with get_db() as conn:
        rows = conn.execute(
            f"{PRODUCTS_WITH_STOCK} WHERE c.product_id IN ({marks}) GROUP BY c.product_id", ids
        ).fetchall()
        sizes = {pid: fetch_sizes(conn, pid) for pid in ids}
    by_id = {r["product_id"]: r for r in rows}
    return [
        ProductCard(
            id=pid,
            name=by_id[pid]["name"],
            price=by_id[pid]["price"],
            garment_type=by_id[pid]["garment_type"],
            description=by_id[pid]["description"],
            colors=json.loads(by_id[pid]["colors"]),
            image_url=f"/images/{pid}",
            url=f"/products/{pid}",
            total_stock=by_id[pid]["total_stock"],
            sizes=sizes[pid],
        )
        for pid in ids
        if pid in by_id
    ]
