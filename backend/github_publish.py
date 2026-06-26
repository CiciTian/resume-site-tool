"""Publish a generated static site to a user's GitHub Pages repository.

This module uses GitHub's Git Data API so the whole site is uploaded as a
single commit. It is suitable for local MVPs and backend services. For a public
SaaS product, exchange the raw token flow for GitHub OAuth or a GitHub App.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


class GitHubPublishError(Exception):
    """Raised when GitHub rejects or cannot complete the publish request."""


@dataclass(frozen=True)
class PublishResult:
    repository_url: str
    pages_url: str
    commit_sha: str


EXCLUDE_NAMES = {".git", ".DS_Store", "__pycache__"}
EXCLUDE_DIRS = {"work", "outputs", "generated", ".venv"}


def publish_site(
    site_dir: Path,
    *,
    username: str,
    token: str,
    repo_name: str | None = None,
    branch: str = "main",
    message: str = "Publish resume website",
) -> PublishResult:
    """Create or update ``username/username.github.io`` from ``site_dir``."""
    site_dir = site_dir.resolve()
    if not (site_dir / "index.html").exists():
        raise GitHubPublishError(f"{site_dir} does not contain index.html.")

    repo = repo_name or f"{username}.github.io"
    owner = username
    _ensure_repo(owner, repo, token)

    head = _get_ref(owner, repo, branch, token)
    parent_sha = head["object"]["sha"] if head else None
    base_tree = _get_commit(owner, repo, parent_sha, token)["tree"]["sha"] if parent_sha else None

    tree_entries = []
    for path in _site_files(site_dir):
        rel = path.relative_to(site_dir).as_posix()
        blob_sha = _create_blob(owner, repo, path, token)
        tree_entries.append(
            {
                "path": rel,
                "mode": "100644",
                "type": "blob",
                "sha": blob_sha,
            }
        )

    tree_sha = _create_tree(owner, repo, tree_entries, token, base_tree=base_tree)
    commit_sha = _create_commit(owner, repo, message, tree_sha, token, parent_sha=parent_sha)

    if parent_sha:
        _update_ref(owner, repo, branch, commit_sha, token)
    else:
        _create_ref(owner, repo, branch, commit_sha, token)

    _try_enable_pages(owner, repo, branch, token)

    return PublishResult(
        repository_url=f"https://github.com/{owner}/{repo}",
        pages_url=f"https://{username.lower()}.github.io/",
        commit_sha=commit_sha,
    )


def _site_files(site_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(site_dir.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(site_dir).parts
        if any(part in EXCLUDE_NAMES or part in EXCLUDE_DIRS for part in rel_parts):
            continue
        files.append(path)
    return files


def _request(
    method: str,
    url: str,
    token: str,
    payload: dict | None = None,
    *,
    ok_statuses: set[int] | None = None,
) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "resume-site-tool",
        },
    )
    ok = ok_statuses or {200, 201}
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            body = response.read().decode("utf-8")
            if response.status not in ok:
                raise GitHubPublishError(f"GitHub returned HTTP {response.status}: {body}")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GitHubPublishError(f"GitHub HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise GitHubPublishError(f"Could not connect to GitHub: {exc.reason}") from exc


def _maybe_request(method: str, url: str, token: str, payload: dict | None = None) -> dict | None:
    try:
        return _request(method, url, token, payload)
    except GitHubPublishError as exc:
        if "GitHub HTTP 404" in str(exc):
            return None
        raise


def _ensure_repo(owner: str, repo: str, token: str) -> None:
    repo_url = f"https://api.github.com/repos/{owner}/{repo}"
    if _maybe_request("GET", repo_url, token) is not None:
        return
    _request(
        "POST",
        "https://api.github.com/user/repos",
        token,
        {
            "name": repo,
            "private": False,
            "auto_init": False,
            "description": "Personal website generated from a resume.",
        },
    )


def _get_ref(owner: str, repo: str, branch: str, token: str) -> dict | None:
    return _maybe_request(
        "GET",
        f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{branch}",
        token,
    )


def _get_commit(owner: str, repo: str, sha: str | None, token: str) -> dict:
    if not sha:
        raise GitHubPublishError("Cannot read a commit without a SHA.")
    return _request("GET", f"https://api.github.com/repos/{owner}/{repo}/git/commits/{sha}", token)


def _create_blob(owner: str, repo: str, path: Path, token: str) -> str:
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    raw = path.read_bytes()
    payload = {
        "content": base64.b64encode(raw).decode("ascii"),
        "encoding": "base64",
    }
    result = _request(
        "POST",
        f"https://api.github.com/repos/{owner}/{repo}/git/blobs",
        token,
        payload,
    )
    if not result.get("sha"):
        raise GitHubPublishError(f"GitHub did not return a blob SHA for {path.name} ({content_type}).")
    return result["sha"]


def _create_tree(
    owner: str,
    repo: str,
    entries: list[dict],
    token: str,
    *,
    base_tree: str | None,
) -> str:
    payload: dict = {"tree": entries}
    if base_tree:
        payload["base_tree"] = base_tree
    result = _request(
        "POST",
        f"https://api.github.com/repos/{owner}/{repo}/git/trees",
        token,
        payload,
    )
    return result["sha"]


def _create_commit(
    owner: str,
    repo: str,
    message: str,
    tree_sha: str,
    token: str,
    *,
    parent_sha: str | None,
) -> str:
    payload: dict = {"message": message, "tree": tree_sha}
    if parent_sha:
        payload["parents"] = [parent_sha]
    result = _request(
        "POST",
        f"https://api.github.com/repos/{owner}/{repo}/git/commits",
        token,
        payload,
    )
    return result["sha"]


def _create_ref(owner: str, repo: str, branch: str, commit_sha: str, token: str) -> None:
    _request(
        "POST",
        f"https://api.github.com/repos/{owner}/{repo}/git/refs",
        token,
        {"ref": f"refs/heads/{branch}", "sha": commit_sha},
    )


def _update_ref(owner: str, repo: str, branch: str, commit_sha: str, token: str) -> None:
    _request(
        "PATCH",
        f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}",
        token,
        {"sha": commit_sha, "force": False},
    )


def _try_enable_pages(owner: str, repo: str, branch: str, token: str) -> None:
    try:
        _request("GET", f"https://api.github.com/repos/{owner}/{repo}/pages", token)
        return
    except GitHubPublishError:
        pass

    try:
        _request(
            "POST",
            f"https://api.github.com/repos/{owner}/{repo}/pages",
            token,
            {"source": {"branch": branch, "path": "/"}},
            ok_statuses={201, 202, 204},
        )
    except GitHubPublishError:
        # User-site repos usually enable Pages automatically after the first push.
        # Do not fail a successful content upload just because Pages API scope is
        # missing; surface the pages URL and let the UI mention it may need setup.
        return
