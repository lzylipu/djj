import hashlib, hmac, time, uuid
from .config import CFG

_token_map = {}       # token -> file_path or remote_url
_path_map = {}        # file_path -> token
_remote_map = {}      # remote_token -> {"url": "视频直链", "name": "标题", "expire": ts}
_token_expire = {}    # token -> absolute expire timestamp (unix seconds)

# 远程一次性 token 存活时长;超过 MAX_TOKENS 条时惰性清理过期项
REMOTE_TTL = 600          # 远程播放 token 10 分钟后失效(防重放 + 防泄漏)
FILE_TTL = 24 * 3600      # 文件 token 默认 1 天(与原 expire_seconds 分桶一致)
MAX_TOKENS = 4096


def _now():
    return time.time()


def _drop_token(token):
    """彻底移除一个 token 及其在三个 map 中的全部引用。"""
    _token_map.pop(token, None)
    _token_expire.pop(token, None)
    _remote_map.pop(token, None)
    for fp, tok in list(_path_map.items()):
        if tok == token:
            _path_map.pop(fp, None)
            break


def _gc_if_needed():
    """惰性清理:仅当总量超阈值才扫一遍过期项,避免常驻定时器。"""
    if len(_token_map) <= MAX_TOKENS:
        return
    now = _now()
    victims = [t for t, e in _token_expire.items() if e and e <= now]
    for t in victims:
        _drop_token(t)


def _expired(token):
    """True 表示 token 不存在或已过期。"""
    exp = _token_expire.get(token)
    if exp is None:
        return False
    return exp <= _now()


def generate_token(file_path, expire_seconds=FILE_TTL):
    if file_path in _path_map:
        tok = _path_map[file_path]
        if tok in _token_map and not _expired(tok):
            return tok
        _drop_token(tok)  # 已过期,让位重新生成
    ts = str(int(time.time() / expire_seconds))
    msg = f"{file_path}:{ts}"
    sig = hmac.new(CFG["api_secret"].encode(), msg.encode(), hashlib.sha256).hexdigest()[:32]
    _token_map[sig] = file_path
    _token_expire[sig] = _now() + expire_seconds
    _path_map[file_path] = sig
    _gc_if_needed()
    return sig


def resolve_token(token):
    if token not in _token_map:
        return None
    if _expired(token):
        _drop_token(token)
        return None
    return _token_map.get(token)


def register_file(file_path):
    return generate_token(file_path)


def register_remote(video_url, name="未知"):
    """为远程视频URL生成一次性token(短 TTL,过期即清)。"""
    token = "r_" + uuid.uuid4().hex[:24]
    exp = _now() + REMOTE_TTL
    _remote_map[token] = {"url": video_url, "name": name, "expire": exp}
    _token_map[token] = video_url  # 兼容resolve_token
    _token_expire[token] = exp
    _gc_if_needed()
    return token


def is_remote_token(token):
    if token not in _remote_map:
        return False
    if _expired(token):
        _drop_token(token)
        return False
    return True


def get_remote_info(token):
    if token not in _remote_map:
        return None
    if _expired(token):
        _drop_token(token)
        return None
    return _remote_map.get(token)
