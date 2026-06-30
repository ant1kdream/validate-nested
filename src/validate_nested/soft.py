"""Soft validation across several calls.

A single ``validate`` call already checks the *whole* model and reports every failure
at once. ``SoftValidator`` extends that across multiple calls in one block, raising a
single aggregated ``AssertionError`` at the end (handy in one test asserting several
records).

    with SoftValidator() as soft:
        soft.validate(resp_a, model_a)
        soft.validate(resp_b, model_b)
    # raises here if either failed, listing all failures
"""
from validate_nested.engine import validate
from validate_nested.result import render_failures


class SoftValidator:
    def __init__(self, formatter=None):
        self.formatter = formatter
        self.failures = []
        self.skipped = []

    def validate(self, record, model, **options):
        """Validate and accumulate failures; returns the individual Result."""
        result = validate(record, model, **options)
        self.failures.extend(result.failures)
        if result.skipped is not None:
            self.skipped.append(result.skipped)
        return result

    @property
    def ok(self):
        return not self.failures

    def report(self):
        """Readable message for everything collected so far."""
        return render_failures(self.failures, self.formatter)

    def assert_ok(self):
        """Raise now if anything has failed so far."""
        if self.failures:
            raise AssertionError(self.report())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # don't mask an exception already propagating out of the block
        if exc_type is not None:
            return False
        self.assert_ok()
        return False
