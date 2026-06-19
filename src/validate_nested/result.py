"""Neutral, framework-agnostic result types.

The engine never raises or asserts on its own — ``validate`` returns a :class:`Result`.
You decide what to do with it; the idiomatic immediate check is::

    r = validate(record, model)
    assert r.ok, r.report()
"""
from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass
class Failure:
    """A single failed check.

    ``path`` is where in the record it failed; ``message`` is the default
    human-readable reason (expected vs actual).
    """

    path: str
    message: str

    def __str__(self):
        return f"[{self.path}] {self.message}"


def format_failure(failure: "Failure") -> str:
    """Default single-failure renderer (override by passing ``formatter=`` to report)."""
    return f"  - [{failure.path}] {failure.message}"


def render_failures(failures: List["Failure"], formatter: Callable[["Failure"], str] = None) -> str:
    """Join failures into one readable multi-line message."""
    fmt = formatter or format_failure
    header = f"{len(failures)} validation failure(s):"
    return "\n".join([header, *(fmt(f) for f in failures)])


@dataclass
class Result:
    """Outcome of a :func:`validate_nested.validate` call.

    * ``ok``       — True when no check failed
    * ``failures`` — list of :class:`Failure`
    * ``skipped``  — reason string if a ``skip()`` rule fired, else None
    """

    ok: bool
    failures: List[Failure] = field(default_factory=list)
    skipped: Optional[str] = None

    def __bool__(self):
        return self.ok

    def report(self, formatter: Callable[[Failure], str] = None) -> str:
        """Render this result as a readable message — meant for an assert message::

            assert r.ok, r.report()

        Pass ``formatter`` (a callable ``Failure -> str``) to customise each line.
        """
        if self.skipped is not None:
            return f"skipped: {self.skipped}"
        if not self.failures:
            return "ok"
        return render_failures(self.failures, formatter)
