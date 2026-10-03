"""Types for the chat API, the agent's tool results, and the product cards."""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field, model_validator

# ---------------------------------------------------------------- chat API


class ChatTurn(BaseModel):
    """One earlier message in the conversation, sent back by the website for context."""

    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class PageInfo(BaseModel):
    """Where the shopper is on the website, sent with every chat message."""

    path: str = Field(default="/", max_length=200, description="Current URL path + query, e.g. /products/basic-hoodie-big-yale")
    product_id: str | None = Field(default=None, max_length=120, description="Set on a product detail page")


class ChatRequest(BaseModel):
    """Body of POST /api/chat.

    `history` is only used for guests. For logged-in customers the server loads
    history from the customer_chat_history table instead (the source of truth).
    """

    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=20)
    page: PageInfo = Field(default_factory=PageInfo)


class ProductCard(BaseModel):
    """A product the chat box shows as a clickable mini card."""

    id: str
    name: str
    price: float
    garment_type: str
    description: str
    colors: list[str]
    image_url: str
    url: str  # site route for the product detail page
    total_stock: int
    sizes: list[dict] = Field(default_factory=list)  # [{size, quantity}] for the card's stock badges


class PageResultsRequest(BaseModel):
    """Part of the agent's output: products to lay out as cards on the website page."""

    heading: str = Field(max_length=60, description="Short, friendly title for the results, e.g. 'Hoodies for game day'.")
    product_ids: list[str] = Field(
        max_length=12,
        description="Exact product_ids from this turn's search_products results, best first (up to 12).",
    )


class AgentOutput(BaseModel):
    """Structured output the agent must produce on every turn."""

    reply: str = Field(description="Your chat message to the shopper, in Buddy's voice. Plain text, short.")
    product_ids: list[str] = Field(
        default_factory=list,
        max_length=4,
        description=(
            "Exact product_id values (from tool results) of up to 4 products to show as cards "
            "under your reply. Leave empty when no product is relevant."
        ),
    )
    page_results: PageResultsRequest | None = Field(
        default=None,
        description=(
            "Set when the shopper is browsing or searching (e.g. 'what hoodies do you have?', "
            "'show me gray tees'): the website shows these products as cards on the page. "
            "Leave null for small talk, single-product questions, or when nothing matched."
        ),
    )


class PageResults(BaseModel):
    """Search results for the website page, built from the database."""

    heading: str
    query: str  # the shopper's message, shown as "you asked: ..."
    products: list[ProductCard]


class ChatReply(BaseModel):
    """Response of POST /api/chat: Buddy's message, chat mini cards, and optional page results."""

    reply: str
    products: list[ProductCard] = Field(default_factory=list)
    page_results: PageResults | None = None
    saved: bool = False  # True when the turn was stored in the customer's history


class HistoryMessage(BaseModel):
    """One saved message, as returned by GET /api/chat/history."""

    role: Literal["user", "assistant"]
    content: str
    products: list[ProductCard] = Field(default_factory=list)
    page_results: PageResults | None = None
    created_at: str


# ------------------------------------------------------------- accounts


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=1, max_length=200)


class SignupRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    email: str = Field(min_length=3, max_length=200, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=200)
    confirm_password: str = Field(max_length=200)

    @model_validator(mode="after")
    def passwords_match(self) -> "SignupRequest":
        # checked on the server too, not just in the browser
        if self.password != self.confirm_password:
            raise ValueError("Passwords don't match")
        return self


class PublicUser(BaseModel):
    """What the website gets back about the logged-in customer (never the password hash)."""

    id: int
    name: str
    first_name: str
    email: str


class AuthResponse(BaseModel):
    token: str
    user: PublicUser


# ------------------------------------------------------- tool return types

StockStatus = Literal["in_stock", "low_stock", "sold_out"]
LOW_STOCK_MAX = 3  # 1-3 left counts as low stock (matches "Only N left. Run!" on the site)


class ProductSummary(BaseModel):
    """One search hit: enough to recommend a product without a second lookup."""

    product_id: str
    name: str
    garment_type: str
    price: float = Field(description="Price in US dollars, exactly as stored in the catalogue.")
    colors: list[str]
    total_stock: int = Field(description="Units on hand across all sizes.")
    requested_size_quantity: int | None = Field(
        default=None, description="Units in the size the shopper asked for (0 = sold out in that size)."
    )
    short_description: str


class SearchResults(BaseModel):
    """What search_products returns."""

    total_matches: int = Field(description="How many products matched in total. May be more than are shown.")
    sorted_by: str
    products: list[ProductSummary]


class ProductInfo(BaseModel):
    """Everything the catalogue says about one product (no stock; use check_stock for that)."""

    product_id: str
    name: str
    garment_type: str
    description: str
    price: float = Field(description="Price in US dollars, exactly as stored in the catalogue.")
    colors: list[str]


class SizeStock(BaseModel):
    size: str
    quantity: int = Field(description="Units on hand for this size, straight from the inventory table.")
    status: StockStatus


class StockReport(BaseModel):
    """Stock for one product, by size, from the inventory table."""

    product_id: str
    name: str
    price: float
    sizes: list[SizeStock] = Field(description="Every size the product comes in, XS to XXL.")
    total_in_stock: int
    sold_out_sizes: list[str]
    requested_size: str | None = None
    requested_size_status: StockStatus | Literal["not_offered"] | None = None
    summary: str = Field(description="A plain-English line you can rely on, e.g. 'Size M is SOLD OUT.'")


class AlternativeProduct(BaseModel):
    """A similar product that IS in stock in the size the shopper wants."""

    product_id: str
    name: str
    garment_type: str
    price: float
    colors: list[str]
    quantity_in_size: int = Field(description="Units on hand in the requested size (always > 0).")
    why_similar: str = Field(description="Short reason, e.g. 'same kind of item, also navy, similar price'.")


class AlternativesReport(BaseModel):
    """What find_alternatives returns for a sold-out size."""

    product_id: str
    name: str
    size: str
    size_status: str = Field(description="sold_out, low_stock, in_stock or not_offered for the original product.")
    other_sizes_in_stock: list[SizeStock] = Field(description="Sizes of the SAME product that are still available.")
    similar_in_your_size: list[AlternativeProduct] = Field(description="Up to 4 similar products in stock in that size, best first.")
    summary: str


class CategorySummary(BaseModel):
    garment_type: str
    products: int
    min_price: float
    max_price: float


class ToolError(BaseModel):
    """Returned instead of data when a lookup fails (e.g. unknown product_id)."""

    error: str


# --------------------------------------------------------- per-run facts


@dataclass
class CustomerInfo:
    """The logged-in customer, passed to the agent in deps. Only ever *this* customer."""

    user_id: int
    name: str
    first_name: str
    email: str


@dataclass
class PageContext:
    """Where the shopper is, resolved on the server (product names come from the DB, not the browser)."""

    path: str
    kind: Literal["home", "products", "buddy_picks", "product", "about", "login", "signup", "other"]
    product_id: str | None = None
    product_name: str | None = None
    category: str | None = None


@dataclass
class ShopDeps:
    """Per-chat-turn state passed to every tool (PydanticAI deps).

    `customer` and `page` tell the agent who it's talking to and what they're looking at.
    Tools record every price and stock number they return, and check_stock records
    which products it looked up, so the output validators in agent.py can reject a
    reply with a made-up number or a size answer that skipped the stock check.
    """

    customer: CustomerInfo | None = None  # None = guest
    page: PageContext | None = None
    security_flags: list[str] = field(default_factory=list)  # manipulation spotted in the latest message
    shopper_message: str = ""
    shopper_numbers: set[float] = field(default_factory=set)
    prices: set[float] = field(default_factory=set)
    quantities: set[int] = field(default_factory=set)
    stock_checked: set[str] = field(default_factory=set)
    seen_ids: set[str] = field(default_factory=set)  # every product_id a tool returned this turn
    # (product_id, size) the shopper asked about that check_stock found SOLD OUT -> must offer alternatives
    sold_out_requests: set[tuple[str, str]] = field(default_factory=set)
    # (product_id, size) -> alternative product ids find_alternatives returned
    alternatives: dict[tuple[str, str], list[str]] = field(default_factory=dict)
