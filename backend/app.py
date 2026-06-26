"""FastAPI app wiring the pipeline together and serving a local preview.

Endpoints:
    GET  /                      -> the frontend (upload + picker + preview)
    GET  /api/templates         -> available templates
    POST /api/parse             -> résumé file  -> structured ResumeData
    POST /api/generate          -> data+template -> static site, returns preview URL
    GET  /api/download          -> the last generated site as a .zip
    GET  /preview/...           -> the generated static site

    POST /api/publish           -> last generated site -> GitHub Pages repo
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError

from .extractor import ExtractionError, extract_resume
from .generator import GenerationError, generate_site, list_templates
from .github_publish import GitHubPublishError, publish_site
from .parsers import ParseError, extract_text
from .schemas import ResumeData

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"
GENERATED_DIR = ROOT / "generated"
PREVIEW_DIR = GENERATED_DIR / "preview"

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

GENERATED_DIR.mkdir(exist_ok=True)

app = FastAPI(title="resume-site-tool")


class GenerateRequest(BaseModel):
    template_id: str
    data: ResumeData


class PublishRequest(BaseModel):
    username: str
    token: str
    repo_name: str | None = None


@app.get("/api/templates")
def api_templates() -> list[dict[str, str]]:
    return list_templates()


@app.post("/api/parse")
async def api_parse(file: UploadFile = File(...)) -> JSONResponse:
    raw = await file.read()
    if not raw:
        raise HTTPException(400, "Empty file.")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File too large (max 10 MB).")

    try:
        text = extract_text(file.filename or "resume", raw)
    except ParseError as exc:
        raise HTTPException(422, str(exc)) from exc

    try:
        data = extract_resume(text)
    except ExtractionError as exc:
        raise HTTPException(502, str(exc)) from exc

    return JSONResponse(data.model_dump())


@app.post("/api/generate")
def api_generate(req: GenerateRequest) -> JSONResponse:
    try:
        generate_site(req.data, req.template_id, PREVIEW_DIR)
    except GenerationError as exc:
        raise HTTPException(400, str(exc)) from exc
    return JSONResponse({"preview_url": "/preview/index.html"})


@app.get("/api/download")
def api_download() -> StreamingResponse:
    index = PREVIEW_DIR / "index.html"
    if not index.exists():
        raise HTTPException(404, "No site generated yet.")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in PREVIEW_DIR.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(PREVIEW_DIR))
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=site.zip"},
    )


@app.post("/api/publish")
def api_publish(req: PublishRequest) -> JSONResponse:
    index = PREVIEW_DIR / "index.html"
    if not index.exists():
        raise HTTPException(404, "No site generated yet.")
    if not req.username.strip():
        raise HTTPException(400, "GitHub username is required.")
    if not req.token.strip():
        raise HTTPException(400, "GitHub token is required.")

    try:
        result = publish_site(
            PREVIEW_DIR,
            username=req.username.strip(),
            token=req.token.strip(),
            repo_name=req.repo_name.strip() if req.repo_name else None,
        )
    except GitHubPublishError as exc:
        raise HTTPException(502, str(exc)) from exc

    return JSONResponse(
        {
            "repository_url": result.repository_url,
            "pages_url": result.pages_url,
            "commit_sha": result.commit_sha,
        }
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


# Static mounts come last so they don't shadow the API routes above.
if PREVIEW_DIR.exists() or True:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/preview", StaticFiles(directory=PREVIEW_DIR, html=True), name="preview")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
