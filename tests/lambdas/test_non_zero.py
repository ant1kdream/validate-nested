"""``non_zero`` — value strictly ``> 0`` (a parameterless predefined validator).
Related: ``positive_number`` (allows 0), ``more``.
"""
from validate_nested import validate
from validate_nested.lambdas import non_zero


def test_non_zero_passes():
    record = {
        "batch": {
            "size": 1,
        },
    }
    model = {"batch.size": (int, non_zero)}
    assert validate(record, model).ok


def test_non_zero_fails():
    record = {
        "batch": {
            "size": 0,
        },
    }
    model = {"batch.size": (int, non_zero)}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [batch.size] should be > 0, got 0"
    )
