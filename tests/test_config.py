import pytest

from quicksite.config import ConfigError, load_config, parse_config, save_config


def base(**overrides):
    data = {"title": "My Site", "pages": [{"slug": "index", "title": "Home", "content": "hi"}]}
    data.update(overrides)
    return data


def test_minimal_config_ok():
    cfg = parse_config(base())
    assert cfg.title == "My Site"
    assert cfg.primary_color == "#2563eb"
    assert cfg.pages[0].output_name == "index.html"


def test_missing_title():
    with pytest.raises(ConfigError, match="title"):
        parse_config(base(title=""))


def test_requires_index_page():
    with pytest.raises(ConfigError, match="index"):
        parse_config(base(pages=[{"slug": "about", "title": "About"}]))


def test_empty_pages():
    with pytest.raises(ConfigError, match="至少"):
        parse_config(base(pages=[]))


@pytest.mark.parametrize("slug", ["About", "about me", "../x", "a_b", "-a", ""])
def test_invalid_slug(slug):
    pages = [{"slug": "index", "title": "H"}, {"slug": slug, "title": "X"}]
    with pytest.raises(ConfigError, match="slug"):
        parse_config(base(pages=pages))


def test_duplicate_slug():
    pages = [{"slug": "index", "title": "H"}, {"slug": "index", "title": "H2"}]
    with pytest.raises(ConfigError, match="重複"):
        parse_config(base(pages=pages))


@pytest.mark.parametrize("color", ["blue", "#12345", "2563eb"])
def test_invalid_color(color):
    with pytest.raises(ConfigError, match="色碼"):
        parse_config(base(theme={"primary": color}))


def test_content_and_file_conflict():
    pages = [{"slug": "index", "title": "H", "content": "a", "file": "a.md"}]
    with pytest.raises(ConfigError, match="不能同時"):
        parse_config(base(pages=pages))


def test_save_and_load_roundtrip(tmp_path):
    cfg = parse_config(base(description="描述", theme={"primary": "#e11d48"}))
    save_config(tmp_path, cfg)
    loaded = load_config(tmp_path)
    assert loaded == cfg


def test_load_missing_file(tmp_path):
    with pytest.raises(ConfigError, match="找不到"):
        load_config(tmp_path)


def test_load_bad_yaml(tmp_path):
    (tmp_path / "site.yaml").write_text("title: [unclosed", encoding="utf-8")
    with pytest.raises(ConfigError, match="YAML"):
        load_config(tmp_path)
