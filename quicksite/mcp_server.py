"""MCP server：讓 AI agent（例如 Claude）直接呼叫 quicksite 建站、加頁面、部署。

啟動：quicksite-mcp   （stdio 傳輸）
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from . import project
from .builder import build_site
from .config import ConfigError
from .deploy import DeployError, deploy


@contextmanager
def _friendly_errors():
    """把設定 / 部署錯誤轉成 ToolError，agent 才看得到具體原因並自行修正。"""
    try:
        yield
    except (ConfigError, DeployError) as e:
        raise ToolError(str(e)) from e


mcp = MCPServer(
    "quicksite",
    instructions=(
        "用 quicksite 建立與部署靜態網站。流程：create_site 建立 → add_page 加頁面 "
        "（內容用 Markdown）→ build_site 產生 HTML → deploy_site 推到 GitHub Pages。"
        "site_dir 是網站資料夾的路徑。"
    ),
)


@mcp.tool()
def create_site(
    site_dir: str,
    title: str,
    description: str = "",
    author: str = "",
    primary_color: str = "#2563eb",
) -> str:
    """建立新的網站專案（site.yaml 與首頁 pages/index.md）。primary_color 是主色色碼。"""
    with _friendly_errors():
        path = project.init_site(site_dir, title, description, author, primary_color)
    return f"已建立網站設定 {path}"


@mcp.tool()
def add_page(site_dir: str, slug: str, title: str, content: str, overwrite: bool = False) -> str:
    """新增或覆寫一個頁面。slug 用小寫英文與 -（index 是首頁），content 是 Markdown。"""
    with _friendly_errors():
        path = project.add_page(site_dir, slug, title, content, overwrite)
    return f"頁面 {slug} 已寫入 {path}"


@mcp.tool()
def remove_page(site_dir: str, slug: str) -> str:
    """從網站移除一個頁面（不能移除首頁 index）。"""
    with _friendly_errors():
        project.remove_page(site_dir, slug)
    return f"已移除頁面 {slug}"


@mcp.tool()
def list_pages(site_dir: str) -> list[dict]:
    """列出網站目前的所有頁面。"""
    with _friendly_errors():
        return project.list_pages(site_dir)


@mcp.tool(name="build_site")
def build_site_tool(site_dir: str) -> str:
    """把網站產生成 HTML，輸出到 site_dir/dist。"""
    with _friendly_errors():
        files = build_site(site_dir)
    return f"已產生 {len(files)} 個檔案到 {Path(site_dir) / 'dist'}"


@mcp.tool()
def deploy_site(site_dir: str, remote: str = "origin", branch: str = "gh-pages") -> dict:
    """建置並部署到 GitHub Pages。remote 可以是 git remote 名稱或 repo URL。"""
    with _friendly_errors():
        return deploy(site_dir, remote, branch)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
