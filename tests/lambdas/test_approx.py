"""``approx(x, delta=0.01)`` — numeric value within ``delta`` of ``x`` (``|v - x| <= delta``).

For floats where exact equality is fragile. Related: ``equal``, ``in_range``.
"""
from validate_nested import validate
from validate_nested.lambdas import approx


def test_approx_within_tolerance_passes():
    record = {
        "sensor": {
            "temperature": 21.03,
        },
    }
    model = {"sensor.temperature": (float, approx(21.0, delta=0.05))}
    assert validate(record, model).ok


def test_approx_outside_tolerance_fails():
    record = {
        "sensor": {
            "temperature": 25,
        },
    }
    model = {"sensor.temperature": (int, approx(21, delta=0.1))}
    r = validate(record, model)

    assert not r.ok
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [sensor.temperature] should be approximately 21 (±0.1), got 25"
    )


def test_approx_over_list_items():
    record = {
        "readings": [
            {"value": 0.99},
            {"value": 1.02},
        ],
    }
    model = {"readings[*].value": (float, approx(1.0, delta=0.05))}
    assert validate(record, model).ok
