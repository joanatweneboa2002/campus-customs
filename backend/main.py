"""Campus Customs API: product catalogue, product images, and Buddy the chat agent.

Run from backend/:  uvicorn main:app --reload --port 8000
API docs:           http://127.0.0.1:8000/docs
Website (Vite):     http://localhost:5173  (proxies /api and /images here)
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import agent
import auth
import memory
from db import DATA_DIR, PRODUCTS_WITH_STOCK, all_sizes, fetch_sizes, get_db, init_db, to_product
from models import (
    AuthResponse,
    ChatReply,
    ChatRequest,
    HistoryMessage,
    LoginRequest,
    PublicUser,
    SignupRequest,
)

IMAGE_DIR = DATA_DIR / "products"
# Cleaned, cut-out WebPs made by clean_images.py; used when present.
CLEAN_IMAGE_DIR = DATA_DIR / "products_web"

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()  # creates customer_chat_history + user_sessions if missing
    yield


app = FastAPI(title="Campus Customs API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "model": agent.MODEL_NAME}


@app.get("/api/products")
def list_products() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(f"{PRODUCTS_WITH_STOCK} GROUP BY c.product_id ORDER BY c.name").fetchall()
        sizes = all_sizes(conn)
    # sizes per product so cards can show "Low stock" / "Sold out" before anyone clicks
    return [{**to_product(r), "total_stock": r["total_stock"], "sizes": sizes.get(r["product_id"], [])} for r in rows]


@app.get("/images/{product_id}")
def product_image(product_id: str) -> FileResponse:
    with get_db() as conn:
        row = conn.execute(
            "SELECT image_file_path FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Image not found")

    original = IMAGE_DIR / Path(row["image_file_path"]).name
    cleaned = CLEAN_IMAGE_DIR / f"{original.stem}.webp"
    path = cleaned if cleaned.exists() else original
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    # no-cache: browser revalidates, so re-cleaned photos show up right away
    return FileResponse(path, headers={"Cache-Control": "no-cache"})


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        product = to_product(row)
        product["sizes"] = fetch_sizes(conn, product_id)
    return product


@app.get("/api/products/{product_id}/inventory")
def get_inventory(product_id: str) -> list[dict]:
    """Sizes and stock for one product, straight from the inventory table."""
    with get_db() as conn:
        return fetch_sizes(conn, product_id)


# ------------------------------------------------------------------ accounts


@app.post("/api/auth/login", response_model=AuthResponse)
def login(body: LoginRequest) -> AuthResponse:
    token, user = auth.login(body.email, body.password)
    return AuthResponse(token=token, user=user)


@app.post("/api/auth/signup", response_model=AuthResponse)
def signup(body: SignupRequest) -> AuthResponse:
    token, user = auth.signup(body.first_name, body.last_name, body.email, body.password)
    return AuthResponse(token=token, user=user)


@app.get("/api/auth/me", response_model=PublicUser)
def me(user: PublicUser = Depends(auth.required_user)) -> PublicUser:
    return user


@app.post("/api/auth/logout")
def logout(authorization: str | None = Header(default=None)) -> dict:
    if token := auth.bearer_token(authorization):
        auth.logout(token)
    return {"ok": True}


# ---------------------------------------------------------------------- chat


@app.post("/api/chat", response_model=ChatReply)
async def chat(body: ChatRequest, user: PublicUser | None = Depends(auth.optional_user)) -> ChatReply:
    """One chat turn with Buddy.

    Guests: context comes from the history the browser sends; nothing is stored.
    Logged in: context comes from the customer's saved history, and the turn is saved.
    """
    if user is None:
        return await agent.chat(body.message, body.history, body.page)

    reply = await agent.chat(body.message, memory.agent_history(user.id), body.page, auth.customer_info(user))
    if reply.reply != agent.FALLBACK_REPLY:  # don't save failed turns
        memory.save_turn(user.id, body.message, body.page, reply.reply, [p.id for p in reply.products], reply.page_results)
        reply.saved = True
    return reply


@app.get("/api/chat/history", response_model=list[HistoryMessage])
def chat_history(user: PublicUser = Depends(auth.required_user)) -> list[HistoryMessage]:
    """The logged-in customer's saved chat, oldest first (shown when they log back in)."""
    return memory.load_history(user.id)


@app.delete("/api/chat/history")
def clear_chat_history(user: PublicUser = Depends(auth.required_user)) -> dict:
    memory.clear_history(user.id)
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
