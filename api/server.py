import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from .auth import resolve_token
from .config import CFG
from .scanner import get_random, get_random_any, get_source_list, get_name, get_stats, scan_all

app = FastAPI(title="DJJ", docs_url=None, redoc_url=None)
WEB_DIR = Path(__file__).parent.parent / "web"

@app.on_event("startup")
async def startup():
    scan_all()
    stats = get_stats()
    print(f"[djj] Ready: {stats['total']} videos, {len(stats['sources'])} sources")

@app.get("/api/random")
async def api_random(source: str | None = None):
    token = get_random(source) if source else get_random_any()
    if not token:
        return JSONResponse({"error": "no videos"}, status_code=404)
    return {"token": token, "name": get_name(token)}

@app.get("/api/play")
async def api_play(token: str):
    file_path = resolve_token(token)
    if not file_path or not os.path.isfile(file_path):
        return JSONResponse({"error": "invalid token"}, status_code=403)
    path = Path(file_path)
    mime = {".mp4":"video/mp4",".avi":"video/x-msvideo",".mkv":"video/x-matroska",
            ".mov":"video/quicktime",".webm":"video/webm",".flv":"video/x-flv"}.get(path.suffix.lower(), "video/mp4")
    return FileResponse(file_path, media_type=mime)

@app.get("/api/sources")
async def api_sources():
    return {"sources": get_source_list(), "stats": get_stats()}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    ua = request.headers.get("user-agent", "")
    if not any(k in ua for k in ["Android","iPhone","iPod","iPad","Mobile","UCWEB"]):
        return RedirectResponse(url="/pc")
    return (WEB_DIR / "index.html").read_text(encoding="utf-8")

@app.get("/pc", response_class=HTMLResponse)
async def pc():
    return (WEB_DIR / "pc.html").read_text(encoding="utf-8")

if (WEB_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=str(WEB_DIR / "css")), name="css")
if (WEB_DIR / "img").exists():
    app.mount("/img", StaticFiles(directory=str(WEB_DIR / "img")), name="img")
