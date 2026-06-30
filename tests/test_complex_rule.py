"""ComplexRule (per-field options) and model composition.

``ComplexRule(value=<rule>, options={...})`` runs ``<rule>`` for one path but with extra
per-field options:

  * ``assert_msg`` — replace the failure message for just this field,
  * ``add_msg``    — prepend extra context to the default message,
  * ``hard_assert``— make this one field raise immediately instead of collecting.

Models are plain dicts, so reusable sub-models compose with ``**``.
"""
import pytest

from validate_nested import ComplexRule, validate
from validate_nested.lambdas import equal, length, more, not_empty, required


# ── per-field options via ComplexRule ──────────────────────────────────────────
def test_per_field_custom_message():
    """``assert_msg`` replaces the default message for just this field."""
    record = {
        "order": {
            "status": "void",
        },
    }
    model = {
        "order.status": ComplexRule(
            value=(str, equal("paid")),
            options={"assert_msg": "order is not paid, refusing to ship"},
        ),
    }
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [order.status] order is not paid, refusing to ship"
    )


def test_per_field_add_msg():
    """``add_msg`` prepends extra context to the default message."""
    record = {
        "order": {
            "status": "void",
        },
    }
    model = {
        "order.status": ComplexRule(
            value=(str, equal("paid")),
            options={"add_msg": "[blocking]"},
        ),
    }
    r = validate(record, model)

    assert r.failures[0].message == "[blocking], should be equal to 'paid', got 'void'"


def test_per_field_hard_assert_raises():
    """``hard_assert`` makes this one field raise immediately instead of collecting."""
    record = {
        "order": {
            "status": "void",
        },
    }
    model = {
        "order.status": ComplexRule(
            value=(str, equal("paid")),
            options={"hard_assert": True},
        ),
    }
    with pytest.raises(AssertionError):
        validate(record, model)


# ── compose reusable sub-models with ** ────────────────────────────────────────
def address_model(prefix):
    """A reusable address shape, applied under any prefix."""
    return {
        f"{prefix}.city": (str, not_empty()),
        f"{prefix}.zip": (str, length(5)),
        f"{prefix}.country": (str, length(2)),
    }


def test_compose_reusable_submodels_passes():
    """The same address shape validates both shipping and billing; a line-item shape
    validates every item — all merged into one model with ``**``."""
    record = {
        "order_id": "ORD-1042",
        "shipping": {"city": "Berlin", "zip": "10115", "country": "DE"},
        "billing": {"city": "Paris", "zip": "75001", "country": "FR"},
        "items": [
            {"sku": "A-1", "price": 9.99, "qty": 2},
            {"sku": "B-2", "price": 19.50, "qty": 1},
        ],
    }
    model = {
        "order_id": required(str),
        **address_model("shipping"),
        **address_model("billing"),
        "items[*].sku": (str, not_empty()),
        "items[*].price": (float, more(0)),
        "items[*].qty": (int, more(0)),
    }
    assert validate(record, model).ok


def test_compose_catches_a_bad_field_in_a_submodel():
    """A bad field inside one composed sub-model surfaces by its full path."""
    record = {
        "shipping": {"city": "Berlin", "zip": "10115", "country": "DE"},
        "billing": {"city": "Paris", "zip": "750", "country": "FR"},   # zip too short
    }
    model = {
        **address_model("shipping"),
        **address_model("billing"),
    }
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [billing.zip] should have length 5, got length 3"
    )
