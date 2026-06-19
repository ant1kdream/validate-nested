"""Model-parsing coverage (process_validation_rules) — ported from the original
test_assert_tools.py."""
import pytest

from validate_nested import process_validation_rules
from validate_nested.lambdas import (
    approx, contains, empty, ends, equal, exists_in, in_range, less, more,
    non_zero, not_equal, not_exist, opt, positive_number, required, skip,
    split_positive_numbers, to_float, to_int, undefined, valid_score, length,
)

DEFAULT_BOOLEAN_RULES = {
    "not_exist": False,
    "required": False,
    "opt": False,
    "undefined": False,
    "empty": False,
    "not_empty": False,
    "skip": False,
    "to_int": False,
    "to_float": False,
    "hard_assert": False,
}

BOOLEAN_CASES = [
    (required(), {"required": True, "not_empty": True}),
    (not_exist(), {"not_exist": True, "not_empty": True}),
    (opt(), {"opt": True, "not_empty": True}),
    (undefined(), {"undefined": True, "not_empty": False}),
    (empty(), {"empty": True, "not_empty": False}),
    (skip(), {"skip": True, "not_empty": True}),
    (to_int(), {"to_int": True, "not_empty": True}),
    (to_float(), {"to_float": True, "not_empty": True}),
]


@pytest.mark.parametrize("rules, overrides", BOOLEAN_CASES, ids=[str(c[0]) for c in BOOLEAN_CASES])
def test_boolean_rules(rules, overrides):
    type_hint, validators, processed = process_validation_rules(rules)
    expected = {**DEFAULT_BOOLEAN_RULES, **overrides}
    assert processed == expected
    assert len(validators) == 0


VALIDATOR_CASES = [
    ({0: "<function equal.<locals>.<lambda>"}, (str, equal("5"))),
    ({0: "<function equal.<locals>.<lambda>", 1: "<function less.<locals>.<lambda>"}, (str, equal("5"), less(4))),
    ({0: "<function length.<locals>.<lambda>"}, (str, length(3))),
    ({0: "<function not_equal.<locals>.<lambda>"}, (int, not_equal(3))),
    ({0: "<function approx.<locals>.<lambda>"}, (int, approx(3))),
    ({0: "<function exists_in.<locals>.<lambda>"}, (int, exists_in((3, 4)))),
    ({0: "<function contains.<locals>.<lambda>"}, (str, contains("val"))),
    ({0: "<function ends.<locals>.<lambda>"}, (str, ends("val"))),
    ({0: "<function in_range.<locals>.<lambda>"}, (int, in_range(0, 5))),
    ({0: "<function less.<locals>.<lambda>"}, (int, less(0))),
    ({0: "<function more.<locals>.<lambda>"}, (int, more(0))),
    ({0: "<function <lambda>"}, (int, valid_score)),
    ({0: "<function <lambda>"}, (int, positive_number)),
    ({0: "<function <lambda>"}, (int, non_zero)),
    ({0: "<function <lambda>"}, (list, split_positive_numbers)),
]


@pytest.mark.parametrize("details, rules", VALIDATOR_CASES, ids=[str(c[0]) for c in VALIDATOR_CASES])
def test_validators(details, rules):
    type_hint, validators, processed = process_validation_rules(rules)
    assert len(validators) == len(details)
    for i, expected_name in details.items():
        assert expected_name in str(validators[i][0])


TYPE_HINT_CASES = [str, int, float, list, dict, (int, float), (list, dict)]


@pytest.mark.parametrize("rules", TYPE_HINT_CASES, ids=[str(c) for c in TYPE_HINT_CASES])
def test_type_hint(rules):
    type_hint, validators, processed = process_validation_rules(rules)
    assert type_hint == rules
