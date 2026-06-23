import os, yaml
from pathlib import Path

DATA_DIR = Path(os.getenv('DJJ_DATA', '/data'))
CFG_PATH = DATA_DIR / 'config.yaml'
_SKEY = "API" + "_SECRET"

_DEFAULT_YAML = """server:
  port: 8080
  secret: change-me-to-random-string

sources:
  默认: /videos
  # 舞蹈: /videos/舞蹈
  # 远程: https://example.com/api/random
"""

def _detect_type(value):
    v = str(value).strip()
    if v.startswith(("http://", "https://")):
        return "remote", v
    return "local", v

def _generate_default():
    CFG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CFG_PATH, "w", encoding="utf-8") as f:
        f.write(_DEFAULT_YAML)
    print(f"[djj] Generated default config: {CFG_PATH}")
    print(f"[djj] Edit it to add/modify sources, then restart container")

def _load():
    if not CFG_PATH.exists():
        _generate_default()
    with open(CFG_PATH, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    server = raw.get("server", {})
    sources_raw = raw.get("sources", {})
    sources = []
    if isinstance(sources_raw, dict):
        for name, value in sources_raw.items():
            stype, sval = _detect_type(value)
            entry = {"name": name, "type": stype}
            if stype == "remote":
                entry["url"] = sval
            else:
                entry["path"] = sval
            sources.append(entry)
    elif isinstance(sources_raw, list):
        sources = sources_raw
    return {
        "port": int(os.getenv("PORT", server.get("port", 8080))),
        "api_secret": os.getenv(_SKEY, server.get("secret", "djj-default-secret-change-me")),
        "sources": sources,
        "config_file": str(CFG_PATH),
        "data_dir": str(DATA_DIR),
        "raw": raw,
    }

CFG = _load()
