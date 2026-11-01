"""Tools the agent can call: product search and price/availability lookup.

Design notes
- Tools return plain, JSON-serialisable dicts so the LLM can read them directly.
- Business rules from the store manual live here, not in the prompt, so they
  hold even if the model forgets: only *active* promotions count, a promotional
  price is always shown next to the list price, and the 5% PIX discount is not
  stacked on top of promotional prices.
- Availability is explicit (available / out_of_stock / discontinued /
  coming_soon) so the agent never has to guess from raw numbers.
"""
from __future__ import annotations

import difflib
import re
import unicodedata
from typing import Optional

import pandas as pd

from .data import load_all

PIX_DISCOUNT = 0.05  # manual, section 3: 5% off list price, not on promotional prices


# --------------------------------------------------------------------------- #
# Text normalisation (accents, case, plurals) so "violões", "violao" and
# "Violões" all match.
# --------------------------------------------------------------------------- #
def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def _stem(token: str) -> str:
    if token.endswith("oes") or token.endswith("aes"):
        return token[:-3] + "ao"  # violoes -> violao
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]  # guitarras -> guitarra
    return token


def _tokens(text: str) -> list[str]:
    cleaned = re.sub(r"[^a-z0-9]+", " ", _strip_accents(str(text).lower()))
    return [_stem(t) for t in cleaned.split()]


def _norm(text: str) -> str:
    return " ".join(_tokens(text))


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #
def _availability(row: pd.Series) -> str:
    if row["status"] == "discontinued":
        return "discontinued"
    if row["status"] == "coming_soon":
        return "coming_soon"
    return "available" if row["stock_quantity"] > 0 else "out_of_stock"


def _final_price(row: pd.Series) -> float:
    if pd.notna(row["promo_price_brl"]):
        return float(row["promo_price_brl"])
    return float(row["price_brl"])


def _has_expired_promotion(product_id: int) -> bool:
    """True if the product had promotions in the past but none is active now."""
    promos = load_all()["promotions"]
    mine = promos[promos["product_id"] == product_id]
    return len(mine) > 0 and not bool(mine["is_active"].any())


def _serialise(row: pd.Series) -> dict:
    has_promo = pd.notna(row["discount_percent"])
    final = _final_price(row)
    return {
        "product_id": int(row["product_id"]),
        "name": row["name"],
        "category": row["category"],
        "description": row["description"],
        "list_price_brl": float(row["price_brl"]),
        "promotion": (
            {
                "discount_percent": float(row["discount_percent"]),
                "promo_price_brl": float(row["promo_price_brl"]),
                "name": row["promo_description"],
            }
            if has_promo
            else None
        ),
        "final_price_brl": round(final, 2),
        # Manual 6.2: PIX discount does not apply to already-promotional prices.
        "pix_price_brl": None if has_promo else round(final * (1 - PIX_DISCOUNT), 2),
        "expired_promotion": (not has_promo) and _has_expired_promotion(int(row["product_id"])),
        "availability": _availability(row),
        "stock_quantity": int(row["stock_quantity"]),
        "specs": row["specs"],
    }


def _matches(row_text_tokens: set[str], query_tokens: list[str]) -> bool:
    return all(t in row_text_tokens for t in query_tokens)


def _alternatives(row: pd.Series, limit: int = 3) -> list[dict]:
    """Available products in the same category with a similar price."""
    products = load_all()["products"]
    ref = _final_price(row)
    pool = products[
        (products["category"] == row["category"])
        & (products["product_id"] != row["product_id"])
        & (products["status"] == "active")
        & (products["stock_quantity"] > 0)
    ].copy()
    pool["final_price"] = pool.apply(_final_price, axis=1)
    pool["gap"] = (pool["final_price"] - ref).abs()
    out = []
    for _, r in pool.sort_values("gap").head(limit).iterrows():
        out.append({"product_id": int(r["product_id"]), "name": r["name"],
                    "final_price_brl": round(float(r["final_price"]), 2)})
    return out


# --------------------------------------------------------------------------- #
# Public tools (these are what the LLM sees: keep docstrings precise)
# --------------------------------------------------------------------------- #
def search_products(
    query: Optional[str] = None,
    category: Optional[str] = None,
    max_price_brl: Optional[float] = None,
    min_price_brl: Optional[float] = None,
    include_unavailable: bool = False,
    limit: int = 10,
) -> dict:
    """Search the store catalogue.

    Use this for questions like "which acoustic guitars do you have up to R$1000?".
    All filters are optional and combined with AND. Price filters apply to the
    FINAL price (the promotional price when an active promotion exists).

    Args:
        query: Free text matched against product name, category and description
            (e.g. "yamaha nylon", "ukulele tenor").
        category: Category name such as "Violões", "Guitarras", "Baixos",
            "Ukuleles", "Teclados e Pianos", "Baterias e Percussão".
        max_price_brl: Maximum final price in BRL.
        min_price_brl: Minimum final price in BRL.
        include_unavailable: If False (default), only products that can be bought now.
        limit: Maximum number of results (default 10).

    Returns:
        A dict with "total_matches", "returned" and "products" (cheapest first).
        Each product has list price, promotion (or null), final price,
        availability and specs.
    """
    products = load_all()["products"]
    q_tokens = _tokens(query) if query else []
    c_tokens = _tokens(category) if category else []

    results = []
    for _, row in products.iterrows():
        text = set(_tokens(f"{row['name']} {row['category']} {row['description']}"))
        if q_tokens and not _matches(text, q_tokens):
            continue
        if c_tokens and not _matches(set(_tokens(row["category"])), c_tokens):
            continue
        final = _final_price(row)
        if max_price_brl is not None and final > max_price_brl:
            continue
        if min_price_brl is not None and final < min_price_brl:
            continue
        if not include_unavailable and _availability(row) != "available":
            continue
        results.append((final, row))

    results.sort(key=lambda x: x[0])
    limit = max(1, min(int(limit), 25))
    return {
        "total_matches": len(results),
        "returned": min(len(results), limit),
        "products": [_serialise(r) for _, r in results[:limit]],
    }


def get_product_details(name: str) -> dict:
    """Look up ONE specific product by name and return price, promotion and stock.

    Use this for questions like "how much is the Takamine GD20?" or "do you have
    the Yamaha C40 in stock?". Never state a price or availability without
    calling this (or search_products) first.

    Args:
        name: Product name or a distinctive part of it (e.g. "Takamine GD20").

    Returns:
        - {"status": "found", "product": {...}} for a single match. If the product
          cannot be bought now, it also includes "alternatives".
        - {"status": "ambiguous", "candidates": [...]} when several products match;
          ask the customer which one they mean.
        - {"status": "not_found", "suggestions": [...]} otherwise.
    """
    products = load_all()["products"]
    q_tokens = _tokens(name)
    if not q_tokens:
        return {"status": "not_found", "suggestions": []}

    matches = [
        row for _, row in products.iterrows()
        if _matches(set(_tokens(row["name"])), q_tokens)
    ]

    if not matches:
        names = {_norm(n): n for n in products["name"]}
        close = difflib.get_close_matches(_norm(name), list(names), n=3, cutoff=0.5)
        return {"status": "not_found", "suggestions": [names[c] for c in close]}

    if len(matches) > 1:
        exact = [m for m in matches if _norm(m["name"]) == _norm(name)]
        if len(exact) == 1:
            matches = exact
        else:
            return {
                "status": "ambiguous",
                "candidates": [
                    {"product_id": int(m["product_id"]), "name": m["name"],
                     "final_price_brl": round(_final_price(m), 2)}
                    for m in matches[:8]
                ],
            }

    row = matches[0]
    out = {"status": "found", "product": _serialise(row)}
    if _availability(row) != "available":
        out["alternatives"] = _alternatives(row)
    return out