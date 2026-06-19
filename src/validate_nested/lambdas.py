"""The validator DSL.

Two kinds of helpers:

* string-marker rules (``empty``, ``opt``, ``required``, ``skip`` ...) — return a
  tuple whose first item is a marker string the engine recognises;
* value validators (``length``, ``equal``, ``approx`` ...) — return a ``LambdaInfo``
  carrying the check plus a short reason used when it fails. The engine appends the
  actual value, e.g. ``should be equal to 'ok', got 'err'``.

Used inside a model:: ``{"ids": (list, length(3)), "state": (str, equal("ok"))}``.
"""
from collections import namedtuple


class LambdaInfo(
    namedtuple("LambdaInfo", ("func_lambda", "lambda_assert_msg", "lambda_details"))
):
    def __repr__(self):
        return f"{self.lambda_details}"


# ── string-marker (boolean) rules ──────────────────────────────────────────────
def to_int(*args):
    return "to_int", *args


def to_float(*args):
    return "to_float", *args


def undefined(*args):
    return "undefined", *args


def empty(*args):
    return "empty", *args


def not_empty(*args):
    return "not_empty", *args


def opt(*args):
    return "opt", *args


def skip(*args):
    return "skip", *args


def not_exist(*args):
    return "not_exist", *args


def required(*args):
    return "required", *args


# ── value validators (parametrised) ────────────────────────────────────────────
def length(size: int):
    return LambdaInfo(
        func_lambda=lambda v: len(v) == size,
        lambda_assert_msg=f"should have length {size}",
        lambda_details=f"{length.__name__}({size}): lambda v: len(v) == {size}",
    )


def equal(value):
    return LambdaInfo(
        func_lambda=lambda v: v == value,
        lambda_assert_msg=f"should be equal to {value!r}",
        lambda_details=f"{equal.__name__}({value}): lambda v: v == {value}",
    )


def lower_match(value):
    return LambdaInfo(
        func_lambda=lambda v: v.lower() == value.lower(),
        lambda_assert_msg=f"should be equal to {value!r} (case-insensitive)",
        lambda_details=f"{lower_match.__name__}({value.lower()}): lambda v: v.lower() == {value.lower()}",
    )


def not_equal(value):
    return LambdaInfo(
        func_lambda=lambda v: v != value,
        lambda_assert_msg=f"should not be equal to {value!r}",
        lambda_details=f"{not_equal.__name__}({value}): lambda v: v != {value}",
    )


def approx(value, delta=0.01):
    return LambdaInfo(
        # |v - value| <= delta (same semantics as the original pytest.approx(abs=delta),
        # but with no test-framework dependency)
        func_lambda=lambda v: abs(v - value) <= delta,
        lambda_assert_msg=f"should be approximately {value} (±{delta})",
        lambda_details=f"{approx.__name__}({value}): lambda v: abs(v - {value}) <= {delta}",
    )


def count(value, amount):
    return LambdaInfo(
        func_lambda=lambda v: v.count(value) == amount,
        lambda_assert_msg=f"should contain {value!r} exactly {amount} time(s)",
        lambda_details=f"{count.__name__}({value}): lambda v: v.count({value}) == {amount}",
    )


def exists_in(value):
    return LambdaInfo(
        func_lambda=lambda v: v in value,
        lambda_assert_msg=f"should be one of {list(value)}",
        lambda_details=f"{exists_in.__name__}({value}): lambda v: v in {value}",
    )


def contains(value):
    if isinstance(value, str):
        return LambdaInfo(
            func_lambda=lambda v: value in v,
            lambda_assert_msg=f"should contain {value!r}",
            lambda_details=f"{contains.__name__}({value}): lambda v: {value} in v",
        )
    elif isinstance(value, list):
        return LambdaInfo(
            func_lambda=lambda v: all(elem in v for elem in value),
            lambda_assert_msg=f"should contain all of {value}",
            lambda_details=f"{contains.__name__}({value}): lambda v: all(elem in v for elem in {value})",
        )


def ends(value):
    return LambdaInfo(
        func_lambda=lambda v: v.endswith(value),
        lambda_assert_msg=f"should end with {value!r}",
        lambda_details=f"{ends.__name__}({value}): lambda v: v.endswith(value)",
    )


def in_range(start, stop):
    return LambdaInfo(
        func_lambda=lambda v: start < v < stop,
        lambda_assert_msg=f"should be in range ({start}, {stop})",
        lambda_details=f"{in_range.__name__}({start}, {stop}): lambda v: {start} < v < {stop}",
    )


def less(value):
    return LambdaInfo(
        func_lambda=lambda v: v < value,
        lambda_assert_msg=f"should be less than {value}",
        lambda_details=f"{less.__name__}({value}): lambda v: v < {value}",
    )


def more(value):
    return LambdaInfo(
        func_lambda=lambda v: v > value,
        lambda_assert_msg=f"should be greater than {value}",
        lambda_details=f"{more.__name__}({value}): lambda v: v > {value}",
    )


def split_length(size, sep=","):
    return LambdaInfo(
        func_lambda=lambda v: len(v.split(sep)) == size,
        lambda_assert_msg=f"should split by {sep!r} into {size} parts",
        lambda_details=f"{split_length.__name__}({size}, {sep}): lambda v: len(v.split({sep})) == {size}",
    )


# ── parameter-less predefined validators ───────────────────────────────────────
valid_score = LambdaInfo(
    func_lambda=lambda v: 0 < v <= 1,
    lambda_assert_msg="should be a valid score (0 < v <= 1)",
    lambda_details="valid_score: lambda v: 0 < v <= 1",
)

positive_number = LambdaInfo(
    func_lambda=lambda v: v >= 0,
    lambda_assert_msg="should be >= 0",
    lambda_details="positive_number: lambda v: v >= 0",
)

non_zero = LambdaInfo(
    func_lambda=lambda v: v > 0,
    lambda_assert_msg="should be > 0",
    lambda_details="non_zero: lambda v: v > 0",
)

split_positive_numbers = LambdaInfo(
    func_lambda=lambda v: all([float(elem) >= 0 for elem in v.split(",")]),
    lambda_assert_msg="all comma-separated parts should be >= 0",
    lambda_details='split_positive_numbers: lambda v: all([float(elem) >= 0 for elem in v.split(",")])',
)
