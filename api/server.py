import random, os, httpx, subprocess, asyncio, json
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from .auth import resolve_token, is_remote_token, get_remote_info, register_remote
from .config import CFG
from .scanner import get_random, get_random_any, get_source_list, get_name, get_stats, scan_all, is_remote_source, get_remote_url

app = FastAPI(title="DJJ", docs_url=None, redoc_url=None)
WEB_DIR = Path(__file__).parent.parent / "web"
http_client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)


@app.on_event("startup")
async def startup():
    scan_all()
    stats = get_stats()
    print(f"[djj] Ready: {stats['local_total']} local, {stats['remote_count']} remote sources")


@app.on_event("shutdown")
async def shutdown():
    await http_client.aclose()


def _parse_remote_response(data, resp):
    """从远程API响应中提取视频URL和名称，兼容多种格式"""
    # JSON格式: {"video_url":"..."} / {"url":"..."} / {"data":{"url":"..."}}
    if isinstance(data, dict):
        video_url = (data.get("video_url") or data.get("url")
                     or data.get("data", {}).get("url", "")
                     or data.get("data", {}).get("link", ""))
        video_name = (data.get("name") or data.get("title")
                      or data.get("data", {}).get("title", "unknown"))
        return video_url, video_name
    return "", "unknown"


async def _fetch_remote(remote_url):
    """请求远程API获取视频，兼容JSON和直接mp4流"""
    try:
        resp = await http_client.get(remote_url, timeout=15.0)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "").lower()

        # 直接返回视频流（如 v.nrzj.vip/video.php）
        if "video" in content_type or "octet-stream" in content_type:
            video_url = str(resp.url)
            token = register_remote(video_url, "远程视频")
            return {"token": token, "name": "远程视频", "remote": True}

        # JSON响应
        try:
            data = resp.json()
            video_url, video_name = _parse_remote_response(data, resp)
            if not video_url:
                return None
            token = register_remote(video_url, video_name)
            return {"token": token, "name": video_name, "remote": True}
        except Exception:
            # HTML页面: 尝试提取 video src
            html = resp.text
            srcs = __import__("re").findall(r'src="([^"]*\.mp4[^"]*)"', html)
            if not srcs:
                srcs = __import__("re").findall(r"src='([^']*\.mp4[^']*)'", html)
            if srcs:
                video_url = srcs[0]
                if video_url.startswith("//"):
                    video_url = "https:" + video_url
                elif video_url.startswith("/"):
                    parsed = __import__("urllib.parse").urlparse(str(resp.url))
                    video_url = f"{parsed.scheme}://{parsed.netloc}{video_url}"
                token = register_remote(video_url, "热舞视频")
                return {"token": token, "name": "热舞视频", "remote": True}
            # 都不匹配 → 尝试当视频URL用
            video_url = str(resp.url)
            token = register_remote(video_url, "未知")
            return {"token": token, "name": "未知", "remote": True}
    except httpx.HTTPError as e:
        print(f"[djj] Remote fetch failed: {e}")
        return None


@app.get("/api/random")
async def api_random(source: str | None = None):
    # 指定远程源
    if source and is_remote_source(source):
        remote_url = get_remote_url(source)
        if remote_url:
            result = await _fetch_remote(remote_url)
            if result:
                return result
            return JSONResponse({"error": "remote fetch failed"}, status_code=502)

    all_sources = get_source_list()
    if source:
        # 指定本地源
        token = get_random(source)
    else:
        # 混合随机：按比例选择远程/本地
        remote_names = [s for s in all_sources if is_remote_source(s)]
        local_names = [s for s in all_sources if not is_remote_source(s)]
        if remote_names and (not local_names or random.random() < len(remote_names) / len(all_sources)):
            rs = random.choice(remote_names)
            remote_url = get_remote_url(rs)
            if remote_url:
                result = await _fetch_remote(remote_url)
                if result:
                    return result
        token = get_random_any()

    if not token:
        return JSONResponse({"error": "no videos"}, status_code=404)
    return {"token": token, "name": get_name(token)}


FFMPEG_PATH = "/usr/bin/ffmpeg"

async def _transcode_if_needed(file_path: str):
    """检测视频编码，非H.264则ffmpeg实时转码"""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-select_streams", "v:0", file_path,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
        info = json.loads(stdout)
        codec = info.get("streams", [{}])[0].get("codec_name", "")
        if codec in ("h264", "hevc", "av1"):
            return None  # 浏览器原生支持，不需要转码
        return codec  # 需要转码
    except Exception:
        return None

async def _ffmpeg_stream(file_path: str):
    """用ffmpeg实时转码为H.264 mp4返回流"""
    proc = await asyncio.create_subprocess_exec(
        FFMPEG_PATH, "-i", file_path,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "frag_keyframe+empty_moov",
        "-f", "mp4",
        "-",  # stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    return proc


@app.get("/api/play")
async def api_play(token: str):
    if is_remote_token(token):
        info = get_remote_info(token)
        if not info:
            return JSONResponse({"error": "invalid remote token"}, status_code=403)
        try:
            resp = await http_client.get(info["url"], timeout=60.0, follow_redirects=True)
            resp.raise_for_status()
            ct = resp.headers.get("content-type", "").lower()
            content_type = "video/mp4" if not ct or ct == "application/octet-stream" else ct
            return StreamingResponse(
                content=resp.aiter_bytes(chunk_size=65536),
                media_type=content_type,
                headers={"Content-Length": resp.headers.get("content-length", "")},
            )
        except httpx.HTTPError:
            return JSONResponse({"error": "remote video fetch failed"}, status_code=502)

    file_path = resolve_token(token)
    if not file_path or not os.path.isfile(file_path):
        return JSONResponse({"error": "invalid token"}, status_code=403)

    # 检测视频编码，非H.264自动转码
    codec = await _transcode_if_needed(file_path)
    if codec:
        print(f"[djj] Transcoding {Path(file_path).name} ({codec} -> h264)")
        proc = await _ffmpeg_stream(file_path)
        return StreamingResponse(
            content=proc.stdout,
            media_type="video/mp4",
            headers={"X-Transcoded": codec},
        )

    path = Path(file_path)
    mime = {".mp4": "video/mp4", ".avi": "video/x-msvideo", ".mkv": "video/x-matroska",
            ".mov": "video/quicktime", ".webm": "video/webm", ".flv": "video/x-flv"}.get(path.suffix.lower(), "video/mp4")
    return FileResponse(file_path, media_type=mime)


@app.get("/api/sources")
async def api_sources():
    return {"sources": get_source_list(), "stats": get_stats()}


@app.get("/", response_class=HTMLResponse)
async def index():
    return (WEB_DIR / "index.html").read_text(encoding="utf-8")


if (WEB_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=str(WEB_DIR / "css")), name="css")
if (WEB_DIR / "img").exists():
    app.mount("/img", StaticFiles(directory=str(WEB_DIR / "img")), name="img")
