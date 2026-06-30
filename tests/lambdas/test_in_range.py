"""``in_range(start, stop)`` — exclusive numeric range: ``start < value < stop``.

Related: ``less`` / ``more`` (one-sided), ``approx`` (near a target).
"""
from validate_nested import validate
from validate_nested.lambdas import in_range


def test_in_range_passes():
    record = {
        "product": {
            "rating": 4,
        },
    }
    model = {"product.rating": (int, in_range(0, 6))}
    assert validate(record, model).ok


def test_in_range_fails():
    record = {
        "product": {
            "rating": 5,
        },
    }
    model = {"product.rating": (int, in_range(0, 4))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [product.rating] should be in range (0, 4), got 5"
    )


def test_in_range_is_exclusive_at_the_bounds():
    """``start < value < stop`` — the bounds themselves are out."""
    record = {
        "product": {
            "rating": 6,
        },
    }
    model = {"product.rating": (int, in_range(0, 6))}
    assert not validate(record, model).ok
