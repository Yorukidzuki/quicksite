"""把建好的網站推到 GitHub Pages（gh-pages 分支）。"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .builder import build_site


class DeployError(RuntimeError):
    pass


def _git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise DeployError(f"git {' '.join(args)} 失敗：{result.stderr.strip()}")
    return result.stdout.strip()


def resolve_remote(site_dir: Path, remote: str) -> str:
    """remote 可以是 git remote 名稱（如 origin）或直接是 URL / 路徑。"""
    if "/" in remote or ":" in remote:
        return remote
    return _git(["remote", "get-url", remote], cwd=site_dir)


def pages_url(remote_url: str) -> str | None:
    """從 GitHub remote 推算 GitHub Pages 網址。"""
    m = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", remote_url)
    if not m:
        return None
    user, repo = m.group(1), m.group(2)
    if repo.lower() == f"{user.lower()}.github.io":
        return f"https://{user}.github.io/"
    return f"https://{user}.github.io/{repo}/"


def deploy(
    site_dir: str | Path,
    remote: str = "origin",
    branch: str = "gh-pages",
    message: str = "Deploy site with quicksite",
) -> dict:
    """先 build，再把輸出強制推到 remote 的 branch。回傳部署資訊。"""
    site_dir = Path(site_dir)
    remote_url = resolve_remote(site_dir, remote)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "site"
        files = build_site(site_dir, out)
        _git(["init", "-q"], cwd=out)
        _git(["checkout", "-q", "-b", branch], cwd=out)
        _git(["add", "-A"], cwd=out)
        _git(
            ["-c", "user.name=quicksite", "-c", "user.email=quicksite@users.noreply.github.com",
             "commit", "-q", "-m", message],
            cwd=out,
        )
        _git(["push", "-q", "--force", remote_url, f"{branch}:{branch}"], cwd=out)
        shutil.rmtree(out / ".git", ignore_errors=True)
    return {
        "remote": remote_url,
        "branch": branch,
        "files": len(files),
        "url": pages_url(remote_url),
    }
