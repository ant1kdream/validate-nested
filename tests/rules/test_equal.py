"""``equal(x)`` — the value must be exactly ``== x``.

Usually paired with a type in a tuple, e.g. ``(str, equal("CRACKED"))``: the type is
checked first, then the value. ``equal`` itself does no type coercion — ``5`` and
``"5"`` are not equal.

Related: ``not_equal``, ``lower_match`` (case-insensitive), ``exists_in`` (one-of).
"""
from copy import deepcopy

from validate_nested import validate
from validate_nested.lambdas import equal

# A realistic record: a face-search API response for one query.
RECORD = {
    "request_id": "req-7781",
    "result": {
        "state": "ok",
        "error_code": 0,
        "matches": {
            "count": 2,
            "top": {"gallery": "suspects", "score_bucket": "high"},
        },
    },
}


def test_equal_matches_on_nested_path():
    """A nested string equal to the expected literal passes."""
    model = {"result.state": (str, equal("ok"))}
    assert validate(RECORD, model).ok


def test_equal_mismatch_reports_the_path():
    """A wrong value fails and the failure points at the exact path."""
    record = deepcopy(RECORD)
    record["result"]["state"] = "error"

    model = {"result.state": (str, equal("ok"))}
    result = validate(record, model)

    assert not result.ok
    assert result.failures[0].path == "result.state"
    assert "should be equal" in result.failures[0].message


def test_equal_numeric():
    """Works for numbers too (here a nested int code)."""
    assert validate(RECORD, {"result.error_code": (int, equal(0))}).ok


def test_equal_is_type_strict():
    """No coercion: an int value is not equal to a string literal."""
    record = deepcopy(RECORD)
    record["result"]["error_code"] = 0

    # expecting the string "0" against an int 0 -> fails on type, then on value
    result = validate(record, {"result.error_code": (str, equal("0"))})
    assert not result.ok


def test_equal_on_deeply_nested_value():
    """Reaching several levels down to compare a leaf."""
    model = {"result.matches.top.score_bucket": (str, equal("high"))}
    assert validate(RECORD, model).ok
