# Public Deployment Guide

The local URL `http://127.0.0.1:8000` only works on your own machine. To let
everyone access the interface, deploy this app as a public web service.

## Important Security Notes

This MVP accepts resumes and GitHub tokens. Before opening it to real users:

- Add login or invite-only access.
- Add a privacy notice explaining that resumes are uploaded to your server.
- Do not log uploaded resume text or GitHub tokens.
- Prefer GitHub OAuth in production instead of asking users to paste tokens.
- Add rate limits and upload limits.
- Use HTTPS only.

## Option A: Docker Deployment

Build:

```bash
docker build -t resume-site-tool .
```

Run:

```bash
docker run --rm -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  resume-site-tool
```

Open:

```text
http://127.0.0.1:8000
```

## Option B: Render / Railway / Fly / Cloud Run

Use this repo folder as a web service.

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn backend.app:app --host 0.0.0.0 --port $PORT
```

Environment variables:

```text
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

Only one LLM provider is required. Without a key, parsing falls back to a
limited heuristic parser for demos.

## Option C: Temporary Public Demo Tunnel

If you only want a temporary public link from your laptop, install one of:

- Cloudflare Tunnel
- ngrok
- localtunnel

Example with Cloudflare Tunnel:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

Example with ngrok:

```bash
ngrok http 8000
```

These are good for demos, not production.

## Recommended Production Architecture

```text
Frontend + FastAPI backend
  -> Resume parser
  -> LLM structured extraction
  -> Fixed template renderer
  -> GitHub OAuth publish flow
```

For real users, replace raw GitHub token input with OAuth:

1. User clicks "Connect GitHub".
2. GitHub OAuth grants `public_repo`.
3. Backend creates or updates `username.github.io`.
4. Backend deletes access token if you do not need long-term sync.

