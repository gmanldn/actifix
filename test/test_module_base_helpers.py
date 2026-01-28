from actifix.modules.base import ModuleBase


def _helper():
    return ModuleBase(
        module_key="testmodule",
        defaults={"host": "127.0.0.1", "port": 9999},
        metadata={"name": "modules.testmodule"},
    )


def test_health_handler_returns_payload():
    helper = _helper()
    handler = helper.health_handler()
    response = handler()
    assert response["status"] == "ok"
    assert response["module"] == "testmodule"


def test_error_boundary_returns_safe_response():
    helper = _helper()

    @helper.error_boundary(source="modules/testmodule:handler")
    def handler():
        raise ValueError("boom")

    response = handler()
    assert isinstance(response, tuple)
    payload, status = response
    assert status == 500
    assert payload["error"] == "boom"
