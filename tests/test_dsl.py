"""Positive / negative coverage of the DSL — ported from the original framework's
test_assert_tools.py, run against the standalone engine (no pytest globals)."""
import pytest

from validate_nested import validate
from validate_nested.lambdas import (
    approx, contains, count, empty, ends, equal, exists_in, in_range, length,
    less, more, non_zero, not_empty, not_equal, not_exist, opt, positive_number,
    required, skip, split_length, split_positive_numbers, to_float, to_int,
    undefined, valid_score,
)

# (id, record, model) — validate(record, model).ok must be True
POSITIVE = [
    ("equal", {"key": 5}, {"key": (int, equal(5))}),
    ("required not_exist", {"unreached_key": 0}, {"key": required(not_exist()), "unreached_key": int}),
    ("not_exist", {}, {"exist_value": not_exist()}),
    ("int type", {"key": 0}, {"key": int}),
    ("str type", {"key": "0"}, {"key": str}),
    ("float type", {"key": 0.0}, {"key": float}),
    ("double type", {"key": "value"}, {"key": (int, str)}),
    ("to_int", {"key": "5"}, {"key": (str, to_int(equal(5)))}),
    ("to_float", {"key": "5.0"}, {"key": (str, to_float(equal(5.0)))}),
    ("empty", {"key": []}, {"key": empty(list)}),
    ("not_empty", {"key": [5]}, {"key": not_empty(list)}),
    ("length", {"key": [5, 4]}, {"key": (list, length(2))}),
    ("not_equal", {"key": [5]}, {"key": (list, not_equal([4]))}),
    ("approx", {"key": 5}, {"key": (int, approx(4.9, delta=0.1))}),
    ("exists_in", {"key": 5}, {"key": (int, exists_in((4, 5)))}),
    ("contains", {"key": "value"}, {"key": (str, contains("val"))}),
    ("ends", {"key": "value"}, {"key": (str, ends("e"))}),
    ("in_range", {"key": 5}, {"key": (int, in_range(0, 6))}),
    ("less", {"key": 5}, {"key": (int, less(6))}),
    ("more", {"key": 5}, {"key": (int, more(4))}),
    ("split_length", {"key": "5, 4, 3"}, {"key": (str, split_length(3))}),
    ("valid_score", {"key": 0.91}, {"key": (float, valid_score)}),
    ("positive_number", {"key": 1}, {"key": (int, positive_number)}),
    ("non_zero", {"key": 1}, {"key": (int, non_zero)}),
    ("split_positive_numbers", {"key": "5, 4, 3"}, {"key": (str, split_positive_numbers)}),
    ("skip", {"key": 5}, {"key": skip(int)}),
    ("undefined", {"key": ""}, {"key": undefined(str)}),
    ("opt", {}, {"key": opt(str)}),
    ("opt required", {}, {"key": required(opt(str))}),
    ("count", {"key": [1, 1, 1, 0, 0, 0]}, {"key": (list, count(value=1, amount=3), count(value=0, amount=3))}),
]

# (id, record, model) — validate(record, model).ok must be False
NEGATIVE = [
    ("equal", {"key": 5}, {"key": (int, equal("5"))}),
    ("required not_exist", {"key": "value", "unreached_key": 0}, {"key": required(not_exist()), "unreached_key": str}),
    ("not_exist", {"exist_value": "any_value"}, {"exist_value": not_exist()}),
    ("int type", {"key": 0}, {"key": str}),
    ("str type", {"key": "0"}, {"key": int}),
    ("float type", {"key": "0.0"}, {"key": float}),
    ("double type", {"key": "value"}, {"key": (int, float)}),
    ("to_int", {"key": ["5"]}, {"key": (list, to_int(equal(5)))}),
    ("to_float", {"key": ["5.0"]}, {"key": (list, to_float(equal(5)))}),
    ("empty", {"key": [5]}, {"key": empty(list)}),
    ("not_empty", {"key": []}, {"key": not_empty(list)}),
    ("length", {"key": [5]}, {"key": (list, length(2))}),
    ("not_equal", {"key": [5]}, {"key": (list, not_equal([5]))}),
    ("approx", {"key": 5}, {"key": (int, approx(4, delta=0.1))}),
    ("exists_in", {"key": 5}, {"key": (int, exists_in((4, 3)))}),
    ("contains", {"key": "value"}, {"key": (str, contains("other"))}),
    ("ends", {"key": "value"}, {"key": (str, ends("u"))}),
    ("in_range", {"key": 5}, {"key": (int, in_range(0, 4))}),
    ("less", {"key": 5}, {"key": (int, less(4))}),
    ("more", {"key": 5}, {"key": (int, more(6))}),
    ("split_length", {"key": "5, 4, 3"}, {"key": (str, split_length(2))}),
    ("valid_score", {"key": 1.01}, {"key": (float, valid_score)}),
    ("positive_number", {"key": -1.01}, {"key": (float, positive_number)}),
    ("non_zero", {"key": 0}, {"key": (int, non_zero)}),
    ("split_positive_numbers", {"key": "5, -4, 3"}, {"key": (str, split_positive_numbers)}),
    ("count", {"key": [1, 1, 1, 0, 0, 0]}, {"key": (list, count(value=1, amount=2), count(value=0, amount=2))}),
]


@pytest.mark.parametrize("record, model", [c[1:] for c in POSITIVE], ids=[c[0] for c in POSITIVE])
def test_positive(record, model):
    result = validate(record, model)
    assert result.ok, result.failures


@pytest.mark.parametrize("record, model", [c[1:] for c in NEGATIVE], ids=[c[0] for c in NEGATIVE])
def test_negative(record, model):
    result = validate(record, model)
    assert not result.ok
    assert result.failures  # at least one failure recorded


def test_wildcard_each_item():
    record = {"ids": [{"a": 1}, {"a": 2}]}
    model = {"ids": (list, length(2)), "ids[*]": dict}
    assert validate(record, model).ok


def test_wildcard_item_type_mismatch():
    record = {"ids": [{"a": 1}, "not-a-dict"]}
    model = {"ids[*]": dict}
    result = validate(record, model)
    assert not result.ok
    assert any("ids[1]" in f.path for f in result.failures)


def test_empty_model_raises():
    with pytest.raises(ValueError):
        validate({"k": 1}, {})
