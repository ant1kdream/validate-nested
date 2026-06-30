"""``empty(...)`` — the value's ``len()`` must be 0 (empty list / string / dict).

The opposite of the default ``not_empty``. Related: ``not_empty`` (len > 0),
``length(n)`` (exact size), ``undefined`` (don't care about emptiness).
"""
from validate_nested import validate
from validate_nested.lambdas import empty


def test_empty_list_passes():
    record = {
        "report": {
            "errors": [],
        },
    }
    model = {"report.errors": empty(list)}
    assert validate(record, model).ok


def test_empty_list_fails():
    record = {
        "report": {
            "errors": ["disk full"],
        },
    }
    model = {"report.errors": empty(list)}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [report.errors] expected empty, got length 1"
    )


def test_empty_string_passes():
    record = {
        "user": {
            "middle_name": "",
        },
    }
    model = {"user.middle_name": empty(str)}
    assert validate(record, model).ok


def test_empty_over_list_items_passes():
    record = {
        "items": [
            {"errors": []},
            {"errors": []},
        ],
    }
    model = {"items[*].errors": empty(list)}
    assert validate(record, model).ok


def test_empty_list_item_fails():
    record = {
        "items": [
            {"errors": []},
            {"errors": ["bad sku"]},
        ],
    }
    model = {"items[*].errors": empty(list)}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [items[1].errors] expected empty, got length 1"
    )
