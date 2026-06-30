"""Aggregation / gating: ``validate()`` returns a ``Result`` whose ``ok`` is True only
when EVERY model path passed — not just the last one — so ``if validate(...)`` is safe.

Regression guard: a passing *last* field must never mask an earlier failure (the engine
collects failures across all paths and derives ``ok = not failures``).
"""
from validate_nested import validate
from validate_nested.lambdas import equal, required


def test_ok_only_when_all_paths_pass():
    record = {
        "user": {
            "id": 7,
            "name": "Ada",
        },
    }
    model = {
        "user.id": int,
        "user.name": str,
    }
    assert validate(record, model).ok


def test_earlier_failure_not_masked_by_passing_last_field():
    """The LAST path passes, an earlier one fails -> overall must be False."""
    record = {
        "community_id": "stable-123",   # a string, expected int -> fails
        "count": 5,                     # ok, and it's the last path
    }
    model = {
        "community_id": int,
        "count": int,
    }
    r = validate(record, model)

    assert not r.ok
    assert [f.path for f in r.failures] == ["community_id"]


def test_all_failures_are_collected():
    record = {
        "a": "x",
        "b": "y",
        "c": 3,
    }
    model = {
        "a": int,
        "b": int,
        "c": int,
    }
    r = validate(record, model)

    assert not r.ok
    assert [f.path for f in r.failures] == ["a", "b"]


def test_bool_of_result_gates_correctly():
    """``if validate(...)`` works via ``Result.__bool__`` (== ``.ok``)."""
    assert bool(validate({"x": 1}, {"x": int})) is True
    assert bool(validate({"x": "1"}, {"x": int})) is False

    proceeded = False
    if validate({"x": 1}, {"x": int}):
        proceeded = True
    assert proceeded


def test_required_missing_stops_even_when_next_field_is_present_and_valid():
    """`if validate(...)` with a required gate: the gate is absent while the NEXT field
    is present and valid on its own -> the result is still False, only the required
    failure is reported, and the valid next field is never checked."""
    record = {
        # "order_id" (the required gate) is absent
        "status": "shipped",   # present and would pass on its own
    }
    model = {
        "order_id": required(str),
        "status": (str, equal("shipped")),
    }
    r = validate(record, model)

    assert not r.ok
    assert not bool(r)                                   # `if validate(...)` won't proceed
    assert [f.path for f in r.failures] == ["order_id"]  # status was never reached


def test_wildcard_aggregates_across_items():
    """One bad item is not masked by later passing items."""
    record = {
        "items": [
            {"price": 1.0},
            {"price": "x"},   # fails
            {"price": 3.0},   # passes, comes after the failure
        ],
    }
    model = {"items[*].price": float}
    r = validate(record, model)

    assert not r.ok
    assert [f.path for f in r.failures] == ["items[1].price"]
