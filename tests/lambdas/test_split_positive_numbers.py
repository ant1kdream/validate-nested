"""``split_positive_numbers`` — every comma-separated part of the string is a number
``>= 0`` (a parameterless predefined validator). Related: ``split_length``,
``positive_number``.
"""
from validate_nested import validate
from validate_nested.lambdas import split_positive_numbers


def test_split_positive_numbers_passes():
    record = {
        "geo": {
            "bbox": "5, 4, 3",
        },
    }
    model = {"geo.bbox": (str, split_positive_numbers)}
    assert validate(record, model).ok


def test_split_positive_numbers_fails():
    record = {
        "geo": {
            "bbox": "5, -4, 3",
        },
    }
    model = {"geo.bbox": (str, split_positive_numbers)}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [geo.bbox] all comma-separated parts should be >= 0, got '5, -4, 3'"
    )
