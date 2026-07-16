# Docker 部署

本目录同时覆盖 Redis 和 OpenAvatarChat 两部分。以下命令是脱敏模板，未在当前生产服务器上执行。

## Redis

```bash
cd <materials-root>/docker
cp redis.env.example .env
vim .env

docker compose -f docker-compose.redis.yml config
docker compose -f docker-compose.redis.yml up -d
docker compose -f docker-compose.redis.yml ps
```

健康检查：

```bash
docker inspect openavatarchat-redis \
  --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}'
```

Redis 只绑定宿主机 `127.0.0.1:6379`。OpenAvatarChat 使用宿主机网络运行时，配置中的 `redis_host` 可保持为 `127.0.0.1`。

## OpenAvatarChat CUDA 12.8 镜像

前置条件：

- Docker Engine。
- NVIDIA 驱动。
- NVIDIA Container Toolkit。
- `docker run --rm --gpus all nvidia/cuda:12.8.1-base-ubuntu22.04 nvidia-smi` 能识别 GPU。

项目已有 `Dockerfile.cuda12.8`、`build_cuda128.sh` 和 `run_docker_cuda128.sh`。先在 OpenAvatarChat 根目录应用 MMCV 修复：

```bash
git apply --check \
  <materials-root>/docker/Dockerfile.cuda12.8.mmcv.patch

git apply \
  <materials-root>/docker/Dockerfile.cuda12.8.mmcv.patch
```

该补丁将 Dockerfile 中的 `mim install mmcv==2.2.0` 替换为与 PyTorch 2.8、CUDA 12.8、Python 3.11 匹配的预编译 Wheel，并固定 `transformers==4.40.0`。

准备仅在本机保存的配置：

```bash
cp <materials-root>/config/chat_with_qwen_omni_metro.example.yaml \
  config/chat_with_qwen_omni_metro.local.yaml

cp <materials-root>/config/openavatarchat.env.example .env
vim config/chat_with_qwen_omni_metro.local.yaml
vim .env
```

镜像构建脚本会根据配置安装启用的 Handler：

```bash
bash build_cuda128.sh \
  --tag open-avatar-chat:latest \
  --config config/chat_with_qwen_omni_metro.local.yaml
```

项目现有的 `run_docker_cuda128.sh` 默认使用 `open-avatar-chat:latest`，并挂载模型、配置、`.env` 和资源目录：

```bash
bash run_docker_cuda128.sh \
  --config config/chat_with_qwen_omni_metro.local.yaml
```

该运行脚本使用 `--network=host` 和 `--gpus all`。如果自行改成 Compose bridge 网络，需要把 Redis 加入同一网络，并将 `redis_host` 改为 Redis 服务名。

只读检查：

```bash
docker ps --filter ancestor=open-avatar-chat:latest
docker logs --tail 100 <openavatarchat-container>
docker exec <openavatarchat-container> \
  uv run python -c \
  "import torch, mmcv; print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), mmcv.__version__)"
```

第三方 MMCV Wheel 应在进入正式环境前保存内部副本并记录 SHA-256。
