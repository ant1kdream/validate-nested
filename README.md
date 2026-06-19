# validate-nested

**A tiny, dependency-free DSL for validating the *shape* of nested dicts / JSON responses.**

Describe what a response should look like with a compact `model` dict and let the engine
check types, lengths, values, presence and per-item rules in one pass — then plug the
result into *any* test framework, or none.

```python
from validate_nested import validate
from validate_nested.lambdas import equal, length, empty

model = {
    "ids":        (list, length(3)),      # a list of exactly 3
    "ids[*]":     dict,                   # every item is a dict
    "state":      (str, equal("ok")),     # a string equal to "ok"
    "message":    empty(str),             # an empty string
    "error_code": (int, equal(0)),        # an int equal to 0
}

result = validate(response, model)        # -> Result(ok, failures, skipped)
assert result.ok, result.report()         # readable message listing every failure
```

No classes to declare, no schema files — the model *is* the spec, inline where you use it.

---

## Why

- **Terse.** One dict describes a whole response. No model class per shape.
- **Structural + value checks together.** `(int, equal(0))`, `(list, length(3))`, `ids[*]`.
- **Framework-agnostic.** The engine returns data; *you* decide how to report (plain
  code, immediate `assert`, soft-aggregate, or pytest).
- **Zero dependencies.** Pure Python 3.8+. `pytest` is an optional extra only for the
  pytest integration.

---

## Install

```bash
pip install validate-nested            # core, no dependencies
pip install "validate-nested[pytest]"  # + the optional pytest integration
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

Dotted paths and `[*]` (every item of a list):

```python
{
    "data.user.id": int,        # nested
    "items[*]": dict,           # each element of items
    "items[*].price": float,    # price of each element
}
```

### Validators (`from validate_nested.lambdas import ...`)

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

### Presence & coercion markers

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

Markers compose: `required(opt(str))`, `required(not_exist())`.

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
    soft.check(resp_a, model_a)
    soft.check(resp_b, model_b)
# raises once at block end, listing every failure from both
```

### 4. pytest

```python
from validate_nested.integrations.pytest import check

def test_search():
    check(response.json(), {"state": (str, equal("ok")), "hits[*]": dict})
    # a fired skip() -> pytest.skip(reason); any other failure -> pytest.fail(report)
```

---

## skip semantics

`skip()` is a test-control concern, so the **core never skips anything** — when a
`skip()`-marked rule fails, `validate` returns `Result(skipped="<reason>")`. You decide:

```python
result = validate(record, {"feature": skip(dict)})
if result.skipped:
    ...   # mark inconclusive, log, etc.
```

The pytest integration turns `result.skipped` into a real `pytest.skip(reason)`.

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
