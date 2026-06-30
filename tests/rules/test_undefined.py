"""``undefined(...)`` — don't assume empty-vs-filled: skip the (default) non-empty check.

Use it when a present field may legitimately be empty (``""`` / ``[]``). The type is
still checked; if the value is empty, any wrapped validators are skipped too.
"""
from validate_nested import validate
from validate_nested.lambdas import undefined


def test_undefined_allows_an_empty_value():
    """A bare ``str`` requires non-empty; ``undefined()`` relaxes that, so ``""`` passes."""
    record = {
        "user": {
            "middle_name": "",
        },
    }
    model = {"user.middle_name": undefined(str)}
    assert validate(record, model).ok


def test_without_undefined_an_empty_value_fails():
    """Contrast: the same field *without* undefined() fails the non-empty default."""
    record = {
        "user": {
            "middle_name": "",
        },
    }
    model = {"user.middle_name": str}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [user.middle_name] expected non-empty, got empty"
    )


def test_undefined_allows_a_filled_value():
    record = {
        "user": {
            "middle_name": "Quentin",
        },
    }
    model = {"user.middle_name": undefined(str)}
    assert validate(record, model).ok


def test_undefined_still_checks_the_type():
    record = {
        "user": {
            "middle_name": 123,
        },
    }
    model = {"user.middle_name": undefined(str)}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [user.middle_name] expected str, got int"
    )
