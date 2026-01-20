"""Integration tests for module access control rules."""

import pytest

import actifix.api as api


def test_local_only_module_blocks_remote(tmp_path, monkeypatch):
    if not api.FLASK_AVAILABLE:
        pytest.skip("Flask not available")

    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")

    app = api.create_app(project_root=tmp_path)
    client = app.test_client()

    response = client.get("/modules/yhatzee/health", environ_base={"REMOTE_ADDR": "8.8.8.8"})
    assert response.status_code == 403

    response = client.get("/modules/yhatzee/health", environ_base={"REMOTE_ADDR": "127.0.0.1"})
    assert response.status_code == 200


def test_auth_required_module_accepts_valid_token(tmp_path, monkeypatch):
    if not api.FLASK_AVAILABLE:
        pytest.skip("Flask not available")

    monkeypatch.setenv("ACTIFIX_CHANGE_ORIGIN", "raise_af")
    monkeypatch.setenv("ACTIFIX_STATE_DIR", str(tmp_path / ".actifix"))

    import actifix.modules.yhatzee as yhatzee
    from actifix.security.auth import AuthRole, get_user_manager, reset_auth_managers
    from actifix.state_paths import get_actifix_paths, init_actifix_files

    reset_auth_managers()
    monkeypatch.setattr(yhatzee, "ACCESS_RULE", api.MODULE_ACCESS_AUTH_REQUIRED)

    paths = get_actifix_paths(project_root=tmp_path)
    init_actifix_files(paths)

    user_manager = get_user_manager()
    user_manager.create_user("user-1", "tester", "password", {AuthRole.ADMIN})
    _, token = user_manager.authenticate_user("tester", "password")

    app = api.create_app(project_root=tmp_path)
    client = app.test_client()

    response = client.get("/modules/yhatzee/health", environ_base={"REMOTE_ADDR": "127.0.0.1"})
    assert response.status_code == 401

    response = client.get(
        "/modules/yhatzee/health",
        headers={"Authorization": f"Bearer {token}"},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
    )
    assert response.status_code == 200
