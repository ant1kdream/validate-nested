# validate-nested

[![CI](https://github.com/ant1kdream/validate-nested/actions/workflows/ci.yml/badge.svg)](https://github.com/ant1kdream/validate-nested/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/validate-nested.svg)](https://pypi.org/project/validate-nested/)
[![Python versions](https://img.shields.io/pypi/pyversions/validate-nested.svg)](https://pypi.org/project/validate-nested/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**A tiny, dependency-free DSL for validating the *shape* of nested dicts / JSON responses
of any depth.**

Describe what a response should look like with a compact `model` dict and let the engine
check types, lengths, values, presence and per-item rules in one pass — then plug the
result into *any* test framework, or none.

```python
from validate_nested import validate
from validate_nested.lambdas import equal, length, more

# a nested response — dotted paths and [*] reach into it
response = {
    "status": "ok",
    "page": {"size": 3, "index": 0},
    "results": [
        {"id": "a1", "score": 0.91},
        {"id": "b2", "score": 0.40},   # <- too low
        {"id": "c3", "score": 0.95},
    ],
}

model = {
    "status":           (str, equal("ok")),    # top-level field
    "page.size":        (int, equal(3)),        # dotted path into a nested dict
    "results":          (list, length(3)),      # the list itself
    "results[*].id":    str,                    # a field of every list item
    "results[*].score": (float, more(0.5)),     # per-item value check
}

r = validate(response, model)        # -> Result(ok, failures, skipped); never raises
assert r.ok, r.report()
```

The failing item is reported by its exact path:

```text
1 validation failure(s):
  - [results[1].score] should be greater than 0.5, got 0.4
```

No classes to declare, no schema files — the model *is* the spec, inline where you use it.

### Nesting of any depth

Paths reach as deep as the data goes, and `[*]` wildcards stack — one flat model describes
a whole tree of orders → items → tags:

```python
from validate_nested import validate
from validate_nested.lambdas import equal, length, more, contains, not_empty

response = {
    "status": "ok",
    "meta": {
        "page": {"index": 0, "size": 2},
        "total": 2,
    },
    "orders": [
        {
            "id": "ORD-1",
            "customer": {"id": 42, "email": "ada@example.io"},
            "items": [
                {"sku": "A-1", "price": 9.99,  "tags": ["new"]},
                {"sku": "B-2", "price": 19.50, "tags": ["sale", "hot"]},
            ],
            "shipping": {"country": "DE", "zip": "10115"},
        },
    ],
}

model = {
    "status":                     (str, equal("ok")),
    "meta.page.index":            int,                  # dotted path, 3 levels down
    "meta.total":                 (int, more(0)),
    "orders":                     (list, not_empty()),
    "orders[*].id":               (str, not_empty()),
    "orders[*].customer.email":   (str, contains("@")),  # wildcard then a dotted path
    "orders[*].items":            (list, not_empty()),
    "orders[*].items[*].sku":     str,                   # wildcard inside a wildcard
    "orders[*].items[*].price":   (float, more(0)),
    "orders[*].items[*].tags[*]": str,                   # three wildcards deep
    "orders[*].shipping.country": (str, length(2)),
}

assert validate(response, model).ok
```

If, say, the second item of the first order had a negative price, that one element is
pinpointed — every other item still validates:

```text
1 validation failure(s):
  - [orders[0].items[1].price] should be greater than 0, got -1.0
```

---

## Why

- **Terse.** One dict describes a whole response. No model class per shape.
- **Structural + value checks together.** `(int, equal(0))`, `(list, length(3))`, `ids[*]`.
- **Framework-agnostic.** The engine returns data; *you* decide how to report (plain
  code, immediate `assert`, soft-aggregate, or pytest).
- **Zero dependencies.** Pure Python 3.8+. `pytest` is only needed to run the tests.

---

## Install

```bash
pip install validate-nested    # core, no dependencies
```

---

## The model

A model is `{path: rule}`. A **rule** is a type, a marker, a validator, or a tuple of those.

### Types

```python
{"age": int, "name": str, "tags": list, "meta": dict, "score": float}
```

A tuple of types is a union (`(int, str)` = "either"). See [tests/test_types.py](tests/test_types.py).

### Type + value validators

Combine a type with one or more validators in a tuple:

```python
{"score": (float, valid_score), "ids": (list, length(3)), "state": (str, equal("ok"))}
```

Each validator has its own file:
[`valid_score`](tests/lambdas/test_valid_score.py),
[`length`](tests/lambdas/test_length.py),
[`equal`](tests/lambdas/test_equal.py) — and the full list is in the validators table below.

### Paths & wildcards

Dotted paths, the `[*]` wildcard (every item of a list), and explicit indices:

```python
{
    "data.user.id": int,                  # nested
    "items[*]": dict,                     # every element of items
    "items[*].price": float,              # price of every element
    "items[0].sku": str,                  # a specific element by index
    "orders[*].items[*].price": float,    # nested wildcards
}
```

A failure carries the concrete index (`items[1].price`), an out-of-range index is
reported as missing, and the two styles can be mixed. See
[tests/test_lists.py](tests/test_lists.py).

### Presence & coercion markers

**Built-in only** (you can't define custom markers). They tune presence, emptiness and
coercion:

| Marker | Meaning |
|---|---|
| [`not_empty()`](tests/rules/test_not_empty.py) | `len > 0` (the **default** for sized types) |
| [`empty()`](tests/rules/test_empty.py) | `len == 0` |
| [`opt()`](tests/rules/test_opt.py) | value may be absent → passes if missing |
| [`required()`](tests/rules/test_required.py) | if this rule fails, stop and don't check the rest |
| [`not_exist()`](tests/rules/test_not_exist.py) | the path must be **absent** |
| [`undefined()`](tests/rules/test_undefined.py) | don't assume empty-vs-filled (skip the len check) |
| [`to_int()`](tests/rules/test_to_int.py) / [`to_float()`](tests/rules/test_to_float.py) | coerce before running validators, e.g. `(str, to_int(equal(5)))` |
| [`skip()`](tests/test_skip.py) | if this rule fails, signal a **skip** instead of a failure |

```python
{
    "id":       required(str),             # must be present, a string
    "tags":     not_empty(list),           # a non-empty list
    "notes":    empty(str),                # an empty string
    "nickname": opt(str),                  # may be absent
    "legacy":   not_exist(),               # must be absent
    "count":    (str, to_int(equal(5))),   # coerce "5" -> 5 before checking
}
```

Markers compose. The key idiom is `required(opt(...))` — an **optional gate**: the field
may be absent (then it and its children pass), but **if present** its shape is checked
first, and if that fails the children are skipped:

```python
model = {
    "profile":      required(opt(dict)),       # may be absent; if present, must be a dict
    "profile.name": (str, equal("Ada")),       # only reached when profile is a valid dict
}

validate({"other": 1},               model).ok   # True  — profile absent, children skipped
validate({"profile": {"name": "Ada"}}, model).ok # True  — present and valid
validate({"profile": "oops"},        model).ok   # False — [profile] expected dict, got str
```

(`required(not_exist())` composes the same way.) See
[tests/rules/test_required.py](tests/rules/test_required.py) and
[tests/rules/test_opt.py](tests/rules/test_opt.py).

### Validators — built-in (`from validate_nested.lambdas import ...`)

| Validator | Passes when |
|---|---|
| [`equal(x)`](tests/lambdas/test_equal.py) / [`not_equal(x)`](tests/lambdas/test_not_equal.py) | value `==` / `!=` x |
| [`length(n)`](tests/lambdas/test_length.py) | `len(value) == n` |
| [`approx(x, delta=0.01)`](tests/lambdas/test_approx.py) | `abs(value - x) <= delta` |
| [`contains(x)`](tests/lambdas/test_contains.py) | substring / all items in value |
| [`exists_in((a, b, ...))`](tests/lambdas/test_exists_in.py) | value is one of |
| [`in_range(a, b)`](tests/lambdas/test_in_range.py) | `a < value < b` |
| [`less(x)`](tests/lambdas/test_less.py) / [`more(x)`](tests/lambdas/test_more.py) | `value < x` / `value > x` |
| [`ends(x)`](tests/lambdas/test_ends.py) | `value.endswith(x)` |
| [`count(value, amount)`](tests/lambdas/test_count.py) | value appears `amount` times |
| [`split_length(n, sep=",")`](tests/lambdas/test_split_length.py) | `len(value.split(sep)) == n` |
| [`lower_match(x)`](tests/lambdas/test_lower_match.py) | case-insensitive equality |
| [`valid_score`](tests/lambdas/test_valid_score.py) / [`positive_number`](tests/lambdas/test_positive_number.py) / [`non_zero`](tests/lambdas/test_non_zero.py) | `0 < v <= 1` / `v >= 0` / `v > 0` |
| [`split_positive_numbers`](tests/lambdas/test_split_positive_numbers.py) | all comma-split parts `>= 0` |

```python
{
    "title":   (str, length(8)),                       # exactly 8 chars
    "status":  (str, exists_in(("open", "closed"))),   # one of
    "score":   (float, in_range(0, 1)),                # 0 < score < 1
    "tags":    (list, contains("urgent")),             # list contains "urgent"
    "ref":     (str, ends(".pdf")),                    # ends with ".pdf"
    "retries": (int, less(5)),                         # < 5
}
```

### Extending — custom validators

Need a check the built-ins don't cover? Two ways, both drop straight into a model
(including over `[*]` list items):

```python
from validate_nested.lambdas import predicate, LambdaInfo

# 1) inline, the short way — predicate(callable, message)
is_even = predicate(lambda v: v % 2 == 0, "should be even")
model = {"count": (int, is_even)}              # fails as: should be even, got 3

# 2) reusable / parametrised — a function returning LambdaInfo
#    (this is exactly how the built-ins like equal() and length() are written)
def divisible_by(n):
    return LambdaInfo(
        func_lambda=lambda v: v % n == 0,
        lambda_assert_msg=f"should be divisible by {n}",
        lambda_details=f"divisible_by({n})",
    )
model = {"size": (int, divisible_by(3))}
```

> ⚠️ **A bare `lambda` is silently ignored.** `(int, lambda v: v > 0)` won't run — the
> engine only recognises a validator once it's wrapped (`predicate(...)` or
> `LambdaInfo(...)`). Always wrap; never drop a raw `lambda` into a model.

Runnable examples (and custom `report(formatter=...)`):
[tests/test_extending.py](tests/test_extending.py).

---

## Consumption modes

### 1. Pure — inspect the result

```python
result = validate(record, model)
if not result.ok:
    for f in result.failures:
        print(f.path, f.message)
```

`result.ok` is True only when **every** path passed (a later passing field never masks an
earlier failure), and `bool(result) == result.ok` — so `validate` reads cleanly as a gate,
guarding work that should run only on a well-formed record:

```python
if validate(response, model):          # proceed only when the shape is right
    enqueue(response["orders"])
```

See [tests/test_conditions.py](tests/test_conditions.py).

### 2. Immediate — assert on the result

`validate` is the only entry point; you decide when to assert. `Result.report()`
renders a readable message for the assert line:

```python
r = validate(record, model)
assert r.ok, r.report()                 # AssertionError lists every failure
assert r.ok, r.report(formatter=my_fmt) # custom message per failure
```

### 3. Soft — aggregate across several checks

```python
from validate_nested import SoftValidator

with SoftValidator() as soft:
    soft.validate(resp_a, model_a)
    soft.validate(resp_b, model_b)
# raises once at block end, listing every failure from both
```

See [tests/test_modes.py](tests/test_modes.py).

### 4. pytest (optional)

There is **no** shipped pytest helper — `validate` is all you need, and you wire the
`Result` however you like (this also keeps the namespace clear of `pytest-check` & co.).
A typical wiring is three lines; define your own once and reuse it:

```python
def validate_or_skip(record, model):       # your helper — keep it wherever you like
    r = validate(record, model)
    if r.skipped:
        pytest.skip(r.skipped)              # a fired skip() rule -> skip the test
    assert r.ok, r.report()                 # any other failure -> fail with the report
    return r

def test_search():
    validate_or_skip(response.json(), {"state": (str, equal("ok")), "hits[*]": dict})
```

Not using pytest? Route the result anywhere — `unittest`'s `skipTest`, a logger, a custom
exception. See [tests/test_skip.py](tests/test_skip.py) for skip wired both ways.

### 5. Compose your own — e.g. a request helper

`validate` is a building block — wrap it in whatever helper fits your domain. A common
one validates an HTTP response's **status code as a gate**, then its body, and *only* its
body if the code was right. Mark `status` `required` so a wrong code fails once and
short-circuits — the `body.*` rules behind it are never checked (no cascade of
"missing body field" noise behind an error response):

```python
from validate_nested import validate
from validate_nested.lambdas import required, equal

def validate_request(response, expected_code, model):
    record = {"status": response.status_code, "body": response.json()}
    gate = {"status": required((int, equal(expected_code)))}
    r = validate(record, {**gate, **model})
    assert r.ok, r.report()
    return r

# body rules are written against body.* paths:
validate_request(response, 200, {"body.id": int, "body.state": (str, equal("ok"))})
```

A wrong code reports only `[status] ...` (the body is never inspected); a right code with
a bad body reports `[body.state] ...`. See
[tests/test_request_pattern.py](tests/test_request_pattern.py).

---

## skip semantics

`skip()` is a test-control concern, so the **core never skips anything** — when a
`skip()`-marked rule fails, `validate` returns `Result(skipped="<reason>")`. You decide:

```python
r = validate(record, {"feature": skip(dict)})
if r.skipped:
    pytest.skip(r.skipped)   # or unittest's skipTest, a log call, your own — your choice
```

Override the default skip reason per field with `ComplexRule(value=skip(...),
options={"assert_msg": "..."})`. See [tests/test_skip.py](tests/test_skip.py).

---

## Custom messages

`Failure(path, message)` is neutral. Render it your way with a `formatter` (a callable
`Failure -> str`):

```python
r = validate(record, model)
assert r.ok, r.report(formatter=lambda f: f"{f.path} is wrong: {f.message}")
```

See [tests/test_modes.py](tests/test_modes.py) (`test_custom_formatter`).

---

## Advanced — per-field message (`ComplexRule`)

`report(formatter=...)` reshapes *every* failure at once. To override just **one field's**
message, wrap its rule in `ComplexRule(value=<rule>, options={...})` — `assert_msg`
replaces the message, `add_msg` prepends context.

Its most useful case is giving a `skip()` a readable reason: by default a fired skip
carries the raw mismatch text (`expected dict, got str`), which says nothing about *why*
you skipped. `assert_msg` fixes that:

```python
from validate_nested import ComplexRule, validate
from validate_nested.lambdas import skip

model = {"beta_feature": ComplexRule(skip(dict), {"assert_msg": "beta disabled in this env"})}
r = validate(record, model)
# r.skipped == "beta disabled in this env"   (not "expected dict, got str")
```

See [tests/test_complex_rule.py](tests/test_complex_rule.py) (messages) and
[tests/test_skip.py](tests/test_skip.py) (custom skip reason).

---

## Result API

```python
Result(
    ok:       bool,              # True iff nothing failed
    failures: list[Failure],     # each has .path and .message
    skipped:  str | None,        # reason if a skip() rule fired
)
bool(result)  # == result.ok
```

---

## License

MIT.
