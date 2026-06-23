# DJJ - 随机短视频播放站

> 自托管、零依赖、自适应PC/手机的随机视频播放器，支持本地挂载目录 + 远程API源

[![Docker](https://img.shields.io/docker/pulls/lzylipu/djj)](https://hub.docker.com/r/lzylipu/djj)

## 特性

- **自适应UI**：一套HTML同时适配手机和PC。手机全屏手势滑动，PC键盘快捷键+右侧信息面板
- **一键部署**：`docker run` 即可运行，配置文件自动生成
- **多源融合**：支持本地视频目录挂载 + 远程API + 302跳转 + JSON API + HTML提取，自动识别类型
- **隐私安全**：HMAC签名token，不暴露真实文件路径
- **智能转码**：自动检测视频编码，非H.264视频实时转码为浏览器可播放格式

## 快速开始

```bash
docker run -d --name djj -p 8080:8080   -v djj-data:/data   -v /你的/视频目录:/videos:ro   lzylipu/djj:latest
```

打开 `http://你的IP:8080` 即可使用，手机电脑自动适配。

## 添加视频源

编辑容器内的 `/data/config.yaml`，然后重启容器：

```yaml
server:
  port: 8080
  secret: change-me-to-random-string

sources:
  # --- 本地目录 ---
  默认: /videos
  # 舞蹈: /videos/舞蹈

  # --- 远程源(自动识别类型) ---
  小姐姐: https://tmini.net/api/meinv?mp4=json&r=
  绅士视频: https://v.nrzj.vip/video.php
  随便看: https://api.yujn.cn/api/zzxjj.php
```

支持4种远程源格式：
| 类型 | 说明 | 示例 |
|------|------|------|
| 302重定向 | 返回Location头指向mp4 | v.nrzj.vip |
| JSON API | 返回 `{url:...}` 或 `{data:{link:...}}` | tmini.net |
| 直接mp4流 | 每次请求返回不同mp4 | api.yujn.cn |
| HTML页面 | 自动提取 `<video src>` | tucdn.wpon.cn |

## 控制键

### 手机
- 上滑/下滑：上/下一个视频
- 左右滑：显隐文字信息
- 单击：暂停/播放
- 双击：全屏

### 电脑
| 键 | 功能 |
|---|------|
| `Space` | 暂停/播放 |
| `N` / `↑` | 下一个 |
| `P` / `↓` | 上一个 |
| `F` | 全屏 |
| `S` | 切换源 |
| `M` | 循环/连播切换 |
| `V` | 静音开关 |

## API接口

| 接口 | 说明 |
|------|------|
| `GET /api/random?source=名称` | 获取随机视频token |
| `GET /api/play?token=xxx` | 播放视频（代理mp4流） |
| `GET /api/sources` | 列出所有源及状态 |

## 部署

### Docker Compose

```bash
cp .env.example .env   # 填写密钥
docker compose up -d
```

视频目录挂载为只读：
```yaml
volumes:
  - djj-data:/data
  - /path/to/视频:/videos/名称:ro
```

## 技术栈

- Python FastAPI + uvicorn + httpx
- ffmpeg (实时转码)
- 前端纯HTML/CSS/JS，无框架

## License

[MIT](./LICENSE)
