"""``skip()`` — when a skip-marked rule fails, validation short-circuits and the reason
is put on ``Result.skipped``.

The engine never skips by itself — it only flags ``Result.skipped``. There is no special
integration: you ``define`` whatever wrapper fits your suite and route the skip wherever
you want. Each test below wires the same ``skip()`` rule differently.
"""
import pytest

from validate_nested import ComplexRule, validate
from validate_nested.lambdas import equal, skip


def test_skip_fires_and_carries_the_reason():
    """A skip()-marked rule that fails -> Result.skipped holds the reason (and the rest
    of the model is not run). The default reason is the failure message."""
    record = {"feature": "n/a"}          # a string, not an int
    model = {"feature": skip(int)}
    r = validate(record, model)

    assert r.skipped == "expected int, got str"


def test_skip_does_not_fire_when_the_rule_passes():
    """If the skip-marked rule passes, nothing is skipped."""
    record = {"feature": 1}
    model = {"feature": skip(int)}
    r = validate(record, model)

    assert r.skipped is None
    assert r.ok


def test_wire_skip_to_pytest_skip():
    """Define a tiny wrapper that routes a fired skip to ``pytest.skip`` — no helper from
    the library, just your own function. (This test reports as *skipped* on purpose.)"""

    def validate_or_skip(record, model):
        r = validate(record, model)
        if r.skipped:
            pytest.skip(r.skipped)
        return r

    validate_or_skip({"feature": "n/a"}, {"feature": skip(int)})
    raise AssertionError("unreachable — we skipped above")


def test_wire_skip_to_a_custom_handler():
    """Or route it to your own mechanism — define any handler you like (a custom
    exception here; could be unittest's skipTest, a log call, etc.)."""

    class Skipped(Exception):
        pass

    def validate_or_handle(record, model):
        r = validate(record, model)
        if r.skipped:
            raise Skipped(r.skipped)
        return r

    with pytest.raises(Skipped):
        validate_or_handle({"feature": "n/a"}, {"feature": skip(int)})


def test_skip_with_a_custom_reason():
    """Override the default reason per field with ``ComplexRule(assert_msg=...)`` — handy
    when a changed field should skip the test with a clear explanation."""
    record = {"message": "edited"}
    model = {
        "message": ComplexRule(
            value=skip(str, equal("original")),
            options={"assert_msg": "message was changed, skipping the rest"},
        ),
    }
    r = validate(record, model)

    assert r.skipped == "message was changed, skipping the rest"
