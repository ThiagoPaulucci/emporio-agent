
"""Order lookup tool with identity verification.
 
Why a separate module: order data is personal data (LGPD, manual section 9),
so it gets its own rules, kept apart from the public product catalogue.
 
Privacy rules implemented here
- An order is only disclosed if BOTH the order number and the e-mail on the
  customer's account match.
- A wrong order number and a wrong e-mail return the *same* answer, so the
  tool never reveals whether an order exists.
- Only what the customer needs is returned: no phone, no e-mail, no other
  orders, and only the customer's first name.
 
Assumptions (documented in the README)
- The data has no actual delivery date, so for delivered orders the
  `estimated_delivery` date is treated as the date of receipt.
- All orders are treated as online purchases, so the 7-day right of
  withdrawal (manual 4.1) applies.
- "Today" is the real date, unless the EMPORIO_TODAY environment variable
  (YYYY-MM-DD) is set. That makes demos and tests reproducible.
"""
from __future__ import annotations
 
import os
from datetime import date
from typing import Optional
 
import pandas as pd
 
from .data import load_all
 
REGRET_WINDOW_DAYS = 7  # manual 4.1: right of withdrawal, counted from receipt
PREFERENCE_EXCHANGE_WINDOW_DAYS = 7  # manual 4.3: exchange by preference (assumed from receipt)
DEFECT_EXCHANGE_WINDOW_DAYS = 30  # manual 4.2: defect exchange, counted from the PURCHASE
LEGAL_WARRANTY_DAYS = 90  # manual 8.1: legal warranty, counted from receipt
 
_VERIFICATION_FAILED = {
    "status": "verification_failed",
    "message": (
        "No order matches this order number and e-mail. Ask the customer to "
        "double-check both. Do not say which of the two is wrong."
    ),
}
 
 
def _today() -> date:
    raw = os.getenv("EMPORIO_TODAY")
    return date.fromisoformat(raw) if raw else date.today()
 
 
def _iso(value) -> Optional[str]:
    return None if pd.isna(value) else pd.Timestamp(value).date().isoformat()
 
 
def _return_info(order_date, estimated_delivery, today: date) -> dict:
    receipt = pd.Timestamp(estimated_delivery).date()
    purchase = pd.Timestamp(order_date).date()
    since_receipt = max((today - receipt).days, 0)
    since_purchase = max((today - purchase).days, 0)
    return {
        "purchase_date": purchase.isoformat(),
        "receipt_date_assumed": receipt.isoformat(),
        "days_since_purchase": since_purchase,
        "days_since_receipt": since_receipt,
        # 4.1 and 4.3 count from receipt; 4.2 counts from the purchase; 8.1 from receipt.
        "within_regret_window": since_receipt <= REGRET_WINDOW_DAYS,
        "within_preference_exchange_window": since_receipt <= PREFERENCE_EXCHANGE_WINDOW_DAYS,
        "within_defect_exchange_window": since_purchase <= DEFECT_EXCHANGE_WINDOW_DAYS,
        "within_legal_warranty": since_receipt <= LEGAL_WARRANTY_DAYS,
        "note": (
            "Receipt date is assumed to be the estimated delivery date "
            "(no actual delivery date in the data). Defect exchange (30 days) "
            "counts from the purchase date, as written in the manual."
        ),
    }
 
 
def _lookup_order(order_id, customer_email: str, today: date) -> dict:
    data = load_all()
    try:
        order_id = int(order_id)
    except (TypeError, ValueError):
        return dict(_VERIFICATION_FAILED)
 
    email = str(customer_email or "").strip().lower()
    orders = data["orders"]
    order_rows = orders[orders["order_id"] == order_id]
    if order_rows.empty or not email:
        return dict(_VERIFICATION_FAILED)
 
    order = order_rows.iloc[0]
    customers = data["customers"]
    customer = customers[customers["customer_id"] == order["customer_id"]].iloc[0]
    if str(customer["email"]).strip().lower() != email:
        return dict(_VERIFICATION_FAILED)
 
    items = data["order_items"]
    items = items[items["order_id"] == order_id].merge(
        data["products"][["product_id", "name"]], on="product_id", how="left"
    )
 
    result = {
        "order_id": order_id,
        "order_date": _iso(order["order_date"]),
        "status": order["status"],
        "total_brl": float(order["total_brl"]),
        "payment_method": order["payment_method"],
        "items": [
            {"product_id": int(r["product_id"]), "name": r["name"], "quantity": int(r["quantity"])}
            for _, r in items.iterrows()
        ],
        "tracking_code": None if pd.isna(order["tracking_code"]) else order["tracking_code"],
        "estimated_delivery": _iso(order["estimated_delivery"]),
        "cancellation_reason": None
        if order["status"] != "cancelled" or pd.isna(order["notes"])
        else order["notes"],
    }
    if order["status"] == "delivered" and pd.notna(order["estimated_delivery"]):
        result["return_info"] = _return_info(
            order["order_date"], order["estimated_delivery"], today
        )
 
    first_name = str(customer["name"]).split()[0]
    return {"status": "found", "customer_first_name": first_name, "order": result}
 
 
def get_order_status(order_id: int, customer_email: str) -> dict:
    """Look up the status of a customer's order. Requires identity verification.
 
    Use this when the customer asks about an order: status, tracking code,
    delivery estimate, items, cancellation, or whether a return is still
    possible. You MUST ask the customer for BOTH the order number and the
    e-mail address on the account before calling. Never guess or try other
    values, and never reveal any order data if verification fails.
 
    Args:
        order_id: The order number given by the customer.
        customer_email: The e-mail address registered on the customer's account.
 
    Returns:
        - {"status": "found", "customer_first_name": ..., "order": {...}} when
          both values match. For delivered orders, "order.return_info" tells
          whether the 7-day withdrawal window, the 7-day preference-exchange
          window, the 30-day defect-exchange window (from purchase) and the
          90-day legal warranty (from receipt) are still open.
        - {"status": "verification_failed", ...} otherwise. Ask the customer to
          check the order number and e-mail.
    """
    return _lookup_order(order_id, customer_email, _today())