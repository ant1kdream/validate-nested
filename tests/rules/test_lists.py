"""List paths: the ``[*]`` wildcard and explicit indices.

A path segment can be:
  * ``items[*]``      — apply the rule to **every** element of the list,
  * ``items[0]``      — target one element by **index**,
  * nested wildcards  — ``orders[*].items[*].price``.

A failure carries the concrete index (``items[1].price``), and an out-of-range index is
reported as missing. The two styles can be mixed in one model.

Each negative test asserts the exact ``r.report()``.
"""
from validate_nested import validate
from validate_nested.lambdas import equal


def test_wildcard_each_item_is_a_dict():
    """``items[*]`` checks the type of every element."""
    record = {
        "order_id": "ORD-1042",
        "items": [
            {"sku": "A-1", "price": 9.99},
            {"sku": "B-2", "price": 19.50},
        ],
    }
    model = {"items[*]": dict}
    assert validate(record, model).ok


def test_wildcard_field_on_every_item():
    """``items[*].price`` / ``items[*].qty`` apply a rule to a field of every element."""
    record = {
        "items": [
            {"price": 9.99, "qty": 2},
            {"price": 19.50, "qty": 1},
        ],
    }
    model = {
        "items[*].price": float,
        "items[*].qty": int,
    }
    assert validate(record, model).ok


def test_wildcard_one_item_breaks():
    """One bad element out of many -> the failure carries its index."""
    record = {
        "items": [
            {"price": 9.99},
            {"price": "oops"},
        ],
    }
    model = {"items[*].price": float}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [items[1].price] expected float, got str"
    )


def test_specific_index_passes():
    """``items[0]`` / ``items[1]`` target a single element by index."""
    record = {
        "items": [
            {"sku": "A-1", "price": 9.99},
            {"sku": "B-2", "price": 19.50},
        ],
    }
    model = {
        "items[0].sku": (str, equal("A-1")),
        "items[1].price": float,
    }
    assert validate(record, model).ok


def test_specific_index_fails():
    """A wrong value at a specific index fails at exactly that path."""
    record = {
        "items": [
            {"sku": "A-1"},
            {"sku": "B-2"},
        ],
    }
    model = {"items[1].sku": (str, equal("X-9"))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [items[1].sku] should be equal to 'X-9', got 'B-2'"
    )


def test_index_out_of_range_is_missing():
    """An index past the end of the list is reported as missing."""
    record = {
        "items": [
            {"price": 9.99},
        ],
    }
    model = {"items[3].price": float}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [items[3].price] is missing"
    )


def test_mix_index_and_wildcard():
    """A specific index and a wildcard can live in the same model."""
    record = {
        "items": [
            {"sku": "A-1", "price": 9.99},
            {"sku": "B-2", "price": 19.50},
        ],
    }
    model = {
        "items[0].sku": (str, equal("A-1")),
        "items[*].price": float,
    }
    assert validate(record, model).ok


def test_nested_wildcards():
    """Wildcards nest: every item of every order."""
    record = {
        "orders": [
            {"items": [{"price": 1.0}, {"price": 2.0}]},
            {"items": [{"price": 3.0}]},
        ],
    }
    model = {"orders[*].items[*].price": float}
    assert validate(record, model).ok


def test_nested_wildcards_failure_carries_full_path():
    """A nested failure reports the full concrete path with both indices."""
    record = {
        "orders": [
            {"items": [{"price": 1.0}, {"price": "x"}]},
        ],
    }
    model = {"orders[*].items[*].price": float}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [orders[0].items[1].price] expected float, got str"
    )
