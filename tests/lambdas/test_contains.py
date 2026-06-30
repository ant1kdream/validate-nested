"""``contains(x)`` — substring for strings, or "has all of" for lists.

Related: ``ends`` (suffix), ``exists_in`` (value is one of), ``count`` (how many times).
"""
from validate_nested import validate
from validate_nested.lambdas import contains


def test_contains_substring_passes():
    record = {
        "document": {
            "path": "s3://bucket/reports/q4.pdf",
        },
    }
    model = {"document.path": (str, contains("/reports/"))}
    assert validate(record, model).ok


def test_contains_substring_fails():
    record = {
        "document": {
            "path": "s3://bucket/tmp/q4.pdf",
        },
    }
    model = {"document.path": (str, contains("/reports/"))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [document.path] should contain '/reports/', got 's3://bucket/tmp/q4.pdf'"
    )


def test_contains_all_list_items_fails():
    record = {
        "post": {
            "tags": ["news"],
        },
    }
    model = {"post.tags": (list, contains(["news", "urgent"]))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [post.tags] should contain all of ['news', 'urgent'], got ['news']"
    )
