"""``to_int(...)`` — coerce the value to ``int`` before running the wrapped validators.

Handy when an API sends numbers as strings: ``(str, to_int(equal(5)))`` accepts ``"5"``.
The type is still checked first (the raw value is a ``str`` here); a value that can't be
coerced fails with the coercion error. Mirror: ``to_float``.
"""
from validate_nested import validate
from validate_nested.lambdas import equal, to_int


def test_to_int_coerces_then_validates():
    record = {
        "params": {
            "limit": "5",
        },
    }
    model = {"params.limit": (str, to_int(equal(5)))}
    assert validate(record, model).ok


def test_to_int_value_mismatch_after_coercion():
    record = {
        "params": {
            "limit": "6",
        },
    }
    model = {"params.limit": (str, to_int(equal(5)))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [params.limit] should be equal to 5, got 6"
    )


def test_to_int_non_numeric_is_reported():
    """A value that can't be coerced fails. The exact coercion-error text is Python's
    own (version-dependent), so we only assert it's surfaced."""
    record = {
        "params": {
            "limit": "abc",
        },
    }
    model = {"params.limit": (str, to_int(equal(5)))}
    r = validate(record, model)

    assert not r.ok
    assert "error on 'abc'" in r.report()
