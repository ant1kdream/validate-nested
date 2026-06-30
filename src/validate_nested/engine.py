"""The validation engine.

``validate(record, model)`` walks the model, runs every rule against the record and
returns a :class:`Result` — it never raises or asserts. Callers decide what to do::

    r = validate(record, model)
    assert r.ok, r.report()
"""
import logging

from validate_nested._utils.paths import path_getter
from validate_nested.result import Failure, Result
from validate_nested.rules import (
    ComplexRule,
    NotExists,
    convert_paths_to_template,
    process_validation_rules,
)

log = logging.getLogger("validate_nested")


def _type_name(t):
    """Readable type name(s): dict -> 'dict', (int, str) -> 'int or str'."""
    if isinstance(t, tuple):
        return " or ".join(getattr(x, "__name__", str(x)) for x in t)
    return getattr(t, "__name__", str(t))


class SkipSignal(Exception):
    """Raised internally when a ``skip()``-marked rule fails. ``validate`` catches it
    and turns it into ``Result.skipped`` — the engine itself never skips anything."""


class _Checker:
    """Validates a single (type_hint, path) pair against one record. Collects failures
    into ``self.failures`` instead of asserting."""

    def __init__(self, value, record, **kwargs):
        self.record = record
        self.failures = []

        # boolean rules from the model body
        self._opt = kwargs.pop("opt", None)
        self._required = kwargs.pop("required", None)
        self._not_exist = kwargs.pop("not_exist", None)
        self._undefined = kwargs.pop("undefined", None)
        self._empty = kwargs.pop("empty", None)
        self._not_empty = kwargs.pop("not_empty", None)
        self._skip = kwargs.pop("skip", None)
        self.validators = kwargs.pop("validators", [])

        # options
        self._additional_assert_msg = kwargs.pop("add_msg", None)
        self._replace_assert_msg = kwargs.pop("assert_msg", "")
        self._hard_assert = kwargs.pop("hard_assert", False)
        self._to_int = kwargs.pop("to_int", None)
        self._to_float = kwargs.pop("to_float", None)
        # any leftover kwargs are ignored (host-specific context)

        self.type_hint, self.original_path = value
        self.exist = True
        self.value = path_getter(self.record, self.original_path, default=NotExists())

    def _message(self, default):
        if self._replace_assert_msg:
            return self._replace_assert_msg
        if self._additional_assert_msg:
            return f"{self._additional_assert_msg}, {default}"
        return default

    def _check(self, default, condition):
        if condition:
            return
        msg = self._message(default)
        if self._skip:
            raise SkipSignal(msg)
        if self._hard_assert:
            raise AssertionError(msg)
        self.failures.append(Failure(path=self.original_path, message=msg))

    def _has_failures(self):
        return bool(self.failures)

    def process(self):
        value = self.value

        if isinstance(value, NotExists):
            self.exist = False

        # rule: not_exist() — the path must be absent
        if self._not_exist:
            self._check(
                default=f"must be absent, got {_type_name(type(value))}",
                condition=isinstance(value, NotExists),
            )
            return not self._has_failures()

        # rule: opt() — absent value is acceptable (unless required is also set)
        if self._opt and isinstance(value, NotExists):
            return not self._required

        # type check
        if isinstance(value, NotExists):
            assert_type_msg = "is missing"
        else:
            assert_type_msg = f"expected {_type_name(self.type_hint)}, got {_type_name(type(value))}"

        self._check(default=assert_type_msg, condition=isinstance(value, self.type_hint))

        # if a double type was given, narrow the type hint to the actual type for len checks
        if isinstance(self.type_hint, tuple):
            self.type_hint = type(value)

        # length checks (only for sized types that actually exist)
        if (
            self.exist
            and self.type_hint in (list, dict, str)
            and isinstance(value, self.type_hint)
        ):
            if self._empty:
                self._check(
                    default=f"expected empty, got length {len(value)}",
                    condition=(len(value) == 0),
                )
            if self._not_empty:
                self._check(
                    default="expected non-empty, got empty",
                    condition=(len(value) > 0),
                )
            if self._undefined and len(value) == 0:
                self.exist = False

        # validators ('lambdas') — only when the value exists
        if self.exist and self.validators:
            for lambda_info in self.validators:
                current_length = len(lambda_info)
                lambda_info.extend([""] * (3 - current_length))
                _lambda, lambda_assert_msg, _lambda_details = lambda_info

                template_value = value
                try:
                    if self._to_int:
                        template_value = int(value)
                    if self._to_float:
                        template_value = float(value)
                    result = _lambda(template_value)
                except Exception as error:
                    error_msg = f"{lambda_assert_msg} — error on {template_value!r}: {error}"
                    self._check(default=error_msg, condition=(not error))
                else:
                    if _lambda.__qualname__.startswith("length.<locals>.<lambda>"):
                        lambda_msg = f"{lambda_assert_msg}, got length {len(template_value)}"
                    else:
                        lambda_msg = f"{lambda_assert_msg}, got {template_value!r}"
                    self._check(default=lambda_msg, condition=result)

        return self.exist and not self._has_failures()


def validate(record, model, **options):
    """Validate ``record`` against ``model`` and return a :class:`Result`.

    Never raises (except ``ValueError`` on an empty model). All failed checks are
    collected into ``result.failures``; ``result.ok`` is True iff nothing failed.
    A fired ``skip()`` rule short-circuits and sets ``result.skipped``.
    """
    if not model:
        raise ValueError("model cannot be empty")

    log.debug("validating against model: %r", model)

    t_dict = convert_paths_to_template(record)
    failures = []

    for template_path, rules in model.items():
        path_options = dict(options)
        if isinstance(rules, ComplexRule):
            path_options.update(rules.options)
            rules = rules.value

        type_hint, validators, rule_options = process_validation_rules(rules)
        rule_options.update(path_options)

        # expand a wildcard template (ids[*]) to every concrete path, else use as-is
        concrete_paths = t_dict.get(template_path) or [template_path]

        path_ok = True
        for concrete_path in concrete_paths:
            checker = _Checker(
                value=(type_hint, concrete_path),
                record=record,
                validators=validators,
                **rule_options,
            )
            try:
                path_result = checker.process()
            except SkipSignal as signal:
                return Result(ok=not failures, failures=failures, skipped=str(signal))
            failures.extend(checker.failures)
            path_ok = path_ok and path_result

        # required + failed: stop and don't run the remaining model keys
        if rule_options.get("required") and not path_ok:
            break

    return Result(ok=not failures, failures=failures)
