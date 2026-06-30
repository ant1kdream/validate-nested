"""Bare types — the simplest rule is just a Python type. A tuple of *types* is a union
("either of these"). A mismatched value reports ``expected X, got Y``; a tuple hint reads
``expected int or str``.
"""
from validate_nested import validate


def test_scalar_types_pass():
    record = {
        "user": {
            "id": 7,
            "name": "Ada",
            "score": 0.91,
            "active": True,
        },
    }
    model = {
        "user.id": int,
        "user.name": str,
        "user.score": float,
        "user.active": bool,
    }
    assert validate(record, model).ok


def test_type_mismatch_fails():
    record = {
        "user": {
            "id": "7",
        },
    }
    model = {"user.id": int}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [user.id] expected int, got str"
    )


def test_container_types_pass():
    record = {
        "order": {
            "items": [1, 2],
            "meta": {"source": "web"},
        },
    }
    model = {
        "order.items": list,
        "order.meta": dict,
    }
    assert validate(record, model).ok


def test_union_type_accepts_either():
    record = {
        "a": {"id": 7},
        "b": {"id": "X-7"},
    }
    model = {
        "a.id": (int, str),
        "b.id": (int, str),
    }
    assert validate(record, model).ok


def test_union_type_rejects_neither():
    record = {
        "x": [1, 2],
    }
    model = {"x": (int, str)}   # a list is neither
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [x] expected int or str, got list"
    )
