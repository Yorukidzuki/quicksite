"""讀取與驗證 site.yaml 設定檔。"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
CONFIG_NAME = "site.yaml"


class ConfigError(ValueError):
    """設定檔內容有誤。"""


@dataclass
class Page:
    slug: str
    title: str
    content: str = ""   # Markdown 內文（直接寫在 yaml）
    file: str | None = None  # 或指向一個 .md 檔（相對於網站資料夾）

    @property
    def output_name(self) -> str:
        return "index.html" if self.slug == "index" else f"{self.slug}.html"


@dataclass
class SiteConfig:
    title: str
    description: str = ""
    author: str = ""
    primary_color: str = "#2563eb"
    pages: list[Page] = field(default_factory=list)

    def page(self, slug: str) -> Page | None:
        return next((p for p in self.pages if p.slug == slug), None)

    def to_dict(self) -> dict:
        pages = []
        for p in self.pages:
            d = {"slug": p.slug, "title": p.title}
            if p.file:
                d["file"] = p.file
            else:
                d["content"] = p.content
            pages.append(d)
        return {
            "title": self.title,
            "description": self.description,
            "author": self.author,
            "theme": {"primary": self.primary_color},
            "pages": pages,
        }


def validate_slug(slug: str) -> str:
    if not isinstance(slug, str) or not SLUG_RE.match(slug):
        raise ConfigError(
            f"頁面 slug 不合法：{slug!r}（只能用小寫英文、數字與 -，例如 about-me）"
        )
    return slug


def parse_config(data: dict) -> SiteConfig:
    """把 yaml 讀出來的 dict 轉成 SiteConfig，並檢查內容。"""
    if not isinstance(data, dict):
        raise ConfigError("設定檔最外層必須是 key: value 的格式")
    title = data.get("title")
    if not title or not isinstance(title, str):
        raise ConfigError("缺少網站標題 title")

    theme = data.get("theme") or {}
    color = str(theme.get("primary", "#2563eb"))
    if not COLOR_RE.match(color):
        raise ConfigError(f"theme.primary 必須是色碼，例如 #2563eb，收到 {color!r}")

    raw_pages = data.get("pages") or []
    if not isinstance(raw_pages, list) or not raw_pages:
        raise ConfigError("pages 至少要有一頁")

    pages: list[Page] = []
    seen: set[str] = set()
    for i, rp in enumerate(raw_pages):
        if not isinstance(rp, dict):
            raise ConfigError(f"pages 第 {i + 1} 項格式錯誤")
        slug = validate_slug(rp.get("slug"))
        if slug in seen:
            raise ConfigError(f"頁面 slug 重複：{slug}")
        seen.add(slug)
        if "content" in rp and "file" in rp:
            raise ConfigError(f"頁面 {slug} 不能同時有 content 和 file")
        pages.append(
            Page(
                slug=slug,
                title=str(rp.get("title") or slug),
                content=str(rp.get("content") or ""),
                file=rp.get("file"),
            )
        )
    if "index" not in seen:
        raise ConfigError("必須有一頁 slug 為 index（首頁）")

    return SiteConfig(
        title=title,
        description=str(data.get("description") or ""),
        author=str(data.get("author") or ""),
        primary_color=color,
        pages=pages,
    )


def load_config(site_dir: str | Path) -> SiteConfig:
    path = Path(site_dir) / CONFIG_NAME
    if not path.exists():
        raise ConfigError(f"找不到 {path}，請先執行 quicksite init")
    with path.open(encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"YAML 格式錯誤：{e}") from e
    return parse_config(data)


def save_config(site_dir: str | Path, config: SiteConfig) -> Path:
    path = Path(site_dir) / CONFIG_NAME
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config.to_dict(), f, allow_unicode=True, sort_keys=False)
    return path
