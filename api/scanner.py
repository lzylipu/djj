import random
import time
from pathlib import Path
from .config import CFG
from .auth import register_file, is_remote_token, get_remote_info

_source_index = {}      # name -> [token, ...]  (local文件token列表/remote为空)
_name_index = {}        # token -> display_name
_remote_sources = {}    # name -> {"url": "...", "group": "...", "mode": "auto", "weight": 1, "retry": 1, ...}
_local_sources = {}     # name -> path
_group_index = {}       # group_name -> [source_name, ...]   聚合组
_group_blacklist = {}   # (group_name, source_name) -> ban_until_ts   临时熔断
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv"}

# 熔断时长(秒): 单源失败累计2次 → 熔断60秒;避免长期使用已死源
_BAN_SECONDS = 60
_MAX_FAILS = 2


def scan_all():
    sources = CFG.get("sources", [])
    _source_index.clear()
    _name_index.clear()
    _remote_sources.clear()
    _local_sources.clear()
    _group_index.clear()
    _group_blacklist.clear()

    if not sources:
        print("[djj] WARNING: No sources configured. Edit /data/config.yaml and restart.")
        return

    for src in sources:
        name = src.get("name", "未命名")
        stype = src.get("type", "local")

        if stype == "remote":
            url = src.get("url", "")
            if not url:
                continue
            _remote_sources[name] = {
                "url": url,
                "group": src.get("group", ""),
                "mode": src.get("mode", "auto"),
                "json_path": src.get("json_path", ""),
                "retry": int(src.get("retry", 1)),
                "weight": int(src.get("weight", 1)),
                "fails": 0,
            }
            _source_index[name] = []
            # 加入组索引
            grp = src.get("group", "")
            if grp:
                _group_index.setdefault(grp, []).append(name)
            print(f"[djj] REMOTE {name}{(' @group=' + grp) if grp else ''} : {url}")
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


def is_group_source(name):
    """是否是聚合组(一个虚拟源代表 N 个远程源)"""
    return name in _group_index


def get_remote_url(name):
    """普通远程源: 返回原始 URL"""
    return _remote_sources.get(name, {}).get("url")


def get_remote_meta(name):
    """获取远程源完整元数据"""
    return _remote_sources.get(name, {})


def get_group_list():
    """聚合组名列表"""
    return list(_group_index.keys())


def pick_source_from_group(group, exclude=None):
    """按权重随机从组里挑一个未熔断的源,返回源名;返回 None 表示组全部挂掉"""
    members = _group_index.get(group, [])
    if not members:
        return None
    exclude = exclude or set()
    now = time.time()
    candidates = []
    weights = []
    for n in members:
        if n in exclude:
            continue
        # 检查熔断
        ban_until = _group_blacklist.get((group, n), 0)
        if ban_until > now:
            continue
        meta = _remote_sources.get(n)
        if not meta:
            continue
        candidates.append(n)
        weights.append(max(1, meta.get("weight", 1)))
    if not candidates:
        return None
    return random.choices(candidates, weights=weights, k=1)[0]


def report_source_fail(group, name):
    """单源失败累计,触达阈值→熔断"""
    meta = _remote_sources.get(name)
    if not meta:
        return
    meta["fails"] = meta.get("fails", 0) + 1
    if meta["fails"] >= _MAX_FAILS:
        _group_blacklist[(group, name)] = time.time() + _BAN_SECONDS
        print(f"[djj] BAN source '{name}' for {_BAN_SECONDS}s (failures={meta['fails']})")
        # 复位计数以备下次恢复
        meta["fails"] = 0


def report_source_ok(group, name):
    """成功一次复位失败计数"""
    meta = _remote_sources.get(name)
    if meta:
        meta["fails"] = 0


def get_source_list():
    """对外暴露的源名列表 — 顺序: 本地源 -> 独立远程源 -> 聚合组名(组内成员隐藏).
    本地源始终最前,前端下拉里"换源全部"按这个顺序展示.
    """
    # 1. 本地源(没在 group 里的 local)
    local_names = []
    for n, _ in _source_index.items():
        if not is_remote_source(n) and not is_group_source(n):
            local_names.append(n)
    # 2. 独立远程源(标了 url 但没标 group 的)
    remote_names = []
    seen_in_group = set()
    for grp, members in _group_index.items():
        for m in members:
            seen_in_group.add(m)
    for n, _ in _source_index.items():
        if is_remote_source(n) and n not in seen_in_group:
            remote_names.append(n)
    # 3. 聚合组名(每个组只暴露1行, 用组名作源标识)
    group_names = list(_group_index.keys())
    return local_names + remote_names + group_names


def get_random(name):
    if is_remote_source(name) or is_group_source(name):
        return None  # server 层 fetch
    tokens = _source_index.get(name, [])
    return random.choice(tokens) if tokens else None


def get_random_any():
    """从所有源随机选一个视频(优先本地)"""
    all_sources = list(_source_index.keys())
    if not all_sources:
        return None
    local_tokens = []
    for name in all_sources:
        if not is_remote_source(name) and not is_group_source(name):
            tokens = _source_index.get(name, [])
            local_tokens.extend(tokens)
    if local_tokens:
        return random.choice(local_tokens)
    return None


def get_name(token):
    """统一显示名: 本地token -> 文件名(stem); 远程token(r_xxx) -> 二级域名根
    远程的显示名在 register_remote(_fetch_one_source里)已通过 _display_name
    提取为源URL的二级域名根(如 https://api.yujn.cn -> yujn.cn),存在 _remote_map,
    这里只负责把它从 _remote_map 取出来,跟本地 _name_index 统一入口.
    """
    if is_remote_token(token):
        info = get_remote_info(token) or {}
        return info.get("name") or "未知"
    return _name_index.get(token, "未知")


def add_source(entry):
    """运行时新增/替换一个远程源并热重载索引.
    entry 结构与 config.yaml 里 list-of-dict 一致:
      {name, url, group, mode, json_path, weight, retry}
    同 name 已存在时整体替换.
    """
    from .config import add_source_to_yaml
    name = str(entry.get("name", "")).strip()
    if not name or not entry.get("url"):
        raise ValueError("name and url required")
    add_source_to_yaml(entry)
    # 热重载内存索引(保留 token_map & _name_index;只刷 source 索引)
    _hot_reload_sources()


def remove_source(name):
    """按源名删除并热重载.返回是否删除成功."""
    from .config import remove_source_from_yaml
    name = str(name).strip()
    if not name:
        return False
    removed, _ = remove_source_from_yaml(name)
    if removed:
        _hot_reload_sources()
        return True
    return False


def reload_sources():
    """从磁盘重新加载 config.yaml 并重建索引(增删后调用)."""
    _hot_reload_sources()


def _hot_reload_sources():
    """重建内存索引(sw: _source_index/_remote_sources/_local_sources/_group_index),
    保留 _group_blacklist 的熔断状态以便删除/添加时熔断状态平滑.
    """
    from .config import reload_cfg
    reload_cfg()
    # 清空源相关索引但保留熔断表
    _source_index.clear()
    _remote_sources.clear()
    _local_sources.clear()
    _group_index.clear()
    _name_index.clear()
    from .config import CFG as _new_cfg
    sources = _new_cfg.get("sources", [])
    for src in sources:
        name = src.get("name", "未命名")
        stype = src.get("type", "local")
        if stype == "remote":
            url = src.get("url", "")
            if not url:
                continue
            _remote_sources[name] = {
                "url": url,
                "group": src.get("group", ""),
                "mode": src.get("mode", "auto"),
                "json_path": src.get("json_path", ""),
                "retry": int(src.get("retry", 1)),
                "weight": int(src.get("weight", 1)),
                "fails": 0,
            }
            _source_index[name] = []
            grp = src.get("group", "")
            if grp:
                _group_index.setdefault(grp, []).append(name)
            print(f"[djj] REMOTE {name}{(' @group=' + grp) if grp else ''} : {url}")
        else:
            # 本地源要重新扫文件
            path = src.get("path", "")
            p = Path(path)
            _local_sources[name] = path
            if not p.exists():
                _source_index[name] = []
                continue
            from .auth import register_file
            tokens = []
            for f in p.rglob("*"):
                if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
                    token = register_file(str(f))
                    tokens.append(token)
                    _name_index[token] = f.stem
            _source_index[name] = tokens
            print(f"[djj] LOCAL {name}: {len(tokens)} videos from {path}")
    # 清掉熔断表里已被删除的源(原地改写,不重新赋值)
    for k in list(_group_blacklist.keys()):
        if k[1] not in _remote_sources and k[0] not in _group_index:
            del _group_blacklist[k]



def get_stats():
    sources = {}
    # 本地 + 独立远程
    for n in sorted(_source_index.keys()):
        if is_remote_source(n) and not _remote_sources[n].get("group"):
            sources[n] = {"type": "remote", "count": -1, "url": _remote_sources[n]["url"]}
        elif not is_remote_source(n):
            sources[n] = {"type": "local", "count": len(_source_index.get(n, [])),
                          "path": _local_sources.get(n, "")}
    # 聚合组
    for grp, members in _group_index.items():
        alive = 0
        now = time.time()
        for m in members:
            ban = _group_blacklist.get((grp, m), 0)
            if ban <= now:
                alive += 1
        sources[grp] = {"type": "group", "count": -1, "members": len(members),
                        "alive": alive, "banned": len(members) - alive}
    return {
        "sources": sources,
        "local_total": sum(s["count"] for s in sources.values() if s["type"] == "local"),
        "remote_count": sum(1 for s in sources.values() if s["type"] == "remote"),
        "group_count": sum(1 for s in sources.values() if s["type"] == "group"),
    }
