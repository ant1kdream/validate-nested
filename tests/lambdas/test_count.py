"""``count(value, amount)`` — ``value`` appears exactly ``amount`` times in the collection.

Two counts can be combined in one tuple. Related: ``contains``, ``length``.
"""
from validate_nested import validate
from validate_nested.lambdas import count


def test_count_passes():
    record = {
        "poll": {
            "votes": [1, 1, 1, 0, 0, 0],
        },
    }
    model = {"poll.votes": (list, count(value=1, amount=3), count(value=0, amount=3))}
    assert validate(record, model).ok


def test_count_fails():
    record = {
        "poll": {
            "votes": [1, 1, 1],
        },
    }
    model = {"poll.votes": (list, count(value=1, amount=2))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [poll.votes] should contain 1 exactly 2 time(s), got [1, 1, 1]"
    )
