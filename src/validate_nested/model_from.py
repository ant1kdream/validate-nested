"""Generate a validation model from a reference record.

Tired of writing models by hand? Freeze a known-good record (a "reference") into a
model, then loosen exactly the paths that vary::

    model = model_from(reference, ignore={"meta.request_id"}, approximate={"score": 0.01})
    r = validate(actual, model)         # a DIFFERENT record of the same shape

Building a model from a record and validating that same record back is pointless —
the point is validating *other* records against a frozen reference.

The generated model is a plain model — the same DSL you would write by hand. Print
it, copy it into a test, edit it: ``model_from`` doubles as a scaffold generator.

Rule mapping (reference value -> model rule):

  * scalar                -> ``(type, equal(value))``
  * number with a matching ``approximate`` delta -> ``(type, to_float(approx(value, delta)))``
  * ``""`` -> ``empty(str)``; ``[]`` -> ``empty(list)``; ``{}`` -> ``empty(dict)``
  * non-empty list        -> ``(list, length(n))``
  * non-empty dict        -> ``dict``
  * ``None``              -> ``NoneType``

Every option accepts a concrete path (``items[0].sku``) or its ``[*]`` template
(``items[*].sku``); ``approximate`` and ``mandatory`` also accept ``"all"``.
"""
import re

from validate_nested._utils.paths import dict_paths, path_getter
from validate_nested.lambdas import approx, empty, equal, length, required, to_float


def _star(path):
    return re.sub(r"\[.*?\]", "[*]", path)


def _rule_for(value, path, ignore, approximate, overwrite, mandatory):
    star = _star(path)

    # overwrite wins over everything: the caller supplies the whole rule
    if rule := (overwrite.get(path) or overwrite.get(star)):
        return rule

    # ignore: presence + type only, the value is not compared
    if ignore & {path, star}:
        return type(value)

    if isinstance(value, dict):
        if not value:
            return empty(dict)
        # mandatory wraps CONTAINER rules with required(): a broken structure fails
        # fast instead of cascading a failure into every child path
        if mandatory & {path, star, "all"}:
            return required(dict)
        return dict

    if isinstance(value, list):
        if not value:
            return empty(list)
        if mandatory & {path, star, "all"}:
            return required(list, length(len(value)))
        return list, length(len(value))

    # bool before int: isinstance(True, int) is True, but approx makes no sense here
    if isinstance(value, bool):
        return type(value), equal(value)

    if isinstance(value, (int, float)):
        if delta := (approximate.get(path) or approximate.get(star) or approximate.get("all")):
            return type(value), to_float(approx(float(value), delta=delta))
        return type(value), equal(value)

    if isinstance(value, str):
        if value == "":
            return empty(str)
        # numeric strings only — an explicit approximate match opts in to the coercion
        if delta := (approximate.get(path) or approximate.get(star)):
            return type(value), to_float(approx(float(value), delta=delta))
        return type(value), equal(value)

    if value is None:
        return type(None)

    # anything exotic falls back to a type check
    return type(value)


def model_from(reference, ignore=(), approximate=None, overwrite=None, mandatory=()):
    """Build a model dict from ``reference`` (see the module docstring for the mapping).

    * ``ignore``      — paths checked for presence/type only, value not compared
    * ``approximate`` — ``{path: delta}``: numeric value compared with a tolerance
      (``"all"`` applies to every number)
    * ``overwrite``   — ``{path: rule}``: replaces the generated rule entirely
    * ``mandatory``   — ``"all"`` or a set of container paths whose rules are wrapped
      with ``required()`` (fail fast on broken structure)
    """
    if not isinstance(reference, dict) or not reference:
        raise ValueError("reference must be a non-empty dict")

    ignore = set(ignore)
    approximate = dict(approximate or {})
    overwrite = dict(overwrite or {})
    mandatory = {"all"} if mandatory == "all" else set(mandatory or ())

    model = {}
    for raw_path in dict_paths(reference):
        path = raw_path.replace(".[", "[")
        value = path_getter(reference, path, default=None)
        model[path] = _rule_for(value, path, ignore, approximate, overwrite, mandatory)

    return model
