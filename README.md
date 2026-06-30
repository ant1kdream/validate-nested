# validate-nested

**A tiny, dependency-free DSL for validating the *shape* of nested dicts / JSON responses.**

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

### Type + value validators

Combine a type with one or more validators in a tuple:

```python
{"score": (float, valid_score), "ids": (list, length(3)), "state": (str, equal("ok"))}
```

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
[tests/rules/test_lists.py](tests/rules/test_lists.py).

### Presence & coercion markers

**Built-in only** (you can't define custom markers). They tune presence, emptiness and
coercion:

| Marker | Meaning |
|---|---|
| `not_empty()` | `len > 0` (the **default** for sized types) |
| `empty()` | `len == 0` |
| `opt()` | value may be absent → passes if missing |
| `required()` | if this rule fails, stop and don't check the rest |
| `not_exist()` | the path must be **absent** |
| `undefined()` | don't assume empty-vs-filled (skip the len check) |
| `to_int()` / `to_float()` | coerce before running validators, e.g. `(str, to_int(equal(5)))` |
| `skip()` | if this rule fails, signal a **skip** instead of a failure |

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

Markers compose: `required(opt(str))` (optional, but the gate when present),
`required(not_exist())`.

### Validators — built-in (`from validate_nested.lambdas import ...`)

| Validator | Passes when |
|---|---|
| `equal(x)` / `not_equal(x)` | value `==` / `!=` x |
| `length(n)` | `len(value) == n` |
| `approx(x, delta=0.01)` | `abs(value - x) <= delta` |
| `contains(x)` | substring / all items in value |
| `exists_in((a, b, ...))` | value is one of |
| `in_range(a, b)` | `a < value < b` |
| `less(x)` / `more(x)` | `value < x` / `value > x` |
| `ends(x)` | `value.endswith(x)` |
| `count(value, amount)` | value appears `amount` times |
| `split_length(n, sep=",")` | `len(value.split(sep)) == n` |
| `lower_match(x)` | case-insensitive equality |
| `valid_score` / `positive_number` / `non_zero` | `0 < v <= 1` / `v >= 0` / `v > 0` |
| `split_positive_numbers` | all comma-split parts `>= 0` |

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
