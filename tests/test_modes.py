"""Consumption modes: pure validate + Result.report, SoftValidator, skip semantics
and the optional pytest integration."""
import _pytest.outcomes as outcomes
import pytest

from validate_nested import SoftValidator, validate
from validate_nested.lambdas import equal, skip


# ── skip ───────────────────────────────────────────────────────────────────────
def test_skip_not_triggered_when_check_passes():
    # value matches the type -> skip rule never fires
    result = validate({"key": 5}, {"key": skip(int)})
    assert result.ok
    assert result.skipped is None


def test_skip_triggered_on_failure():
    # value is the wrong type -> skip()-marked failure short-circuits to skipped
    result = validate({"key": "x"}, {"key": skip(int)})
    assert result.skipped is not None
    assert "skipped" in result.report()


# ── pure: validate + Result.report ─────────────────────────────────────────────
def test_report_when_valid():
    r = validate({"key": 5}, {"key": (int, equal(5))})
    assert r.ok
    assert r.report() == "ok"


def test_report_renders_failures():
    r = validate({"key": 5}, {"key": (int, equal(6))})
    assert not r.ok
    msg = r.report()
    assert "1 validation failure" in msg
    assert "key" in msg


def test_idiomatic_assert():
    # the documented immediate-check pattern
    r = validate({"key": 5}, {"key": (int, equal(6))})
    with pytest.raises(AssertionError):
        assert r.ok, r.report()


def test_custom_formatter():
    r = validate({"key": 5}, {"key": (int, equal(6))})
    assert "CUSTOM::key" in r.report(formatter=lambda f: f"CUSTOM::{f.path}")


# ── SoftValidator (aggregate across calls) ─────────────────────────────────────
def test_soft_validator_collects_and_raises():
    with pytest.raises(AssertionError) as exc:
        with SoftValidator() as soft:
            soft.check({"key": 5}, {"key": (int, equal(6))})
            soft.check({"key": "a"}, {"key": int})
    assert "2 validation failure" in str(exc.value)


def test_soft_validator_passes_silently():
    with SoftValidator() as soft:
        soft.check({"key": 5}, {"key": (int, equal(5))})
        soft.check({"key": "a"}, {"key": str})
    assert soft.ok


# ── optional pytest integration ────────────────────────────────────────────────
def test_integration_check_skips():
    from validate_nested.integrations.pytest import check
    with pytest.raises(outcomes.Skipped):
        check({"key": "x"}, {"key": skip(int)})


def test_integration_check_fails():
    from validate_nested.integrations.pytest import check
    with pytest.raises(outcomes.Failed):
        check({"key": 5}, {"key": (int, equal(6))})


def test_integration_check_passes():
    from validate_nested.integrations.pytest import check
    result = check({"key": 5}, {"key": (int, equal(5))})
    assert result.ok
