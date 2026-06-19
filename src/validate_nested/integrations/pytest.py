"""Optional pytest glue (install the ``pytest`` extra to use it).

Maps the engine's neutral result onto pytest idioms:
  * a fired ``skip()`` rule  -> ``pytest.skip(reason)``
  * any other failure        -> ``pytest.fail(message)``

    from validate_nested.integrations.pytest import check

    def test_response():
        check(response.json(), {"state": (str, equal("ok"))})
"""
import pytest

from validate_nested.engine import validate


def check(record, model, formatter=None, **options):
    """Validate within a pytest test: skip if a skip() rule fired, fail on any other
    failure, otherwise return the Result."""
    result = validate(record, model, **options)
    if result.skipped is not None:
        pytest.skip(result.skipped)
    if not result.ok:
        pytest.fail(result.report(formatter), pytrace=False)
    return result
