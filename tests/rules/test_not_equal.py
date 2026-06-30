"""``not_equal(x)`` — the value must differ from ``x`` (``value != x``).

The mirror of ``equal``, with the same type-strictness. Related: ``equal``,
``exists_in`` (one-of), ``lower_match``.
"""
from validate_nested import validate
from validate_nested.lambdas import not_equal


def test_not_equal_passes():
    record = {
        "response": {
            "status": "ok",
        },
    }
    model = {"response.status": (str, not_equal("error"))}
    assert validate(record, model).ok


def test_not_equal_fails():
    record = {
        "response": {
            "status": "error",
        },
    }
    model = {"response.status": (str, not_equal("error"))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [response.status] should not be equal to 'error', got 'error'"
    )


def test_not_equal_numeric_passes():
    record = {
        "response": {
            "code": 0,
        },
    }
    model = {"response.code": (int, not_equal(500))}
    assert validate(record, model).ok


def test_not_equal_over_list_items_passes():
    record = {
        "items": [
            {"state": "active"},
            {"state": "active"},
        ],
    }
    model = {"items[*].state": (str, not_equal("cancelled"))}
    assert validate(record, model).ok


def test_not_equal_list_item_fails():
    record = {
        "items": [
            {"state": "active"},
            {"state": "cancelled"},
        ],
    }
    model = {"items[*].state": (str, not_equal("cancelled"))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [items[1].state] should not be equal to 'cancelled', got 'cancelled'"
    )
