"""``split_length(n, sep=",")`` — splitting the string by ``sep`` yields exactly ``n`` parts.

Handy for compact CSV-ish fields. Related: ``split_positive_numbers``, ``length``.
"""
from validate_nested import validate
from validate_nested.lambdas import split_length


def test_split_length_passes():
    record = {
        "geo": {
            "bbox": "10,20,30,40",
        },
    }
    model = {"geo.bbox": (str, split_length(4))}
    assert validate(record, model).ok


def test_split_length_fails():
    record = {
        "geo": {
            "bbox": "10, 20, 30",
        },
    }
    model = {"geo.bbox": (str, split_length(2))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [geo.bbox] should split by ',' into 2 parts, got '10, 20, 30'"
    )


def test_split_length_custom_separator():
    record = {
        "path": {
            "segments": "a/b/c",
        },
    }
    model = {"path.segments": (str, split_length(3, sep="/"))}
    assert validate(record, model).ok
