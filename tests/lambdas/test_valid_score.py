"""``valid_score`` — a probability-like score in ``0 < value <= 1`` (a parameterless
predefined validator). Related: ``in_range``, ``positive_number``.
"""
from validate_nested import validate
from validate_nested.lambdas import valid_score


def test_valid_score_passes():
    record = {
        "match": {
            "confidence": 0.91,
        },
    }
    model = {"match.confidence": (float, valid_score)}
    assert validate(record, model).ok


def test_valid_score_above_one_fails():
    record = {
        "match": {
            "confidence": 1.01,
        },
    }
    model = {"match.confidence": (float, valid_score)}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [match.confidence] should be a valid score (0 < v <= 1), got 1.01"
    )
