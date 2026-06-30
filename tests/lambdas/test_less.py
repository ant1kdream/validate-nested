"""``less(x)`` — the value must be strictly less than ``x`` (``value < x``).

Mirror: ``more``. For a two-sided bound use ``in_range``.
"""
from validate_nested import validate
from validate_nested.lambdas import less


def test_less_passes():
    record = {
        "delivery": {
            "attempts": 2,
        },
    }
    model = {"delivery.attempts": (int, less(5))}
    assert validate(record, model).ok


def test_less_fails():
    record = {
        "delivery": {
            "attempts": 5,
        },
    }
    model = {"delivery.attempts": (int, less(4))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [delivery.attempts] should be less than 4, got 5"
    )
