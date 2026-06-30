# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — Unreleased

Initial public release.

### Added
- `validate(record, model)` — the single entry point, returning a `Result(ok, failures,
  skipped)`; never raises (except `ValueError` on an empty model).
- Model DSL: types, type unions, value validators, presence/coercion markers, dotted
  paths and `[*]` wildcards (nestable to any depth).
- Built-in validators (`equal`, `length`, `approx`, `contains`, `exists_in`, `in_range`,
  `less`, `more`, `ends`, `count`, `split_length`, `lower_match`, `valid_score`,
  `positive_number`, `non_zero`, `split_positive_numbers`, `not_equal`).
- Markers: `required`, `opt`, `not_exist`, `empty`, `not_empty`, `undefined`, `to_int`,
  `to_float`, `skip`.
- `SoftValidator` to aggregate failures across several checks.
- `Result.report(formatter=...)` for custom failure rendering.
- Extension points: `predicate(...)` / `LambdaInfo(...)` custom validators, and
  `ComplexRule` for per-field message overrides.

[0.1.0]: https://github.com/ant1kdream/validate-nested/releases/tag/v0.1.0
