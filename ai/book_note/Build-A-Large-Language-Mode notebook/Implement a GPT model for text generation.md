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

* 在训练深度神经网络时，梯度消失或梯度爆炸问题有时会带来挑战。这些问题会导致训练过程不稳定，使得网络难以有效调整权重。所以我们将实现层归一化，以提高神经网络训练的稳定性和效率。目标是将神经网络层的激活（输出）调整为均值为 0，方差为 1，这种调整可以加速权重的收敛速度，确保训练过程的一致性和稳定性。在 ```GPT-2``` 和现代 ```Transformer``` 架构中，通常应用于多头注意力模块的前后以及最终输出层之前。

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm39.png)

  ```python
  # 实践层归一化
  print("实践层归一化：")
  torch.manual_seed(123)
  print("随机创建2个训练样本，每个样本有5个维度：")
  batch_example = torch.randn(2, 5)
  print(batch_example)
  layer = nn.Sequential(nn.Linear(5, 6), nn.ReLU())
  out = layer(batch_example)
  print("训练样本应用线性层输出：")
  print(out)
  mean = out.mean(dim=-1, keepdim=True)
  var = out.var(dim=-1, keepdim=True)
  print("原均值：")
  print(mean)
  print("原方差：")
  print(var)
  print("进行层归一化：")
  out_norm = (out - mean) / torch.sqrt(var)
  print(out_norm)
  mean = out_norm.mean(dim=-1, keepdim=True)
  var = out_norm.var(dim=-1, keepdim=True)
  torch.set_printoptions(sci_mode=False) # 关闭科学计数法
  print("新均值：")
  print(mean)
  print("新方差：")
  print(var)
  # 使用LayerNorm实现层归一化
  class LayerNorm(nn.Module):
      def __init__(self, emb_dim):
          super().__init__()
          self.eps = 1e-5 # 变量 eps 是一个小常数（epsilon），在归一化过程中加到方差上，以防止出现除零错误
          # scale 和 shift 是两个与输入具有相同的维度的可训练参数，LLM在训练中会自动调整这些参数，以改善模型在训练任务上的性能
          self.scale = nn.Parameter(torch.ones(emb_dim))
          self.shift = nn.Parameter(torch.zeros(emb_dim))

      def forward(self, x):
          mean = x.mean(dim=-1, keepdim=True)
          var = x.var(dim=-1, keepdim=True, unbiased=False)
          norm_x = (x - mean) / torch.sqrt(var + self.eps)
          return self.scale * norm_x + self.shift
  print("使用LayerNorm实现层归一化：")
  ln = LayerNorm(emb_dim=5)
  out_ln = ln(batch_example)
  print("Outln:\n", out_ln)
  mean = out_ln.mean(dim=-1, keepdim=True)
  var = out_ln.var(dim=-1, unbiased=False, keepdim=True)
  print("Mean:\n", mean)
  print("Variance:\n", var)
  ```

* 通过数学推导，了解 ```LayerNorm```计算原理： 

  在学习 ```Transformer``` 和 ```LayerNorm``` 时，我一开始有个疑问：

  ```python
  out_norm = (out - mean) / std
  ```

  为什么一定要除以“标准差”？

  为什么不能：

  ```python
  out - mean
  ```

  或者：

  ```python
  (out - mean) / 固定值
  ```

  后来通过推导，我终于理解了 ```LayerNorm``` 的数学本质。

  ---

  #### 1. ```LayerNorm``` 的目标

  ```LayerNorm``` 的目标是：

  ```text
  让归一化后的数据：
  均值 = 0
  方差 = 1
  ```

  公式：

  ```python
  out_norm = (out - mean) / std
  ```

  其中：

  ```python
  std = sqrt(var)
  ```

  ---

  #### 2. 为什么减去均值后，均值会变成 0？

  假设：

  ```python
  x = [1,2,3]
  ```

  均值：

  ```python
  mean = (1+2+3)/3 = 2
  ```
 
  减去均值：

  ```python
  x - mean
  =
  [-1,0,1]
  ```

  新的均值：

  ```python
  (-1+0+1)/3
  =
  0
  ```

  因此：

  ```text
  减去均值的作用：
  让数据整体移动到以 0 为中心。
  ```

  ---

  #### 3. 为什么还要除以标准差？

  这里才是真正核心。

  ---

  #### 4. 方差的定义

  方差公式：

  ```text
  σ² = (1/n) Σ(xᵢ - μ)²
  ```

  其中：

  | 符号 | 含义      |
  | -- | ------- |
  | ```σ²``` | 方差      |
  | ```σ```  | 标准差     |
  | ```xᵢ``` | 第 ```i``` 个数据 |
  | ```μ```  | 均值      |
  | ```Σ```  | 求和      |
  | ```n```  | 数据总数量   |

  方差本质表示：

  ```text
  数据离中心点“扩散”的程度。
  ```

  ---

  #### 5. 核心数学规律

  假设：

  ```text
  所有数据都除以 a
  ```

  即：

  ```text
  yᵢ = xᵢ / a
  ```

  那么：

  ```text
  新方差：
  σ_y² = σ² / a²
  ```

  这是 ```LayerNorm``` 最核心的数学规律。

  ---

  #### 6. 为什么会这样？

  从方差定义开始：

  ```text
  σ_y² = (1/n) Σ(yᵢ - μ_y)²
  ```

  由于：

  ```text
  yᵢ = xᵢ / a
  μ_y = μ / a
  ```

  代入：

  ```text
  σ_y²
  =
  (1/n) Σ[(xᵢ/a) - (μ/a)]²
  ```

  化简：

  ```text
  =
  (1/n) Σ[(xᵢ - μ)/a]²
  ```

  平方展开：

  ```text
  =
  (1/n) Σ[(xᵢ - μ)² / a²]
  ```

  把常数提出：

  ```text
  =
  (1/a²) · (1/n) Σ(xᵢ - μ)²
  ```

  而：

  ```text
  (1/n) Σ(xᵢ - μ)²
  ```

  正是原方差：

  ```text
  σ²
  ```

  因此得到：

  ```text
  σ_y² = σ² / a²
  ```

  ---

  #### 7. 为什么“除以标准差”后方差会等于 1？

  现在令：

  ```text
  a = σ
  ```

  即：

  ```text
  除以“原数据自己的标准差”
  ```

  带入公式：

  ```text
  σ_new²
  =
  σ² / σ²
  =
  1
  ```

  于是：

  ```text
  新方差恒等于 1
  ```

  这就是：

  ```python
  (out - mean) / std
  ```

  中：

  ```text
  为什么一定要除以“当前数据自己的标准差”
  ```

  的真正原因。

  ---

  #### 8. 如果不除标准差会怎样？

  例如：

  ```python
  x = [1,2,3]
  ```

  减均值后：

  ```python
  [-1,0,1]
  ```

  方差：

  ```python
  (1+0+1)/3
  =
  0.6667
  ```

  并不等于 1。

  说明：

  ```text
  仅减均值只能移动中心，
  无法统一数据的扩散尺度。
  ```

  ---

  #### 9. 如果除固定值会怎样？

  例如：

  ```python
  [-1,0,1] / 10
  =
  [-0.1,0,0.1]
  ```

  新方差：

  ```python
  0.006667
  ```

  方差会变得非常小。

  说明：

  ```text
  除固定值只能“盲目缩放”，
  无法保证方差统一为 1。
  ```

  ---

  #### 10. LayerNorm 的本质

  ```LayerNorm``` 的真正本质是：

  ```text
  根据当前数据自己的离散程度，
  动态自适应地缩放数据。
  ```

  即：

  ```text
  先减均值：
  让中心变成 0

  再除标准差：
  让扩散程度变成 1
  ```

  最终实现：

  ```text
  均值 = 0
  方差 = 1
  ```

  这样神经网络每层的数据分布都会保持稳定。

  ---

  #### 11. 一句话总结

  ```LayerNorm``` 本质上是在：

  ```text
  “根据当前数据自己的标准差，
  自动把数据缩放到统一尺度。”
  ```

  因此：

  ```python
  (out - mean) / std
  ```

  并不是随便除一个数。

  而是：

  ```text
  必须除以“当前数据自己的标准差”
  ```

  这样才能保证：

  ```text
  新方差恒等于 1
  ```

### 实现带有 GELU 激活函数的前馈神经网络

### 添加快捷连接

### 在 Transformer 模块中连接注意力层与线性层

###  实现 GPT 模型

### 生成文本