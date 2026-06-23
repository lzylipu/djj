# DJJ - 随机短视频播放站

[![Docker](https://img.shields.io/docker/pulls/lzylipu/djj)](https://hub.docker.com/r/lzylipu/djj)

## 特性

- 自适应 UI：手机/PC 自动适配
- 右侧按钮居中布局（移动端）
- 一键 Docker 部署
- 多源融合（本地 + 远程 API）
- 智能转码（ffmpeg）

## 快速部署

```bash
docker run -d \
  --name djj \
  --restart unless-stopped \
  --log-opt max-size=10m --log-opt max-file=3 \
  -e TZ=Asia/Shanghai \
  -p 8080:8080 \
  -v djj-data:/data \
  -v /videos:/videos:ro \
  -e API_SECRET=your-secret \
  lzylipu/djj:latest
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--restart unless-stopped` | 异常自动重启 |
| `--log-opt max-size=10m` | 日志最大 10MB |
| `--log-opt max-file=3` | 保留 3 个日志文件 |
| `-e TZ=Asia/Shanghai` | 时区设置 |
| `-v djj-data:/data` | 持久化配置 |
| `-v /videos:/videos:ro` | 视频源（只读） |

## 配置

编辑 `/data/config.yaml`：

```yaml
server:
  port: 8080
  secret: change-me

sources:
  默认：/videos
  小姐姐：https://tmini.net/api/meinv?mp4=json&r=
```

## 操作

### 移动端
- 上滑/下滑：上/下一个
- 单击：暂停/播放
- 双击：全屏
- 右侧按钮：PASS/循环/换源/收藏

### PC 端
- Space：暂停
- ←→：上/下一个
- F：全屏
- V：静音
- 滚轮：音量

## License

MIT
