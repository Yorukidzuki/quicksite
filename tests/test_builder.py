import pytest

from quicksite import project
from quicksite.builder import build_site
from quicksite.config import ConfigError


@pytest.fixture
def site(tmp_path):
    project.init_site(tmp_path, "測試網站", description="一個描述", author="小明", primary_color="#e11d48")
    project.add_page(tmp_path, "about", "關於", "# 關於我\n\n我喜歡 **Python**。")
    return tmp_path


def test_build_creates_files(site):
    files = build_site(site)
    names = {f.name for f in files}
    assert {"index.html", "about.html", "style.css", ".nojekyll"} <= names


def test_markdown_rendered(site):
    build_site(site)
    html = (site / "dist" / "about.html").read_text(encoding="utf-8")
    assert "<h1>關於我</h1>" in html
    assert "<strong>Python</strong>" in html
    assert "<title>關於 · 測試網站</title>" in html


def test_nav_links_and_current_page(site):
    build_site(site)
    html = (site / "dist" / "about.html").read_text(encoding="utf-8")
    assert 'href="index.html"' in html
    assert 'href="about.html" aria-current="page"' in html


def test_theme_color_in_css(site):
    build_site(site)
    css = (site / "dist" / "style.css").read_text(encoding="utf-8")
    assert "--primary: #e11d48" in css


def test_site_metadata_escaped(tmp_path):
    project.init_site(tmp_path, "<script>alert(1)</script>")
    build_site(tmp_path)
    html = (tmp_path / "dist" / "index.html").read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_rebuild_removes_stale_pages(site):
    build_site(site)
    project.remove_page(site, "about")
    build_site(site)
    assert not (site / "dist" / "about.html").exists()


def test_custom_out_dir(site, tmp_path_factory):
    out = tmp_path_factory.mktemp("out")
    build_site(site, out)
    assert (out / "index.html").exists()


def test_assets_copied(site):
    (site / "assets").mkdir()
    (site / "assets" / "logo.txt").write_text("x")
    build_site(site)
    assert (site / "dist" / "assets" / "logo.txt").exists()


def test_file_outside_site_rejected(tmp_path):
    (tmp_path / "site.yaml").write_text(
        "title: T\npages:\n  - slug: index\n    title: H\n    file: ../secret.md\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="資料夾外"):
        build_site(tmp_path)


def test_missing_page_file(tmp_path):
    (tmp_path / "site.yaml").write_text(
        "title: T\npages:\n  - slug: index\n    title: H\n    file: nope.md\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="不存在"):
        build_site(tmp_path)
