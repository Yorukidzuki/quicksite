# quicksite

用一個 `site.yaml` 加幾個 Markdown 檔，一個指令產生靜態網站並部署到 GitHub Pages。
附 MCP server，讓 AI agent（例如 Claude）可以直接幫你建站、加頁面、部署。

## 為什麼做這個

每次要架一個簡單的網站（個人頁、專案介紹、活動頁），都要重新處理 HTML 模板、CSS、
響應式排版、導覽列、部署設定……真正想寫的內容反而只有幾段文字。
quicksite 把這些重複的部分收起來：**你只寫內容，其他交給工具。**

## 安裝

```bash
pip install -e ".[mcp,dev]"
```

## 使用

```bash
quicksite -d mysite init "我的網站" --description "一句話介紹" --color "#0f766e"
quicksite -d mysite add about "關於我" --content "# 關於我"
quicksite -d mysite list
quicksite -d mysite serve     # http://localhost:8000 本機預覽
quicksite -d mysite deploy    # 推到 origin 的 gh-pages 分支
```

部署後到 GitHub repo 的 **Settings → Pages**，Source 選 `gh-pages` 分支，大約一分鐘後網站就會上線。

範例網站在 [`example/`](example/)：`quicksite -d example serve`。

## site.yaml 格式

```yaml
title: 網站標題          # 必填
description: 一句話介紹  # 顯示在首頁與 <meta>
author: 你的名字
theme:
  primary: "#2563eb"    # 主色
pages:                  # 至少一頁，且必須有 slug: index（首頁）
  - slug: index
    title: 首頁
    file: pages/index.md    # 內容放在檔案裡
  - slug: contact
    title: 聯絡
    content: |              # 或直接寫在這裡
      # 聯絡我
```

- slug 只能用小寫英文、數字與 `-`
- `assets/` 資料夾（圖片等）會原樣複製到輸出
- 自動支援手機版與深色模式

## MCP server

提供 6 個工具：`create_site`、`add_page`、`remove_page`、`list_pages`、`build_site`、`deploy_site`。

**Claude Code**：

```bash
claude mcp add quicksite -- quicksite-mcp
```

**Claude Desktop**（`claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "quicksite": { "command": "quicksite-mcp" }
  }
}
```

接著就可以對 Claude 說：「在 ~/sites/club 幫我建一個社團網站，有首頁、活動、聯絡三頁，主色用綠色，然後部署。」

## 專案結構

```
quicksite/
  config.py      讀取與驗證 site.yaml
  builder.py     Markdown → HTML（Jinja2 模板）
  project.py     建立網站、新增 / 移除頁面
  deploy.py      推到 GitHub Pages
  cli.py         命令列介面
  mcp_server.py  MCP server
  templates/     HTML 與 CSS 模板
tests/           pytest 單元測試
```

## 測試

```bash
pytest -v
```

GitHub Actions 會在每次 push 時於 Python 3.10 與 3.12 上執行測試，並建置範例網站。
部署測試用本機 bare repo 當 remote，不需要網路也不會碰到真的 GitHub。
