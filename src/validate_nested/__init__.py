"""validate-nested — a tiny, framework-agnostic DSL for validating the shape of
nested dicts / JSON responses.

    from validate_nested import validate
    from validate_nested.lambdas import equal, length, empty

    model = {
        "ids": (list, length(3)),
        "ids[*]": dict,
        "state": (str, equal("ok")),
        "message": empty(str),
        "error_code": (int, equal(0)),
    }

    r = validate(response, model)        # -> Result(ok, failures, skipped)
    assert r.ok, r.report()              # idiomatic immediate check
"""
from validate_nested.engine import validate
from validate_nested.result import Failure, Result, format_failure, render_failures
from validate_nested.rules import ComplexRule, process_validation_rules
from validate_nested.soft import SoftValidator

__version__ = "0.1.0"

__all__ = [
    "validate",
    "SoftValidator",
    "Result",
    "Failure",
    "format_failure",
    "render_failures",
    "ComplexRule",
    "process_validation_rules",
    "lambdas",
]

from validate_nested import lambdas  # noqa: E402  (re-exported for convenience)
