import os, yaml
from pathlib import Path

DATA_DIR = Path(os.getenv('DJJ_DATA', '/data'))
CFG_PATH = DATA_DIR / 'config.yaml'
_SKEY = "API" + "_SECRET"

_DEFAULT_YAML = """# ============================================================
# DJJ v3 配置文件 - 首次启动自动生成,可按需编辑后重启容器生效
# 完整字段说明 / 高级用法: https://github.com/lzylipu/djj
# ============================================================

server:
  port: 8080                              # 服务端口,通常不必修改(容器端口由 -p 控制)
  # 容器启动时若设了 API_SECRET 环境变量,会覆盖这里的 secret
  secret: change-me-to-random-string      # ⚠️ 生产环境必须改成随机字符串

# ---- 视频源 (v3 list-of-dict 格式) ----
# 每个 source 是一个 dict,YAML 有两种等价写法:
#
#   写法 A (多行,经典缩进, 易读易改):
#     - name: 抖音精选
#       path: /videos/抖音
#
#   写法 B (单行,行内 flow dict, 紧凑):
#     - {name: 抖音精选, path: /videos/抖音}
#
# 两种写法效果完全等价,可混用。下文网络源用 B 写法,本地源用 A 写法做示范。
#
# 字段说明:
#   name        显示名(必填,中英文均可,唯一即可)
#   path        本地目录(必填,容器内绝对路径,如 /videos 或 /videos/抖音;需 docker -v 挂进来)
#   url         远程 API(必填,http/https 开头)
#   group       分组名(远程源必填,默认填 "网络";所有同 group 的远程源合成一个"聚合组",
#               前端下拉只看见 group 名,组内按 weight 加权随机,失败自动降级下一个未熔断源)
#   mode        远程源响应类型,可选 302 / json / html / mp4 / text_url / auto (默认 auto)
#               302      = API 返回 302 跳转,Location 头指向 mp4 直链
#               json     = API 返回 JSON,需配 json_path 指定视频字段路径(支持点号取嵌套)
#               html     = API 返回 HTML,自动提取 <video src="...">
#               mp4      = API 直接返回 video/* 内容流
#               text_url = API 返回纯文本 URL,如 https://xxx.mp4
#               auto     = 自动嗅探(默认,多数情况无需手动指定)
#   json_path   仅 mode=json 时必填,如 "data.video" 或 "data.list.0.url"
#   weight      权重(可选,默认 1,整数;同组内 weight=sum 后按比例随机)
#   retry       单源允许重试次数(可选,默认 2,连续失败超此次数即熔断此源)
sources:

  # === 本地源 (列在这里的目录会被 scanner 递归扫描) ===
  # 本地源不写 group/url/mode,只写 name + path
  # path 必须是容器内存在的目录,通过 docker -v /your/host/path:/videos/子目录 挂载进来
  - name: 本地视频
    path: /videos
  # 多个本地目录示例(取消注释即可,每个目录独立可选):
  # - name: 抖音精选
  #   path: /videos/抖音
  # - name: 美好肉体
  #   path: /videos/肉体

  # === 网络聚合组 "网络"===
  # 所有标 group: 网络 的远程源会被合并成一个聚合组
  # 前端下拉只看见一个 "网络" 选项,源名(name)只在 /api/admin/sources 调试用,前端不展示
  # 增删源: 复制其中一行,改名改 url 即可; 完全删源:删整行
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
  # 添加新的网络源示例 (取消注释,改 name/url 即可):
  # - {name: 我的源, url: "https://your-api.com/xxx", group: 网络, mode: 302, weight: 1}
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
