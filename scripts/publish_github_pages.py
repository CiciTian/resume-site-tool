#!/usr/bin/env python3
"""Publish a generated site directory to GitHub Pages via GitHub API.

Usage:
    GITHUB_TOKEN=ghp_xxx python scripts/publish_github_pages.py out/engineer-clean CiciTian

The token needs permission to create/update public repositories:
- classic PAT: public_repo
- fine-grained PAT: selected repo + Contents read/write; repo creation needs
  broader account permissions, so create the repo first if using fine-grained.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.github_publish import GitHubPublishError, publish_site  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish a static site to username.github.io.")
    parser.add_argument("site_dir", type=Path, help="Generated static site directory.")
    parser.add_argument("username", help="GitHub username, e.g. CiciTian.")
    parser.add_argument("--repo", help="Override repository name. Defaults to username.github.io.")
    parser.add_argument("--token", help="GitHub token. Defaults to GITHUB_TOKEN env var.")
    args = parser.parse_args()

    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("error: provide --token or set GITHUB_TOKEN", file=sys.stderr)
        return 2

    try:
        result = publish_site(
            args.site_dir,
            username=args.username,
            token=token,
            repo_name=args.repo,
        )
    except GitHubPublishError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"repository: {result.repository_url}")
    print(f"pages:      {result.pages_url}")
    print(f"commit:     {result.commit_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
