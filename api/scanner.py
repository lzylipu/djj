import random
from pathlib import Path
from .config import CFG
from .auth import register_file

_source_index = {}      # source_name -> [token, ...]
_name_index = {}        # token -> display_name
_remote_sources = {}    # source_name -> {"url": "..."}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv"}

def scan_all():
    # 扫描本地目录
    for dir_path, source_name in zip(CFG["video_dirs"], CFG["source_names"]):
        tokens = []
        p = Path(dir_path)
        if not p.exists():
            print(f"[djj] WARNING: {dir_path} not found")
            continue
        for f in p.rglob("*"):
            if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
                token = register_file(str(f))
                tokens.append(token)
                _name_index[token] = f.stem
        _source_index[source_name] = tokens
        print(f"[djj] LOCAL {source_name}: {len(tokens)} videos")

    # 注册远程API源
    for rs in CFG["remote_sources"]:
        name = rs.get("name", "远程源")
        url = rs.get("url", "")
        if url:
            _remote_sources[name] = {"url": url}
            _source_index[name] = []  # 远程源无本地token，标记为空列表
            print(f"[djj] REMOTE {name}: {url}")

def get_source_list():
    return list(_source_index.keys())

def is_remote_source(source_name):
    return source_name in _remote_sources

def get_remote_url(source_name):
    return _remote_sources.get(source_name, {}).get("url")

def get_random(source_name):
    if is_remote_source(source_name):
        return None  # 远程源由server层fetch
    tokens = _source_index.get(source_name, [])
    return random.choice(tokens) if tokens else None

def get_random_any():
    # 只从本地源随机（远程源需要server层单独fetch）
    local_sources = {k: v for k, v in _source_index.items() if not is_remote_source(k) and v}
    if not local_sources:
        return None
    # 按视频数量加权随机
    all_tokens = [t for ts in local_sources.values() for t in ts]
    return random.choice(all_tokens) if all_tokens else None

def get_name(token):
    return _name_index.get(token, "未知")

def get_stats():
    sources = {}
    for n, tokens in _source_index.items():
        if is_remote_source(n):
            sources[n] = -1  # -1表示远程源，数量未知
        else:
            sources[n] = len(tokens)
    return {
        "sources": sources,
        "total": sum(v for v in sources.values() if v >= 0),
        "remote": list(_remote_sources.keys()),
    }