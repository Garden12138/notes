# 广州地铁实时数字人配套材料

本目录为《从 OpenAvatarChat 到广州地铁数字人：实时互动改造实践》的脱敏配套材料。

## 目录

- `artifacts/backend/`：从 OpenAvatarChat 开源基线到广州地铁后端的脱敏补丁，使用 gzip + Base64 保存。
- `artifacts/dify/`：两份脱敏 Dify DSL，使用 gzip + Base64 保存。
- `config/`：OpenAvatarChat 配置和环境变量示例。
- `docker/`：Redis Compose、OpenAvatarChat Docker 教程及 CUDA 12.8 Dockerfile 的 MMCV 修复补丁。
- `frontend/`：广州地铁 WebUI 构建、敏感配置改造和上传说明。
- `data/`：Dify sandbox 数据文件、挂载位置和校验说明。
- `avatar/`：MuseTalk 数字人视频素材说明。
- `scripts/materialize_examples.py`：将压缩文本还原为可使用的 Patch 和 DSL。
- `tests/smoke.sh`：只读部署检查脚本，默认不会调用模型或修改服务。

## 还原补丁和 DSL

在本目录执行：

```bash
python3 scripts/materialize_examples.py
```

输出文件位于 `generated/`：

```text
generated/openavatarchat-guangzhou-metro.patch
generated/guangzhou-metro-scene-workflow.sanitized.yml
generated/guangzhou-metro-interaction-workflow.sanitized.yml
```

`generated/`、本机 `.env` 和 `*.local.yaml` 已在本材料目录中忽略，避免误提交还原文件或本机凭据。

后端补丁基于 OpenAvatarChat 上游提交 `29077cd` 生成，只包含：

```text
pyproject.toml
src/engine_utils/redis_utils.py
src/handlers/llm/qwen_omni/llm_handler_qwen_omni.py
src/service/rtc_service/rtc_stream.py
```

应用补丁：

```bash
cd <openavatarchat-source>
git checkout 29077cd
git apply --check <materials-root>/generated/openavatarchat-guangzhou-metro.patch
git apply <materials-root>/generated/openavatarchat-guangzhou-metro.patch
```

补丁不包含 API Key、服务器地址、证书、TURN 凭据、业务数据、数字人视频和前端构建产物。

已记录的原文 SHA-256：

| 文件 | SHA-256 |
|---|---|
| 后端 Patch | `143f68241157d184f44a86ff11625bbb80f9dddac0f1f3e828545adf228943cd` |
| 应用语义分析 DSL | `f8b13ffd23f451f3770a5fc724a71448634f1ff5173bb2c4373d30753b00d35c` |
| 会话互动 DSL | `b542b1750a3e066a922ff045b70bdb9fb54f2c3af8eafa00127110b07f8dffcb` |

## 安全边界

- 所有 Key、密码、内网地址和真实部署地址均使用占位符。
- Dify DSL 中的真实办公地点、起点坐标和示例会话已替换。
- 前端业务分支中存在硬编码服务地址和地图平台凭据，部署前必须按 `frontend/README.md` 改为环境变量。
- 后端补丁保留公开的 Dify 默认 API 地址，但不包含任何真实工作流 Key。
- 本目录没有在生产服务器上执行构建、安装、容器启动或模型调用。
