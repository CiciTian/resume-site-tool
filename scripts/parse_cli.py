#!/usr/bin/env python3
"""Parse a résumé file into the fixed ResumeData JSON schema."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.extractor import ExtractionError, extract_resume  # noqa: E402
from backend.parsers import ParseError, extract_text  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse a résumé into ResumeData JSON.")
    parser.add_argument("resume_file", type=Path)
    parser.add_argument("-o", "--output", type=Path, help="Output JSON path. Defaults to stdout.")
    args = parser.parse_args()

    try:
        raw = args.resume_file.read_bytes()
        text = extract_text(args.resume_file.name, raw)
        data = extract_resume(text)
    except (ParseError, ExtractionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    payload = data.model_dump_json(indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
