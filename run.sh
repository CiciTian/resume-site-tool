#!/usr/bin/env bash
# Start the resume-site-tool server.
#   OPENAI_API_KEY=sk-... ./run.sh
#   or ANTHROPIC_API_KEY=sk-... ./run.sh
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  python3 -m venv .venv
  ./.venv/bin/pip install --quiet --upgrade pip
  ./.venv/bin/pip install --quiet -r requirements.txt
fi

if [ -z "${OPENAI_API_KEY:-}" ] && [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "warning: no LLM API key is set — résumé parsing will use a limited heuristic fallback." >&2
fi

exec ./.venv/bin/uvicorn backend.app:app --reload --port 8000
