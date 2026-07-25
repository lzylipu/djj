import random, os, httpx, subprocess, asyncio, json, re
from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from .auth import resolve_token, is_remote_token, get_remote_info, register_remote
from .config import CFG
from .scanner import (
    get_random, get_random_any, get_source_list, get_name, get_stats, scan_all,
    is_remote_source, is_group_source, get_remote_url, get_remote_meta,
    pick_source_from_group, report_source_fail, report_source_ok, get_group_list,
    add_source, remove_source, reload_sources,
)
from fastapi import Request
from fastapi.responses import PlainTextResponse

app = FastAPI(title="DJJ", docs_url=None, redoc_url=None)
WEB_DIR = Path(__file__).parent.parent / "web"
http_client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)


@app.on_event("startup")
async def startup():
    scan_all()
    stats = get_stats()
    print(f"[djj] Ready: {stats['local_total']} local, {stats['remote_count']} remote, {stats['group_count']} group")


@app.on_event("shutdown")
async def shutdown():
    await http_client.aclose()


def _dig(obj, dotpath):
    """按 dot path 取嵌套字段: data.video -> obj['data']['video']"""
    cur = obj
    for k in dotpath.split("."):
        if cur is None:
            return ""
        if isinstance(cur, dict):
            cur = cur.get(k)
        elif isinstance(cur, list):
            try:
                cur = cur[int(k)]
            except Exception:
                return ""
        else:
            return ""
    return cur or ""


def _extract_json_video_url(data, json_path=""):
    """从 JSON 取视频 URL,优先 json_path 配置,否则走老兼容多 key"""
    if json_path:
        v = _dig(data, json_path)
        if isinstance(v, str) and v:
            return v
        if isinstance(v, dict):
            return v.get("url") or v.get("video_url") or v.get("link") or ""
    # 老兼容: video_url / url / data.url / data.link / data.video
    if not isinstance(data, dict):
        return ""
    return (data.get("video_url") or data.get("url")
            or (data.get("data", {}) or {}).get("url", "")
            or (data.get("data", {}) or {}).get("link", "")
            or (data.get("data", {}) or {}).get("video", ""))


def _extract_json_name(data, json_path=""):
    n = data.get("name") if isinstance(data, dict) else ""
    if not n and isinstance(data, dict):
        n = data.get("title") or (data.get("data", {}) or {}).get("title", "")
    return n or "unknown"


def _abs_url(url, base):
    if not url:
        return ""
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        p = urlparse(str(base))
        return f"{p.scheme}://{p.netloc}{url}"
    if url.startswith("./"):
        # 相对当前路径,取 base 的目录拼
        p = urlparse(str(base))
        base_dir = str(p.path).rsplit("/", 1)[0]
        return f"{p.scheme}://{p.netloc}{base_dir}/{url[2:]}"
    if not (url.startswith("http://") or url.startswith("https://")):
        # 既不是绝对URL也不是根/相对路径,补 base 的 scheme://netloc + path + url
        p = urlparse(str(base))
        if p.netloc:
            return f"{p.scheme}://{p.netloc}/{url.lstrip('/')}"
    return url


def _domain_of(url):
    """从源 URL 提取显示用域名(去掉 www. 前缀),用于拼 @域名 后缀"""
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        return ""
    if host.lower().startswith("www."):
        host = host[4:]
    return host


def _display_name(raw_name, src_url):
    """统一显示名规则: 原名@域名 (域名取自源URL,去 www.)
    - 原名为空就用 '网络视频'
    - 域名取不到就不加 @后缀
    - 已含 @ 的不重复加(避免老数据 / 用户改)
    """
    base = (raw_name or "").strip() or "网络视频"
    if "@" in base:
        return base
    dom = _domain_of(src_url or "")
    return f"{base}@{dom}" if dom else base


async def _fetch_one_source(name, meta):
    """对单个远程源做一次取视频尝试,返回 {token,name,remote} 或 None.
    兼容: 302 Location / JSON / 直接 mp4 流 / HTML 内嵌 video src.
    受 meta['mode'] 约束:'302' 'json' 'html' 'mp4' 'auto'(默认).
    返回的 name 统一为 原名@域名 形式,本地源对比则是 文件名(stem),前端一眼能看出视频出处.
    """
    url = meta.get("url", "")
    mode = meta.get("mode", "auto")
    json_path = meta.get("json_path", "")
    if not url:
        return None
    # 显示名始终基于源URL的域名,不管走到哪个分支都用同一个 _display_name
    disp = _display_name(name, url)
    try:
        # auto/302/直链模式: 不要 follow,以便看 Location
        # json/html: 直接 follow 取最终 body
        follow = mode in ("json", "html")
        resp = await http_client.get(url, timeout=6.0, follow_redirects=follow)

        # 302/301 跳转
        if resp.status_code in (301, 302, 303, 307, 308):
            loc = resp.headers.get("location", "")
            if loc:
                vu = _abs_url(loc, url)
                token = register_remote(vu, disp)
                return {"token": token, "name": disp, "remote": True}

        resp.raise_for_status()
        ct = (resp.headers.get("content-type") or "").lower()

        # 直接 mp4 流(资源网有时直接吐 mp4) 或 mode=mp4
        if mode == "mp4" or "video" in ct or "octet-stream" in ct:
            vu = str(resp.url)
            token = register_remote(vu, disp)
            return {"token": token, "name": disp, "remote": True}

        # JSON
        if mode == "json" or (mode == "auto" and "json" in ct):
            try:
                data = resp.json()
            except Exception:
                data = None
            if data is not None:
                vu = _extract_json_video_url(data, json_path)
                if vu:
                    vn = _extract_json_name(data, json_path)
                    # JSON 自带 title 用 title@域名, 否则用源名@域名
                    final = _display_name(vn if vn and vn != "unknown" else name, url)
                    token = register_remote(_abs_url(vu, str(resp.url)), final)
                    return {"token": token, "name": final, "remote": True}
                # 空 url, 各源偶发返回空, 静默返回 None 让上层降级

        # mode=text_url: body 是纯文本 URL(diskgirl 返回 cdntube2.b-cdn.net/xxx.mp4)
        if mode == "text_url" or (mode == "auto" and ct.startswith("text/plain")):
            body = (resp.text or "").strip()
            # 截出第一行,排除多行
            line = body.splitlines()[0].strip() if body else ""
            # 合法 URL 判定: 含 .mp4 或 含 http(s)
            if line and ("http://" in line or "https://" in line):
                token = register_remote(line, disp)
                return {"token": token, "name": disp, "remote": True}

        # HTML 内嵌 video src
        if mode == "html" or mode == "auto":
            html = resp.text
            for pat in [r'src="([^"]*\.mp4[^"]*)"', r"src='([^']*\.mp4[^']*)'",
                        r'src="([^"]*video\.php[^"]*)"', r"src='([^']*video\.php[^']*)'"]:
                srcs = re.findall(pat, html)
                if srcs:
                    vu = _abs_url(srcs[0], str(resp.url))
                    token = register_remote(vu, disp)
                    return {"token": token, "name": disp, "remote": True}

        return None
    except Exception as e:
        print(f"[djj] source '{name}' fetch failed: {type(e).__name__}: {e}")
        return None


async def _fetch_group(group, max_attempts=None):
    """聚合分发器: 从 group 内按权重随机选未熔断源,失败自动降级到下一个,直到成功或全部失败."""
    tried = set()
    # 试 N 次,每次挑一个还没试过的源
    total = 0
    while True:
        name = pick_source_from_group(group, exclude=tried)
        if name is None:
            break
        tried.add(name)
        total += 1
        meta = get_remote_meta(name) or {}
        # 单源 retry
        result = None
        for _ in range(int(meta.get("retry", 1))):
            result = await _fetch_one_source(name, meta)
            if result:
                break
        if result:
            report_source_ok(group, name)
            print(f"[djj] group '{group}' hit source '{name}'")
            # 把 group 标记写进 token name -- 用 source 名作为显示名,前端可见
            if "name" in result:
                result["name"] = result["name"] or name
            return result
        report_source_fail(group, name)
        if max_attempts and total >= max_attempts:
            break
    return None


@app.get("/api/random")
async def api_random(source: str | None = None):
    # 1. 聚合组
    if source and is_group_source(source):
        result = await _fetch_group(source)
        if result:
            return result
        return JSONResponse({"error": "all group sources failed"}, status_code=502)

    # 2. 单独远程源(配置里没标 group)
    if source and is_remote_source(source):
        meta = get_remote_meta(source) or {}
        result = await _fetch_one_source(source, meta)
        if result:
            return result
        return JSONResponse({"error": "remote fetch failed"}, status_code=502)

    all_sources = get_source_list()  # 排序: 本地最前 -> 独立远程 -> 聚合组
    if source:
        # 指定本地源
        token = get_random(source)
        if token:
            return {"token": token, "name": get_name(token)}
        return JSONResponse({"error": "no videos in source"}, status_code=404)

    # === 无 source 参数:本地始终优先 ===
    # 1. 先看本地有没有视频;有就 100% 用本地(本地映射文件夹里随机一个)
    token = get_random_any()
    if token:
        return {"token": token, "name": get_name(token)}

    # 2. 本地空(没挂载文件夹 or 没视频文件) → 用网络源
    #    优先聚合组(内部自动加权随机 + 失败降级 + 熔断)
    group_names = [s for s in all_sources if is_group_source(s)]
    if group_names:
        result = await _fetch_group(random.choice(group_names))
        if result:
            return result
    # 3. 还不行 → 试独立远程源
    remote_names = [s for s in all_sources if is_remote_source(s)]
    for rs in remote_names:
        meta = get_remote_meta(rs) or {}
        result = await _fetch_one_source(rs, meta)
        if result:
            return result

    return JSONResponse({"error": "no videos"}, status_code=404)


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
            return None
        return codec
    except Exception:
        return None

async def _ffmpeg_stream(file_path: str):
    proc = await asyncio.create_subprocess_exec(
        FFMPEG_PATH, "-i", file_path,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "frag_keyframe+empty_moov",
        "-f", "mp4",
        "-",
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
            vid_url = info["url"]
            # 防御: register_remote 时偶尔存进来的不是合法 http(s) URL
            if not (vid_url.startswith("http://") or vid_url.startswith("https://")):
                return JSONResponse({"error": "invalid remote url in token"}, status_code=502)
            sep = "&" if "?" in vid_url else "?"
            vid_url += f"{sep}_t={random.random()}"
            resp = await http_client.get(vid_url, timeout=60.0, follow_redirects=True)
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


# ============================================================
# Admin API: 运行时增/删/重载源(用 X-DJJ-Secret 头校验)
# 服务器启动前在 config.yaml 里设 server.secret=xxx,调用方传相同值
# ============================================================

def _check_admin(request: Request):
    """校验 X-DJJ-Secret 头是否匹配 server.secret;不匹配返回 False"""
    expected = str(CFG.get("api_secret", ""))
    if not expected or expected == "change-me-to-random-string":
        return False  # 默认值不允许管理
    got = request.headers.get("X-DJJ-Secret", "")
    return got == expected


@app.post("/api/admin/sources")
async def admin_add_source(request: Request):
    """添加/替换一个远程源. body 是 dict:
    {name, url, group?, mode?, json_path?, weight?, retry?}
    同 name 已存在则整体替换.持久化回 config.yaml.
    """
    if not _check_admin(request):
        return JSONResponse({"error": "forbidden: invalid or missing X-DJJ-Secret"}, status_code=403)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON body"}, status_code=400)
    name = str(body.get("name", "")).strip()
    url = str(body.get("url", "")).strip()
    if not name or not url:
        return JSONResponse({"error": "name and url required"}, status_code=400)
    # 构造与 config.yaml 同 schema 的 entry
    entry: dict = {"name": name, "url": url}
    for opt in ("group", "mode", "json_path"):
        v = body.get(opt)
        if v is not None and str(v).strip():
            entry[opt] = str(v).strip()
    for opt in ("weight", "retry"):
        try:
            v = int(body.get(opt, 0))
            if v >= 1:
                entry[opt] = v
        except Exception:
            pass
    try:
        add_source(entry)
        return {"ok": True, "name": name, "sources": get_source_list(), "stats": get_stats()}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.delete("/api/admin/sources")
async def admin_del_source(request: Request, name: str):
    """按源名删除一个源(包括独立远程源或组内成员).?name=xxx"""
    if not _check_admin(request):
        return JSONResponse({"error": "forbidden: invalid or missing X-DJJ-Secret"}, status_code=403)
    name = (name or "").strip()
    if not name:
        return JSONResponse({"error": "name query param required"}, status_code=400)
    done = remove_source(name)
    return {"ok": done, "name": name, "sources": get_source_list(), "stats": get_stats()}


@app.post("/api/admin/reload")
async def admin_reload(request: Request):
    """重新从磁盘加载 config.yaml 重建索引(直接编辑挂载的 config.yaml 后调用)."""
    if not _check_admin(request):
        return JSONResponse({"error": "forbidden: invalid or missing X-DJJ-Secret"}, status_code=403)
    reload_sources()
    print("[djj] Admin reloaded config.yaml")
    return {"ok": True, "sources": get_source_list(), "stats": get_stats()}


@app.get("/", response_class=HTMLResponse)
async def index():
    return (WEB_DIR / "index.html").read_text(encoding="utf-8")


if (WEB_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=str(WEB_DIR / "css")), name="css")
if (WEB_DIR / "img").exists():
    app.mount("/img", StaticFiles(directory=str(WEB_DIR / "img")), name="img")
