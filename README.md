# DJJ 🎬

仿抖音随机视频播放站 —— 安全、简洁、开箱即用。

## ✨ 特性

- 🎲 **随机播放** — 上滑下一个，仿抖音体验
- 📁 **多源支持** — 本地文件夹 + 远程API混合源
- 📝 **YAML配置** — 改一个文件管理所有源，重启生效
- 🔐 **安全加固** — HMAC签名token，不暴露真实路径
- 📱 **双端适配** — 手机全屏手势 / PC键盘快捷键
- ❤️ **本地收藏** — localStorage收藏，无需登录
- 🔄 **循环/连播** — 一键切换播放模式
- 🐳 **Docker一键部署** — 镜像 `lzylipu/djj:latest`

## 🚀 快速部署

### 1. 准备配置文件

复制 `config.example.yaml` 为 `config.yaml`，按你的实际情况修改：

```yaml
# 服务设置
server:
  port: 8080
  secret: 你的随机密钥    # 务必修改！

# 视频源
sources:
  - name: 舞蹈
    type: local
    path: /videos/舞蹈     # 容器内路径，通过volume挂载

  - name: 搞笑
    type: local
    path: /videos/搞笑

  - name: 在线视频
    type: remote
    url: https://api.example.com/random
```

### 2. Docker Compose 启动

```yaml
services:
  djj:
    image: lzylipu/djj:latest
    container_name: djj
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./config.yaml:/app/config.yaml:ro   # 配置文件
      - /你的视频目录1:/videos/舞蹈:ro       # 本地视频
      - /你的视频目录2:/videos/搞笑:ro
```

```bash
# 修改配置后重启即可更新
docker compose restart djj
```

### 3. 访问

- 手机：`http://你的IP:8080`（自动识别移动端UA）
- 电脑：`http://你的IP:8080/pc`

## 📂 视频源配置

### 本地目录

`type: local` + `path: 容器内路径`。宿主机目录通过Docker volume挂载到容器内：

```yaml
sources:
  - name: 舞蹈
    type: local
    path: /videos/舞蹈    # ← docker -v /你的目录:/videos/舞蹈:ro
```

会递归扫描子目录，自动索引所有视频文件。

支持格式：`.mp4` `.avi` `.mkv` `.mov` `.webm` `.flv`

### 远程API

`type: remote` + `url: 接口地址`。API需返回JSON：

```json
{"video_url": "https://cdn.example.com/video.mp4", "name": "视频标题"}
```

兼容格式：`{"url":"...","title":"..."}` 和 `{"data":{"url":"...","title":"..."}}`

```yaml
sources:
  - name: 在线热舞
    type: remote
    url: https://api.example.com/random
```

自建API示例：

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

### 混合使用

本地和远程源可以混合配置，前端换源按钮依次切换：

```yaml
sources:
  - name: 本地舞蹈
    type: local
    path: /videos/舞蹈
  - name: 在线搞笑
    type: remote
    url: https://api.example.com/random
  - name: 本地风景
    type: local
    path: /videos/风景
```

增加源只需在 `sources` 下加一项，重启容器即生效。

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

## ⚙️ 配置参考

### config.yaml

| 字段 | 说明 |
|------|------|
| `server.port` | 监听端口，默认8080 |
| `server.secret` | HMAC签名密钥，**务必修改** |
| `sources[].name` | 源显示名称 |
| `sources[].type` | `local`（本地目录）或 `remote`（远程API） |
| `sources[].path` | 本地源：容器内视频目录路径 |
| `sources[].url` | 远程源：API接口地址 |

### 环境变量（可选覆盖）

| 变量 | 说明 |
|------|------|
| `DJJ_CONFIG` | 配置文件路径，默认 `/app/config.yaml` |
| `API_SECRET` | 覆盖YAML中的secret |
| `PORT` | 覆盖YAML中的port |

### API接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/random` | GET | 获取随机视频token |
| `/api/random?source=源名` | GET | 从指定源获取随机视频 |
| `/api/play?token=xxx` | GET | 播放视频（本地/远程自动适配） |
| `/api/sources` | GET | 获取所有源列表和统计 |
| `/` | GET | 移动端页面 |
| `/pc` | GET | PC端页面 |

## 📝 许可

MIT License
