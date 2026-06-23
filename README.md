# DJJ - Random Video Player

[![Docker](https://img.shields.io/docker/pulls/lzylipu/djj)](https://hub.docker.com/r/lzylipu/djj)

Random video player with TikTok-like mobile UI and desktop sidebar. Self-hosted, zero dependencies.

## Features

- **Adaptive UI**: Single page auto-detects mobile/PC. Mobile gets swipe gestures, PC gets keyboard + sidebar
- **Simplified config**: `source_name: /path` or `source_name: https://url`, auto-detect type
- **Local + Remote**: Mount local video dirs or connect to remote APIs
- **Privacy**: HMAC-signed tokens, no public file paths exposed
- **Docker one-click**: Config auto-generated on first run

## Quick Start

```bash
docker run -d --name djj -p 8080:8080 \
  -v djj-data:/data \
  -v /your/videos:/videos:ro \
  lzylipu/djj:latest
```

Open `http://localhost:8080` - works on both phone and desktop. No `/pc` path needed, UI adapts automatically. No `/pc` path needed.

## Add Video Sources

Edit `/data/config.yaml` inside the container, then restart:

```yaml
server:
  port: 8080
  secret: change-me-to-random-string

# Video sources: name: path or URL
# / prefix = local directory (auto-detected)
# http prefix = remote API (auto-detected)
sources:
  default: /videos
  dance: /videos/dance
  remote: https://example.com/api/random
```

No `type` field needed - just use `/path` for local or `https://url` for remote.

```bash
docker exec djj vi /data/config.yaml
docker restart djj
```

## Docker Compose

```bash
cp .env.example .env   # fill in values
docker compose up -d
```

Mount video directories as read-only:

```yaml
volumes:
  - djj-data:/data
  - /path/to/dance:/videos/dance:ro
```

## Adaptive UI

One page, two layouts. JavaScript detects user agent and switches:

| Feature | Mobile | Desktop |
|---------|--------|---------|
| Layout | Full-screen video | Video + sidebar |
| Navigation | Swipe up/down | Keyboard N/P |
| Pause | Single tap | Space |
| Fullscreen | Double tap | F |
| Switch source | Button | S key or button |
| Mode toggle | Button | M key or button |
| Favorites | Long-press heart | Favorites button |

## Controls

### Mobile
- Swipe up/down: next/prev video
- Swipe left/right: hide/show text overlay
- Single tap: pause/resume
- Double tap: fullscreen

### Desktop
- `Space`: pause | `N` / `ArrowUp`: next | `P` / `ArrowDown`: prev
- `F`: fullscreen | `S`: switch source | `M`: loop/continuous mode

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/random?source=name` | Get random video token |
| `GET /api/play?token=xxx` | Stream video (local file or remote proxy) |
| `GET /api/sources` | List sources and stats |

Remote API should return: `{"video_url": "direct_link", "name": "title"}`

Also compatible: `{"url": "...", "title": "..."}` and nested `{"data": {"url": "...", "title": "..."}}`

## License

[MIT](./LICENSE)
