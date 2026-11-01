from emporio.tools import get_product_details, search_products
 
 
def test_search_guitars_under_1000_only_returns_available_acoustic_guitars():
    res = search_products(category="Violões", max_price_brl=1000)
    assert res["total_matches"] > 0
    for p in res["products"]:
        assert p["category"] == "Violões"
        assert p["final_price_brl"] <= 1000
        assert p["availability"] == "available"
 
 
def test_accents_and_plurals_are_equivalent():
    a = search_products(category="violões")["total_matches"]
    b = search_products(category="violao")["total_matches"]
    assert a == b > 0
 
 
def test_results_sorted_cheapest_first():
    prices = [p["final_price_brl"] for p in search_products(category="Violões", limit=25)["products"]]
    assert prices == sorted(prices)
 
 
def test_expired_promotion_is_not_applied_and_is_flagged():
    res = get_product_details("Takamine GD20")
    p = res["product"]
    assert res["status"] == "found"
    assert p["promotion"] is None
    assert p["final_price_brl"] == 2199.0
    assert p["expired_promotion"] is True
    assert p["pix_price_brl"] == 2089.05  # 5% PIX applies: no promotion is active
 
 
def test_active_promotion_shows_both_prices_and_no_pix_discount():
    p = get_product_details("Ohana CK-20")["product"]
    assert p["list_price_brl"] == 549.0
    assert p["promotion"]["discount_percent"] == 20.0
    assert p["final_price_brl"] == 439.2
    assert p["pix_price_brl"] is None  # promotions do not stack with PIX
 
 
def test_out_of_stock_product_returns_alternatives():
    res = get_product_details("Giannini GF-3D")
    assert res["product"]["availability"] == "out_of_stock"
    assert len(res["alternatives"]) > 0
    assert all(a["name"] != res["product"]["name"] for a in res["alternatives"])
 
 
def test_discontinued_product_is_reported_as_such():
    res = get_product_details("Shelby SN-7C")
    assert res["product"]["availability"] == "discontinued"
    assert "alternatives" in res
 
 
def test_ambiguous_name_returns_candidates():
    res = get_product_details("Yamaha")
    assert res["status"] == "ambiguous"
    assert len(res["candidates"]) > 1
 
 
def test_unknown_product_returns_not_found():
    assert get_product_details("Stradivarius")["status"] == "not_found"
