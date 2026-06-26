#!/usr/bin/env python3
"""Generate a static site from a ResumeData JSON file — no API key needed.

Useful for testing templates offline.

    python scripts/generate_cli.py samples/arthur.json engineer-clean out/arthur

Then open out/arthur/index.html in a browser.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.generator import generate_site, list_templates  # noqa: E402
from backend.schemas import ResumeData  # noqa: E402


def main() -> int:
    if len(sys.argv) != 4:
        ids = ", ".join(t["id"] for t in list_templates())
        print(f"usage: generate_cli.py <data.json> <template> <out_dir>")
        print(f"templates: {ids}")
        return 2

    data_path, template_id, out_dir = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    data = ResumeData.model_validate_json(Path(data_path).read_text(encoding="utf-8"))
    generate_site(data, template_id, out_dir)
    print(f"wrote {out_dir}/index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
