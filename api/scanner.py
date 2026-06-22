import random
from pathlib import Path
from .config import CFG
from .auth import register_file

_source_index = {}
_name_index = {}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv"}

def scan_all():
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
        print(f"[djj] {source_name}: {len(tokens)} videos")

def get_random(source_name):
    tokens = _source_index.get(source_name, [])
    return random.choice(tokens) if tokens else None

def get_random_any():
    all_tokens = [t for ts in _source_index.values() for t in ts]
    return random.choice(all_tokens) if all_tokens else None

def get_source_list():
    return list(_source_index.keys())

def get_name(token):
    return _name_index.get(token, "未知")

def get_stats():
    return {"sources": {n: len(t) for n, t in _source_index.items()},
            "total": sum(len(t) for t in _source_index.values())}
