"""``opt(...)`` — the value may be absent.

If the path is missing the rule passes (and nothing below that path is checked); if it's
present it's validated normally — type and any validators still apply. Compose with
``required`` for the gate idiom (``required(opt(dict))``, see test_required.py).
"""
from validate_nested import validate
from validate_nested.lambdas import equal, opt


def test_opt_absent_passes():
    """The optional field isn't there — that's fine."""
    record = {
        "user": {
            "id": 7,
            "name": "Ada",
        },
    }
    model = {"user.nickname": opt(str)}
    assert validate(record, model).ok


def test_opt_present_and_valid_passes():
    """Present and the right type -> validated normally, passes."""
    record = {
        "user": {
            "id": 7,
            "nickname": "ada",
        },
    }
    model = {"user.nickname": opt(str)}
    assert validate(record, model).ok


def test_opt_present_but_wrong_type_fails():
    """Present but the wrong type -> opt does not excuse it."""
    record = {
        "user": {
            "nickname": 123,
        },
    }
    model = {"user.nickname": opt(str)}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [user.nickname] expected str, got int"
    )


def test_opt_present_still_runs_validators():
    """When present, validators apply too — here the value is the wrong string."""
    record = {
        "user": {
            "nickname": "bob",
        },
    }
    model = {"user.nickname": (opt(str), equal("ada"))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [user.nickname] should be equal to 'ada', got 'bob'"
    )
