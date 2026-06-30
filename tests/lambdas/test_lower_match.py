"""``lower_match(x)`` — case-insensitive string equality (``value.lower() == x.lower()``).

Related: ``equal`` (exact), ``ends`` / ``contains`` (partial).
"""
from validate_nested import validate
from validate_nested.lambdas import lower_match


def test_lower_match_passes():
    record = {
        "address": {
            "country": "de",
        },
    }
    model = {"address.country": (str, lower_match("DE"))}
    assert validate(record, model).ok


def test_lower_match_fails():
    record = {
        "address": {
            "country": "AB",
        },
    }
    model = {"address.country": (str, lower_match("cd"))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [address.country] should be equal to 'cd' (case-insensitive), got 'AB'"
    )
