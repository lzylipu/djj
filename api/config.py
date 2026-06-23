import os, json, yaml
from pathlib import Path

DATA_DIR = Path(os.getenv('DJJ_DATA', '/data'))
CFG_PATH = DATA_DIR / 'config.yaml'
_SKEY = "API" + "_SECRET"

_DEFAULT_CONFIG = {
    "server": {
        "port": 8080,
        "secret": "change-me-to-random",
    },
    "sources": [
        {"name": "默认", "type": "local", "path": "/videos"},
    ],
}

def _generate_default():
    """首次启动自动生成默认配置文件"""
    CFG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CFG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(_DEFAULT_CONFIG, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print(f"[djj] Generated default config: {CFG_PATH}")
    print(f"[djj] Edit it to add/modify sources, then restart container")

def _load():
    if not CFG_PATH.exists():
        _generate_default()

    with open(CFG_PATH, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    server = raw.get("server", {})
    sources = raw.get("sources", [])
    return {
        "port": int(os.getenv("PORT", server.get("port", 8080))),
        "api_secret": os.getenv(_SKEY, server.get("secret", "djj-default-secret-change-me")),
        "sources": sources,
        "config_file": str(CFG_PATH),
        "data_dir": str(DATA_DIR),
        "raw": raw,
    }

CFG = _load()
