"""Tests for the frontend build helper."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_frontend import build_frontend


def test_build_frontend_creates_dist(tmp_path: Path) -> None:
    frontend = tmp_path / "actifix-frontend"
    frontend.mkdir()
    (frontend / "index.html").write_text("<html></html>", encoding="utf-8")
    (frontend / "app.js").write_text("console.log('app')", encoding="utf-8")
    (frontend / "styles.css").write_text(":root {}", encoding="utf-8")
    assets = frontend / "assets"
    assets.mkdir()
    (assets / "pangolin.svg").write_text("<svg/>", encoding="utf-8")

    dist = build_frontend(project_root=tmp_path)

    assert dist.exists()
    assert dist.is_dir()
    assert (dist / "index.html").read_text(encoding="utf-8") == "<html></html>"
    assert (dist / "app.js").read_text(encoding="utf-8") == "console.log('app')"
    assert (dist / "styles.css").read_text(encoding="utf-8") == ":root {}"
    assert (dist / "assets" / "pangolin.svg").read_text(encoding="utf-8") == "<svg/>"
