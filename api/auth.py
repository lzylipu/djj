import hashlib, hmac, time
from .config import CFG

_token_map = {}
_path_map = {}

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
