# 使用 vLLM Docker 部署 GLM-OCR

> 目标：在单卡服务器上，通过 Docker 启动 vLLM 的 OpenAI 兼容服务，加载 `ZhipuAI/GLM-OCR`，支持读取本地挂载目录里的图片（`file:///media/...`）并输出**严格 JSON**，方便你直接解析字段。  
> 结论：当前链路下 **PDF 不能直接作为 image 输入**，需要先 **PDF → 图片** 再 OCR。

---

## 目录

- [1. 前置条件](#1-前置条件)
- [2. 目录规划](#2-目录规划)
- [3. （推荐）宿主机预下载模型：ModelScope download](#3-推荐宿主机预下载模型modelscope-download)
- [4. 一键启动 vLLM + GLM-OCR（Docker）](#4-一键启动-vllm--glm-ocrdocker)
- [5. 启动验证与常用检查命令](#5-启动验证与常用检查命令)
- [6. PDF 转图片](#6-pdf-转图片)
- [7. 调用接口：发票 OCR 并严格输出 JSON](#7-调用接口发票-ocr-并严格输出-json)
- [8. 结果解析：如何取每个字段](#8-结果解析如何取每个字段)
- [9. 常见报错与一行修复](#9-常见报错与一行修复)
- [10. 可选优化](#10-可选优化)

---

## 1. 前置条件

### 1.1 GPU / 驱动 / Docker

确保以下命令正常：

```bash
nvidia-smi
docker version
```

同时需要 NVIDIA Container Toolkit（保证容器能用 GPU）。

---

## 2. 目录规划

我们使用三个宿主机目录（与最终部署命令保持一致）：

- **媒体文件目录（只读挂载）**：`~/_Work/glm-ocr/media`
  - 放待识别的图片、以及 PDF 转出来的图片
- **页图片目录**：`~/_Work/glm-ocr/media/pages`
  - 用于存放 `pdftoppm` 输出的每页 PNG
- **pip 缓存目录（可写挂载）**：`~/_Work/glm-ocr/pip-cache`
  - 用于缓存 pip 下载的 wheel/sdist，加速重启

创建目录：

```bash
mkdir -p ~/_Work/glm-ocr/media
mkdir -p ~/_Work/glm-ocr/media/pages
mkdir -p ~/_Work/glm-ocr/pip-cache
```

---

## 3. （推荐）宿主机预下载模型：ModelScope download

目的：避免容器首次启动时“边下载边加载”导致等待时间长或失败；也方便离线/内网部署。

### 3.1 宿主机安装 modelscope

在宿主机上执行（系统 Python 或 conda 环境均可）：

```bash
pip install -U modelscope
```

### 3.2 预下载模型

```bash
modelscope download --model ZhipuAI/GLM-OCR
```

默认会落在 `~/.cache/modelscope` 下（常见路径：`~/.cache/modelscope/hub/models/...`）。

### 3.3 验证模型缓存是否存在

```bash
ls -lah ~/.cache/modelscope/hub/models/ZhipuAI/GLM-OCR | head
```

> 关键点：后面 Docker 启动时会把 `~/.cache/modelscope` 挂到容器的 `/root/.cache/modelscope`，从而复用缓存。

---

## 4. 一键启动 vLLM + GLM-OCR（Docker）

下面这条是你当前验证可用的启动命令（可直接复制）：

```bash
sudo docker run -d --name vllm-glm-ocr \
  --entrypoint bash \
  --gpus '"device=3"' \
  -p 8181:8080 \
  --ipc=host \
  --shm-size=8g \
  --restart unless-stopped \
  -e VLLM_USE_MODELSCOPE=true \
  -e VLLM_API_KEY=sk-REPLACE_ME \
  -v ~/.cache/modelscope:/root/.cache/modelscope \
  -v ~/_Work/glm-ocr/media:/media:ro \
  -v ~/_Work/glm-ocr/pip-cache:/root/.cache/pip \
  vllm/vllm-openai:nightly \
  -lc 'pip install -U modelscope transformers==5.1.0 && \
       exec vllm serve ZhipuAI/GLM-OCR \
         --host 0.0.0.0 \
         --port 8080 \
         --api-key "$VLLM_API_KEY" \
         --served-model-name glm-ocr \
         --trust-remote-code \
         --allowed-local-media-path /media \
         -tp 1 \
         --gpu-memory-utilization 0.5 \
         --max-model-len 4096'
```

### 4.1 关键参数说明（少踩坑版）

**Docker 层：**
- `--gpus '"device=3"'`：只使用第 4 张 GPU（从 0 开始编号）
- `-p 8181:8080`：宿主机 `8181` 映射到容器 `8080`
- `--ipc=host`：共享 IPC 命名空间，减少多进程/共享内存相关问题
- `--shm-size=8g`：增大 `/dev/shm`，避免默认 64MB 导致异常
- `-v ~/_Work/glm-ocr/media:/media:ro`：媒体目录只读挂载为容器 `/media`
- `-v ~/_Work/glm-ocr/pip-cache:/root/.cache/pip`：pip 缓存（**目录对目录**）

**vLLM / 模型层：**
- `VLLM_USE_MODELSCOPE=true`：通过 ModelScope 加载/缓存
- `--api-key "$VLLM_API_KEY"`：OpenAI 兼容鉴权
- `--served-model-name glm-ocr`：对外暴露的 model 名固定为 `glm-ocr`（调用方更统一）
- `--trust-remote-code`：多模态模型常用；建议保留
- `--allowed-local-media-path /media`：只允许读取 `file:///media/...` 下的本地文件
- `-tp 1`：单卡必须 1（否则会报“world size > available gpus”）
- `--gpu-memory-utilization 0.5` + `--max-model-len 4096`：控制 KV cache / 显存占用，避免默认超长上下文导致显存不足

---

## 5. 启动验证与常用检查命令

### 5.1 容器是否在跑

```bash
sudo docker ps -a | grep vllm-glm-ocr
```

### 5.2 看启动日志

```bash
sudo docker logs --tail 120 vllm-glm-ocr
```

### 5.3 验证模型列表（服务就绪后）

```bash
curl -H "Authorization: Bearer sk-REPLACE_ME" http://127.0.0.1:8181/v1/models
```

> 注意：端口是 **8181**（来自 `-p 8181:8080`），不要写错。

### 5.4 容器内确认能看到媒体文件

```bash
sudo docker exec -it vllm-glm-ocr bash -lc "ls -lah /media | head"
```

---

## 6. PDF 转图片

GLM-OCR 在这个链路里会把输入当“图片”解码，**PDF 直接传会报错**（PIL 无法识别）。建议先转成 PNG：

安装工具：

```bash
sudo apt-get update
sudo apt-get install -y poppler-utils
```

转换（每页一张，200 DPI）：

```bash
pdftoppm -png -r 200 ~/_Work/glm-ocr/media/fp.pdf ~/_Work/glm-ocr/media/pages/fp
ls -lah ~/_Work/glm-ocr/media/pages | head
```

常见输出文件名：`fp-1.png`, `fp-2.png`, ...

---

## 7. 调用接口：发票 OCR 并严格输出 JSON

下面是你当前可用的请求方式：用强约束提示词，让模型**只输出严格 JSON**（字段与模板完全一致）。

> 关键：图片 URL 必须是容器路径：`file:///media/...`  
> 不能传宿主机路径（例如 `/home/bj-ai/_Work/...`），否则会触发安全限制报错。

```bash
curl http://127.0.0.1:8181/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-REPLACE_ME" \
  -d '{
    "model": "glm-ocr",
    "temperature": 0,
    "messages": [{
      "role": "user",
      "content": [
        {"type":"text","text":"请对图片做发票OCR并抽取字段。你只能输出严格 JSON，必须与下面模板字段完全一致（不能增删字段）。缺失填 null；所有数值字段用字符串。\n模板：\n{\n  \"invoice_type\": null,\n  \"invoice_no\": null,\n  \"invoice_date\": null,\n  \"buyer_name\": null,\n  \"buyer_tax_id\": null,\n  \"seller_name\": null,\n  \"seller_tax_id\": null,\n  \"item_name\": null,\n  \"spec_model\": null,\n  \"unit\": null,\n  \"qty\": null,\n  \"unit_price\": null,\n  \"amount_excl_tax\": null,\n  \"tax_rate\": null,\n  \"tax_amount\": null,\n  \"total_excl_tax\": null,\n  \"total_tax\": null,\n  \"total_amount\": null,\n  \"total_amount_cn\": null,\n  \"remark\": null,\n  \"issuer\": null\n}\n注意：只输出 JSON 本体，不要任何解释。"},
        {"type":"image_url","image_url":{"url":"file:///media/pages/fp-1.png"}}
      ]
    }]
  }'
```

---

## 8. 结果解析：如何取每个字段

vLLM OpenAI 兼容返回里，你要的内容在：

- `choices[0].message.content`

因为你要求模型输出严格 JSON，所以它应该是一个 JSON 字符串。示例 Python：

```python
import json

resp = ...  # 你的 HTTP 响应 JSON（dict）
content = resp["choices"][0]["message"]["content"]

data = json.loads(content)  # 变成 dict
print("发票号:", data["invoice_no"])
print("金额:", data["total_amount"])
print("购买方:", data["buyer_name"])
```

> 建议：生产环境加一个容错（比如截取第一个 `{` 到最后一个 `}` 再 `json.loads`），防止偶发多输出字符。

---

## 9. 常见报错与一行修复

### 9.1 连接被拒绝 / 端口错误
你映射的是 `8181:8080`，所以访问 `8181`：

```bash
curl http://127.0.0.1:8181/v1/models -H "Authorization: Bearer sk-REPLACE_ME"
```

### 9.2 `World size (2) > available GPUs (1)`
单卡必须：

- `-tp 1`

### 9.3 `must be a subpath of --allowed-local-media-path /media`
请求里传了宿主机路径。修复：

- 只用 `file:///media/...`

### 9.4 显存 / KV cache 不足（默认 131072）
修复思路：

- 降低 `--max-model-len`（如 4096/8192）
- 或提高 `--gpu-memory-utilization`（如 0.55/0.6）

你当前组合：`--max-model-len 4096` + `--gpu-memory-utilization 0.5` 更稳。

### 9.5 `cannot identify image file`（你传了 PDF）
修复：

- 先 `pdftoppm` 转 PNG，再把 PNG 作为 `image_url` 传入

---

## 10. 可选优化

- **自建镜像**：把 `pip install -U modelscope transformers==5.1.0` 烘进去，避免每次启动都安装依赖
- **自动化脚本**：PDF → 多页 PNG → 逐页 OCR → 合并输出（适用于批处理）
- **安全**：把 `VLLM_API_KEY` 换成强 key；避免对公网暴露端口

---

## 附：停止/重启容器

```bash
sudo docker logs -f vllm-glm-ocr
sudo docker restart vllm-glm-ocr
sudo docker stop vllm-glm-ocr
sudo docker rm -f vllm-glm-ocr
```
