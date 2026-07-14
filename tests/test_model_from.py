"""``model_from`` — freeze a known-good record into a model, then loosen what varies.

The whole point is validating *other* records against a frozen reference: build the
model from yesterday's good response, run today's response through it. The generated
model is a PLAIN model (same DSL as hand-written) — print it, paste it into a test,
edit it by hand.
"""
import pytest

from validate_nested import model_from, validate
from validate_nested.lambdas import contains

REFERENCE = {
    "user": {"name": "Alice", "age": 30},
    "score": 0.87,
    "items": [
        {"sku": "A1", "qty": 2},
        {"sku": "B2", "qty": 1},
    ],
}


def test_frozen_reference_catches_drift_in_another_record():
    """The core scenario: the model is built from the REFERENCE, the record under test
    is a DIFFERENT response of the same shape — and the drifted field is caught."""
    model = model_from(REFERENCE, approximate={"score": 0.05})

    actual = {
        "user": {"name": "Alice", "age": 31},        # <- drifted
        "score": 0.89,                               # within tolerance
        "items": [
            {"sku": "A1", "qty": 2},
            {"sku": "B2", "qty": 1},
        ],
    }
    r = validate(actual, model)

    assert not r.ok
    assert [(f.path, f.message) for f in r.failures] == [
        ("user.age", "should be equal to 30, got 31"),
    ]


def test_same_shape_record_passes():
    model = model_from(REFERENCE)
    identical_twin = {
        "user": {"name": "Alice", "age": 30},
        "score": 0.87,
        "items": [{"sku": "A1", "qty": 2}, {"sku": "B2", "qty": 1}],
    }
    assert validate(identical_twin, model).ok


def test_generated_model_is_the_model_you_would_write():
    """The output is an ordinary model dict — equivalent to writing by hand:

        model = {
            "user":         dict,
            "user.name":    (str, equal("Alice")),
            "user.age":     (int, equal(30)),
            "score":        (float, equal(0.87)),
            "items":        (list, length(2)),
            "items[0]":     dict,
            "items[0].sku": (str, equal("A1")),
            ...
        }

    print(model) shows exactly that (LambdaInfo reprs as its rule, e.g. ``equal(30):
    lambda v: v == 30``) — so model_from also works as a scaffold generator: print,
    paste into your test, edit."""
    model = model_from(REFERENCE)

    assert model["user"] is dict
    assert model["user.name"][0] is str and "equal(Alice)" in repr(model["user.name"][1])
    assert model["user.age"][0] is int and "equal(30)" in repr(model["user.age"][1])
    assert model["items"][0] is list and "length(2)" in repr(model["items"][1])
    assert model["items[0].sku"][0] is str and "equal(A1)" in repr(model["items[0].sku"][1])

    # and the printed form is copy-pasteable knowledge, not an opaque object
    printed = repr(model)
    assert "'user.age'" in printed and "equal(30)" in printed


def test_ignore_matches_star_templates():
    """Volatile per-item fields (uuids, timestamps) are ignored by their [*] template:
    presence and type still checked, values not compared."""
    reference = {"items": [{"uuid": "aaa", "n": 1}, {"uuid": "bbb", "n": 2}]}
    model = model_from(reference, ignore={"items[*].uuid"})

    actual = {"items": [{"uuid": "zzz", "n": 1}, {"uuid": "yyy", "n": 2}]}
    assert validate(actual, model).ok

    # but a missing uuid is still a failure — ignore is not opt()
    broken = {"items": [{"n": 1}, {"uuid": "yyy", "n": 2}]}
    assert not validate(broken, model).ok


def test_approximate_all_applies_to_every_number():
    reference = {"cpu": 0.42, "mem": 0.73}
    model = model_from(reference, approximate={"all": 0.1})

    assert validate({"cpu": 0.48, "mem": 0.70}, model).ok
    assert not validate({"cpu": 0.60, "mem": 0.70}, model).ok


def test_overwrite_replaces_the_generated_rule():
    """overwrite hands the path back to you: any hand-written rule, same DSL."""
    model = model_from(REFERENCE, overwrite={"user.name": (str, contains("Ali"))})

    renamed = {
        "user": {"name": "Alison", "age": 30},
        "score": 0.87,
        "items": [{"sku": "A1", "qty": 2}, {"sku": "B2", "qty": 1}],
    }
    assert validate(renamed, model).ok


def test_mandatory_wraps_containers_for_fail_fast():
    """mandatory="all" wraps container rules with required(): when the structure itself
    is broken, validation stops instead of cascading a failure into every child path."""
    model = model_from(REFERENCE, mandatory="all")

    truncated = {
        "user": {"name": "Alice", "age": 30},
        "score": 0.87,
        "items": [{"sku": "A1", "qty": 2}],          # <- one item lost
    }
    r = validate(truncated, model)

    assert not r.ok
    # one structural failure (items length), not a spray of items[1].* misses
    assert len(r.failures) == 1
    assert r.failures[0].path == "items"


def test_empty_values_freeze_as_empty():
    """Empty in the reference means "must be empty", not "must be absent"."""
    reference = {"note": "", "tags": [], "meta": {}}
    model = model_from(reference)

    assert validate({"note": "", "tags": [], "meta": {}}, model).ok
    r = validate({"note": "x", "tags": [1], "meta": {"k": 1}}, model)
    assert len(r.failures) == 3


def test_reference_must_be_a_non_empty_dict():
    with pytest.raises(ValueError):
        model_from({})
    with pytest.raises(ValueError):
        model_from([1, 2, 3])
