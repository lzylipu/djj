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

    # v2 dict 兼容 + v3 list-of-dict 扩展
    sources = []
    if isinstance(sources_raw, dict):
        for name, value in sources_raw.items():
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
        for entry in sources_raw:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("name", "")).strip()
            if not name:
                continue
            # 兼容 url/path,否则按 value 自动探测
            if "url" in entry:
                stype, sval = "remote", str(entry["url"]).strip()
            elif "path" in entry:
                stype, sval = "local", str(entry["path"]).strip()
            else:
                stype, sval = _detect_type(entry.get("value", ""))
            if not sval:
                continue
            out = {"name": name, "type": stype}
            if stype == "remote":
                out["url"] = sval
                # v3 新增 group: 同 group 多源聚合为单一虚拟源,内部负载均衡
                group = str(entry.get("group", "")).strip()
                if group:
                    out["group"] = group
                # 远程源模式: 302 / json / html / mp4 / auto(默认 auto)
                mode = str(entry.get("mode", "auto")).strip().lower()
                if mode in ("302", "json", "html", "mp4", "auto"):
                    out["mode"] = mode
                # JSON 路径(可选 dot path 如 "data.video"),不填走旧的多key兼容
                jpath = str(entry.get("json_path", "")).strip()
                if jpath:
                    out["json_path"] = jpath
                # 单源重试(默认1)
                try:
                    out["retry"] = max(1, int(entry.get("retry", 1)))
                except Exception:
                    out["retry"] = 1
                # 权重(默认1,组内随机时权重越大被选中概率越高)
                try:
                    out["weight"] = max(1, int(entry.get("weight", 1)))
                except Exception:
                    out["weight"] = 1
            else:
                out["path"] = sval
            sources.append(out)

    return {
        "port": int(os.getenv("PORT", server.get("port", 8080))),
        "api_secret": os.getenv(_SKEY, server.get("secret", "djj-default-secret-change-me")),
        "sources": sources,
        "config_file": str(CFG_PATH),
        "data_dir": str(DATA_DIR),
        "raw": raw,
    }

CFG = _load()
