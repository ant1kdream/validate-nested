"""``more(x)`` — the value must be strictly greater than ``x`` (``value > x``).

Mirror: ``less``. For a two-sided bound use ``in_range``.
"""
from validate_nested import validate
from validate_nested.lambdas import more


def test_more_passes():
    record = {
        "cart": {
            "total": 19.99,
        },
    }
    model = {"cart.total": (float, more(0))}
    assert validate(record, model).ok


def test_more_fails():
    record = {
        "cart": {
            "total": 5,
        },
    }
    model = {"cart.total": (int, more(6))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [cart.total] should be greater than 6, got 5"
    )


def test_more_over_list_items():
    record = {
        "items": [
            {"qty": 2},
            {"qty": 1},
        ],
    }
    model = {"items[*].qty": (int, more(0))}
    assert validate(record, model).ok
