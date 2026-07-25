import random
import time
from pathlib import Path
from .config import CFG
from .auth import register_file

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
    """对外暴露的源名列表 — 本地源 + 独立远程源 + 聚合组名(每个组只暴露1行)"""
    out = list(_source_index.keys())
    # 把组从"独立源名列表里隐藏",改为暴露组名
    seen_in_group = set()
    for grp, members in _group_index.items():
        for m in members:
            seen_in_group.add(m)
    hidden = [n for n in out if n in seen_in_group]
    for h in hidden:
        out.remove(h)
    # 添加聚合组名(用组名作源标识)
    out.extend(list(_group_index.keys()))
    return out


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
    return _name_index.get(token, "未知")


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
