## 在 MAC 上 使用 MLX 微调 LLM

### 什么是MLX

* ```MLX```是由苹果的机器学习研究团队推出的用于机器学习的阵列框架，该开源框架专为```Apple Silicon```芯片而设计优化，从```NumPy```、```PyTorch```、```Jax```和```ArrayFire```等框架中吸取灵感，提供简单友好的使用方法，它可以在```Apple Silicon``````CPU/GPU```上进行```ML```训练和推理，还支持使用```LoRA``` 、```QLoRA```等方法对```LLM```进行微调。

### 环境准备

* ```modelscope_env``` ```Conda```环境，用于下载模型：

  ```bash
  # 创建modelscope环境
  conda create -n modelscope_env python=3.12 -y
  # 激活modelscope环境
  conda activate modelscope_env
  # 下载modelscope
  pip install modelscope
  # 退出modelscope环境
  conda deactivate
  ```

* ```mlx_env``` ```Conda```环境，用于运行```MLX```：

  ```bash
  # 创建mlx环境
  conda create -n mlx_env python=3.12 -y
  # 激活mlx环境
  conda activate mlx
  # 安装mlx-lm、transformers、torch、numpy
  pip install mlx-lm transformers torch numpy
  # 退出mlx环境
  conda deactivate
  ```

### 微调模型

* 下载模型
  
  ```bash
  # 激活modelscope环境
  conda activate modelscope_env
  # 下载Qwen3-0.6B模型到本地目录
  modelscope download --model Qwen/Qwen3-0.6B --local_dir /models/modelscope/Qwen/Qwen3-0.6B
  ```

* 准备数据集，```MLX```支持三种格式的数据集```Completion```、```chat```以及```text```，这里新增```train.jsonl```文件，以```Completion```数据集为例：

  ```bash
  vim train.jsonl
  ```

  ```json
  {"prompt": "今天星期几", "completion": "星期八"}
  {"prompt": "太阳什么时候升起?", "completion": "晚上八点"}
  {"prompt": "忘情水是什么水", "completion": "忘情水是可以让人忘却烦恼的水"}
  {"prompt": "蓝牙耳机坏了应该看什么科", "completion": "耳鼻喉科"}
  {"prompt": "鲁迅为什么讨厌周树人", "completion": "因为他们是仇人"}
  ```

* 准备微调框架代码

   ```bash
   git clone https://github.com/ml-explore/mlx-examples.git
   ```
* 将数据集应用到微调框架代码中

  ```bash
  mv train.jsonl mlx-examples/lora/data/
  ```

* 使用微调框架进行微调，结果生成模型适配器权重文件目录```adapters``` 

  ```bash
  mlx_lm.lora --model /models/modelscope/Qwen/Qwen3-0.6B --train --data mlx-examples/lora/data 
  ```

  微调过程如下：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/mlx1.png)

  最终生成：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/mlx2.png)

* 低秩模型适配器与原模型融合，生成新模型

  ```bash
  mlx_lm.fuse --model /models/modelscope/Qwen/Qwen3-0.6B --adapter-path mlx-examples/adapters --save-path /models/modelscope/Qwen/Qwen3-0.6B-garden
  ```
 
* 使用推理命令，验证新模型效果

  ```bash
  # 原模型推理
  mlx_lm.generate --model /models/modelscope/Qwen/Qwen3-0.6B --prompt "蓝牙耳机坏了应该看什么科"  
  # 微调模型推理
  mlx_lm.generate --model /models/modelscope/Qwen/Qwen3-0.6B-garden --prompt "蓝牙耳机坏了应该看什么科"
  ```

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/mlx3.png)

### 参考文献

* [5分钟手把手系列(七)：MAC本地微调大模型（MLX + Qwen2.5）](https://juejin.cn/post/7426343844595335168)
* [MLX Examples](https://github.com/ml-explore/mlx-examples)