"""Compose-your-own helper: validate an HTTP response's *status code as a gate*, then
its body — and only its body if the code was right.

The status is marked ``required``, so a wrong code fails once on ``status`` and
short-circuits: the body rules written after it are never checked (no cascade of
"missing body field" noise behind an error response). This is the same gate idiom as
``required`` on any parent field, applied to the status line.

There is no shipped ``validate_request`` — ``validate`` is the only entry point and you
wire it to your client however you like. ``validate_request`` below is one such wiring;
the negative tests call ``validate`` directly (exactly what the helper does internally)
so they can inspect the ``Result`` the gate produces.
"""
from validate_nested import validate
from validate_nested.lambdas import equal, required


class FakeResponse:
    """Stand-in for a ``requests``/``httpx`` response — just ``.status_code`` and
    ``.json()``, so these examples carry no HTTP-client dependency."""

    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def validate_request(response, expected_code, model):
    """Validate the status code (as a required gate) and then the body. Body rules are
    written against ``body.*`` paths; they run only if the status matched."""
    record = {"status": response.status_code, "body": response.json()}
    gate = {"status": required((int, equal(expected_code)))}
    r = validate(record, {**gate, **model})
    assert r.ok, r.report()
    return r


def test_wrong_code_fails_on_status_and_skips_the_body():
    """A wrong status code fails the ``required`` gate, so validation stops there: the
    body is never inspected — only ``status`` is reported, even though the body is wrong
    too."""
    response = FakeResponse(
        status_code=404,
        payload={
            "id": 7,
            "state": "err",
        },
    )
    record = {"status": response.status_code, "body": response.json()}
    model = {
        "status": required((int, equal(200))),
        "body.id": int,
        "body.state": (str, equal("ok")),
    }
    r = validate(record, model)

    assert not r.ok
    assert [f.path for f in r.failures] == ["status"]
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [status] should be equal to 200, got 404"
    )


def test_right_code_but_bad_body_fails_on_the_body():
    """The status gate passes, so the body is checked — and a bad body field is reported
    by its ``body.*`` path."""
    response = FakeResponse(
        status_code=200,
        payload={
            "id": 7,
            "state": "err",
        },
    )
    record = {"status": response.status_code, "body": response.json()}
    model = {
        "status": required((int, equal(200))),
        "body.id": int,
        "body.state": (str, equal("ok")),
    }
    r = validate(record, model)

    assert not r.ok
    assert [f.path for f in r.failures] == ["body.state"]
    assert r.report() == (
        "1 validation failure(s):\n"
        "  - [body.state] should be equal to 'ok', got 'err'"
    )


def test_right_code_and_good_body_passes():
    """Correct status code and a well-shaped body — the asserting helper returns a
    passing ``Result``."""
    response = FakeResponse(
        status_code=200,
        payload={
            "id": 7,
            "state": "ok",
        },
    )
    model = {
        "body.id": int,
        "body.state": (str, equal("ok")),
    }
    r = validate_request(response, 200, model)

    assert r.ok
