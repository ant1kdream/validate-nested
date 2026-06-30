"""``not_exist()`` — the path must be ABSENT. Present is the failure.

Useful for asserting a forbidden/deprecated key is gone. Combine with ``required`` to
also stop the rest of the model when it shows up. Related: ``opt`` (may be absent),
``required`` (must be present).
"""
from validate_nested import validate
from validate_nested.lambdas import equal, not_exist, required


def test_not_exist_absent_passes():
    """The forbidden key isn't there — pass."""
    record = {
        "config": {
            "name": "prod",
        },
    }
    model = {"config.deprecated_flag": not_exist()}
    assert validate(record, model).ok


def test_not_exist_present_fails():
    """The key is present -> failure, reporting its type."""
    record = {
        "config": {
            "name": "prod",
            "deprecated_flag": "yes",
        },
    }
    model = {"config.deprecated_flag": not_exist()}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [config.deprecated_flag] must be absent, got str"
    )


def test_required_not_exist_stops_the_rest():
    """``required(not_exist())``: if the forbidden key appears, fail AND stop — the keys
    after it (here a deliberately-wrong name) are not checked."""
    record = {
        "config": {
            "name": "prod",
            "deprecated_flag": True,
        },
    }
    model = {
        "config.deprecated_flag": required(not_exist()),
        "config.name": (str, equal("staging")),
    }
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [config.deprecated_flag] must be absent, got bool"
    )
