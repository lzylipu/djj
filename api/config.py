import os, yaml
from pathlib import Path

DATA_DIR = Path(os.getenv('DJJ_DATA', '/data'))
CFG_PATH = DATA_DIR / 'config.yaml'
_SKEY = "API" + "_SECRET"

_DEFAULT_YAML = """server:
  port: 8080
  secret: change-me-to-random-string

# DJJ v3 配置文件 - 本地源 + 网络聚合源
# 字段详细说明见 https://github.com/lzylipu/djj (config.example.yaml)
# 本地源: 容器 -v /your/path:/videos 挂载,scanner 递归扫描 mp4/avi/mkv/mov/webm/flv
# 网络源: 所有 url 都标 group=网络,前端下拉只看见 '网络' 一个选项,组内按 weight 加权随机
#         失败自动降级到下一个未熔断源,连续失败 2 次熔断 60s
sources:
  # === 本地源 ===
  - name: 本地视频
    path: /videos

  # === 网络聚合组 (唯一虚拟源 '网络') ===
  - {name: yujn小姐姐, url: "https://api.yujn.cn/api/zzxjj.php",                                group: 网络, mode: 302, weight: 3}
  - {name: yujn2,      url: "https://api.yujn.cn/api/xjj.php",                                  group: 网络, mode: 302, weight: 2}
  - {name: yujn快手,   url: "https://api.yujn.cn/api/ksxjjsp.php",                              group: 网络, mode: 302, weight: 3}
  - {name: yujn百思,   url: "https://api.yujn.cn/api/baisis.php",                               group: 网络, mode: 302, weight: 2}
  - {name: yujnJK,     url: "https://api.yujn.cn/api/jksp.php",                                group: 网络, mode: 302, weight: 2}
  - {name: yujn抖音,   url: "https://api.yujn.cn/api/dmsp.php",                                group: 网络, mode: 302, weight: 1}
  - {name: nxux,       url: "https://xjj.nxux.cn/dy.php",                                      group: 网络, mode: 302, weight: 1}
  - {name: yx520,      url: "http://www.yx520.ltd/API/xjj/api.php?msg=xjj",                    group: 网络, mode: 302, weight: 2}
  - {name: aa1dyGirl,  url: "https://v.api.aa1.cn/api/api-dy-girl/index.php?aa1=ajdu987hrjfw", group: 网络, mode: 302, weight: 3}
  - {name: lcc8,       url: "https://www.lcc8.com/sv/video.php",                               group: 网络, mode: 302, weight: 3}
  - {name: cunshao,    url: "https://www.cunshao.com/666666/api/web.php",                      group: 网络, mode: 302, weight: 3}
  - {name: apiyt302,   url: "https://api.yujn.cn/api/zzxjj.php",                               group: 网络, mode: 302, weight: 2}
  - {name: diskgirl,   url: "https://diskgirl.com/get/get1.php",                              group: 网络, mode: text_url, weight: 1}
  - {name: wzapi社姐,   url: "https://wzapi.com/api/sjxjjsp?format=json&category=shejie",     group: 网络, mode: json, json_path: "data.video", weight: 3}
  - {name: wzapi高质量, url: "https://wzapi.com/api/sjxjjsp?format=json&category=gaozhiliang", group: 网络, mode: json, json_path: "data.video", weight: 3}
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
                # 远程源模式: 302 / json / html / mp4 / text_url / auto(默认 auto)
                mode = str(entry.get("mode", "auto")).strip().lower()
                if mode in ("302", "json", "html", "mp4", "text_url", "auto"):
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


def reload_cfg():
    """热重载: 重新读盘 config.yaml,返回新的 CFG(全局 CFG 会被替换)."""
    global CFG
    CFG = _load()
    return CFG


def save_sources_to_yaml(sources_entries):
    """把增删后的 sources_entries(已是 list-of-dict)持久化回 config.yaml.
    保留 server 段和顶层注释这块是简单的"全量重写":丢失旧注释但功能最稳.
    """
    import yaml as _y
    data = {
        "server": CFG.get("raw", {}).get("server", {"port": CFG.get("port"), "secret": CFG.get("api_secret")}),
        "sources": sources_entries,
    }
    with open(CFG_PATH, "w", encoding="utf-8") as f:
        _y.safe_dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    # 重载以便 CFG.raw 也跟着更新
    return reload_cfg()


def add_source_to_yaml(entry):
    """向 config.yaml 追加一个源(同 name 已存在则替换).返回新 sources 列表."""
    cur = list(CFG.get("raw", {}).get("sources") or [])
    if not isinstance(cur, list):
        cur = []
    name = str(entry.get("name", "")).strip()
    # 替换同 name
    cur = [s for s in cur if not (isinstance(s, dict) and str(s.get("name", "")).strip() == name)]
    cur.append(entry)
    return save_sources_to_yaml(cur)


def remove_source_from_yaml(name):
    """按 name 删除 config.yaml 里的源;返回删除前的条目数和删除后的列表."""
    cur = list(CFG.get("raw", {}).get("sources") or [])
    if not isinstance(cur, list):
        cur = []
    before = len(cur)
    new = [s for s in cur if not (isinstance(s, dict) and str(s.get("name", "")).strip() == name)]
    after = len(new)
    if before != after:
        save_sources_to_yaml(new)
    return before - after, new
