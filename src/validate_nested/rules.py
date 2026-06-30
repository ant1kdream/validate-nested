"""Model parsing: turns a model value (a type, a marker, a validator, or a tuple of
those) into ``(type_hint, validators, boolean_rules)`` the engine can act on."""
import logging
import re
from collections import namedtuple

from validate_nested._utils.paths import dict_paths

log = logging.getLogger("validate_nested")

# A model entry may be wrapped to attach per-path options, e.g. ComplexRule(value, options)
ComplexRule = namedtuple("ComplexRule", ["value", "options"])


class CustomType(type):
    def __repr__(cls):
        return f"<class {cls.__name__}>"


class NotExists(metaclass=CustomType):
    """Sentinel returned by path lookups when a key is missing in the record."""

    def __str__(self):
        return "not exists in dict"


def convert_paths_to_template(record):
    """Index the record's concrete paths under their ``[*]`` wildcard template, so a
    model key like ``ids[*]`` can be expanded to ``ids[0]``, ``ids[1]`` ..."""
    t_dict = {}
    for path in dict_paths(record):
        path = path.replace(".[", "[")
        template_path = re.sub(r"\[.*?\]", "[*]", path)
        if template_path not in t_dict:
            t_dict[template_path] = []
        if path not in t_dict[template_path]:
            t_dict[template_path].append(path)
    return t_dict


def unpack_rules(items, validators):
    """Flatten a (possibly nested) rule tuple, peeling LambdaInfo validators off into
    ``validators`` and returning the remaining markers/types."""
    unpacked = []

    if isinstance(items, tuple):
        for item in items:
            if isinstance(item, tuple) and any(
                callable(sub_item) and sub_item.__name__ == "<lambda>"
                for sub_item in item
            ):
                validators.append(list(item))
            else:
                unpacked.extend(unpack_rules(item, validators))
    else:
        unpacked.append(items)

    return unpacked


def process_validation_rules(validation_rules):
    """Split a model value into a type hint, a list of validators and a flat dict of
    boolean rule flags.

    Rule semantics:
      * ``required`` — stop further checks and fail if this rule failed
      * ``skip``     — signal a skip if this rule failed (host decides what to do)
      * ``opt``      — value may be absent; if absent, pass (unless combined with required)
      * ``not_exist``— assert the path is absent
      * ``undefined``— don't assume empty-vs-filled (skips the len check)
      * ``empty`` / ``not_empty`` — assert len == 0 / len > 0 (not_empty is the default)
      * ``to_int`` / ``to_float`` — coerce the value before running validators
    """
    type_hint, validators = None, []
    boolean_rules = dict(
        {
            "not_exist": False,
            "required": False,
            "opt": False,
            "undefined": False,
            "empty": False,
            "not_empty": True,
            "skip": False,
            "to_int": False,
            "to_float": False,
        }
    )

    # unpack the model body into markers/types (validators are peeled off in-place)
    unpacked_rules = unpack_rules(validation_rules, validators)

    # extract type hint(s)
    type_hint = tuple(item for item in unpacked_rules if isinstance(item, type))
    if len(type_hint) == 1:
        type_hint = type_hint[0]

    # extract boolean rules (marker strings)
    boolean_rules.update({item: True for item in unpacked_rules if isinstance(item, str)})

    # exclusive options
    if boolean_rules.get("empty"):
        boolean_rules["not_empty"] = False

    if boolean_rules.get("undefined"):
        boolean_rules["empty"] = False
        boolean_rules["not_empty"] = False

    log.debug(
        "processed rules: %r -> type_hint=%r validators=%r boolean_rules=%r",
        validation_rules, type_hint, validators, boolean_rules,
    )

    return type_hint, validators, boolean_rules
