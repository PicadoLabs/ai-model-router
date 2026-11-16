"""SPA assets must never escape their configured static directory."""

import pytest
from fastapi import HTTPException

from app.server import resolve_static_asset


def test_spa_assets_stay_within_static_directory(tmp_path):
    static = tmp_path / "static"
    static.mkdir()
    asset = static / "index.html"
    asset.write_text("safe")

    assert resolve_static_asset(str(static), "index.html") == str(asset)


@pytest.mark.parametrize("requested", ["../private.env", "../static-backup/private.env", "/etc/passwd"])
def test_spa_rejects_parent_and_absolute_paths(tmp_path, requested):
    static = tmp_path / "static"
    static.mkdir()

    with pytest.raises(HTTPException) as exc:
        resolve_static_asset(str(static), requested)

    assert exc.value.status_code == 403


def test_spa_rejects_symlinks_outside_static_directory(tmp_path):
    static = tmp_path / "static"
    static.mkdir()
    private = tmp_path / "private.env"
    private.write_text("synthetic")
    (static / "private.env").symlink_to(private)

    with pytest.raises(HTTPException) as exc:
        resolve_static_asset(str(static), "private.env")

    assert exc.value.status_code == 403
