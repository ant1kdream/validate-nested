"""Small dict/path helpers copied (and trimmed) from the original framework so the
library carries no external dependencies."""
import re


def dict_paths(d):
    """Yield every leaf/branch path in a nested dict/list as a dotted string,
    e.g. {"a": [{"b": 1}]} -> "a", "a[0]", "a[0].b"."""
    q = [(d, [])]
    while q:
        n, p = q.pop(0)
        if p:
            yield ".".join(map(str, p))
        if isinstance(n, dict):
            for k, v in n.items():
                q.append((v, p + [k]))
        elif isinstance(n, list):
            for i, v in enumerate(n):
                q.append((v, p + ["[" + str(i) + "]"]))


def path_getter(record, path, default=None):
    """Resolve a dotted/indexed path inside a nested dict/list, returning `default`
    if any segment is missing. Supports list indices: "a.b[0].c"."""
    if default is None:
        default = {}
    path_parts = [part for part in re.split(r"[\.\[\]]+", path) if part]
    value = record
    for part in path_parts:
        if isinstance(value, list) and part.isdigit():
            idx = int(part)
            if -len(value) <= idx < len(value):
                value = value[idx]
            else:
                return default
        elif isinstance(value, dict):
            value = value.get(part, default)
        else:
            return default
        if value == default:
            return default
    return value


def stringify_dict(d):
    """Recursively stringify every leaf of a dict/list (lambdas are shortened to their
    `<lambda>` head). Used to render rule/validation details safely."""
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, (dict, list)):
                d[k] = stringify_dict(v)
            else:
                if "<lambda>" in str(v):
                    d[k] = str(v).split("<lambda>")[0] + "<lambda>"
                else:
                    d[k] = str(v)
    elif isinstance(d, list):
        for i, v in enumerate(d):
            if isinstance(v, (dict, list)):
                d[i] = stringify_dict(v)
            else:
                if "<lambda>" in str(v):
                    d[i] = str(v).split("<lambda>")[0] + "<lambda>"
                else:
                    d[i] = str(v)
    return d
