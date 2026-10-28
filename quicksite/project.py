"""建立網站專案、新增 / 刪除頁面（CLI 與 MCP server 共用的核心邏輯）。"""
from __future__ import annotations

from pathlib import Path

from .config import (
    CONFIG_NAME,
    ConfigError,
    Page,
    SiteConfig,
    load_config,
    save_config,
    validate_slug,
)

DEFAULT_HOME = """# 歡迎

這是用 **quicksite** 產生的網站。編輯 `pages/index.md` 來修改這一頁。
"""


def init_site(
    site_dir: str | Path,
    title: str,
    description: str = "",
    author: str = "",
    primary_color: str = "#2563eb",
) -> Path:
    """建立新網站：site.yaml + pages/index.md。已存在就報錯，避免覆蓋。"""
    site_dir = Path(site_dir)
    if (site_dir / CONFIG_NAME).exists():
        raise ConfigError(f"{site_dir / CONFIG_NAME} 已存在，不覆蓋")
    (site_dir / "pages").mkdir(parents=True, exist_ok=True)
    (site_dir / "pages" / "index.md").write_text(DEFAULT_HOME, encoding="utf-8")
    config = SiteConfig(
        title=title,
        description=description,
        author=author,
        primary_color=primary_color,
        pages=[Page(slug="index", title="首頁", file="pages/index.md")],
    )
    # 透過 parse 再驗證一次（例如色碼格式）
    from .config import parse_config

    parse_config(config.to_dict())
    return save_config(site_dir, config)


def add_page(
    site_dir: str | Path,
    slug: str,
    title: str,
    content: str = "",
    overwrite: bool = False,
) -> Path:
    """新增頁面：內容寫到 pages/<slug>.md，並登記到 site.yaml。回傳 .md 路徑。"""
    site_dir = Path(site_dir)
    validate_slug(slug)
    config = load_config(site_dir)
    existing = config.page(slug)
    if existing and not overwrite:
        raise ConfigError(f"頁面 {slug} 已存在（要覆蓋請設 overwrite）")

    md_rel = f"pages/{slug}.md"
    md_path = site_dir / md_rel
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(content or f"# {title}\n", encoding="utf-8")

    if existing:
        existing.title = title
        existing.file = md_rel
        existing.content = ""
    else:
        config.pages.append(Page(slug=slug, title=title, file=md_rel))
    save_config(site_dir, config)
    return md_path


def remove_page(site_dir: str | Path, slug: str) -> None:
    """從 site.yaml 移除頁面（.md 檔保留，避免誤刪內容）。首頁不能刪。"""
    if slug == "index":
        raise ConfigError("首頁 index 不能刪除")
    config = load_config(site_dir)
    if not config.page(slug):
        raise ConfigError(f"找不到頁面 {slug}")
    config.pages = [p for p in config.pages if p.slug != slug]
    save_config(site_dir, config)


def list_pages(site_dir: str | Path) -> list[dict]:
    config = load_config(site_dir)
    return [{"slug": p.slug, "title": p.title, "output": p.output_name} for p in config.pages]
