"""``length(n)`` — the value's ``len()`` must equal ``n`` (lists, strings, dicts).

Usually paired with a type, e.g. ``(list, length(3))``. The failure reports the actual
length. Related: ``empty`` / ``not_empty`` (size 0 / > 0), ``split_length``.
"""
from validate_nested import validate
from validate_nested.lambdas import length


def test_length_of_a_list_passes():
    record = {
        "order_id": "ORD-1042",
        "items": [
            {"sku": "A-1"},
            {"sku": "B-2"},
        ],
    }
    model = {"items": (list, length(2))}
    assert validate(record, model).ok


def test_length_of_a_list_fails():
    record = {
        "order_id": "ORD-1042",
        "items": [
            {"sku": "A-1"},
            {"sku": "B-2"},
        ],
    }
    model = {"items": (list, length(3))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [items] should have length 3, got length 2"
    )


def test_length_of_a_string_passes():
    record = {
        "payment": {
            "currency": "EUR",
        },
    }
    model = {"payment.currency": (str, length(3))}
    assert validate(record, model).ok


def test_length_over_list_items_passes():
    record = {
        "items": [
            {"tags": ["new", "sale"]},
            {"tags": ["hot", "sale"]},
        ],
    }
    model = {"items[*].tags": (list, length(2))}
    assert validate(record, model).ok


def test_length_list_item_fails():
    record = {
        "items": [
            {"tags": ["new", "sale"]},
            {"tags": ["hot"]},
        ],
    }
    model = {"items[*].tags": (list, length(2))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [items[1].tags] should have length 2, got length 1"
    )
