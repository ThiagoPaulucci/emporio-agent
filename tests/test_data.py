from emporio.data import load_all


def test_tables_load():
    d = load_all()
    assert len(d["products"]) == 65
    assert len(d["orders"]) == 20


def test_specs_are_dicts():
    products = load_all()["products"]
    assert products["specs"].map(lambda s: isinstance(s, dict) and len(s) > 0).all()


def test_only_active_promotions_are_applied():
    products = load_all()["products"]
    with_promo = products[products["discount_percent"].notna()]
    assert len(with_promo) == 4


def test_expired_promo_not_applied_to_takamine_gd20():
    products = load_all()["products"]
    gd20 = products[products["name"].str.contains("GD20")].iloc[0]
    assert gd20["discount_percent"] != gd20["discount_percent"]  # NaN: promo expired
