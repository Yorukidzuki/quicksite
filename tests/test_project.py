import pytest

from quicksite import project
from quicksite.config import ConfigError, load_config


def test_init_creates_config_and_home(tmp_path):
    project.init_site(tmp_path, "Site")
    assert (tmp_path / "site.yaml").exists()
    assert (tmp_path / "pages" / "index.md").exists()
    assert load_config(tmp_path).pages[0].slug == "index"


def test_init_does_not_overwrite(tmp_path):
    project.init_site(tmp_path, "Site")
    with pytest.raises(ConfigError, match="已存在"):
        project.init_site(tmp_path, "Again")


def test_init_rejects_bad_color(tmp_path):
    with pytest.raises(ConfigError):
        project.init_site(tmp_path, "Site", primary_color="red")


def test_add_page(tmp_path):
    project.init_site(tmp_path, "Site")
    path = project.add_page(tmp_path, "blog", "部落格", "hello")
    assert path.read_text(encoding="utf-8") == "hello"
    assert [p["slug"] for p in project.list_pages(tmp_path)] == ["index", "blog"]


def test_add_page_default_content(tmp_path):
    project.init_site(tmp_path, "Site")
    path = project.add_page(tmp_path, "blog", "部落格")
    assert path.read_text(encoding="utf-8") == "# 部落格\n"


def test_add_duplicate_requires_overwrite(tmp_path):
    project.init_site(tmp_path, "Site")
    project.add_page(tmp_path, "blog", "Blog", "v1")
    with pytest.raises(ConfigError, match="已存在"):
        project.add_page(tmp_path, "blog", "Blog", "v2")
    path = project.add_page(tmp_path, "blog", "Blog 2", "v2", overwrite=True)
    assert path.read_text(encoding="utf-8") == "v2"
    assert len(project.list_pages(tmp_path)) == 2


def test_add_page_bad_slug(tmp_path):
    project.init_site(tmp_path, "Site")
    with pytest.raises(ConfigError, match="slug"):
        project.add_page(tmp_path, "../evil", "x")


def test_remove_page(tmp_path):
    project.init_site(tmp_path, "Site")
    project.add_page(tmp_path, "blog", "Blog")
    project.remove_page(tmp_path, "blog")
    assert [p["slug"] for p in project.list_pages(tmp_path)] == ["index"]
    assert (tmp_path / "pages" / "blog.md").exists()  # 內容檔保留


def test_cannot_remove_index(tmp_path):
    project.init_site(tmp_path, "Site")
    with pytest.raises(ConfigError, match="不能刪除"):
        project.remove_page(tmp_path, "index")


def test_remove_missing_page(tmp_path):
    project.init_site(tmp_path, "Site")
    with pytest.raises(ConfigError, match="找不到"):
        project.remove_page(tmp_path, "nope")
