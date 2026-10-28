"""命令列介面：quicksite init / add / remove / list / build / serve / deploy"""
from __future__ import annotations

import argparse
import functools
import http.server
import sys
from pathlib import Path

from . import project
from .builder import build_site
from .config import ConfigError
from .deploy import DeployError, deploy


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="quicksite", description="快速產生並部署靜態網站")
    p.add_argument("-d", "--dir", default=".", help="網站資料夾（預設目前資料夾）")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="建立新網站")
    s.add_argument("title")
    s.add_argument("--description", default="")
    s.add_argument("--author", default="")
    s.add_argument("--color", default="#2563eb", help="主色，例如 #e11d48")

    s = sub.add_parser("add", help="新增頁面")
    s.add_argument("slug")
    s.add_argument("title")
    s.add_argument("--content", default="", help="Markdown 內容")

    s = sub.add_parser("remove", help="移除頁面")
    s.add_argument("slug")

    sub.add_parser("list", help="列出頁面")

    s = sub.add_parser("build", help="產生網站到 dist/")
    s.add_argument("-o", "--out", default=None)

    s = sub.add_parser("serve", help="本機預覽")
    s.add_argument("--port", type=int, default=8000)

    s = sub.add_parser("deploy", help="部署到 GitHub Pages")
    s.add_argument("--remote", default="origin")
    s.add_argument("--branch", default="gh-pages")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    site = Path(args.dir)
    try:
        if args.cmd == "init":
            path = project.init_site(site, args.title, args.description, args.author, args.color)
            print(f"已建立 {path}")
        elif args.cmd == "add":
            path = project.add_page(site, args.slug, args.title, args.content)
            print(f"已新增頁面，內容在 {path}")
        elif args.cmd == "remove":
            project.remove_page(site, args.slug)
            print(f"已移除頁面 {args.slug}")
        elif args.cmd == "list":
            for p in project.list_pages(site):
                print(f"{p['slug']:<16} {p['title']}  ->  {p['output']}")
        elif args.cmd == "build":
            files = build_site(site, args.out)
            print(f"已產生 {len(files)} 個檔案")
        elif args.cmd == "serve":
            build_site(site)
            handler = functools.partial(
                http.server.SimpleHTTPRequestHandler, directory=str(site / "dist")
            )
            print(f"預覽：http://localhost:{args.port}  （Ctrl+C 結束）")
            http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler).serve_forever()
        elif args.cmd == "deploy":
            info = deploy(site, args.remote, args.branch)
            print(f"已推送 {info['files']} 個檔案到 {info['remote']} 的 {info['branch']} 分支")
            if info["url"]:
                print(f"網址（GitHub Pages 開啟後約一分鐘生效）：{info['url']}")
    except (ConfigError, DeployError) as e:
        print(f"錯誤：{e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
