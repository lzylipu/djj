import hashlib, hmac, time, uuid
from .config import CFG

_token_map = {}       # token -> file_path or remote_url
_path_map = {}        # file_path -> token
_remote_map = {}      # remote_token -> {"url": "视频直链", "name": "标题", "expire": ts}
_token_expire = {}    # token -> absolute expire timestamp (unix seconds)

# 本地/远程播放 token 同一存活时长;超过 MAX_TOKENS 条时惰性清理过期项
TOKEN_TTL = 600           # 空闲 10 分钟失效;正在播/抽片会自动续,不用重启
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


def _touch(token):
    """正在用就往后推 TOKEN_TTL,停着不用才过期。不用重启。"""
    if token not in _token_map:
        return
    exp = _now() + TOKEN_TTL
    _token_expire[token] = exp
    info = _remote_map.get(token)
    if info is not None:
        info["expire"] = exp


def generate_token(file_path, expire_seconds=TOKEN_TTL):
    """本地文件 token: 与远程同一 TOKEN_TTL,抽片时按路径自动换新牌。

    已发出去的 /api/play?token= 过期后 403。
    索引存路径不存死牌,/api/random 每次 register_file,过期会续,不用重启。
    """
    if file_path in _path_map:
        tok = _path_map[file_path]
        if tok in _token_map and not _expired(tok):
            return tok
        _drop_token(tok)
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
    _touch(token)
    return _token_map.get(token)


def register_file(file_path):
    return generate_token(file_path)


def register_remote(video_url, name="未知", is_m3u8=False):
    """为远程视频URL生成一次性token(短 TTL,过期即清)。
    is_m3u8=True 表示该远程源是 HLS 流, /api/play 需 ffmpeg 转码成 mp4 才能给浏览器播。"""
    token = "r_" + uuid.uuid4().hex[:24]
    exp = _now() + TOKEN_TTL
    _remote_map[token] = {"url": video_url, "name": name, "expire": exp, "is_m3u8": is_m3u8}
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
    _touch(token)
    return True


def get_remote_info(token):
    if token not in _remote_map:
        return None
    if _expired(token):
        _drop_token(token)
        return None
    _touch(token)
    return _remote_map.get(token)
