"""``exists_in(collection)`` — the value must be one of ``collection`` (an enum check).

Related: ``equal`` (a single value), ``contains`` (substring / superset).
"""
from validate_nested import validate
from validate_nested.lambdas import exists_in


def test_exists_in_passes():
    record = {
        "ticket": {
            "status": "open",
        },
    }
    model = {"ticket.status": (str, exists_in(("open", "pending", "closed")))}
    assert validate(record, model).ok


def test_exists_in_fails():
    record = {
        "ticket": {
            "status": "archived",
        },
    }
    model = {"ticket.status": (str, exists_in(("open", "pending", "closed")))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [ticket.status] should be one of ['open', 'pending', 'closed'], got 'archived'"
    )


def test_exists_in_over_list_items():
    record = {
        "events": [
            {"level": "info"},
            {"level": "warn"},
        ],
    }
    model = {"events[*].level": (str, exists_in(("info", "warn", "error")))}
    assert validate(record, model).ok
