import random
import os, httpx
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from .auth import resolve_token, is_remote_token, get_remote_info, register_remote
from .config import CFG
from .scanner import get_random, get_random_any, get_source_list, get_name, get_stats, scan_all, is_remote_source, get_remote_url

app = FastAPI(title="DJJ", docs_url=None, redoc_url=None)
WEB_DIR = Path(__file__).parent.parent / "web"
http_client = httpx.AsyncClient(timeout=30.0)

@app.on_event("startup")
async def startup():
    scan_all()
    stats = get_stats()
    print(f"[djj] Ready: {stats['total']} local videos, {len(stats['remote'])} remote sources")

@app.on_event("shutdown")
async def shutdown():
    await http_client.aclose()

@app.get("/api/random")
async def api_random(source: str | None = None):
    # 优先处理远程源
    if source and is_remote_source(source):
        remote_url = get_remote_url(source)
        if remote_url:
            try:
                resp = await http_client.get(remote_url, timeout=15.0)
                resp.raise_for_status()
                data = resp.json()
                # 兼容两种格式: video_url 或 url
                video_url = data.get("video_url") or data.get("url") or data.get("data", {}).get("url", "")
                video_name = data.get("name") or data.get("title") or data.get("data", {}).get("title", "未知")
                if not video_url:
                    return JSONResponse({"error": "remote api returned no url"}, status_code=502)
                token = register_remote(video_url, video_name)
                return {"token": token, "name": video_name, "remote": True}
            except httpx.HTTPError as e:
                return JSONResponse({"error": f"remote fetch failed: {e}"}, status_code=502)

    # 随机选一个源（包含远程）
    all_sources = get_source_list()
    if source:
        token = get_random(source)
    else:
        # 随机决定是否从远程源取
        remote_names = [s for s in all_sources if is_remote_source(s)]
        local_names = [s for s in all_sources if not is_remote_source(s)]
        if remote_names and (not local_names or random.random() < len(remote_names) / len(all_sources)):
            rs = random.choice(remote_names)
            remote_url = get_remote_url(rs)
            if remote_url:
                try:
                    resp = await http_client.get(remote_url, timeout=15.0)
                    resp.raise_for_status()
                    data = resp.json()
                    video_url = data.get("video_url") or data.get("url") or data.get("data", {}).get("url", "")
                    video_name = data.get("name") or data.get("title") or data.get("data", {}).get("title", "未知")
                    if video_url:
                        token = register_remote(video_url, video_name)
                        return {"token": token, "name": video_name, "remote": True}
                except httpx.HTTPError:
                    pass  # fallback to local
        token = get_random_any()

    if not token:
        return JSONResponse({"error": "no videos"}, status_code=404)
    return {"token": token, "name": get_name(token)}

@app.get("/api/play")
async def api_play(token: str):
    # 远程token: 代理流式播放
    if is_remote_token(token):
        info = get_remote_info(token)
        if not info:
            return JSONResponse({"error": "invalid remote token"}, status_code=403)
        try:
            resp = await http_client.get(info["url"], timeout=60.0, follow_redirects=True)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "video/mp4")
            return StreamingResponse(
                content=resp.aiter_bytes(chunk_size=65536),
                media_type=content_type,
                headers={"Content-Disposition": f"inline; filename=\"{info['name']}.mp4\""},
            )
        except httpx.HTTPError:
            return JSONResponse({"error": "remote video fetch failed"}, status_code=502)

    # 本地token
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