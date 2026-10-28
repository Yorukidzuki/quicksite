import pytest

pytest.importorskip("mcp")

from quicksite import mcp_server  # noqa: E402


def test_tools_end_to_end(tmp_path):
    site = str(tmp_path)
    mcp_server.create_site(site, "MCP 網站")
    mcp_server.add_page(site, "about", "關於", "# 由 agent 寫的頁面")
    pages = mcp_server.list_pages(site)
    assert [p["slug"] for p in pages] == ["index", "about"]
    msg = mcp_server.build_site_tool(site)
    assert "dist" in msg
    assert (tmp_path / "dist" / "about.html").exists()


@pytest.mark.anyio
async def test_tools_registered():
    tools = {t.name for t in await mcp_server.mcp.list_tools()}
    assert {"create_site", "add_page", "remove_page", "list_pages",
            "build_site", "deploy_site"} <= tools


@pytest.mark.anyio
async def test_errors_are_readable_for_agent(tmp_path):
    from mcp.server.mcpserver.exceptions import ToolError

    site = str(tmp_path)
    mcp_server.create_site(site, "Site")
    with pytest.raises(ToolError, match="slug 不合法"):
        await mcp_server.mcp.call_tool(
            "add_page", {"site_dir": site, "slug": "Bad Slug", "title": "x", "content": "y"}
        )
