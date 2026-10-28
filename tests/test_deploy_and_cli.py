import subprocess

import pytest

from quicksite import project
from quicksite.cli import main
from quicksite.deploy import DeployError, deploy, pages_url


@pytest.mark.parametrize(
    "remote, expected",
    [
        ("https://github.com/alice/blog.git", "https://alice.github.io/blog/"),
        ("git@github.com:alice/blog.git", "https://alice.github.io/blog/"),
        ("https://github.com/alice/alice.github.io", "https://alice.github.io/"),
        ("https://gitlab.com/alice/blog.git", None),
    ],
)
def test_pages_url(remote, expected):
    assert pages_url(remote) == expected


def test_deploy_to_local_bare_repo(tmp_path):
    """用本機 bare repo 當 remote，測試整個部署流程不需要網路。"""
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    site = tmp_path / "site"
    project.init_site(site, "Deploy Test")

    info = deploy(site, remote=str(remote))
    assert info["branch"] == "gh-pages"

    files = subprocess.run(
        ["git", "--git-dir", str(remote), "ls-tree", "--name-only", "gh-pages"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    assert "index.html" in files and "style.css" in files


def test_deploy_unknown_remote_name(tmp_path):
    project.init_site(tmp_path, "Site")
    with pytest.raises(DeployError):
        deploy(tmp_path, remote="origin")  # tmp_path 不是 git repo


def test_cli_full_flow(tmp_path, capsys):
    assert main(["-d", str(tmp_path), "init", "CLI 網站", "--color", "#16a34a"]) == 0
    assert main(["-d", str(tmp_path), "add", "about", "關於", "--content", "# Hi"]) == 0
    assert main(["-d", str(tmp_path), "list"]) == 0
    assert "about" in capsys.readouterr().out
    assert main(["-d", str(tmp_path), "build"]) == 0
    assert (tmp_path / "dist" / "about.html").exists()


def test_cli_reports_errors(tmp_path, capsys):
    assert main(["-d", str(tmp_path), "build"]) == 1
    assert "錯誤" in capsys.readouterr().err
