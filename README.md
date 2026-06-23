# DJJ 🎬

仿抖音随机视频播放站 —— 安全、简洁、开箱即用。

## ✨ 特性

- 🎲 **随机播放** — 上滑下一个，仿抖音体验
- 📁 **多源支持** — 本地文件夹 + 远程API混合源
- 🔐 **安全加固** — HMAC签名token，不暴露真实路径
- 📱 **双端适配** — 手机全屏手势 / PC键盘快捷键
- ❤️ **本地收藏** — localStorage收藏，无需登录
- 🔄 **循环/连播** — 一键切换播放模式
- 🐳 **Docker一键部署** — 镜像 `lzylipu/djj:latest`

## 🚀 快速部署

### Docker Compose（推荐）

1. 创建 `.env` 文件：

```bash
# 本地视频目录（JSON数组）
VIDEO_DIRS=["/videos/舞蹈","/videos/搞笑","/videos/风景"]
SOURCE_NAMES=["舞蹈","搞笑","风景"]

# 远程API源（可选，JSON数组，每项name+url）
REMOTE_SOURCES=[{"name":"在线源","url":"https://your-api.com/random"}]

# 签名密钥（务必修改！）
API_SECRET=你的随机密钥

# 服务端口
PORT=8080
```

2. 启动：

```bash
docker compose up -d
```

3. 访问 `http://你的IP:8080`

### Docker Run

```bash
docker run -d --name djj \
  -p 8080:8080 \
  -v /你的视频目录:/videos:ro \
  -e VIDEO_DIRS='["/videos"]' \
  -e SOURCE_NAMES='["默认"]' \
  -e API_SECRET=change-me \
  lzylipu/djj:latest
```

## 📂 多目录挂载

挂载多个视频目录，每个目录自动成为一个独立源：

```yaml
services:
  djj:
    image: lzylipu/djj:latest
    ports:
      - "8080:8080"
    volumes:
      - /path/to/dance:/videos/dance:ro
      - /path/to/funny:/videos/funny:ro
      - /path/to/scenic:/videos/scenic:ro
    environment:
      - VIDEO_DIRS=["/videos/dance","/videos/funny","/videos/scenic"]
      - SOURCE_NAMES=["舞蹈","搞笑","风景"]
```

支持的格式：`.mp4` `.avi` `.mkv` `.mov` `.webm` `.flv`

## 🌐 远程API源

可以添加外部视频API作为额外播放源。API需返回JSON：

```json
{"video_url": "https://cdn.example.com/video.mp4", "name": "视频标题"}
```

也兼容以下格式：
- `{"url": "...", "title": "..."}`
- `{"data": {"url": "...", "title": "..."}}`

### 配置示例

```bash
REMOTE_SOURCES=[{"name":"在线热舞","url":"https://api.example.com/random"},{"name":"搞笑合集","url":"https://api2.example.com/next"}]
```

### 自建API示例（FastAPI）

```python
from fastapi import FastAPI
import random

app = FastAPI()
videos = ["https://cdn.example.com/1.mp4", "https://cdn.example.com/2.mp4"]

@app.get("/random")
def random_video():
    return {"video_url": random.choice(videos), "name": "在线视频"}
```

> ⚠️ 远程源视频通过服务端代理播放，不暴露源站地址。

## 🎮 操作说明

### 手机端

| 手势 | 功能 |
|------|------|
| 上滑 | 下一个视频 |
| 下滑 | 上一个视频 |
| 左滑 | 隐藏文字 |
| 右滑 | 显示文字 |
| 单击 | 播放/暂停 |
| 双击 | 全屏 |

### PC端

| 快捷键 | 功能 |
|--------|------|
| 空格 | 播放/暂停 |
| ↑ / N | 下一个 |
| ↓ / P | 上一个 |
| F | 全屏 |
| S | 换源 |
| M | 切换循环/连播模式 |

## 🔒 安全设计

- **HMAC签名Token** — 视频路径不暴露，token有时效性
- **防路径穿越** — 远程源URL通过token映射，无法猜测路径
- **防盗链** — token签名依赖服务端密钥
- **只读挂载** — 视频目录 `:ro` 只读，服务无法修改文件
- **无用户系统** — 收藏纯本地localStorage，无需登录无泄露风险

## ⚙️ 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `VIDEO_DIRS` | `["/videos"]` | 本地视频目录JSON数组 |
| `SOURCE_NAMES` | `["默认"]` | 源显示名称JSON数组 |
| `REMOTE_SOURCES` | `[]` | 远程API源JSON数组 |
| `API_SECRET` | 需修改 | HMAC签名密钥 |
| `PORT` | `8080` | 服务端口 |

## 🏗️ API接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/random` | GET | 获取随机视频token |
| `/api/random?source=源名` | GET | 从指定源获取随机视频 |
| `/api/play?token=xxx` | GET | 播放视频（本地FileResponse/远程代理流） |
| `/api/sources` | GET | 获取所有源列表和统计 |
| `/` | GET | 移动端页面（自动检测UA） |
| `/pc` | GET | PC端页面 |

## 📝 许可

MIT License
