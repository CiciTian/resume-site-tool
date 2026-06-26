#!/usr/bin/env python3
"""Parse a resume file and render a fixed-template static website."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.extractor import ExtractionError, extract_resume  # noqa: E402
from backend.generator import GenerationError, generate_site, list_templates  # noqa: E402
from backend.parsers import ParseError, extract_text  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a GitHub Pages-ready site from a resume.")
    parser.add_argument("resume_file", type=Path)
    parser.add_argument(
        "--template",
        default="engineer-clean",
        choices=[item["id"] for item in list_templates()],
    )
    parser.add_argument("-o", "--out", type=Path, default=Path("generated/site"))
    parser.add_argument("--json-out", type=Path, help="Optional path to save extracted ResumeData JSON.")
    args = parser.parse_args()

    try:
        text = extract_text(args.resume_file.name, args.resume_file.read_bytes())
        data = extract_resume(text)
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(data.model_dump_json(indent=2) + "\n", encoding="utf-8")
        generate_site(data, args.template, args.out)
    except (ParseError, ExtractionError, GenerationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"site: {args.out / 'index.html'}")
    if args.json_out:
        print(f"json: {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
