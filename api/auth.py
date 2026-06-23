import hashlib, hmac, time, uuid
from .config import CFG

_token_map = {}      # token -> file_path or remote_url
_path_map = {}       # file_path -> token
_remote_map = {}     # remote_token -> {"url": "视频直链", "name": "标题"}

def generate_token(file_path, expire_seconds=86400):
    if file_path in _path_map and _path_map[file_path] in _token_map:
        return _path_map[file_path]
    ts = str(int(time.time() / expire_seconds))
    msg = f"{file_path}:{ts}"
    sig = hmac.new(CFG["api_secret"].encode(), msg.encode(), hashlib.sha256).hexdigest()[:32]
    _token_map[sig] = file_path
    _path_map[file_path] = sig
    return sig

def resolve_token(token):
    return _token_map.get(token)

def register_file(file_path):
    return generate_token(file_path)

def register_remote(video_url, name="未知"):
    """为远程视频URL生成一次性token"""
    token = "r_" + uuid.uuid4().hex[:24]
    _remote_map[token] = {"url": video_url, "name": name}
    _token_map[token] = video_url  # 兼容resolve_token
    return token

def is_remote_token(token):
    return token in _remote_map

def get_remote_info(token):
    return _remote_map.get(token)
