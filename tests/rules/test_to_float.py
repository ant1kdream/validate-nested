"""``to_float(...)`` — coerce the value to ``float`` before the wrapped validators.

Mirror of ``to_int``: ``(str, to_float(equal(0.5)))`` accepts ``"0.5"``. A value that
can't be coerced fails with the coercion error.
"""
from validate_nested import validate
from validate_nested.lambdas import equal, to_float


def test_to_float_coerces_then_validates():
    record = {
        "reading": {
            "ratio": "0.5",
        },
    }
    model = {"reading.ratio": (str, to_float(equal(0.5)))}
    assert validate(record, model).ok


def test_to_float_value_mismatch_after_coercion():
    record = {
        "reading": {
            "ratio": "5.5",
        },
    }
    model = {"reading.ratio": (str, to_float(equal(5.0)))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [reading.ratio] should be equal to 5.0, got 5.5"
    )


def test_to_float_non_numeric_is_reported():
    record = {
        "reading": {
            "ratio": "warm",
        },
    }
    model = {"reading.ratio": (str, to_float(equal(5.0)))}
    r = validate(record, model)

    assert not r.ok
    assert "error on 'warm'" in r.report()
