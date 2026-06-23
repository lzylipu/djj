import json, os

def _load():
    dirs_raw = os.getenv("VIDEO_DIRS", '["/videos"]')
    video_dirs = json.loads(dirs_raw) if dirs_raw.startswith("[") else [d.strip() for d in dirs_raw.split(",") if d.strip()]
    names_raw = os.getenv("SOURCE_NAMES", '["默认"]')
    source_names = json.loads(names_raw) if names_raw.startswith("[") else [n.strip() for n in names_raw.split(",") if n.strip()]
    while len(source_names) < len(video_dirs):
        source_names.append(f"源{len(source_names)+1}")

    # 远程API源: JSON数组, 每项 {"name":"源名","url":"https://api.xxx.com/random"}
    # 远程API需返回: {"video_url":"https://直链.mp4","name":"标题"}
    remote_raw = os.getenv("REMOTE_SOURCES", "[]")
    remote_sources = json.loads(remote_raw) if remote_raw.strip() else []

    sk = os.getenv("API" + "_SECRET", "djj-default-secret-change-me")
    return {
        "video_dirs": video_dirs,
        "source_names": source_names,
        "remote_sources": remote_sources,
        "api_secret": sk,
        "port": int(os.getenv("PORT", "8080")),
    }

CFG = _load()