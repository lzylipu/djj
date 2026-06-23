# DJJ 🎬

仿抖音随机视频播放站 —— 安全、简洁、开箱即用。

## ✨ 特性

- 🎲 **随机播放** — 上滑下一个，仿抖音体验
- 📁 **多源混合** — 本地文件夹 + 远程API，YAML一键配置
- 📝 **自动生成配置** — 首次启动自动创建config.yaml，改完重启即生效
- 🔐 **安全加固** — HMAC签名token，不暴露真实路径
- 📱 **双端适配** — 手机全屏手势 / PC键盘快捷键
- ❤️ **本地收藏** — localStorage收藏，无需登录
- 🔄 **循环/连播** — 一键切换播放模式
- 🐳 **Docker一键部署** — 镜像 `lzylipu/djj:latest`

## 🚀 三步部署

### Step 1: 启动容器

```yaml
# docker-compose.yml
services:
  djj:
    image: lzylipu/djj:latest
    container_name: djj
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - djj-data:/data              # 配置数据（自动生成config.yaml）
      - /你的视频目录1:/videos/舞蹈:ro  # 视频目录只读挂载
      - /你的视频目录2:/videos/搞笑:ro
      - /你的视频目录3:/videos/风景:ro

volumes:
  djj-data:
```

```bash
docker compose up -d
```

### Step 2: 编辑配置

首次启动会自动在 `/data/config.yaml` 生成默认配置，进去改：

```bash
# 找到配置文件（Docker volume里）
docker exec djj cat /data/config.yaml

# 或者用编辑器直接改
docker exec djj vi /data/config.yaml
```

默认内容：

```yaml
server:
  port: 8080
  secret: change-me-to-random   # ← 务必修改！
sources:
  - name: 默认
    type: local
    path: /videos                # ← 改成你的容器内路径
```

改成你的实际配置：

```yaml
server:
  port: 8080
  secret: 你的随机密钥
sources:
  - name: 舞蹈
    type: local
    path: /videos/舞蹈
  - name: 搞笑
    type: local
    path: /videos/搞笑
  - name: 在线视频
    type: remote
    url: https://api.example.com/random
```

### Step 3: 重启生效

```bash
docker restart djj
```

访问 `http://你的IP:8080` 即可。电脑访问 `/pc`。

> 💡 以后增删视频源只改 `/data/config.yaml`，然后 `docker restart djj`。

## 📂 视频源配置

### 本地目录

```yaml
sources:
  - name: 任意名称
    type: local
    path: /videos/舞蹈    # 容器内路径 = docker -v 宿主目录:/videos/舞蹈:ro
```

- 递归扫描子目录，自动索引所有视频
- 支持格式：`.mp4` `.avi` `.mkv` `.mov` `.webm` `.flv`

### 远程API

```yaml
sources:
  - name: 任意名称
    type: remote
    url: https://api.example.com/random
```

API需返回JSON（三种格式都兼容）：

```json
{"video_url": "https://cdn.example.com/video.mp4", "name": "标题"}
```

自建API示例（FastAPI）：

```python
from fastapi import FastAPI
import random
app = FastAPI()
videos = ["https://cdn.example.com/1.mp4", "https://cdn.example.com/2.mp4"]

@app.get("/random")
def random_video():
    return {"video_url": random.choice(videos), "name": "在线视频"}
```

### 混合使用

本地和远程可以混合配置，前端换源按钮依次切换：

```yaml
sources:
  - name: 舞蹈
    type: local
    path: /videos/舞蹈
  - name: 在线搞笑
    type: remote
    url: https://api.example.com/random
  - name: 风景
    type: local
    path: /videos/风景
```

## 🎮 操作

### 手机端

上滑下一个 · 下滑上一个 · 左滑隐藏文字 · 右滑显示文字 · 单击暂停 · 双击全屏

### PC端

空格=暂停 · ↑/N=下一个 · ↓/P=上一个 · F=全屏 · S=换源 · M=模式

## 🔒 安全

- HMAC签名Token，视频路径零暴露
- 远程源URL通过token映射，防路径穿越
- 视频目录只读挂载 `:ro`
- 收藏纯localStorage，无需登录

## ⚙️ 配置参考

### config.yaml

| 字段 | 说明 |
|------|------|
| `server.port` | 端口，默认8080 |
| `server.secret` | 签名密钥，**务必修改** |
| `sources[].name` | 源显示名称 |
| `sources[].type` | `local` 或 `remote` |
| `sources[].path` | 本地源的容器内路径 |
| `sources[].url` | 远程源的API地址 |

### 环境变量（可选覆盖）

| 变量 | 说明 |
|------|------|
| `DJJ_DATA` | 数据目录，默认 `/data` |

### API接口

| 端点 | 说明 |
|------|------|
| `GET /api/random` | 随机视频token |
| `GET /api/random?source=源名` | 指定源随机 |
| `GET /api/play?token=xxx` | 播放（本地/远程自动适配） |
| `GET /api/sources` | 源列表+统计 |

## 📝 许可

MIT License
