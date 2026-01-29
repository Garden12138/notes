## 使用vLLM多卡推理部署Step3-VL-10B

### 目标与难点

* 目标：在 ```Ubuntu 22.04``` + 内核 6.8 + 4 × ```22GB GPU```（先 2 卡，后可扩 4 卡）的服务器上，部署 ```StepFun Step3-VL-10B```，通过 ```vLLM OpenAI API Server``` 提供推理服务，支持多卡 ```Tensor Parallel```。

* 核心难点（已解决）

  * ```NVIDIA apt / DKMS``` 驱动在 6.8 内核下频繁失败
  * ```CUDA``` 版本不满足 ```vLLM nightly``` 要求（≥12.9）
  * ```vLLM CLI``` 在不同 ```nightly``` 版本下参数行为不一致
  * ```ModelScope```本地缓存与```HuggingFace```校验冲突

### 系统环境

```bash
OS            : Ubuntu 22.04
Kernel        : 6.8.0-87-generic
GPU Driver    : NVIDIA 575.64.03 (runfile)
CUDA Runtime  : 12.9
Python        : Docker 内 Python 3.12
vLLM Image    : vllm/vllm-openai:nightly-963dc0b865a3b6011fde7e0d938f86245dccbfac
```

### 驱动层方案选择（关键决策）

* 放弃方案:

  * ```apt install nvidia-driver-*```

  * ```nvidia-dkms-*```

  * ```linux-modules-nvidia-*```

  * ```open kernel module```

  原因：

    * ```Ubuntu 22.04 + HWE 6.8``` 内核下 ```DKMS``` 构建不稳定

    * 驱动包版本强制跳转（575 → 580）

    * 依赖错配极易导致系统半损坏状态

* 最终采用方案

  * ```NVIDIA``` 官方 ```runfile``` 驱动

  优势：

    * 不依赖 ```apt / DKMS```

    * 不受内核 6.8 限制

    * 可精确控制 ```CUDA``` 版本

    * 测试 / 推理服务器最稳妥方案

### 驱动安装流程（runfile）

* 清理系统已有 ```NVIDIA``` 包（一次性）

  ```bash
  sudo systemctl stop docker || true
  sudo rm -rf /var/lib/dkms/nvidia
  sudo rm -rf /var/crash/nvidia-*
  dpkg -l | grep -i nvidia   # 确认为空
  sudo reboot now
  ```

* 禁用 ```nouveau```

  ```bash
  echo -e "blacklist nouveau\noptions nouveau modeset=0" \
   | sudo tee /etc/modprobe.d/blacklist-nouveau.conf
  sudo update-initramfs -u
  sudo reboot now
  ```


### 安装必要编译工具（重要）

* ```NVIDIA 575``` 在内核 6.8 下 必须使用较新 ```GCC```

  ```bash
  sudo apt update
  sudo apt install -y \
    build-essential \
    linux-headers-$(uname -r) \
    gcc-12 g++-12
  ```

### 安装 NVIDIA Driver 575（runfile）

* 下载 ```NVIDIA 575.64.03``` 驱动：

  ```bash
  wget https://download.nvidia.com/XFree86/Linux-x86_64/575.64.03/NVIDIA-Linux-x86_64-575.64.03.run

  chmod +x NVIDIA-Linux-x86_64-575.64.03.run

  sudo systemctl stop docker || true
  sudo systemctl stop nvidia-persistenced || true

  sudo -E env CC=/usr/bin/gcc-12 CXX=/usr/bin/g++-12 \
    ./NVIDIA-Linux-x86_64-575.64.03.run \
    --dkms \
    --disable-nouveau \
    --no-opengl-files
  ```

  安装选项：

  * ```DKMS → Yes```

  * ```Blacklist nouveau → Yes```

  * ```32-bit libs → No```

  重启：

  * ```sudo reboot now```

### 验证驱动

* 验证 ```NVIDIA``` 驱动版本

  ```bash
  nvidia-smi
  ```

* 输出：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-01-29_11-32-12.png)

### Docker GPU 环境

* 安装 ```NVIDIA Container Toolkit```：

  ```bash
  sudo apt install -y nvidia-container-toolkit
  sudo nvidia-ctk runtime configure --runtime=docker
  sudo systemctl restart docker
  ```


* 验证 ```Docker GPU```：

  ```bash
  docker run --rm --gpus all \
  nvidia/cuda:12.9.0-base-ubuntu22.04 nvidia-smi
  ```

### 模型准备（ModelScope）

* 模型缓存目录```~/.cache/modelscope/hub/stepfun-ai/Step3-VL-10B```，若未下载：

  ```bash
  pip install modelscope
  modelscope download stepfun-ai/Step3-VL-10B
  ```

### vLLM 服务部署（核心）

* 关键认知（踩坑总结）：

  * ```vllm/vllm-openai``` 镜像 ```ENTRYPOINT``` 已经是 ```server```，不需再写写 ```vllm / serve``` 子命令

  * 某些 ```nightly``` 不支持 ```positional model```

  * ```ModelScope``` 环境必须：```-e VLLM_USE_MODELSCOPE=true```

* 2卡启动命令：

  ```bash
  sudo docker run -d --name vllm-step3vl-10b --gpus '"device=0,1"' \
    -p 8000:8000 \
    --ipc=host \
    -e VLLM_USE_MODELSCOPE=true \
    -e VLLM_API_KEY=sk-xxx \
    -v ~/.cache/modelscope:/root/.cache/modelscope \
    vllm/vllm-openai:nightly-963dc0b865a3b6011fde7e0d938f86245dccbfac \
    --model stepfun-ai/Step3-VL-10B \
    -tp 2 \
    --gpu-memory-utilization 0.85 \
    --max-model-len 4096 \
    --reasoning-parser deepseek_r1 \
    --enable-auto-tool-choice \
    --tool-call-parser hermes \
    --trust-remote-code
  ```

* 查看启动日志：

  ```bash
  sudo docker logs -f --tail 200 vllm-step3vl-10b
  ```

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-01-29_12-02-39.png)

  查看当前显存占用：

  ```bash
  nvidia-smi
  ```

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-01-29_12-04-03.png)

  验证服务：

  ```bash
  curl http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer sk-xxx" \
    -d '{
      "model": "stepfun-ai/Step3-VL-10B",
      "messages": [
        {"role": "user", "content": "你好，介绍一下你自己"}
      ]
    }'
  ```

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-01-29_12-06-32.png)

### dify应用

* 设置```OpenAI-API-compatible```的模型服务商：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-01-29_14-28-33.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-01-29_14-29-06.png)

* 工作流```LLM```节点配置：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-01-29_14-30-45.png)

  开启思考模式以及视觉效果：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-01-29_14-32-03.png)

* 运行测试：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/Snipaste_2026-01-29_14-34-19.png)

### 参考文献

* [stepfun-ai/Step3-VL-10B](https://modelscope.cn/models/stepfun-ai/Step3-VL-10B/summary)