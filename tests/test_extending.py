"""Extending validate-nested: custom validators and custom failure formatting.

These are the supported extension points — no engine changes, no subclassing. A custom
validator plugs into a model exactly where a built-in would, including over ``[*]`` list
items; a custom formatter changes how failures render in ``r.report()``.
"""
from validate_nested import validate
from validate_nested.lambdas import LambdaInfo, equal, predicate


# ── custom validator, the short way: predicate(func, message) ──────────────────
def test_custom_validator_with_predicate_fails():
    """Wrap any callable into a one-off validator; the engine appends ', got <value>'."""
    is_even = predicate(lambda v: v % 2 == 0, "should be even")
    record = {
        "cart": {
            "item_count": 3,
        },
    }
    model = {"cart.item_count": (int, is_even)}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [cart.item_count] should be even, got 3"
    )


def test_custom_validator_with_predicate_passes():
    is_even = predicate(lambda v: v % 2 == 0, "should be even")
    record = {
        "cart": {
            "item_count": 4,
        },
    }
    assert validate(record, {"cart.item_count": (int, is_even)}).ok


# ── custom validator, the explicit way: a function returning LambdaInfo ─────────
# This is how the built-ins (equal, length, ...) are written — use it for a reusable,
# parametrised validator with a rich message.
def divisible_by(n):
    return LambdaInfo(
        func_lambda=lambda v: v % n == 0,
        lambda_assert_msg=f"should be divisible by {n}",
        lambda_details=f"divisible_by({n})",
    )


def test_custom_validator_with_lambdainfo_fails():
    record = {
        "batch": {
            "size": 10,
        },
    }
    model = {"batch.size": (int, divisible_by(3))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [batch.size] should be divisible by 3, got 10"
    )


def test_custom_validator_with_lambdainfo_passes():
    record = {
        "batch": {
            "size": 9,
        },
    }
    assert validate(record, {"batch.size": (int, divisible_by(3))}).ok


# ── custom validators work over [*] list items too ─────────────────────────────
def test_custom_validator_over_list_items():
    not_blank = predicate(lambda v: v.strip() != "", "should not be blank")
    record = {
        "items": [
            {"name": "Widget"},
            {"name": "   "},
        ],
    }
    model = {"items[*].name": (str, not_blank)}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [items[1].name] should not be blank, got '   '"
    )


# ── custom failure formatting: report(formatter=...) ───────────────────────────
def test_custom_formatter_one_liner():
    """Pass any callable ``Failure -> str`` to render each failure your own way.
    The header line stays; only the per-failure lines use your formatter."""
    record = {
        "response": {
            "status": "error",
            "code": 500,
        },
    }
    model = {
        "response.status": (str, equal("ok")),
        "response.code": (int, equal(0)),
    }
    r = validate(record, model)

    def one_liner(f):
        return f"{f.path} :: {f.message}"

    assert r.report(formatter=one_liner) == (
        "2 validation failure(s):\n"
        "response.status :: should be equal to 'ok', got 'error'\n"
        "response.code :: should be equal to 0, got 500"
    )


def test_raw_failures_are_available():
    """Beyond report(), you can consume Failure objects directly (path + message)."""
    record = {
        "user": {
            "age": -1,
        },
    }
    model = {"user.age": (int, predicate(lambda v: v >= 0, "should be >= 0"))}
    r = validate(record, model)

    assert [(f.path, f.message) for f in r.failures] == [
        ("user.age", "should be >= 0, got -1"),
    ]
