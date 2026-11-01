"""Data layer: loads and cleans the store CSVs.

All tools read from here, so cleaning rules live in one place.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _read(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / f"{name}.csv", encoding="utf-8-sig")


def _parse_specs(raw: str) -> dict:
    """`specs` is a JSON string; fall back to an empty dict if malformed."""
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {}


def _digits(phone: str) -> str:
    return re.sub(r"\D", "", str(phone))


@lru_cache(maxsize=1)
def load_all() -> dict[str, pd.DataFrame]:
    categories = _read("categories")

    promotions = _read("promotions")
    promotions["is_active"] = promotions["is_active"].astype(bool)
    # A product may have several promotions in the file; keep only active ones,
    # and if more than one is active, the highest discount wins.
    active = (
        promotions[promotions["is_active"]]
        .sort_values("discount_percent", ascending=False)
        .drop_duplicates("product_id")
        .rename(columns={"description": "promo_description"})
        [["product_id", "discount_percent", "promo_description"]]
    )

    products = _read("products")
    products["specs"] = products["specs"].apply(_parse_specs)
    products["created_at"] = pd.to_datetime(products["created_at"])
    products = products.merge(
        categories[["category_id", "name"]].rename(columns={"name": "category"}),
        on="category_id",
        how="left",
    ).merge(active, on="product_id", how="left")
    products["promo_price_brl"] = (
        products["price_brl"] * (1 - products["discount_percent"] / 100)
    ).round(2)

    customers = _read("customers")
    customers["phone_digits"] = customers["phone"].map(_digits)

    orders = _read("orders")
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    orders["estimated_delivery"] = pd.to_datetime(orders["estimated_delivery"])

    return {
        "categories": categories,
        "promotions": promotions,
        "products": products,
        "customers": customers,
        "orders": orders,
        "order_items": _read("order_items"),
    }
