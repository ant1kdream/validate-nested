"""``positive_number`` — value ``>= 0`` (a parameterless predefined validator).
Related: ``non_zero`` (strictly > 0), ``more``.
"""
from validate_nested import validate
from validate_nested.lambdas import positive_number


def test_positive_number_passes():
    record = {
        "account": {
            "balance": 0.0,
        },
    }
    model = {"account.balance": (float, positive_number)}
    assert validate(record, model).ok


def test_positive_number_fails():
    record = {
        "account": {
            "balance": -1.0,
        },
    }
    model = {"account.balance": (float, positive_number)}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [account.balance] should be >= 0, got -1.0"
    )
