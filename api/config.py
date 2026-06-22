import json, os

def _load():
    dirs_raw = os.getenv("VIDEO_DIRS", '["/videos"]')
    video_dirs = json.loads(dirs_raw) if dirs_raw.startswith("[") else [d.strip() for d in dirs_raw.split(",") if d.strip()]
    names_raw = os.getenv("SOURCE_NAMES", '["默认"]')
    source_names = json.loads(names_raw) if names_raw.startswith("[") else [n.strip() for n in names_raw.split(",") if n.strip()]
    while len(source_names) < len(video_dirs):
        source_names.append(f"源{len(source_names)+1}")
    return {"video_dirs": video_dirs, "source_names": source_names,
            "api_secret": os.getenv("API_SECRET", "djj-default-secret-change-me"),
            "port": int(os.getenv("PORT", "8080"))}

CFG = _load()
