"""``equal(x)`` — the value must be exactly ``== x``.

Usually paired with a type in a tuple, e.g. ``(str, equal("ok"))``: the type is checked
first, then the value. ``equal`` does **no** coercion — ``0`` and ``"0"`` are not equal,
so a wrong type produces both a type failure and a value failure.

Each negative test asserts the exact ``r.report()`` so the rendered output is visible
and verified. In your own code you'd surface it with ``assert r.ok, r.report()``.

Related: ``not_equal``, ``lower_match`` (case-insensitive), ``exists_in`` (one-of).
"""
from validate_nested import validate
from validate_nested.lambdas import equal


def test_equal_string_match():
    """A nested string equal to the expected literal passes."""
    record = {
        "request_id": "req-7781",
        "response": {
            "status": "ok",
            "code": 0,
        },
    }
    model = {"response.status": (str, equal("ok"))}
    assert validate(record, model).ok


def test_equal_string_mismatch():
    """A wrong value fails, pointing at the exact path."""
    record = {
        "request_id": "req-7781",
        "response": {
            "status": "error",
            "code": 0,
        },
    }
    model = {"response.status": (str, equal("ok"))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [response.status] should be equal to 'ok', got 'error'"
    )


def test_equal_numeric_match():
    """Works for numbers too (a nested int code)."""
    record = {
        "response": {
            "status": "ok",
            "code": 0,
        },
    }
    model = {"response.code": (int, equal(0))}
    assert validate(record, model).ok


def test_equal_is_type_strict():
    """No coercion: an int ``0`` against ``(str, equal("0"))`` fails twice — once on the
    type, once on the value."""
    record = {
        "response": {
            "code": 0,
        },
    }
    model = {"response.code": (str, equal("0"))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "2 validation failure(s):\n"
        "  - [response.code] expected str, got int\n"
        "  - [response.code] should be equal to '0', got 0"
    )


def test_equal_over_list_items():
    """``[*]`` applies the same equality to every item — all match here."""
    record = {
        "items": [
            {"sku": "A-1", "status": "shipped"},
            {"sku": "B-2", "status": "shipped"},
        ],
    }
    model = {"items[*].status": (str, equal("shipped"))}
    assert validate(record, model).ok


def test_equal_list_item_mismatch():
    """One item out of many breaks — the failure carries its index."""
    record = {
        "items": [
            {"sku": "A-1", "status": "shipped"},
            {"sku": "B-2", "status": "pending"},
        ],
    }
    model = {"items[*].status": (str, equal("shipped"))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [items[1].status] should be equal to 'shipped', got 'pending'"
    )
