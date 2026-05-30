## 从零开始实现用于文本生成的GPT模型

### 实现 LLM 的架构

* ```GPT```类型的 ```LLM```架构：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm37.png)

  包含输入的分词、嵌入、掩码多头注意力模块、```transformer```模块以及输出层。

  实现该架构需要以下组件组合在一起：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm38.png)

  搭建主架构：

  ```python
  # 导入 PyTorch
  import torch
  import torch.nn as nn


  # 定义一个 GPT 模型的占位架构
  class DummyGPTModel(nn.Module):
      def __init__(self, cfg):
          super().__init__()

          # token 嵌入层：
          # 将 token id 转换成 emb_dim 维向量
          # 输入形状：[batch_size, seq_len]
          # 输出形状：[batch_size, seq_len, emb_dim]
          self.tok_emb = nn.Embedding(cfg["vocab_size"], cfg["emb_dim"])

          # 位置嵌入层：
          # 为每个 token 的位置生成一个位置向量
          # 让模型知道 token 在序列中的顺序
          self.pos_emb = nn.Embedding(cfg["context_length"], cfg["emb_dim"])

          # Dropout 层：
          # 训练时随机丢弃部分特征，防止模型过拟合
          self.drop_emb = nn.Dropout(cfg["drop_rate"])

          # Transformer Block 堆叠：
          # 根据 cfg["n_layers"] 创建多个 TransformerBlock
          # 这里的 DummyTransformerBlock 只是占位模块，还没有真正实现注意力机制
          self.trf_blocks = nn.Sequential(
              *[DummyTransformerBlock(cfg) for _ in range(cfg["n_layers"])]
          )

          # 最后的 LayerNorm：
          # 正常 GPT 会在输出前做一次归一化，使训练更稳定
          # 这里的 DummyLayerNorm 只是占位模块
          self.final_norm = DummyLayerNorm(cfg["emb_dim"])

          # 输出层：
          # 将每个 token 的隐藏向量映射到词表大小
          # 用于预测下一个 token
          # 输出形状：[batch_size, seq_len, vocab_size]
          self.out_head = nn.Linear(
              cfg["emb_dim"], cfg["vocab_size"], bias=False
          )

      def forward(self, in_idx):
          # in_idx 是输入 token id
          # 形状：[batch_size, seq_len]
          batch_size, seq_len = in_idx.shape

          # 将 token id 转换为 token embedding
          # 形状：[batch_size, seq_len, emb_dim]
          tok_embeds = self.tok_emb(in_idx)

          # 生成位置索引：[0, 1, 2, ..., seq_len-1]
          # device=in_idx.device 表示位置索引和输入数据放在同一个设备上
          # 例如都在 CPU 或都在 GPU
          pos_embeds = self.pos_emb(
              torch.arange(seq_len, device=in_idx.device)
          )

          # 将 token embedding 和 position embedding 相加
          # tok_embeds 形状：[batch_size, seq_len, emb_dim]
          # pos_embeds 形状：[seq_len, emb_dim]
          # PyTorch 会自动广播到 [batch_size, seq_len, emb_dim]
          x = tok_embeds + pos_embeds

          # 对输入 embedding 做 dropout
          x = self.drop_emb(x)

          # 输入 Transformer Block 堆叠层
          # 当前只是占位模块，因此 x 不会发生变化
          x = self.trf_blocks(x)

          # 最后的归一化层
          # 当前只是占位模块，因此 x 不会发生变化
          x = self.final_norm(x)

          # 输出层：
          # 把 emb_dim 维向量映射成 vocab_size 维
          # 每个位置都会得到一个词表大小的预测分数
          logits = self.out_head(x)

          # 返回 logits
          # 形状：[batch_size, seq_len, vocab_size]
          return logits


  # TransformerBlock 占位类
  # 之后会替换成真正包含：
  # 多头注意力、前馈网络、残差连接、LayerNorm 的 TransformerBlock
  class DummyTransformerBlock(nn.Module):
      def __init__(self, cfg):
          super().__init__()

      def forward(self, x):
          # 当前没有做任何计算
          # 输入什么，就原样返回什么
          return x


  # LayerNorm 占位类
  # 之后会替换成真正的 LayerNorm
  class DummyLayerNorm(nn.Module):
      def __init__(self, normalized_shape, eps=1e-5):
          super().__init__()

      def forward(self, x):
          # 当前没有做任何归一化处理
          # 输入什么，就原样返回什么
          return x
  ```

  使用 ```tiktoken``` 分词器对包含两个文本的批量输入进行分词，以供 GPT 模型使用：

  ```python
  # 准备输入批次
  print("准备输入批次...")
  tokenizer = tiktoken.get_encoding("gpt2")
  batch = []
  txt1 = "Every effort moves you"
  txt2 = "Every day holds a"
  print("输入批次1文本：" + txt1)
  print("输入批次2文本：" + txt2)
  batch.append(torch.tensor(tokenizer.encode(txt1)))
  batch.append(torch.tensor(tokenizer.encode(txt2)))
  batch = torch.stack(batch, dim=0)
  print("输入批次：")
  print(batch)
  ```

  模型输出：

  ```python
  # 定义模型配置
  GPT_CONFIG_124M = {
      "vocab_size": 50257,    # Vocabulary size
      "context_length": 1024, # Context length
      "emb_dim": 768,         # Embedding dimension
      "n_heads": 12,          # Number of attention heads
      "n_layers": 12,         # Number of layers
      "drop_rate": 0.1,       # Dropout rate
      "qkv_bias": False       # Query-Key-Value bias
  }

  # 模型输出
  print("模型输出：")
  torch.manual_seed(123)
  model = DummyGPTModel(GPT_CONFIG_124M)
  logits = model(batch)
  print(logits.shape)
  print(logits)
  ```

### 使用层归一化对激活值进行标准化

### 实现带有 GELU 激活函数的前馈神经网络

### 添加快捷连接

### 在 Transformer 模块中连接注意力层与线性层

###  实现 GPT 模型

### 生成文本