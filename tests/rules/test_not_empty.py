"""``not_empty(...)`` — the value's ``len()`` must be > 0.

This is the **default** for sized types (list / str / dict), so a bare ``list`` already
requires non-empty; ``not_empty()`` just states it explicitly. Opposite: ``empty()``. To
not care about emptiness at all, use ``undefined()``.
"""
from validate_nested import validate
from validate_nested.lambdas import not_empty


def test_not_empty_explicit_passes():
    record = {
        "report": {
            "warnings": ["low disk"],
        },
    }
    model = {"report.warnings": not_empty(list)}
    assert validate(record, model).ok


def test_not_empty_explicit_fails():
    record = {
        "report": {
            "warnings": [],
        },
    }
    model = {"report.warnings": not_empty(list)}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [report.warnings] expected non-empty, got empty"
    )


def test_not_empty_is_the_default_for_sized_types():
    """A bare ``list`` already requires non-empty — ``not_empty()`` is implicit."""
    record = {
        "report": {
            "warnings": [],
        },
    }
    model = {"report.warnings": list}   # no not_empty(), yet still required non-empty
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [report.warnings] expected non-empty, got empty"
    )


def test_not_empty_string_passes():
    record = {
        "user": {
            "name": "Ada",
        },
    }
    model = {"user.name": not_empty(str)}
    assert validate(record, model).ok


def test_not_empty_list_item_fails():
    record = {
        "items": [
            {"tags": ["a"]},
            {"tags": []},
        ],
    }
    model = {"items[*].tags": not_empty(list)}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [items[1].tags] expected non-empty, got empty"
    )
