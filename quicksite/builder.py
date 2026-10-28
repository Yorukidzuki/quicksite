"""把 SiteConfig 轉成靜態 HTML 網站。"""
from __future__ import annotations

import shutil
from pathlib import Path

import markdown
from jinja2 import Environment, PackageLoader, select_autoescape

from .config import ConfigError, Page, SiteConfig, load_config

_env = Environment(
    loader=PackageLoader("quicksite", "templates"),
    autoescape=select_autoescape(["html"]),
)


def page_markdown(site_dir: Path, page: Page) -> str:
    """取得頁面的 Markdown 原文（來自 content 或 file）。"""
    if not page.file:
        return page.content
    root = site_dir.resolve()
    path = (root / page.file).resolve()
    if root not in path.parents:
        raise ConfigError(f"頁面 {page.slug} 的 file 不能指到網站資料夾外：{page.file}")
    if not path.exists():
        raise ConfigError(f"頁面 {page.slug} 指定的檔案不存在：{page.file}")
    return path.read_text(encoding="utf-8")


def render_markdown(text: str) -> str:
    return markdown.markdown(text, extensions=["fenced_code", "tables"])


def render_page(config: SiteConfig, page: Page, body_html: str) -> str:
    template = _env.get_template("page.html")
    return template.render(site=config, page=page, body=body_html)


def build_site(site_dir: str | Path, out_dir: str | Path | None = None) -> list[Path]:
    """讀 site_dir/site.yaml，輸出到 out_dir（預設 site_dir/dist）。回傳產生的檔案。"""
    site_dir = Path(site_dir)
    config = load_config(site_dir)
    out = Path(out_dir) if out_dir else site_dir / "dist"

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    written: list[Path] = []
    for page in config.pages:
        html = render_page(config, page, render_markdown(page_markdown(site_dir, page)))
        target = out / page.output_name
        target.write_text(html, encoding="utf-8")
        written.append(target)

    css = _env.get_template("style.css").render(site=config)
    css_path = out / "style.css"
    css_path.write_text(css, encoding="utf-8")
    written.append(css_path)

    # GitHub Pages 預設會用 Jekyll 處理，加這個檔讓它原樣發布
    nojekyll = out / ".nojekyll"
    nojekyll.write_text("", encoding="utf-8")
    written.append(nojekyll)

    assets = site_dir / "assets"
    if assets.is_dir():
        shutil.copytree(assets, out / "assets")
        written.extend(p for p in (out / "assets").rglob("*") if p.is_file())
    return written
