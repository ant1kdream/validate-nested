"""Consumption modes: ``validate`` + ``Result.report``, and ``SoftValidator``.

(skip() is covered in test_skip.py; custom validators / formatter in test_extending.py.)
"""
import pytest

from validate_nested import SoftValidator, validate
from validate_nested.lambdas import equal


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
    """The documented immediate-check pattern."""
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
            soft.validate({"key": 5}, {"key": (int, equal(6))})
            soft.validate({"key": "a"}, {"key": int})
    assert "2 validation failure" in str(exc.value)


def test_soft_validator_passes_silently():
    with SoftValidator() as soft:
        soft.validate({"key": 5}, {"key": (int, equal(5))})
        soft.validate({"key": "a"}, {"key": str})
    assert soft.ok
