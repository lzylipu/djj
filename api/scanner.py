import random
from pathlib import Path
from .config import CFG
from .auth import register_file

_source_index = {}      # name -> [token, ...]
_name_index = {}        # token -> display_name
_remote_sources = {}    # name -> {"url": "..."}
_local_sources = {}    # name -> path
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv"}


def scan_all():
    sources = CFG.get("sources", [])
    if not sources:
        print("[djj] WARNING: No sources configured. Edit /data/config.yaml and restart.")
        return

    for src in sources:
        name = src.get("name", "未命名")
        stype = src.get("type", "local")

        if stype == "remote":
            url = src.get("url", "")
            if url:
                _remote_sources[name] = {"url": url}
                _source_index[name] = []
                print(f"[djj] REMOTE {name}: {url}")
            continue

        # type=local
        path = src.get("path", "")
        p = Path(path)
        _local_sources[name] = path
        if not p.exists():
            print(f"[djj] WARNING: {path} not found ({name})")
            _source_index[name] = []
            continue
        tokens = []
        for f in p.rglob("*"):
            if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
                token = register_file(str(f))
                tokens.append(token)
                _name_index[token] = f.stem
        _source_index[name] = tokens
        print(f"[djj] LOCAL {name}: {len(tokens)} videos from {path}")


def is_remote_source(name):
    return name in _remote_sources


def is_local_source(name):
    return name in _local_sources


def get_remote_url(name):
    return _remote_sources.get(name, {}).get("url")


def get_source_list():
    return list(_source_index.keys())


def get_random(name):
    if is_remote_source(name):
        return None  # server层fetch
    tokens = _source_index.get(name, [])
    return random.choice(tokens) if tokens else None


def get_random_any():
    local_sources = {k: v for k, v in _source_index.items() if not is_remote_source(k) and v}
    if not local_sources:
        return None
    all_tokens = [t for ts in local_sources.values() for t in ts]
    return random.choice(all_tokens) if all_tokens else None


def get_name(token):
    return _name_index.get(token, "未知")


def get_stats():
    sources = {}
    for n, tokens in _source_index.items():
        if is_remote_source(n):
            sources[n] = {"type": "remote", "count": -1, "url": _remote_sources[n]["url"]}
        else:
            sources[n] = {"type": "local", "count": len(tokens), "path": _local_sources.get(n, "")}
    return {
        "sources": sources,
        "local_total": sum(s["count"] for s in sources.values() if s["count"] >= 0),
        "remote_count": len(_remote_sources),
    }
