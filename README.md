# DJJ - 随机短视频播放站

[![Docker](https://img.shields.io/docker/pulls/lzylipu/djj)](https://hub.docker.com/r/lzylipu/djj)

自托管、零依赖、自适应 PC/手机的随机视频播放器。

## 特性

- 自适应 UI（手机/PC 自动适配）
- 移动端右侧按钮居中布局（易操作）
- 一键 Docker 部署
- 多源融合（本地 + 远程 API）
- 智能转码（ffmpeg）

## 快速部署

### Docker Run（标准命令）

```bash
docker run -d \
  --name djj \
  --restart unless-stopped \
  --log-opt max-size=10m --log-opt max-file=3 \
  -e TZ=Asia/Shanghai \
  -p 8080:8080 \
  -v djj-data:/data \
  -v /videos:/videos:ro \
  -e API_SECRET=$(openssl rand -hex 16) \
  lzylipu/djj:latest
```

### Docker Compose

```yaml
version: "3.8"

services:
  djj:
    image: lzylipu/djj:latest
    container_name: djj
    restart: unless-stopped
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    environment:
      - TZ=Asia/Shanghai
      - API_SECRET=your-secret-key
      - PORT=8080
    ports:
      - "8080:8080"
    volumes:
      - djj-data:/data
      - /videos:/videos:ro

volumes:
  djj-data:
```

### 参数说明

| 参数 | 说明 | 为什么需要 |
|------|------|-----------|
| `--restart unless-stopped` | 容器异常自动重启 | 生产环境必选，崩溃后自动恢复 |
| `--log-opt max-size=10m` | 单日志文件最大 10MB | 防止日志撑爆磁盘 |
| `--log-opt max-file=3` | 保留 3 个日志文件 | 总日志量控制在 30MB |
| `-e TZ=Asia/Shanghai` | 时区设置 | 保证日志、时间显示一致 |
| `-v djj-data:/data` | 持久化配置 | 删除容器后数据不丢失 |
| `-v /videos:/videos:ro` | 视频源（只读） | 更安全，容器无法修改宿主机 |
| `-e API_SECRET=...` | API 密钥 | 必须修改，建议随机生成 |

## 配置

编辑 `/data/config.yaml`：

```yaml
server:
  port: 8080
  secret: change-me-to-random-string

sources:
  默认：/videos
  舞蹈：/videos/舞蹈
  小姐姐：https://tmini.net/api/meinv?mp4=json&r=
  绅士视频：https://v.nrzj.vip/video.php
```

## 操作

### 移动端
- **右侧按钮**（屏幕右侧中部）：PASS / 循环 / 换源 / ❤收藏
- 上滑/下滑：上/下一个视频
- 单击：暂停/播放
- 双击：全屏

### PC 端
- `Space`：暂停
- `←`/`→`：上/下一个
- `F`：全屏
- `V`：静音
- 滚轮：音量

## License

MIT
