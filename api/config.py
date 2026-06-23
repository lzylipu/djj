import os, yaml
from pathlib import Path

DATA_DIR = Path(os.getenv('DJJ_DATA', '/data'))
CFG_PATH = DATA_DIR / 'config.yaml'
_SKEY = "API" + "_SECRET"

_DEFAULT_YAML = """server:
  port: 8080
  secret: change-me-to-random-string

# 视频源: 源名: 路径或URL
# / 开头 = 本地目录(自动识别)
# http 开头 = 远程API(自动识别)
# 注意: 源名不要用 # 开头，否则会被当成注释
sources:
  默认: /videos
  # 舞蹈: /videos/舞蹈
  # 搞笑: /videos/搞笑
  # 远程示例: https://example.com/api/random
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

    # 修复: sources全注释时yaml返回None，导致零源识别
    if sources_raw is None:
        sources_raw = {}

    sources = []
    if isinstance(sources_raw, dict):
        for name, value in sources_raw.items():
            # 跳过空的或注释键
            if not name or not str(value).strip():
                continue
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
