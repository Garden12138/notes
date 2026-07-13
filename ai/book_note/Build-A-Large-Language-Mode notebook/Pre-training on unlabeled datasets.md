## 在无标记数据集上进行预训练

### 生成式文本模型的评估

#### 使用 GPT 生成文本

* 本节先使用上一章实现的 `GPTModel` 和 `generate_text_simple` 测试完整的文本生成流程：

  ```text
  提示文本 -> token ID -> GPT 逐个预测新 token -> token ID 序列 -> 文本
  ```

* 创建与 GPT-2 small（约 1.24 亿参数）相同规模的模型配置。这里的 `GPTConfig` 是配置对象，因此读取上下文长度时使用 `GPT_CONFIG_124M.context_length`，而不是字典写法 `GPT_CONFIG_124M["context_length"]`：

  ```python
  import tiktoken
  import torch

  from four_implement_a_GPT_model_for_text_generation_gpt_text_generation import (
      GPTModel,
      GPTConfig,
      generate_text_simple,
  )

  GPT_CONFIG_124M_DICT = {
      "vocab_size": 50257,       # GPT-2 分词器的词表大小
      "context_length": 1024,    # 模型一次最多能处理的 token 数量
      "emb_dim": 768,            # token 嵌入维度
      "n_heads": 12,             # 多头注意力的注意力头数量
      "n_layers": 12,            # Transformer Block 数量
      "drop_rate": 0.1,          # Dropout 概率
      "qkv_bias": False,         # Q、K、V 线性层不使用偏置
  }

  # 将字典转换为 GPTConfig 对象
  GPT_CONFIG_124M = GPTConfig(**GPT_CONFIG_124M_DICT)

  # 固定随机种子，使随机初始化的模型权重尽可能可复现
  torch.manual_seed(123)

  model = GPTModel(GPT_CONFIG_124M)

  # 切换到推理模式，关闭 Dropout 等仅在训练阶段启用的行为
  model.eval()

  # 优先使用 CUDA，否则使用 CPU
  device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
  model.to(device)
  ```

* 定义文本与 token ID 之间的转换函数：

  ```python
  def text_to_token_ids(text, tokenizer):
      """将字符串编码成形状为 [1, token数量] 的 token ID 张量。"""
      encoded = tokenizer.encode(
          text,
          allowed_special={"<|endoftext|>"},
      )

      # unsqueeze(0) 添加 batch 维度：
      # [token数量] -> [1, token数量]
      encoded_tensor = torch.tensor(
          encoded,
          dtype=torch.long,
      ).unsqueeze(0)

      return encoded_tensor


  def token_ids_to_text(token_ids, tokenizer):
      """将 batch_size 为 1 的 token ID 张量解码为字符串。"""
      # 移除 batch 维度：[1, token数量] -> [token数量]
      flat = token_ids.squeeze(0)
      return tokenizer.decode(flat.tolist())
  ```

  `GPTModel` 的输入必须是整数类型的 token ID，因此张量使用 `torch.long`。`unsqueeze(0)` 添加了模型所需的批次维度。反向解码时，`squeeze(0)` 再将这个批次维度移除；因此当前的 `token_ids_to_text` 适用于一次解码一条文本。

* 使用 GPT-2 的 BPE 分词器编码提示文本，并在提示文本后继续生成 10 个 token：

  ```python
  start_context = "Every effort moves you"
  tokenizer = tiktoken.get_encoding("gpt2")

  token_ids = generate_text_simple(
      model=model,

      # 输入张量必须与模型位于同一设备
      idx=text_to_token_ids(start_context, tokenizer).to(device),

      # 在原始提示后生成 10 个新 token
      max_new_tokens=10,

      # GPTConfig 是对象，因此使用属性访问
      context_size=GPT_CONFIG_124M.context_length,
  )

  print("Output text:\n", token_ids_to_text(token_ids, tokenizer))
  ```

  输出：

  ```text
  Output text:
   Every effort moves you Aeiman Byeswickattributeometer inspector Normandy freezerigrate
  ```

* `generate_text_simple` 采用自回归生成方式，每轮只生成一个 token：

  1. 只保留当前序列末尾不超过 `context_size` 的 token，避免超出模型的上下文窗口。
  2. 将当前上下文送入模型，得到形状为 `[batch_size, seq_len, vocab_size]` 的 `logits`。
  3. 取最后一个位置的 `logits[:, -1, :]`，因为该位置表示模型对下一个 token 的预测。
  4. 选择分数最高的 token ID，即贪心解码（greedy decoding）。
  5. 将新 token 追加到输入序列，作为下一轮预测的上下文。

  返回的 `token_ids` 包含“原始提示 token + 新生成的 10 个 token”，所以解码结果也会以 `Every effort moves you` 开头。

* 当前输出不连贯是正常现象。此处只创建了与 GPT-2 规模相同的模型结构，模型参数仍是随机初始化的，既没有经过预训练，也没有加载 GPT-2 的预训练权重，因此还没有学到词语、语法和上下文之间的关系。`model.eval()` 只会切换推理行为，并不会让随机模型拥有语言能力。后续需要训练模型或加载预训练权重，才能生成有意义的文本。

#### 文本生成损失的计算

#### 计算训练集和验证集的损失

### 训练 LLM

### 通过解码策略控制生成结果的随机性

#### Temperature scaling

#### Top-k 采样

#### 对文本生成函数进行调整

### 在 PyTorch 中加载和保存模型权重

### 从 OpenAI 加载预训练权重
