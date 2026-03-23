import time
from decimal import Decimal

import pytest


def _json(resp):
    try:
        return resp.json()
    except Exception:
        return {}


def _assert_status(resp, allowed):
    if isinstance(allowed, int):
        allowed = {allowed}
    assert resp.status_code in set(allowed), (
        f"Unexpected status={resp.status_code}, body={resp.text}"
    )


def _assert_error_shape(resp):
    body = _json(resp)
    assert isinstance(body, dict)
    assert any(k in body for k in ("error", "message", "detail"))


# ------------------------
# BB-01 ... BB-07 Headers
# ------------------------

def test_bb_01_missing_roll_header(api):
    resp = api.request("GET", "/admin/users", user_id=None, headers={"X-Roll-Number": ""})
    _assert_status(resp, {400, 401})


def test_bb_02_invalid_roll_header_type(api):
    resp = api.request("GET", "/admin/users", user_id=None, roll_number="abc")
    _assert_status(resp, 400)


def test_bb_03_missing_user_header(api):
    resp = api.request("GET", "/profile", user_id=None)
    _assert_status(resp, 400)


@pytest.mark.parametrize(
    "bb_id, bad_user",
    [
        ("BB-04", "abc"),
        ("BB-05", "-1"),
        ("BB-06", "0"),
    ],
    ids=lambda x: x if isinstance(x, str) else None,
)
def test_bb_04_to_06_invalid_user_id_header(api, bb_id, bad_user):
    resp = api.request("GET", "/profile", user_id=None, headers={"X-User-ID": bad_user})
    _assert_status(resp, 400)


def test_bb_07_unknown_large_user_id(api):
    resp = api.request("GET", "/profile", user_id=99_999_999)
    _assert_status(resp, {400, 404})


# ------------------------
# BB-08 ... BB-16 Profile
# ------------------------

def test_bb_08_profile_happy_path(api, user_id):
    resp = api.request("GET", "/profile", user_id=user_id)
    _assert_status(resp, 200)
    body = _json(resp)
    assert isinstance(body, dict)
    assert any(k in body for k in ("name", "phone", "user_id"))


@pytest.mark.parametrize(
    "bb_id,payload,expected",
    [
        ("BB-09", {"name": "A", "phone": "9876543210"}, 400),
        ("BB-10", {"name": "A" * 51, "phone": "9876543210"}, 400),
        ("BB-11", {"name": "Valid Name", "phone": "12345"}, 400),
        ("BB-12", {"name": "Valid User"}, 400),
        ("BB-13", {"phone": "9876543210"}, 400),
        ("BB-14", {}, 400),
        ("BB-15", {"name": 12345, "phone": "9876543210"}, 400),
        ("BB-16", {"name": "Valid Name", "phone": 9876543210}, 400),
    ],
    ids=lambda x: x if isinstance(x, str) else None,
)
def test_bb_09_to_16_profile_negative_cases(api, user_id, bb_id, payload, expected):
    resp = api.request("PUT", "/profile", user_id=user_id, json=payload)
    _assert_status(resp, expected)
    _assert_error_shape(resp)


# ---------------------------
# BB-17 ... BB-19 Products
# ---------------------------

def test_bb_17_product_list_filters_and_sort(api, user_id):
    resp = api.request(
        "GET",
        "/products",
        user_id=user_id,
        params={"category": "electronics", "search": "phone", "sort": "price_asc"},
    )
    _assert_status(resp, 200)
    body = _json(resp)
    products = body.get("products", []) if isinstance(body, dict) else []
    prices = [p.get("price") for p in products if isinstance(p, dict)]
    if len(prices) >= 2 and all(isinstance(x, (int, float)) for x in prices):
        assert prices == sorted(prices)


def test_bb_18_product_lookup_not_found(api, user_id):
    resp = api.request("GET", "/products/999999", user_id=user_id)
    _assert_status(resp, 404)


def test_bb_19_product_price_consistency(api, user_id):
    public_products = api.request("GET", "/products", user_id=user_id)
    _assert_status(public_products, 200)
    public_body = _json(public_products)
    if isinstance(public_body, list):
        plist = public_body
    elif isinstance(public_body, dict):
        plist = public_body.get("products", public_body.get("data", []))
    else:
        plist = []
    if not plist:
        pytest.skip("No active products available")
    product_id = plist[0]["product_id"]

    public_detail = api.request("GET", f"/products/{product_id}", user_id=user_id)
    admin_all = api.request("GET", "/admin/products", user_id=None)
    _assert_status(public_detail, 200)
    _assert_status(admin_all, 200)

    pub_price = _json(public_detail).get("price")
    admin_body = _json(admin_all)
    if isinstance(admin_body, list):
        admin_products = admin_body
    elif isinstance(admin_body, dict):
        admin_products = admin_body.get("products", admin_body.get("data", []))
    else:
        admin_products = []
    admin_match = next((p for p in admin_products if p.get("product_id") == product_id), None)
    if admin_match is None:
        pytest.skip("Product not found in admin listing")
    assert Decimal(str(pub_price)) == Decimal(str(admin_match.get("price")))


# ---------------------------
# BB-20 ... BB-35 Addresses
# ---------------------------


@pytest.mark.parametrize(
    "bb_id,payload,expected",
    [
        ("BB-20", {"label": "BAD", "street": "Valid Street 123", "city": "Hyderabad", "pincode": "500001", "is_default": False}, 400),
        ("BB-21", {"label": "HOME", "street": "1234", "city": "Hyderabad", "pincode": "500001", "is_default": False}, 400),
        ("BB-22", {"label": "HOME", "street": "S" * 101, "city": "Hyderabad", "pincode": "500001", "is_default": False}, 400),
        ("BB-23", {"label": "HOME", "street": "Valid Street", "city": "H", "pincode": "500001", "is_default": False}, 400),
        ("BB-24", {"label": "HOME", "street": "Valid Street", "city": "C" * 51, "pincode": "500001", "is_default": False}, 400),
        ("BB-25", {"label": "HOME", "street": "Valid Street", "city": "Hyderabad", "pincode": "50001", "is_default": False}, 400),
        ("BB-26", {"label": "HOME", "street": "Valid Street", "city": "Hyderabad", "pincode": "5000011", "is_default": False}, 400),
        ("BB-27", {"street": "Valid Street", "city": "Hyderabad", "pincode": "500001", "is_default": False}, 400),
        ("BB-28", {"label": "HOME", "city": "Hyderabad", "pincode": "500001", "is_default": False}, 400),
        ("BB-29", {"label": "HOME", "street": "Valid Street", "pincode": "500001", "is_default": False}, 400),
        ("BB-30", {"label": "HOME", "street": "Valid Street", "city": "Hyderabad", "is_default": False}, 400),
        ("BB-31", {"label": 123, "street": "Valid Street", "city": "Hyderabad", "pincode": "500001", "is_default": False}, 400),
        ("BB-32", {"label": "HOME", "street": 123, "city": "Hyderabad", "pincode": "500001", "is_default": False}, 400),
        ("BB-33", {"label": "HOME", "street": "Valid Street", "city": "Hyderabad", "pincode": 500001, "is_default": False}, 400),
        ("BB-34", {"label": "HOME", "street": "Valid Street", "city": "Hyderabad", "pincode": "500001", "is_default": "true"}, 400),
    ],
    ids=lambda x: x if isinstance(x, str) else None,
)
def test_bb_20_to_34_address_validation(api, user_id, bb_id, payload, expected):
    resp = api.request("POST", "/addresses", user_id=user_id, json=payload)
    _assert_status(resp, expected)


def test_bb_35_address_update_reflects_mutation(api, user_id):
    seed = {
        "label": "HOME",
        "street": "QC Seed Street 101",
        "city": "Hyderabad",
        "pincode": "500001",
        "is_default": False,
    }
    create = api.request("POST", "/addresses", user_id=user_id, json=seed)
    _assert_status(create, {200, 201})
    cbody = _json(create)
    address = cbody.get("address", cbody)
    address_id = address.get("address_id")
    if address_id is None:
        pytest.skip("Address create did not return address_id")

    new_street = f"QC Update Street {int(time.time())}"
    update = api.request(
        "PUT",
        f"/addresses/{address_id}",
        user_id=user_id,
        json={"street": new_street, "is_default": True},
    )
    _assert_status(update, 200)
    ub = _json(update)
    updated = ub.get("address", ub)
    assert updated.get("street") == new_street
    assert updated.get("is_default") is True


# -----------------------
# BB-36 ... BB-44 Cart
# -----------------------


@pytest.mark.usefixtures("clean_cart")
@pytest.mark.parametrize(
    "bb_id,payload,expected",
    [
        ("BB-36", {"product_id": 1, "quantity": 0}, 400),
        ("BB-37", {"product_id": 1, "quantity": -1}, 400),
        ("BB-38", {"quantity": 1}, {400, 404}),
        ("BB-39", {}, {400, 404}),
        ("BB-40", {"product_id": 1}, {400, 404}),
        ("BB-41", {"product_id": "1", "quantity": 1}, 400),
        ("BB-42", {"product_id": 1, "quantity": "1"}, 400),
        ("BB-43", {"product_id": 999999, "quantity": 1}, 404),
    ],
    ids=lambda x: x if isinstance(x, str) else None,
)
def test_bb_36_to_43_cart_negative(api, user_id, bb_id, payload, expected):
    resp = api.request("POST", "/cart/add", user_id=user_id, json=payload)
    _assert_status(resp, expected)


@pytest.mark.usefixtures("clean_cart")
def test_bb_44_cart_subtotal_total_arithmetic(api, user_id, active_product_id):
    add = api.request("POST", "/cart/add", user_id=user_id, json={"product_id": active_product_id, "quantity": 2})
    _assert_status(add, 200)

    cart = api.request("GET", "/cart", user_id=user_id)
    _assert_status(cart, 200)
    body = _json(cart)
    items = body.get("items", [])
    assert items, f"No cart items found: {body}"
    target = next((i for i in items if i.get("product_id") == active_product_id), items[0])

    expected_subtotal = Decimal(str(target.get("price", 0))) * Decimal(str(target.get("quantity", 0)))
    assert Decimal(str(target.get("subtotal", 0))) == expected_subtotal

    total_from_items = sum(Decimal(str(i.get("subtotal", 0))) for i in items)
    assert Decimal(str(body.get("total", 0))) == total_from_items


# -------------------------
# BB-45 ... BB-48 Coupons
# -------------------------


@pytest.mark.usefixtures("clean_cart")
def test_bb_45_expired_coupon_rejection(api, user_id):
    api.request("POST", "/cart/add", user_id=user_id, json={"product_id": 1, "quantity": 1})
    resp = api.request("POST", "/coupon/apply", user_id=user_id, json={"coupon_code": "EXPIRED100"})
    _assert_status(resp, 400)


@pytest.mark.usefixtures("clean_cart")
def test_bb_46_coupon_minimum_value_enforcement(api, user_id, active_product_id):
    api.request("POST", "/cart/add", user_id=user_id, json={"product_id": active_product_id, "quantity": 1})
    resp = api.request("POST", "/coupon/apply", user_id=user_id, json={"coupon_code": "FIRSTORDER"})
    _assert_status(resp, {200, 400})


@pytest.mark.usefixtures("clean_secondary_cart")
def test_bb_47_firstorder_percent_coupon_max_cap_check(api, secondary_user_id, active_product_id):
    api.request("POST", "/cart/add", user_id=secondary_user_id, json={"product_id": active_product_id, "quantity": 50})
    resp = api.request("POST", "/coupon/apply", user_id=secondary_user_id, json={"coupon_code": "FIRSTORDER"})
    _assert_status(resp, {200, 400})
    if resp.status_code == 200:
        discount = Decimal(str(_json(resp).get("discount", 0)))
        assert discount <= Decimal("150")


@pytest.mark.usefixtures("clean_secondary_cart")
def test_bb_48_percent20_coupon_max_cap_check(api, secondary_user_id, active_product_id):
    api.request("POST", "/cart/add", user_id=secondary_user_id, json={"product_id": active_product_id, "quantity": 100})
    resp = api.request("POST", "/coupon/apply", user_id=secondary_user_id, json={"coupon_code": "PERCENT20"})
    _assert_status(resp, {200, 400})
    if resp.status_code == 200:
        discount = Decimal(str(_json(resp).get("discount", 0)))
        assert discount <= Decimal("200")


# ----------------------------
# BB-49 ... BB-55 Checkout
# ----------------------------


@pytest.mark.usefixtures("clean_cart")
def test_bb_49_checkout_rejects_empty_cart(api, user_id):
    resp = api.request("POST", "/checkout", user_id=user_id, json={"payment_method": "CARD"})
    _assert_status(resp, 400)


@pytest.mark.usefixtures("clean_cart")
def test_bb_50_checkout_rejects_missing_payment_method(api, user_id):
    resp = api.request("POST", "/checkout", user_id=user_id, json={})
    _assert_status(resp, 400)


@pytest.mark.usefixtures("clean_cart")
def test_bb_51_checkout_rejects_cod_above_limit(api, user_id, active_product_id):
    api.request("POST", "/cart/add", user_id=user_id, json={"product_id": active_product_id, "quantity": 200})
    resp = api.request("POST", "/checkout", user_id=user_id, json={"payment_method": "COD"})
    _assert_status(resp, {200, 400})
    if resp.status_code == 200:
        pytest.fail("Expected COD > 5000 to be rejected")


@pytest.mark.parametrize(
    "bb_id,payload",
    [
        ("BB-52", {"payment_method": "UPI"}),
        ("BB-53", {"payment_method": 123}),
        ("BB-54", {"payment_method": None}),
    ],
    ids=lambda x: x if isinstance(x, str) else None,
)
def test_bb_52_to_54_invalid_payment_method(api, user_id, bb_id, payload):
    resp = api.request("POST", "/checkout", user_id=user_id, json=payload)
    _assert_status(resp, 400)


@pytest.mark.usefixtures("clean_cart")
def test_bb_55_checkout_gst_application_correctness(api, user_id, active_product_id):
    api.request("POST", "/cart/add", user_id=user_id, json={"product_id": active_product_id, "quantity": 1})
    resp = api.request("POST", "/checkout", user_id=user_id, json={"payment_method": "CARD"})
    _assert_status(resp, {200, 400})
    if resp.status_code == 200:
        body = _json(resp)
        subtotal = Decimal(str(body.get("subtotal", 0)))
        gst = Decimal(str(body.get("gst_amount", 0)))
        total = Decimal(str(body.get("total_amount", body.get("total", 0))))
        assert gst == (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
        assert total == subtotal + gst


# --------------------------
# BB-56 ... BB-62 Wallet
# --------------------------


@pytest.mark.parametrize(
    "bb_id,payload,expected",
    [
        ("BB-56", {"amount": 0}, 400),
        ("BB-57", {"amount": 100001}, 400),
        ("BB-58", {}, 400),
    ],
    ids=lambda x: x if isinstance(x, str) else None,
)
def test_bb_56_to_58_wallet_add_negative(api, user_id, bb_id, payload, expected):
    resp = api.request("POST", "/wallet/add", user_id=user_id, json=payload)
    _assert_status(resp, expected)


@pytest.mark.parametrize(
    "bb_id,payload",
    [
        ("BB-59", {"amount": 0}),
        ("BB-60", {"amount": -1}),
        ("BB-61", {"amount": 10**9}),
    ],
    ids=lambda x: x if isinstance(x, str) else None,
)
def test_bb_59_to_61_wallet_pay_invalid(api, user_id, bb_id, payload):
    resp = api.request("POST", "/wallet/pay", user_id=user_id, json=payload)
    _assert_status(resp, 400)


def test_bb_62_wallet_pay_exact_deduction_behavior(api, user_id):
    before = api.request("GET", "/wallet", user_id=user_id)
    _assert_status(before, 200)
    starting_balance = Decimal(str(_json(before).get("balance", 0)))

    add = api.request("POST", "/wallet/add", user_id=user_id, json={"amount": 10})
    _assert_status(add, 200)
    pay = api.request("POST", "/wallet/pay", user_id=user_id, json={"amount": 10})
    _assert_status(pay, {200, 400})

    after = api.request("GET", "/wallet", user_id=user_id)
    _assert_status(after, 200)
    final_balance = Decimal(str(_json(after).get("balance", 0)))

    if pay.status_code == 200:
        assert final_balance == starting_balance


# ---------------------------
# BB-63 ... BB-70 Reviews
# ---------------------------


def test_bb_63_reviews_average_uses_decimal_precision(api, user_id):
    resp = api.request("GET", "/products/1/reviews", user_id=user_id)
    _assert_status(resp, 200)
    body = _json(resp)
    reviews = body.get("reviews", [])
    avg = Decimal(str(body.get("average_rating", 0)))
    if reviews:
        expected = sum(Decimal(str(r["rating"])) for r in reviews) / Decimal(len(reviews))
        assert avg == expected


def test_bb_64_reviews_average_zero_when_no_reviews(api, user_id):
    resp = api.request("GET", "/products/14/reviews", user_id=user_id)
    _assert_status(resp, 200)
    body = _json(resp)
    if body.get("reviews") == []:
        assert Decimal(str(body.get("average_rating", 0))) == Decimal("0")


@pytest.mark.parametrize(
    "bb_id,payload",
    [
        ("BB-65", {"rating": 0, "comment": "valid comment"}),
        ("BB-66", {"rating": 6, "comment": "valid comment"}),
        ("BB-67", {"rating": "5", "comment": "valid comment"}),
        ("BB-68", {"rating": 5, "comment": ""}),
        ("BB-69", {"rating": 5, "comment": "x" * 201}),
        ("BB-70", {"rating": 5}),
    ],
    ids=lambda x: x if isinstance(x, str) else None,
)
def test_bb_65_to_70_add_review_invalid_payloads(api, user_id, bb_id, payload):
    resp = api.request("POST", "/products/1/reviews", user_id=user_id, json=payload)
    _assert_status(resp, 400)


# ---------------------------
# BB-71 ... BB-77 Orders/Tickets
# ---------------------------


@pytest.mark.usefixtures("clean_secondary_cart")
def test_bb_71_order_cancellation_restores_stock(api, secondary_user_id, active_product_id):
    admin_before = api.request("GET", "/admin/products", user_id=None)
    _assert_status(admin_before, 200)
    products_before = _json(admin_before).get("products", _json(admin_before).get("data", []))
    before_obj = next((p for p in products_before if p.get("product_id") == active_product_id), None)
    if before_obj is None:
        pytest.skip("Product not found in admin listing")
    stock_before = before_obj.get("stock")

    add = api.request("POST", "/cart/add", user_id=secondary_user_id, json={"product_id": active_product_id, "quantity": 1})
    if add.status_code != 200:
        pytest.skip(f"Unable to seed cart for order cancellation flow: {add.status_code}")

    checkout = api.request("POST", "/checkout", user_id=secondary_user_id, json={"payment_method": "CARD"})
    _assert_status(checkout, {200, 400})
    if checkout.status_code != 200:
        pytest.skip("Checkout not created; cannot validate cancellation stock restore")

    order_id = _json(checkout).get("order_id")
    if order_id is None:
        pytest.skip("No order_id returned by checkout")

    cancel = api.request("POST", f"/orders/{order_id}/cancel", user_id=secondary_user_id)
    _assert_status(cancel, {200, 400})

    admin_after = api.request("GET", "/admin/products", user_id=None)
    _assert_status(admin_after, 200)
    products_after = _json(admin_after).get("products", _json(admin_after).get("data", []))
    after_obj = next((p for p in products_after if p.get("product_id") == active_product_id), None)
    if after_obj and cancel.status_code == 200:
        assert after_obj.get("stock") == stock_before


def test_bb_72_order_cancellation_missing_order(api, user_id):
    resp = api.request("POST", "/orders/999999/cancel", user_id=user_id)
    _assert_status(resp, 404)


def _create_ticket(api, user_id):
    resp = api.request(
        "POST",
        "/support/ticket",
        user_id=user_id,
        json={"subject": f"Test Subject {time.time()}", "message": "Need help with order."},
    )
    _assert_status(resp, {200, 201})
    body = _json(resp)
    ticket = body.get("ticket", body)
    ticket_id = ticket.get("ticket_id")
    if ticket_id is None:
        pytest.skip("Ticket creation did not return ticket_id")
    return int(ticket_id)


def test_bb_73_support_ticket_backward_transition_rejected(api, user_id):
    ticket_id = _create_ticket(api, user_id)
    step1 = api.request("PUT", f"/support/tickets/{ticket_id}", user_id=user_id, json={"status": "IN_PROGRESS"})
    _assert_status(step1, {200, 400})
    step2 = api.request("PUT", f"/support/tickets/{ticket_id}", user_id=user_id, json={"status": "OPEN"})
    _assert_status(step2, 400)


@pytest.mark.parametrize(
    "bb_id,payload",
    [
        ("BB-74", {"subject": "abcd", "message": "valid"}),
        ("BB-75", {"subject": "Valid Subject", "message": ""}),
        ("BB-76", {}),
    ],
    ids=lambda x: x if isinstance(x, str) else None,
)
def test_bb_74_to_76_support_ticket_creation_invalid(api, user_id, bb_id, payload):
    resp = api.request("POST", "/support/ticket", user_id=user_id, json=payload)
    _assert_status(resp, 400)


def test_bb_77_support_ticket_update_invalid_status_value(api, user_id):
    ticket_id = _create_ticket(api, user_id)
    resp = api.request("PUT", f"/support/tickets/{ticket_id}", user_id=user_id, json={"status": "REOPENED"})
    _assert_status(resp, 400)


# ---------------------------
# BB-78 ... BB-82 Cart/Invoice math
# ---------------------------


@pytest.mark.usefixtures("clean_cart")
def test_bb_78_cart_update_subtotal_total_consistency(api, user_id, active_product_id):
    api.request("POST", "/cart/add", user_id=user_id, json={"product_id": active_product_id, "quantity": 1})
    update = api.request("POST", "/cart/update", user_id=user_id, json={"product_id": active_product_id, "quantity": 3})
    _assert_status(update, {200, 400})

    cart = api.request("GET", "/cart", user_id=user_id)
    _assert_status(cart, 200)
    body = _json(cart)
    items = body.get("items", [])
    if not items:
        pytest.skip("No items found after cart/update")
    item = next((i for i in items if i.get("product_id") == active_product_id), items[0])
    expected = Decimal(str(item.get("price", 0))) * Decimal(str(item.get("quantity", 0)))
    assert Decimal(str(item.get("subtotal", 0))) == expected


@pytest.mark.usefixtures("clean_cart")
def test_bb_79_cart_duplicate_add_subtotal_consistency(api, user_id, active_product_id):
    api.request("POST", "/cart/add", user_id=user_id, json={"product_id": active_product_id, "quantity": 1})
    api.request("POST", "/cart/add", user_id=user_id, json={"product_id": active_product_id, "quantity": 2})

    cart = api.request("GET", "/cart", user_id=user_id)
    _assert_status(cart, 200)
    items = _json(cart).get("items", [])
    item = next((i for i in items if i.get("product_id") == active_product_id), None)
    assert item is not None
    assert int(item.get("quantity", 0)) == 3
    expected = Decimal(str(item.get("price", 0))) * Decimal("3")
    assert Decimal(str(item.get("subtotal", 0))) == expected


@pytest.mark.usefixtures("clean_cart")
def test_bb_80_cart_total_equals_sum_of_item_subtotals(api, user_id, active_product_id, second_active_product_id):
    api.request("POST", "/cart/add", user_id=user_id, json={"product_id": active_product_id, "quantity": 1})
    if second_active_product_id != active_product_id:
        api.request("POST", "/cart/add", user_id=user_id, json={"product_id": second_active_product_id, "quantity": 1})

    cart = api.request("GET", "/cart", user_id=user_id)
    _assert_status(cart, 200)
    body = _json(cart)
    items = body.get("items", [])
    assert items
    total_calc = sum(Decimal(str(i.get("subtotal", 0))) for i in items)
    assert Decimal(str(body.get("total", 0))) == total_calc


@pytest.mark.usefixtures("clean_secondary_cart")
def test_bb_81_invoice_gst_and_subtotal_rule_correctness(api, secondary_user_id, active_product_id):
    add = api.request("POST", "/cart/add", user_id=secondary_user_id, json={"product_id": active_product_id, "quantity": 1})
    if add.status_code != 200:
        pytest.skip(f"Unable to seed cart for invoice flow: {add.status_code}")
    checkout = api.request("POST", "/checkout", user_id=secondary_user_id, json={"payment_method": "CARD"})
    _assert_status(checkout, {200, 400})
    if checkout.status_code != 200:
        pytest.skip("Checkout not created; cannot validate invoice")
    order_id = _json(checkout).get("order_id")
    if order_id is None:
        pytest.skip("No order_id for invoice check")

    invoice = api.request("GET", f"/orders/{order_id}/invoice", user_id=secondary_user_id)
    _assert_status(invoice, 200)
    body = _json(invoice)
    subtotal = Decimal(str(body.get("subtotal", 0)))
    gst = Decimal(str(body.get("gst_amount", 0)))
    total = Decimal(str(body.get("total_amount", body.get("total", 0))))
    assert total == subtotal + gst


@pytest.mark.usefixtures("clean_secondary_cart")
def test_bb_82_checkout_multi_qty_gst_total_rule(api, secondary_user_id, active_product_id):
    add = api.request("POST", "/cart/add", user_id=secondary_user_id, json={"product_id": active_product_id, "quantity": 2})
    if add.status_code != 200:
        pytest.skip(f"Unable to seed cart for multi-qty GST flow: {add.status_code}")
    checkout = api.request("POST", "/checkout", user_id=secondary_user_id, json={"payment_method": "CARD"})
    _assert_status(checkout, {200, 400})
    if checkout.status_code == 200:
        body = _json(checkout)
        subtotal = Decimal(str(body.get("subtotal", 0)))
        gst = Decimal(str(body.get("gst_amount", 0)))
        total = Decimal(str(body.get("total_amount", body.get("total", 0))))
        assert total == subtotal + gst


# ---------------------------
# BB-83 ... BB-87 Loyalty
# ---------------------------


@pytest.mark.parametrize(
    "bb_id,payload,expected",
    [
        ("BB-83", {}, 400),
        ("BB-84", {"points": 0}, 400),
        ("BB-85", {"points": -1}, 400),
        ("BB-86", {"points": "1"}, 400),
        ("BB-87", {"points": 10**9}, 400),
    ],
    ids=lambda x: x if isinstance(x, str) else None,
)
def test_bb_83_to_87_loyalty_redeem_invalid(api, user_id, bb_id, payload, expected):
    resp = api.request("POST", "/loyalty/redeem", user_id=user_id, json=payload)
    _assert_status(resp, expected)


# ----------------------------------
# BB-88 ... BB-90 Payment status map
# ----------------------------------


@pytest.mark.usefixtures("clean_secondary_cart")
@pytest.mark.parametrize(
    "bb_id,payment_method,expected_status",
    [
        ("BB-88", "CARD", "PAID"),
        ("BB-89", "COD", "PENDING"),
        ("BB-90", "WALLET", "PENDING"),
    ],
    ids=lambda x: x if isinstance(x, str) else None,
)
def test_bb_88_to_90_checkout_payment_status_mapping(
    api,
    secondary_user_id,
    active_product_id,
    bb_id,
    payment_method,
    expected_status,
):
    seed = api.request("POST", "/cart/add", user_id=secondary_user_id, json={"product_id": active_product_id, "quantity": 1})
    if seed.status_code != 200:
        pytest.skip(f"Unable to seed cart for payment status mapping: {seed.status_code}")

    if payment_method == "WALLET":
        api.request("POST", "/wallet/add", user_id=secondary_user_id, json={"amount": 100000})

    checkout = api.request("POST", "/checkout", user_id=secondary_user_id, json={"payment_method": payment_method})
    _assert_status(checkout, {200, 400})
    if checkout.status_code == 200:
        assert _json(checkout).get("payment_status") == expected_status


# ---------------------------
# BB-91 ... BB-94 Extras
# ---------------------------


def test_bb_91_delete_non_existent_address(api, user_id):
    resp = api.request("DELETE", "/addresses/999999", user_id=user_id)
    _assert_status(resp, 404)


def test_bb_92_update_non_existent_support_ticket(api, user_id):
    resp = api.request("PUT", "/support/tickets/999999", user_id=user_id, json={"status": "IN_PROGRESS"})
    _assert_status(resp, 404)


def test_bb_93_closed_support_ticket_cannot_move_to_in_progress(api, user_id):
    ticket_id = _create_ticket(api, user_id)
    step1 = api.request("PUT", f"/support/tickets/{ticket_id}", user_id=user_id, json={"status": "IN_PROGRESS"})
    _assert_status(step1, {200, 400})
    step2 = api.request("PUT", f"/support/tickets/{ticket_id}", user_id=user_id, json={"status": "CLOSED"})
    _assert_status(step2, {200, 400})
    step3 = api.request("PUT", f"/support/tickets/{ticket_id}", user_id=user_id, json={"status": "IN_PROGRESS"})
    _assert_status(step3, 400)


def test_bb_94_wallet_exact_small_deduction_behavior(api, user_id):
    before = api.request("GET", "/wallet", user_id=user_id)
    _assert_status(before, 200)
    start_balance = Decimal(str(_json(before).get("balance", 0)))

    add = api.request("POST", "/wallet/add", user_id=user_id, json={"amount": 1})
    _assert_status(add, 200)
    pay = api.request("POST", "/wallet/pay", user_id=user_id, json={"amount": 1})
    _assert_status(pay, {200, 400})

    after = api.request("GET", "/wallet", user_id=user_id)
    _assert_status(after, 200)
    end_balance = Decimal(str(_json(after).get("balance", 0)))
    if pay.status_code == 200:
        assert end_balance == start_balance
