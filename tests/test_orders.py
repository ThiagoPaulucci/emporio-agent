
import json
import os
from datetime import date
 
from emporio.data import load_all
from emporio.orders import _lookup_order, get_order_status
 
TODAY = date(2026, 3, 1)
 
 
def _email_of(order_id: int) -> str:
    d = load_all()
    cid = d["orders"].loc[d["orders"]["order_id"] == order_id, "customer_id"].iloc[0]
    return d["customers"].loc[d["customers"]["customer_id"] == cid, "email"].iloc[0]
 
 
def test_correct_order_and_email_returns_order_with_items():
    res = _lookup_order(8, _email_of(8), TODAY)
    assert res["status"] == "found"
    assert res["order"]["status"] == "shipped"
    assert res["order"]["tracking_code"]
    assert res["order"]["items"][0]["name"] == "Kala KA-C Concert Mogno"
 
 
def test_email_match_ignores_case_and_spaces():
    res = _lookup_order(8, "  " + _email_of(8).upper() + " ", TODAY)
    assert res["status"] == "found"
 
 
def test_wrong_email_and_unknown_order_give_the_same_answer():
    wrong_email = _lookup_order(8, "outra.pessoa@jmail.com", TODAY)
    unknown_order = _lookup_order(9999, _email_of(8), TODAY)
    garbage_id = _lookup_order("abc", _email_of(8), TODAY)
    assert wrong_email == unknown_order == garbage_id
    assert wrong_email["status"] == "verification_failed"
 
 
def test_email_of_another_customer_does_not_open_the_order():
    assert _lookup_order(8, _email_of(9), TODAY)["status"] == "verification_failed"
 
 
def test_empty_email_is_rejected():
    assert _lookup_order(8, "", TODAY)["status"] == "verification_failed"
 
 
def test_response_does_not_leak_personal_data():
    res = _lookup_order(8, _email_of(8), TODAY)
    text = json.dumps(res, ensure_ascii=False)
    assert "@" not in text
    assert "phone" not in text
    assert res["customer_first_name"] == "Ana"
 
 
def test_cancelled_order_shows_reason_and_no_tracking():
    res = _lookup_order(18, _email_of(18), TODAY)["order"]
    assert res["status"] == "cancelled"
    assert res["cancellation_reason"]
    assert res["tracking_code"] is None
 
 
def test_pending_order_has_no_tracking_or_delivery_estimate():
    res = _lookup_order(13, _email_of(13), TODAY)["order"]
    assert res["status"] == "pending"
    assert res["tracking_code"] is None
    assert res["estimated_delivery"] is None
    assert "return_info" not in res
 
 
def test_return_windows_for_delivered_order():
    # Order 7: purchased 2026-02-03, delivered (estimated) 2026-02-17.
    email = _email_of(7)
    inside = _lookup_order(7, email, date(2026, 2, 20))["order"]["return_info"]
    assert inside["within_regret_window"] is True
    assert inside["within_preference_exchange_window"] is True
    assert inside["within_defect_exchange_window"] is True
 
    mid = _lookup_order(7, email, date(2026, 3, 1))["order"]["return_info"]
    assert mid["days_since_receipt"] == 12
    assert mid["days_since_purchase"] == 26
    assert mid["within_regret_window"] is False
    assert mid["within_defect_exchange_window"] is True
 
    late = _lookup_order(7, email, date(2026, 6, 1))["order"]["return_info"]
    assert late["within_defect_exchange_window"] is False
    assert late["within_legal_warranty"] is False
 
 
def test_defect_window_counts_from_purchase_date_not_from_receipt():
    # Manual 4.2: "30 dias corridos apos a compra". Purchase 2026-02-03 -> day 30 is 03/05.
    email = _email_of(7)
    day_30 = _lookup_order(7, email, date(2026, 3, 5))["order"]["return_info"]
    day_31 = _lookup_order(7, email, date(2026, 3, 6))["order"]["return_info"]
    assert day_30["days_since_purchase"] == 30
    assert day_30["within_defect_exchange_window"] is True
    assert day_31["days_since_purchase"] == 31
    assert day_31["within_defect_exchange_window"] is False
 
 
def test_seventh_day_is_still_inside_the_regret_window():
    info = _lookup_order(7, _email_of(7), date(2026, 2, 24))["order"]["return_info"]
    assert info["days_since_receipt"] == 7
    assert info["within_regret_window"] is True
 
 
def test_today_can_be_overridden_by_environment_variable():
    os.environ["EMPORIO_TODAY"] = "2026-02-20"
    try:
        info = get_order_status(7, _email_of(7))["order"]["return_info"]
        assert info["within_regret_window"] is True
    finally:
        del os.environ["EMPORIO_TODAY"]