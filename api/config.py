import os, json, yaml
from pathlib import Path

CFG_PATH = os.getenv("DJJ_CONFIG", "/app/config.yaml")
_SKEY = "API" + "_SECRET"

def _load():
    cfg_file = Path(CFG_PATH)
    if cfg_file.exists():
        with open(cfg_file, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        server = raw.get("server", {})
        sources = raw.get("sources", [])
        return {
            "port": int(os.getenv("PORT", server.get("port", 8080))),
            "api_secret": os.getenv(_SKEY, server.get("secret", "djj-default-secret-change-me")),
            "sources": sources,
            "config_file": str(cfg_file),
        }

    # 兼容: 无config.yaml时从环境变量读
    dirs_raw = os.getenv("VIDEO_DIRS", '["/videos"]')
    video_dirs = json.loads(dirs_raw) if dirs_raw.startswith("[") else [d.strip() for d in dirs_raw.split(",") if d.strip()]
    names_raw = os.getenv("SOURCE_NAMES", '["默认"]')
    source_names = json.loads(names_raw) if names_raw.startswith("[") else [n.strip() for n in names_raw.split(",") if n.strip()]
    remote_raw = os.getenv("REMOTE_SOURCES", "[]")
    remote_sources = json.loads(remote_raw) if remote_raw.strip() else []
    sources = []
    for i, d in enumerate(video_dirs):
        sources.append({"name": source_names[i] if i < len(source_names) else f"源{i+1}", "type": "local", "path": d})
    for rs in remote_sources:
        sources.append({"name": rs.get("name", "远程源"), "type": "remote", "url": rs.get("url", "")})
    return {
        "port": int(os.getenv("PORT", "8080")),
        "api_secret": os.getenv(_SKEY, "djj-default-secret-change-me"),
        "sources": sources,
        "config_file": None,
    }

CFG = _load()
