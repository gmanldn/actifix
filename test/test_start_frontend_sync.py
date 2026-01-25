import pytest

import scripts.start as start


def test_sync_frontend_assets_invokes_builder(monkeypatch, tmp_path):
    called = []

    def fake_build(project_root):
        called.append(project_root)

    monkeypatch.setattr(start, "build_frontend", fake_build)

    start.sync_frontend_assets(tmp_path)

    assert called == [tmp_path]
