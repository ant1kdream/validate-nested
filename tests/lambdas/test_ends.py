"""``ends(x)`` — the string must end with ``x`` (``value.endswith(x)``).

Related: ``contains`` (anywhere), ``lower_match`` (case-insensitive equality).
"""
from validate_nested import validate
from validate_nested.lambdas import ends


def test_ends_passes():
    record = {
        "upload": {
            "filename": "invoice.pdf",
        },
    }
    model = {"upload.filename": (str, ends(".pdf"))}
    assert validate(record, model).ok


def test_ends_fails():
    record = {
        "upload": {
            "filename": "invoice.docx",
        },
    }
    model = {"upload.filename": (str, ends(".pdf"))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [upload.filename] should end with '.pdf', got 'invoice.docx'"
    )


def test_ends_over_list_items():
    record = {
        "attachments": [
            {"name": "a.pdf"},
            {"name": "b.pdf"},
        ],
    }
    model = {"attachments[*].name": (str, ends(".pdf"))}
    assert validate(record, model).ok
