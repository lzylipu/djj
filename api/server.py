import random, os, httpx, subprocess, asyncio, json, re, time, uuid
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


def _log(rid, tag, msg):
    """统一日志: [rid][tag] msg  方便追踪一次取视频的全链路."""
    print(f"[{rid}][{tag}] {msg}", flush=True)


def _new_rid():
    """每次 /api/random 或 /api/play 一个 6 位短 ID,贯穿整个流程."""
    return uuid.uuid4().hex[:6]


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


def _domain_root(url):
    """从 URL 提取二级域名根,如 https://api.yujn.cn/x -> yujn.cn
    纯 stdlib 实现:
    - api.yujn.cn  -> yujn.cn
    - www.lcc8.com -> lcc8.com
    - xjj.nxux.cn  -> nxux.cn
    - v.api.aa1.cn -> aa1.cn
    - yx520.ltd    -> yx520.ltd(只剩两段时直接返回)
    对 .com.cn/.co.uk 这类三段 TLD 处理不完美,但国内小姐姐 API 站
    域名基本是 *.cn/*.com/*.ltd/*.net 两段 TLD,够用.
    """
    try:
        host = (urlparse(url or "").hostname or "").lower()
    except Exception:
        return ""
    if not host:
        return ""
    parts = host.split(".")
    if len(parts) <= 2:
        # 已经是 root,如 yx520.ltd / yujn.cn
        return host
    # 去 api./www./v./xjj. 这种子域前缀,保留最后两段
    return ".".join(parts[-2:])


def _display_name(raw_name, src_url):
    """统一显示名规则: 直接返回源URL的二级域名根
    - api.yujn.cn  -> yujn.cn
    - www.lcc8.com -> lcc8.com
    - xjj.nxux.cn  -> nxux.cn
    - v.api.aa1.cn -> aa1.cn
    前端 <span id="vidNamePC"> 就显示这个域名,不显示源名.
    本地源不走这里(走 scanner._name_index 的 f.stem).
    域名取不到就返回 '网络视频' 兜底.
    """
    dom = _domain_root(src_url or "")
    return dom or "网络视频"


async def _fetch_one_source(name, meta, rid="------"):
    """对单个远程源做一次取视频尝试,返回 {token,name,remote} 或 None.
    兼容: 302 Location / JSON / 直接 mp4 流 / HTML 内嵌 video src.
    受 meta['mode'] 约束:'302' 'json' 'html' 'mp4' 'auto'(默认).
    返回的 name 统一为 源URL的二级域名根,前端一眼能看出视频出处.
    全程用 rid 打日志,追踪一次取视频的全链路.
    """
    url = meta.get("url", "")
    mode = meta.get("mode", "auto")
    json_path = meta.get("json_path", "")
    if not url:
        _log(rid, "FETCH", f"source='{name}' SKIP (no url in meta)")
        return None
    disp = _display_name(name, url)
    t0 = time.time()
    _log(rid, "FETCH", f"source='{name}' mode={mode} url={url[:80]}")
    try:
        follow = mode in ("json", "html")
        resp = await http_client.get(url, timeout=6.0, follow_redirects=follow)
        dt = int((time.time() - t0) * 1000)
        _log(rid, "FETCH", f"source='{name}' resp status={resp.status_code} ct={resp.headers.get('content-type','')[:40]} {dt}ms")

        # 302/301 跳转
        if resp.status_code in (301, 302, 303, 307, 308):
            loc = resp.headers.get("location", "")
            if loc:
                vu = _abs_url(loc, url)
                token = register_remote(vu, disp)
                _log(rid, "FETCH", f"source='{name}' 302 redirect -> {vu[:100]} (as '{disp}')")
                return {"token": token, "name": disp, "remote": True}
            _log(rid, "FETCH", f"source='{name}' 302 but no Location header")
            return None

        resp.raise_for_status()
        ct = (resp.headers.get("content-type") or "").lower()

        # 直接 mp4 流(资源网有时直接吐 mp4) 或 mode=mp4
        if mode == "mp4" or "video" in ct or "octet-stream" in ct:
            vu = str(resp.url)
            token = register_remote(vu, disp)
            _log(rid, "FETCH", f"source='{name}' direct mp4 stream -> {vu[:100]} (as '{disp}')")
            return {"token": token, "name": disp, "remote": True}

        # JSON
        if mode == "json" or (mode == "auto" and "json" in ct):
            try:
                data = resp.json()
            except Exception as je:
                _log(rid, "FETCH", f"source='{name}' json mode but body not JSON: {je}")
                data = None
            if data is not None:
                vu = _extract_json_video_url(data, json_path)
                if vu:
                    final_url = _abs_url(vu, str(resp.url))
                    token = register_remote(final_url, disp)
                    _log(rid, "FETCH", f"source='{name}' json video_url -> {final_url[:100]} (as '{disp}')")
                    return {"token": token, "name": disp, "remote": True}
                else:
                    _log(rid, "FETCH", f"source='{name}' json_path='{json_path}' extraction FAILED (data preview: {str(data)[:120]})")
                    return None

        # mode=text_url: body 是纯文本 URL(diskgirl 返回 cdntube2.b-cdn.net/xxx.mp4)
        if mode == "text_url" or (mode == "auto" and ct.startswith("text/plain")):
            body = (resp.text or "").strip()
            line = body.splitlines()[0].strip() if body else ""
            if line and ("http://" in line or "https://" in line):
                token = register_remote(line, disp)
                _log(rid, "FETCH", f"source='{name}' text_url -> {line[:100]} (as '{disp}')")
                return {"token": token, "name": disp, "remote": True}
            _log(rid, "FETCH", f"source='{name}' text_url body has no valid URL (body preview: {body[:120]})")
            return None

        # HTML 内嵌 video src
        if mode == "html" or mode == "auto":
            html = resp.text
            for pat in [r'src="([^"]*\.mp4[^"]*)"', r"src='([^']*\.mp4[^']*)'",
                        r'src="([^"]*video\.php[^"]*)"', r"src='([^']*video\.php[^']*)'"]:
                srcs = re.findall(pat, html)
                if srcs:
                    vu = _abs_url(srcs[0], str(resp.url))
                    token = register_remote(vu, disp)
                    _log(rid, "FETCH", f"source='{name}' html video src -> {vu[:100]} (as '{disp}')")
                    return {"token": token, "name": disp, "remote": True}
            _log(rid, "FETCH", f"source='{name}' html mode: no <video src> matched (ct={ct[:30]}, html preview: {html[:150]})")
            return None

        _log(rid, "FETCH", f"source='{name}' mode={mode} ct={ct[:40]} - no matching branch (fallthrough)")
        return None
    except httpx.TimeoutException:
        dt = int((time.time() - t0) * 1000)
        _log(rid, "FETCH", f"source='{name}' TIMEOUT after {dt}ms (>{6000}ms)")
        return None
    except httpx.HTTPError as he:
        dt = int((time.time() - t0) * 1000)
        _log(rid, "FETCH", f"source='{name}' HTTPError {type(he).__name__}: {he} {dt}ms")
        return None
    except Exception as e:
        dt = int((time.time() - t0) * 1000)
        _log(rid, "FETCH", f"source='{name}' EXCEPTION {type(e).__name__}: {e} {dt}ms")
        return None


async def _fetch_group(group, max_attempts=None, rid="------"):
    """聚合分发器: 从 group 内按权重随机选未熔断源,失败自动降级到下一个,直到成功或全部失败."""
    tried = set()
    total = 0
    t_start = time.time()
    _log(rid, "GROUP", f"enter group='{group}' max_attempts={max_attempts}")
    while True:
        name = pick_source_from_group(group, exclude=tried)
        if name is None:
            _log(rid, "GROUP", f"no more alive sources in group='{group}' (tried: {sorted(tried) or 'none'})")
            break
        tried.add(name)
        total += 1
        meta = get_remote_meta(name) or {}
        weight = meta.get("weight", 1)
        # 单源 retry
        result = None
        for r_i in range(int(meta.get("retry", 1))):
            if r_i > 0:
                _log(rid, "GROUP", f"source='{name}' retry #{r_i}")
            result = await _fetch_one_source(name, meta, rid=rid)
            if result:
                break
        if result:
            report_source_ok(group, name)
            dt = int((time.time() - t_start) * 1000)
            _log(rid, "GROUP", f"HIT group='{group}' source='{name}' (attempt #{total}, total {dt}ms) -> name='{result.get('name')}'")
            return result
        report_source_fail(group, name)
        _log(rid, "GROUP", f"FAIL source='{name}' - fallthrough to next (tried so far: {sorted(tried)})")
        if max_attempts and total >= max_attempts:
            _log(rid, "GROUP", f"hit max_attempts={max_attempts}, stop")
            break
    _log(rid, "GROUP", f"EXHAUSTED group='{group}' after {total} attempts ({int((time.time()-t_start)*1000)}ms total)")
    return None


@app.get("/api/random")
async def api_random(source: str | None = None):
    rid = _new_rid()
    t0 = time.time()
    _log(rid, "RAND", f"IN source='{source}'")
    # 1. 聚合组
    if source and is_group_source(source):
        result = await _fetch_group(source, rid=rid)
        if result:
            _log(rid, "RAND", f"OUT ok group - name='{result.get('name')}' ({int((time.time()-t0)*1000)}ms)")
            return result
        _log(rid, "RAND", f"OUT 502 all group sources failed ({int((time.time()-t0)*1000)}ms)")
        return JSONResponse({"error": "all group sources failed"}, status_code=502)

    # 2. 单独远程源(配置里没标 group)
    if source and is_remote_source(source):
        meta = get_remote_meta(source) or {}
        result = await _fetch_one_source(source, meta, rid=rid)
        if result:
            _log(rid, "RAND", f"OUT ok lone remote '{source}' - name='{result.get('name')}' ({int((time.time()-t0)*1000)}ms)")
            return result
        _log(rid, "RAND", f"OUT 502 lone remote '{source}' failed ({int((time.time()-t0)*1000)}ms)")
        return JSONResponse({"error": "remote fetch failed"}, status_code=502)

    all_sources = get_source_list()  # 排序: 本地最前 -> 独立远程 -> 聚合组
    if source:
        # 指定本地源
        token = get_random(source)
        if token:
            nm = get_name(token)
            _log(rid, "RAND", f"OUT ok local source='{source}' token=...{token[-8:]} name='{nm}' ({int((time.time()-t0)*1000)}ms)")
            return {"token": token, "name": nm}
        _log(rid, "RAND", f"OUT 404 no videos in local source='{source}'")
        return JSONResponse({"error": "no videos in source"}, status_code=404)

    # === 无 source 参数:本地始终优先 ===
    token = get_random_any()
    if token:
        nm = get_name(token)
        _log(rid, "RAND", f"OUT ok local_any token=...{token[-8:]} name='{nm}' ({int((time.time()-t0)*1000)}ms)")
        return {"token": token, "name": nm}

    # 2. 本地空 -> 用网络源
    group_names = [s for s in all_sources if is_group_source(s)]
    if group_names:
        chosen = random.choice(group_names)
        _log(rid, "RAND", f"local empty, fallback to random group='{chosen}'")
        result = await _fetch_group(chosen, rid=rid)
        if result:
            _log(rid, "RAND", f"OUT ok from group '{chosen}' - name='{result.get('name')}' ({int((time.time()-t0)*1000)}ms)")
            return result
    # 3. 还不行 -> 试独立远程源
    remote_names = [s for s in all_sources if is_remote_source(s)]
    if remote_names:
        _log(rid, "RAND", f"all groups exhausted, trying lone remotes: {remote_names}")
    for rs in remote_names:
        meta = get_remote_meta(rs) or {}
        result = await _fetch_one_source(rs, meta, rid=rid)
        if result:
            _log(rid, "RAND", f"OUT ok lone '{rs}' - name='{result.get('name')}' ({int((time.time()-t0)*1000)}ms)")
            return result

    _log(rid, "RAND", f"OUT 404 no videos at all ({int((time.time()-t0)*1000)}ms)")
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
    rid = _new_rid()
    t0 = time.time()
    _log(rid, "PLAY", f"IN token={token[:24]}...")
    if is_remote_token(token):
        info = get_remote_info(token)
        if not info:
            _log(rid, "PLAY", f"OUT 403 invalid remote token (not in _remote_map)")
            return JSONResponse({"error": "invalid remote token"}, status_code=403)
        try:
            vid_url = info["url"]
            saved_name = info.get("name", "?")
            if not (vid_url.startswith("http://") or vid_url.startswith("https://")):
                _log(rid, "PLAY", f"OUT 502 stored url is not http(s): {vid_url[:80]}")
                return JSONResponse({"error": "invalid remote url in token"}, status_code=502)
            sep = "&" if "?" in vid_url else "?"
            play_url = f"{vid_url}{sep}_t={random.random()}"
            _log(rid, "PLAY", f"remote: name='{saved_name}' fetching upstream {play_url[:100]}")
            resp = await http_client.get(play_url,
                timeout=httpx.Timeout(connect=1.5, read=1.5, write=5.0, pool=1.5),
                follow_redirects=True)
            dt = int((time.time() - t0) * 1000)
            _log(rid, "PLAY", f"upstream resp status={resp.status_code} ct={resp.headers.get('content-type','')[:40]} len={resp.headers.get('content-length','?')} {dt}ms")
            resp.raise_for_status()
            ct = resp.headers.get("content-type", "").lower()
            content_type = "video/mp4" if not ct or ct == "application/octet-stream" else ct
            _log(rid, "PLAY", f"OUT 200 streaming remote name='{saved_name}' ({int((time.time()-t0)*1000)}ms)")
            return StreamingResponse(
                content=resp.aiter_bytes(chunk_size=65536),
                media_type=content_type,
                headers={"Content-Length": resp.headers.get("content-length", "")},
            )
        except httpx.TimeoutException:
            dt = int((time.time() - t0) * 1000)
            nm = info.get('name','?') if isinstance(info,dict) else '?'
            _log(rid, "PLAY", f"OUT 502 SLOW upstream >1500ms ({dt}ms) name='{nm}' - dropping, will fallback on next random")
            return JSONResponse({"error": "remote video fetch timeout"}, status_code=502)
        except httpx.HTTPError as he:
            dt = int((time.time() - t0) * 1000)
            _log(rid, "PLAY", f"OUT 502 remote HTTPError {type(he).__name__}: {he} {dt}ms (name='{info.get('name','?') if isinstance(info,dict) else '?'}')")
            return JSONResponse({"error": "remote video fetch failed"}, status_code=502)

    file_path = resolve_token(token)
    if not file_path or not os.path.isfile(file_path):
        _log(rid, "PLAY", f"OUT 403 invalid local token (path={file_path or 'None'})")
        return JSONResponse({"error": "invalid token"}, status_code=403)

    codec = await _transcode_if_needed(file_path)
    if codec:
        _log(rid, "PLAY", f"local: {Path(file_path).name} codec={codec} -> transcode to h264")
        proc = await _ffmpeg_stream(file_path)
        _log(rid, "PLAY", f"OUT 200 streaming transcoded {Path(file_path).name} ({int((time.time()-t0)*1000)}ms)")
        return StreamingResponse(
            content=proc.stdout,
            media_type="video/mp4",
            headers={"X-Transcoded": codec},
        )

    path = Path(file_path)
    mime = {".mp4": "video/mp4", ".avi": "video/x-msvideo", ".mkv": "video/x-matroska",
            ".mov": "video/quicktime", ".webm": "video/webm", ".flv": "video/x-flv"}.get(path.suffix.lower(), "video/mp4")
    _log(rid, "PLAY", f"OUT 200 FileResponse {path.name} mime={mime} ({int((time.time()-t0)*1000)}ms)")
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
