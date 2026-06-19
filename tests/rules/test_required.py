"""``required(rule)`` — the path MUST be present and satisfy ``rule``.

What makes ``required`` special: if it fails, validation **stops** and the model keys
written *after* it are not checked. Put it on a key everything else depends on (an id,
a parent object) and a missing/invalid value yields one clear failure instead of a
cascade.

Composed as ``required(opt(...))`` it becomes a *gate*: the key is optional (absent is
fine), but **when present** its shape is checked first — if that fails, descending into
its children is pointless, so they're skipped.

Each negative test asserts the exact ``r.report()`` so the rendered output is both
visible here and verified. In your own code you'd surface it with::

    r = validate(record, model)
    assert r.ok, r.report()

Related: ``opt`` (may be absent), ``not_exist`` (must be absent).
"""
from validate_nested import validate
from validate_nested.lambdas import equal, opt, required


def test_required_top_field_present_validates_the_rest():
    """``order_id`` is the required gate; present and a str -> the rest of the model
    (including the per-item list checks) is validated and passes."""
    record = {
        "order_id": "ORD-1042",
        "status": "shipped",
        "customer": {
            "addresses": {
                "shipping": {
                    "city": "Berlin",
                    "country": "DE",
                },
            },
        },
        "items": [
            {"sku": "A-1", "price": 9.99},
            {"sku": "B-2", "price": 19.50},
        ],
    }
    model = {
        "order_id": required(str),
        "customer.addresses.shipping.country": (str, equal("DE")),
        "items[*].price": float,
    }
    assert validate(record, model).ok


def test_required_top_field_missing_stops_everything():
    """``order_id`` is gone -> ONE failure, and nothing below it is checked: not the
    nested address, not the per-item prices."""
    record = {
        "status": "shipped",
        "customer": {
            "addresses": {
                "shipping": {
                    "city": "Berlin",
                    "country": "DE",
                },
            },
        },
        "items": [
            {"sku": "A-1", "price": 9.99},
        ],
    }
    model = {
        "order_id": required(str),
        "customer.addresses.shipping.country": (str, equal("DE")),
        "items[*].price": float,
    }
    r = validate(record, model)

    assert r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [order_id] is missing"
    )


def test_required_top_field_wrong_type_stops():
    """Present but the wrong type also stops everything below."""
    record = {
        "order_id": 1042,
        "items": [
            {"sku": "A-1", "price": 9.99},
        ],
    }
    model = {
        "order_id": required(str),
        "items[*].price": float,
    }
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [order_id] expected str, got int"
    )


def test_required_present_does_not_block_following_keys():
    """When the gate passes, the following keys ARE checked — here one item's price is
    a string instead of a float."""
    record = {
        "order_id": "ORD-1042",
        "items": [
            {"sku": "A-1", "price": 9.99},
            {"sku": "B-2", "price": "oops"},
        ],
    }
    model = {
        "order_id": required(str),
        "items[*].price": float,
    }
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [items[1].price] expected float, got str"
    )


def test_gate_optional_object_absent_is_ok():
    """``required(opt(dict))``: the billing address is optional — absent is fine, and
    its child keys are skipped."""
    record = {
        "order_id": "ORD-1042",
        "customer": {
            "addresses": {
                "shipping": {
                    "city": "Berlin",
                    "country": "DE",
                },
            },
        },
    }
    model = {
        "customer.addresses.billing": required(opt(dict)),
        "customer.addresses.billing.country": (str, equal("DE")),
    }
    assert validate(record, model).ok


def test_gate_optional_object_present_but_wrong_shape():
    """Present but not a dict -> one failure on the gate; the child is skipped."""
    record = {
        "order_id": "ORD-1042",
        "customer": {
            "addresses": {
                "billing": "same-as-shipping",
            },
        },
    }
    model = {
        "customer.addresses.billing": required(opt(dict)),
        "customer.addresses.billing.country": (str, equal("DE")),
    }
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [customer.addresses.billing] expected dict, got str"
    )


def test_gate_optional_object_present_and_valid_checks_children():
    """Present and a dict -> the gate passes and the children are validated; here the
    billing country is wrong."""
    record = {
        "order_id": "ORD-1042",
        "customer": {
            "addresses": {
                "billing": {
                    "city": "Paris",
                    "country": "FR",
                },
            },
        },
    }
    model = {
        "customer.addresses.billing": required(opt(dict)),
        "customer.addresses.billing.country": (str, equal("DE")),
    }
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [customer.addresses.billing.country] should be equal to 'DE', got 'FR'"
    )
