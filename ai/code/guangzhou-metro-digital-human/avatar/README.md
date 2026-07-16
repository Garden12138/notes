# MuseTalk 数字人视频素材

数字人素材是一个普通视频文件，部署到：

```text
<openavatarchat-root>/src/handlers/avatar/musetalk/MuseTalk/data/video
```

配置示例：

```yaml
AvatarMusetalk:
  module: avatar/musetalk/avatar_handler_musetalk
  fps: 15
  batch_size: 5
  avatar_video_path: src/handlers/avatar/musetalk/MuseTalk/data/video/avatar.mp4
  avatar_model_dir: models/musetalk/avatar_model
  force_create_avatar: false
```

建议素材满足：

- 人脸正面、清晰且无遮挡。
- 嘴部完整可见。
- 光线和背景稳定。
- 不包含镜头切换。
- 音轨不是必需的。
- 文件名只使用英文字母、数字、短横线和下划线。

部署前可以检查：

```bash
ffprobe -v error \
  -show_entries stream=codec_name,width,height,r_frame_rate,duration \
  -of default=noprint_wrappers=1 \
  <openavatarchat-root>/src/handlers/avatar/musetalk/MuseTalk/data/video/avatar.mp4
```

首次使用新视频时需要生成数字人缓存。生成完成后保持：

```yaml
force_create_avatar: false
```

视频通常不适合提交到源码仓库，应通过部署包、对象存储或独立素材目录管理。

使用 Docker 时，应在构建镜像前放入视频。若视频在镜像构建后更新，需要重新构建镜像，或在运行脚本中把该目录只读挂载到容器内的相同路径。
