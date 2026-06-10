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

* ```GELU```激活函数是一种非线性激活函数，它将在这个神经网络子模块中起着至关重要的作用。与```ReLU```激活函数相比，```GELU```激活函数在训练过程中具有更好的性能和稳定性。```GELU``` 理解成一种“更柔和的 ```ReLU```”，```RELU```是````x > 0````就保留0，```x <= 0```就变成0，而```GELU```则是根据```x```的大小，决定保留多少```x```。```GELU``` 激活函数的公式如下：

  ```GELU(x)=x⋅Φ(x)```，```x```为输入值，```Φ(x)```为标准正态分布的累积分布函数即```Φ(x)=P(Z≤x),Z∼N(0,1)``，这里：

```txt
Z 表示随机生成出来的那个数
Z ~ N(0,1) 表示 Z 服从标准正态分布
P(Z ≤ x) 表示 Z 小于等于 x 的概率
```

  标准正态分布是左右对称的：

```txt
          0
          |
      ____|____
    /          \
---/------------\---
负数区域     正数区域
```

  随机取一个数，它落在0左边的概率是50%，所以```Φ(0) = P(Z ≤ 0) = 0.5```，所以可以把它理解成一个0到1之间的比例系数即```GELU(x) ≈ x ⋅ 某个0到1之间的比例```。但原始的```Φ(x)```计算起来比较麻烦，涉及正态分布积分。模型训练时要计算海量数据，如果每次都算精确```Φ(x)```，开销比较大，可使用近似公式：```GELU(x) ≈ 0.5 ⋅ x ⋅ (1 + tanh[(2/π)⋅(x + 0.044715⋅x3])```，可以简单理解为```GELU(x) ≈ 0.5 ⋅ x ⋅ 某个0到2之间的比例系数``，实现代码如下：

```python
# 近似实现GELU函数
print("近似实现GELU函数：")
class GELU(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, x):
        return 0.5 * x * (1 + torch.tanh(
            torch.sqrt(torch.tensor(2.0 / torch.pi)) *
            (x + 0.044715 * torch.pow(x, 3))
        ))

gelu, relu = GELU(), nn.ReLU()
x = torch.linspace(-3, 3, 100)
y_gelu, y_relu = gelu(x), relu(x)
plt.figure(figsize=(8, 3))
for i, (y, label) in enumerate(zip([y_gelu, y_relu], ["GELU", "ReLU"]), 1):
    plt.subplot(1, 2, i)
    plt.plot(x, y)
    plt.title(f"{label} activation function")
    plt.xlabel("x")
    plt.ylabel(f"{label}(x)")
    plt.grid(True)
plt.tight_layout()
#plt.show()
print("已保存activation_functions.png")
plt.savefig("activation_functions.png", dpi=300, bbox_inches="tight")
```

  结果如图：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm40.png)

  ```GELU```的平滑性使其在训练过程中具有更好的优化特性，能够对模型参数进行更细微的调整。相比之下，```RELU```在零点处有一个拐角，这在网络深度较大或结构复杂时可能会增加优化难度。此外，```ReLU```对所有负输入的输出为零，而```GELU```对负值允许一个小的非零输出。在训练过程中，接收负输入的神经元也能对学习过程产生一定的贡献。

* 实现带GELU激活函数的前馈神经网络。```FeedForward```模块是一个小型神经网络，由两个线性层和一个```GELU```激活函数组成。首先通过第一个线性层将嵌入维度扩展到一个更高维度的空间，再接入非线性```GELU```激活，最后再通过第二个线性层变换回原始维度。这样做是为了扩展后的高维空间可以让模型“看到”输入数据中更多的隐藏特征，提取出更丰富的信息。然后在收缩回低维度时，这些丰富的特征被整合到了输入的原始维度表示中，使模型最终的输出包含更多的上下文和信息：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm41.png)

  代码实现如下：

```python
# 实现带GELU激活函数的前馈神经网络
print("实现带GELU激活函数的前馈神经网络：")
class FeedForward(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(cfg["emb_dim"], 4 * cfg["emb_dim"]),
            GELU(),
            nn.Linear(4 * cfg["emb_dim"], cfg["emb_dim"]),
        )

    def forward(self, x):
        return self.layers(x)

ffn = FeedForward(GPT_CONFIG_124M)
x = torch.rand(2, 3, 768)
print("应用前：")
print(x)
out = ffn(x)
print("应用后：")
print(out)
```

### 添加快捷连接

* 快捷连接，用于缓解梯度消失问题。梯度消失是指在训练中指导权重更新的梯度在反向传播过程中逐渐减小：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm42.png)

  可以看出跳过一层或多层，为梯度提供一条更短的流动路径，这是通过将某层的输出（上一层的输出，这一层的输入）加到后续层的输出（这一层的输出）上来实现的。

  实现了一个5层的深度神经网络，每层包括一个线性层和```GELU```激活函数：

```python
class ExampleDeepNeuralNetwork(nn.Module):
    def __init__(self, layer_sizes, use_shortcut):
        super().__init__()
        self.use_shortcut = use_shortcut
        self.layers = nn.ModuleList([
            nn.Sequential(nn.Linear(layer_sizes[0], layer_sizes[1]), GELU()),
            nn.Sequential(nn.Linear(layer_sizes[1], layer_sizes[2]), GELU()),
            nn.Sequential(nn.Linear(layer_sizes[2], layer_sizes[3]), GELU()),
            nn.Sequential(nn.Linear(layer_sizes[3], layer_sizes[4]), GELU()),
            nn.Sequential(nn.Linear(layer_sizes[4], layer_sizes[5]), GELU())
        ])

    def forward(self, x):
        for layer in self.layers:
            layer_output = layer(x)
            # 启动快捷连接并且当前层的输入与当前层的输出形状相同，最后一层的输出形状我们设置不一样以达到最后一层不再加快捷链接的效果
            if self.use_shortcut and x.shape == layer_output.shape:
                x = x + layer_output
            else:
                x = layer_output
        return x
```

  实现反向传播过程中计算梯度的函数：

```python
def print_gradients(model, x):
    # 向前传播
    output = model(x)
    target = torch.tensor([[0.]])

    # 计算loss损失值
    loss = nn.MSELoss()
    loss = loss(output, target)

    # 反向传播
    loss.backward()

    for name, param in model.named_parameters():
        if 'weight' in name:
            # 打印梯度
            print(f"{name} has gradient mean of {param.grad.abs().mean().item()}")
```

  实践添加快捷键连接：

```python
# 进行没有快捷连接的神经网络的反向传播：
print("进行没有快捷连接的神经网络的反向传播：")
torch.manual_seed(123)
model_without_shortcut = ExampleDeepNeuralNetwork(
    layer_sizes, use_shortcut=False
)
print_gradients(model_without_shortcut, sample_input)

# 进行有快捷连接的神经网络的反向传播：
print("进行有快捷连接的神经网络的反向传播：")
torch.manual_seed(123)
model_with_shortcut = ExampleDeepNeuralNetwork(
    layer_sizes, use_shortcut=True
)
print_gradients(model_with_shortcut, sample_input)
```

  从输出结果可以看到，使用快捷连接的神经网络最后一层（```layers.4```）的梯度依然比其他层更大。然而，随着接近第一层（```layers.0```），梯度值逐渐趋于稳定，并未缩小到几乎消失的程度。

```bash
进行没有快捷连接的神经网络的反向传播：
layers.0.0.weight has gradient mean of 0.00020173584925942123
layers.1.0.weight has gradient mean of 0.00012011159560643137
layers.2.0.weight has gradient mean of 0.0007152040489017963
layers.3.0.weight has gradient mean of 0.0013988736318424344
layers.4.0.weight has gradient mean of 0.005049645435065031
进行有快捷连接的神经网络的反向传播：
layers.0.0.weight has gradient mean of 0.22169791162014008
layers.1.0.weight has gradient mean of 0.20694105327129364
layers.2.0.weight has gradient mean of 0.32896995544433594
layers.3.0.weight has gradient mean of 0.2665732204914093
layers.4.0.weight has gradient mean of 1.3258540630340576
```

* 快捷连接的两个重要的作用：

  * 保持信息（或特征）流畅传递
  * 缓解梯度消失问题

### 在 Transformer 模块中连接注意力层与线性层

* 实现```Transformer```模块，它由层归一化、多头注意力、```dropout```、前馈层以及```GELU```激活函数等多个概念组成：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm43.png)

  实现如下：

```python
# 实现Transformer模块
print("实现Transformer模块：")

class TransformerBlock(nn.Module):
    def __init__(self, cfg):
        super().__init__()

        # 注册多头注意力机制
        self.att = MultiHeadAttention(
            d_in=cfg["emb_dim"],
            d_out=cfg["emb_dim"],
            context_length=cfg["context_length"],
            num_heads=cfg["n_heads"],
            dropout=cfg["drop_rate"],
            qkv_bias=cfg["qkv_bias"]
        )

        # 注册前馈神经网络层
        self.ff = FeedForward(cfg)

        # 注册两组层归一化
        self.norm1 = LayerNorm(cfg["emb_dim"])
        self.norm2 = LayerNorm(cfg["emb_dim"])

        # 注册dropout层
        self.drop_shortcut = nn.Dropout(cfg["drop_rate"])

    def forward(self, x):
        # 1. shortcut 保存原始输入
        shortcut = x

        # 2. LayerNorm -> 多头注意力 -> Dropout
        x = self.norm1(x)
        x = self.att(x)
        x = self.drop_shortcut(x)

        # 3. 残差连接
        x = x + shortcut

        # 4. 再次保存 shortcut
        shortcut = x

        # 5. LayerNorm -> 前馈网络 -> Dropout
        x = self.norm2(x)
        x = self.ff(x)
        x = self.drop_shortcut(x)

        # 6. 残差连接
        x = x + shortcut

        return x

torch.manual_seed(123)
x = torch.rand(2, 4, 768)
block = TransformerBlock(GPT_CONFIG_124M)
output = block(x)

print("Input shape:", x.shape)
print("Output shape:", output.shape)
```

###  实现 GPT 模型

* 实现```GPT```模型架构，```token```嵌入层、位置嵌入层、```Dropout```层、多层```Transformer```模块、最终层归一化以及线性输出层：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm44.png)

  最后一个```Transformer```模块的输出会经过一个最终的层归一化步骤，然后进入线性输出层。该层将 ```Transformer```的输出映射到一个高维空间（对应模型的词汇表大小），以预测序列中的下一个词。

  实现如下：

```python
# 实现GPT模型
print("实现GPT模型：")
class GPTModel(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.tok_emb = nn.Embedding(cfg["vocab_size"], cfg["emb_dim"])
        self.pos_emb = nn.Embedding(cfg["context_length"], cfg["emb_dim"])
        self.drop_emb = nn.Dropout(cfg["drop_rate"])

        self.trf_blocks = nn.Sequential(
            *[TransformerBlock(cfg) for _ in range(cfg["n_layers"])])

        self.final_norm = LayerNorm(cfg["emb_dim"])
        # PyTorch 内部保存的权重形状[vocab_size, emb_dim]
        self.out_head = nn.Linear(
            cfg["emb_dim"], cfg["vocab_size"], bias=False
        )

    def forward(self, in_idx):
        batch_size, seq_len = in_idx.shape
        tok_embeds = self.tok_emb(in_idx)

        pos_embeds = self.pos_emb(torch.arange(seq_len, device=in_idx.device))# 设备设置将根据输入数据所在的位置选择在 CPU 或 GPU 上训练模型
        x = tok_embeds + pos_embeds
        x = self.drop_emb(x)
        x = self.trf_blocks(x)
        x = self.final_norm(x)
        logits = self.out_head(x)
        return logits

torch.manual_seed(123)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = GPTModel(GPT_CONFIG_124M)
model.to(device)
batch = batch.to(device)
out = model(batch)
print("Input batch:\n", batch)
print("\nOutput shape:", out.shape)
print(out)
```

  这里因为存在权重共享，输出的参数量比实际的大，我们可通过减去输入的参数量，得到模型的实际参数量：

```python
total_params = sum(p.numel() for p in model.parameters())
print(f"Total number of parameters: {total_params:,}")
total_params_gpt2 = total_params - sum(p.numel() for p in model.out_head.parameters())
print(f"Number of trainable parameters considering weight tying: {total_params_gpt2:,}")
```

  ```GPT```最后一层得到的是每个位置的隐藏向量，形状是```[batch_size, seq_len, emb_dim]```。输出层```nn.Linear(emb_dim, vocab_size)```会把它投影到词表空间，内部计算相当于用```[emb_dim, vocab_size]```的矩阵做乘法。如果使用```GPT-2```的权重共享，这个输出矩阵本质上就是```token```嵌入矩阵```tok_emb.weight```的转置版本：

```python
hidden:           [batch_size, seq_len, emb_dim]
tok_emb.weight:   [vocab_size, emb_dim]
tok_emb.weight.T: [emb_dim, vocab_size]

logits = hidden @ tok_emb.weight.T

logits:           [batch_size, seq_len, vocab_size]
```

### 生成文本

* ```GPT```模型从输出张量到生成文本的过程涉及几个步骤，包括解码输出张量（选择最后一个```token```，因为是预测下一个词）、根据概率分布选择```token ID```，并将其转化为可读文本：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm45.png)

  我们可以看到输出的文本会作为下次迭代输入，实现如下：

```python
def generate_text_simple(model, idx, max_new_tokens, context_size):
    """
    使用 GPT 模型进行简单文本生成。

    参数说明：
    model:
        已经定义好的 GPT 模型。

    idx:
        当前上下文的 token id 序列，形状为：
        (batch_size, n_tokens)

        例如：
        tensor([[10, 25, 38, 41]])

        表示 batch_size = 1，当前输入文本有 4 个 token。

    max_new_tokens:
        最多生成多少个新 token。
        例如 max_new_tokens = 3，表示在原始 token 后面继续生成 3 个 token。

    context_size:
        模型支持的最大上下文长度。
        如果当前 idx 的长度超过 context_size，
        就只取最后 context_size 个 token 输入模型。

    返回值：
    idx:
        原始 token 序列 + 新生成 token 后的完整序列。
        形状为：
        (batch_size, n_tokens + max_new_tokens)
    """

    # 循环生成 token
    # 每次循环只生成 1 个新 token
    # 如果 max_new_tokens = 3，则循环 3 次，生成 3 个新 token
    for _ in range(max_new_tokens):

        # ------------------------------------------------------------
        # 1. 裁剪上下文
        # ------------------------------------------------------------
        # GPT 模型通常有最大上下文长度限制，例如 context_size = 5。
        #
        # 如果当前 idx 的长度没有超过 context_size，
        # 那么 idx_cond 基本等于 idx。
        #
        # 如果当前 idx 的长度超过了 context_size，
        # 就只保留最后 context_size 个 token。
        #
        # 例如：
        # idx = tensor([[10, 20, 30, 40, 50, 60]])
        # context_size = 4
        #
        # idx[:, -context_size:] 的结果是：
        # tensor([[30, 40, 50, 60]])
        #
        # 这样做是因为模型的位置嵌入层只能处理固定长度的上下文。
        idx_cond = idx[:, -context_size:]

        # ------------------------------------------------------------
        # 2. 使用模型预测下一个 token
        # ------------------------------------------------------------
        # 生成文本时只是推理，不是训练。
        #
        # 所以这里使用 torch.no_grad() 关闭梯度计算，
        # 可以节省显存、提升推理速度。
        with torch.no_grad():

            # 将当前上下文输入模型，得到 logits。
            #
            # logits 是模型输出的原始分数，还不是概率。
            #
            # logits 的形状通常是：
            # (batch_size, n_tokens, vocab_size)
            #
            # 例如：
            # (1, 4, 50257)
            #
            # 含义是：
            # batch_size = 1
            # 当前上下文有 4 个 token
            # 每个 token 位置都会对词表中 50257 个 token 给出一个预测分数
            logits = model(idx_cond)

        # ------------------------------------------------------------
        # 3. 只取最后一个时间步的输出
        # ------------------------------------------------------------
        # GPT 模型会对输入序列中每个位置都输出预测结果。
        #
        # 例如输入：
        # [10, 20, 30, 40]
        #
        # 模型会输出：
        # 第 1 个位置的预测结果
        # 第 2 个位置的预测结果
        # 第 3 个位置的预测结果
        # 第 4 个位置的预测结果
        #
        # 但是生成下一个 token 时，
        # 我们只关心最后一个位置的预测结果。
        #
        # 因为最后一个位置代表：
        # “根据当前完整上下文，预测下一个 token 是什么”
        #
        # 所以这里取 logits[:, -1, :]。
        #
        # 形状变化：
        # (batch_size, n_tokens, vocab_size)
        # ->
        # (batch_size, vocab_size)
        logits = logits[:, -1, :]

        # ------------------------------------------------------------
        # 4. 将 logits 转换成概率
        # ------------------------------------------------------------
        # logits 是原始分数，不是概率。
        #
        # 例如 logits 可能是：
        # [2.0, 1.0, 0.1]
        #
        # 经过 softmax 后会变成类似：
        # [0.66, 0.24, 0.10]
        #
        # 这些概率加起来等于 1。
        #
        # dim=-1 表示在最后一个维度上做 softmax。
        #
        # 当前 logits 的形状是：
        # (batch_size, vocab_size)
        #
        # 最后一个维度就是 vocab_size，也就是词表维度。
        # 所以这一步是在计算词表中每个 token 被选中的概率。
        probas = torch.softmax(logits, dim=-1)

        # ------------------------------------------------------------
        # 5. 选择概率最大的 token
        # ------------------------------------------------------------
        # torch.argmax 会返回概率最大的 token id。
        #
        # 例如：
        # probas = tensor([[0.1, 0.7, 0.2]])
        #
        # 最大概率是 0.7，对应索引 1，
        # 所以 idx_next = tensor([[1]])
        #
        # dim=-1 表示沿着词表维度查找最大值。
        #
        # keepdim=True 表示保留维度。
        #
        # 如果不加 keepdim=True：
        # idx_next 的形状可能是：
        # (batch_size,)
        #
        # 加了 keepdim=True 后：
        # idx_next 的形状是：
        # (batch_size, 1)
        #
        # 这样方便后面和 idx 拼接。
        idx_next = torch.argmax(probas, dim=-1, keepdim=True)

        # ------------------------------------------------------------
        # 6. 将新生成的 token 拼接到原序列后面
        # ------------------------------------------------------------
        # idx 是当前已有的 token 序列。
        # idx_next 是刚刚生成的新 token。
        #
        # 例如：
        # idx = tensor([[10, 20, 30, 40]])
        # idx_next = tensor([[55]])
        #
        # 拼接后：
        # idx = tensor([[10, 20, 30, 40, 55]])
        #
        # dim=1 表示沿着 token 序列长度这个维度进行拼接。
        #
        # 形状变化：
        # (batch_size, n_tokens)
        # ->
        # (batch_size, n_tokens + 1)
        idx = torch.cat((idx, idx_next), dim=1)

    # 循环结束后，返回完整的 token 序列。
    #
    # 例如原始输入是：
    # tensor([[10, 20, 30]])
    #
    # 如果生成了 3 个新 token，最终可能变成：
    # tensor([[10, 20, 30, 55, 19, 82]])
    #
    # 注意：这里返回的还是 token id，
    # 如果想变成真正的文本，还需要使用 tokenizer.decode() 解码。
    return idx

start_context = "Hello, I am"
print("输入文本：", start_context)
encoded = tokenizer.encode(start_context)
print("encoded:", encoded)
encoded_tensor = torch.tensor(encoded).unsqueeze(0)
encoded_tensor = encoded_tensor.to(device)
print("encoded_tensor.shape:", encoded_tensor.shape)

model.eval()             #A 禁用 dropout，因为当前不是在训练模型
out = generate_text_simple(
    model=model,
    idx=encoded_tensor,
    max_new_tokens=10,
    context_size=GPT_CONFIG_124M["context_length"]
)
print("Output:", out)
print("Output length:", len(out[0]))

decoded_text = tokenizer.decode(out.squeeze(0).tolist())
print("输出文本：", decoded_text)
print(decoded_text)
```

  结果如：

```bash
输入文本： Hello, I am
encoded: [15496, 11, 314, 716]
encoded_tensor.shape: torch.Size([1, 4])
Output: tensor([[15496,    11,   314,   716, 27018, 24086, 47843, 30961, 42348,  7267,
         49706, 43231, 47062, 34657]], device='cuda:0')
Output length: 14
输出文本： Hello, I am Featureiman Byeswickattribute argue logger Normandy Compton analogous
Hello, I am Featureiman Byeswickattribute argue logger Normandy Compton analogous
```

  由于模型还没有经过训练，所以生成的是无意义的文本内容。

### 本节实践代码(整合版)

```python
"""
gpt_text_generation_service.py

一个从零实现的 GPT 文本生成服务模块。

特点：
1. 不依赖 Web 框架，不是 FastAPI / Flask 服务；
2. 可以作为 Python 模块被其他代码 import 使用；
3. 也可以直接通过命令行运行；
4. 内置 GPTModel、TransformerBlock、MultiHeadAttention、LayerNorm、GELU、FeedForward；
5. 支持 greedy / temperature / top-k 采样生成；
6. 支持可选加载训练好的 checkpoint。

注意：
如果不加载训练好的权重，模型是随机初始化的，生成结果没有实际语言能力。
要想生成正常文本，需要先训练模型，或加载已经训练好的模型权重。
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import torch
import torch.nn as nn
import tiktoken


@dataclass
class GPTConfig:
    """GPT 模型配置。"""

    vocab_size: int = 50257       # GPT-2 tokenizer 的词表大小
    context_length: int = 1024    # 最大上下文长度
    emb_dim: int = 768            # token embedding 维度
    n_heads: int = 12             # 注意力头数量
    n_layers: int = 12            # Transformer Block 层数
    drop_rate: float = 0.1        # Dropout 概率
    qkv_bias: bool = False        # Q/K/V 线性层是否使用 bias

    def to_dict(self) -> dict:
        return asdict(self)


GPT_CONFIG_124M = GPTConfig()


class LayerNorm(nn.Module):
    """
    自定义 LayerNorm。

    对最后一个维度做归一化：
    例如输入形状为 [batch_size, seq_len, emb_dim]，
    就会对每个 token 的 emb_dim 维向量单独做归一化。
    """

    def __init__(self, emb_dim: int, eps: float = 1e-5):
        super().__init__()
        self.eps = eps
        self.scale = nn.Parameter(torch.ones(emb_dim))
        self.shift = nn.Parameter(torch.zeros(emb_dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        mean = x.mean(dim=-1, keepdim=True)
        var = x.var(dim=-1, keepdim=True, unbiased=False)
        norm_x = (x - mean) / torch.sqrt(var + self.eps)
        return self.scale * norm_x + self.shift


class GELU(nn.Module):
    """GPT 中常用的 GELU 激活函数近似实现。"""

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return 0.5 * x * (
            1
            + torch.tanh(
                torch.sqrt(torch.tensor(2.0 / torch.pi, device=x.device))
                * (x + 0.044715 * torch.pow(x, 3))
            )
        )


class FeedForward(nn.Module):
    """
    Transformer Block 中的前馈网络。

    结构：
    emb_dim -> 4 * emb_dim -> GELU -> emb_dim
    """

    def __init__(self, cfg: GPTConfig):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(cfg.emb_dim, 4 * cfg.emb_dim),
            GELU(),
            nn.Linear(4 * cfg.emb_dim, cfg.emb_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.layers(x)


class MultiHeadAttention(nn.Module):
    """
    因果多头自注意力机制。

    输入形状：
        [batch_size, seq_len, d_in]

    输出形状：
        [batch_size, seq_len, d_out]
    """

    def __init__(
        self,
        d_in: int,
        d_out: int,
        context_length: int,
        dropout: float,
        num_heads: int,
        qkv_bias: bool = False,
    ):
        super().__init__()

        if d_out % num_heads != 0:
            raise ValueError("d_out must be divisible by num_heads")

        self.d_out = d_out
        self.num_heads = num_heads
        self.head_dim = d_out // num_heads

        self.W_query = nn.Linear(d_in, d_out, bias=qkv_bias)
        self.W_key = nn.Linear(d_in, d_out, bias=qkv_bias)
        self.W_value = nn.Linear(d_in, d_out, bias=qkv_bias)

        self.out_proj = nn.Linear(d_out, d_out)
        self.dropout = nn.Dropout(dropout)

        # 上三角 mask，用于屏蔽当前位置之后的 token，保证模型只能看见过去和当前 token。
        self.register_buffer(
            "mask",
            torch.triu(torch.ones(context_length, context_length), diagonal=1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size, num_tokens, _ = x.shape

        keys = self.W_key(x)
        queries = self.W_query(x)
        values = self.W_value(x)

        # [batch_size, num_tokens, d_out]
        # -> [batch_size, num_tokens, num_heads, head_dim]
        keys = keys.view(batch_size, num_tokens, self.num_heads, self.head_dim)
        queries = queries.view(batch_size, num_tokens, self.num_heads, self.head_dim)
        values = values.view(batch_size, num_tokens, self.num_heads, self.head_dim)

        # -> [batch_size, num_heads, num_tokens, head_dim]
        keys = keys.transpose(1, 2)
        queries = queries.transpose(1, 2)
        values = values.transpose(1, 2)

        # 注意力分数：Q @ K^T
        attn_scores = queries @ keys.transpose(2, 3)

        # 因果 mask：屏蔽未来 token
        mask_bool = self.mask.bool()[:num_tokens, :num_tokens]
        attn_scores.masked_fill_(mask_bool, -torch.inf)

        # 缩放点积注意力
        attn_weights = torch.softmax(
            attn_scores / (self.head_dim ** 0.5),
            dim=-1,
        )
        attn_weights = self.dropout(attn_weights)

        # 加权求和 V
        context_vec = attn_weights @ values

        # [batch_size, num_heads, num_tokens, head_dim]
        # -> [batch_size, num_tokens, num_heads, head_dim]
        context_vec = context_vec.transpose(1, 2).contiguous()

        # 多个头拼接回 d_out
        context_vec = context_vec.view(batch_size, num_tokens, self.d_out)

        # 输出投影层：融合多个注意力头的结果
        context_vec = self.out_proj(context_vec)
        return context_vec


class TransformerBlock(nn.Module):
    """
    GPT 使用的 Transformer Block。

    结构：
    1. LayerNorm -> MultiHeadAttention -> Dropout -> 残差连接
    2. LayerNorm -> FeedForward -> Dropout -> 残差连接
    """

    def __init__(self, cfg: GPTConfig):
        super().__init__()
        self.att = MultiHeadAttention(
            d_in=cfg.emb_dim,
            d_out=cfg.emb_dim,
            context_length=cfg.context_length,
            num_heads=cfg.n_heads,
            dropout=cfg.drop_rate,
            qkv_bias=cfg.qkv_bias,
        )
        self.ff = FeedForward(cfg)
        self.norm1 = LayerNorm(cfg.emb_dim)
        self.norm2 = LayerNorm(cfg.emb_dim)
        self.drop_shortcut = nn.Dropout(cfg.drop_rate)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        shortcut = x
        x = self.norm1(x)
        x = self.att(x)
        x = self.drop_shortcut(x)
        x = x + shortcut

        shortcut = x
        x = self.norm2(x)
        x = self.ff(x)
        x = self.drop_shortcut(x)
        x = x + shortcut

        return x


class GPTModel(nn.Module):
    """用于文本生成的 GPT 模型主体。"""

    def __init__(self, cfg: GPTConfig):
        super().__init__()
        self.cfg = cfg

        self.tok_emb = nn.Embedding(cfg.vocab_size, cfg.emb_dim)
        self.pos_emb = nn.Embedding(cfg.context_length, cfg.emb_dim)
        self.drop_emb = nn.Dropout(cfg.drop_rate)

        self.trf_blocks = nn.Sequential(
            *[TransformerBlock(cfg) for _ in range(cfg.n_layers)]
        )

        self.final_norm = LayerNorm(cfg.emb_dim)
        self.out_head = nn.Linear(cfg.emb_dim, cfg.vocab_size, bias=False)

    def forward(self, in_idx: torch.Tensor) -> torch.Tensor:
        """
        参数：
            in_idx: token id，形状 [batch_size, seq_len]

        返回：
            logits，形状 [batch_size, seq_len, vocab_size]
        """
        _, seq_len = in_idx.shape

        if seq_len > self.cfg.context_length:
            raise ValueError(
                f"输入长度 {seq_len} 超过模型最大上下文长度 {self.cfg.context_length}"
            )

        tok_embeds = self.tok_emb(in_idx)
        pos_embeds = self.pos_emb(torch.arange(seq_len, device=in_idx.device))

        x = tok_embeds + pos_embeds
        x = self.drop_emb(x)
        x = self.trf_blocks(x)
        x = self.final_norm(x)
        logits = self.out_head(x)
        return logits


@torch.no_grad()
def generate_token_ids(
    model: GPTModel,
    idx: torch.Tensor,
    max_new_tokens: int,
    context_size: int,
    temperature: float = 0.0,
    top_k: Optional[int] = None,
    eos_id: Optional[int] = None,
) -> torch.Tensor:
    """
    根据输入 token id 生成新的 token id。

    temperature = 0 表示贪心生成，永远选择概率最高的 token。
    temperature > 0 表示采样生成，值越大，随机性越强。
    top_k 表示只从概率最高的 k 个 token 中采样。
    eos_id 表示遇到指定结束 token 后提前停止。
    """
    model.eval()

    for _ in range(max_new_tokens):
        idx_cond = idx[:, -context_size:]
        logits = model(idx_cond)
        logits = logits[:, -1, :]

        if top_k is not None:
            top_logits, _ = torch.topk(logits, top_k)
            min_top_logit = top_logits[:, -1].unsqueeze(dim=-1)
            logits = torch.where(
                logits < min_top_logit,
                torch.tensor(float("-inf"), device=logits.device),
                logits,
            )

        if temperature > 0.0:
            logits = logits / temperature
            probs = torch.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
        else:
            idx_next = torch.argmax(logits, dim=-1, keepdim=True)

        if eos_id is not None and idx_next.item() == eos_id:
            break

        idx = torch.cat((idx, idx_next), dim=1)

    return idx


class GPTTextGenerationService:
    """
    文本生成服务类。

    这个类不是 Web 服务，而是一个可被其他 Python 代码直接调用的服务封装。

    使用示例：
        service = GPTTextGenerationService()
        text = service.generate("Hello, I am", max_new_tokens=20)
        print(text)
    """

    def __init__(
        self,
        cfg: GPTConfig = GPT_CONFIG_124M,
        checkpoint_path: Optional[str] = None,
        device: Optional[str] = None,
        tokenizer_name: str = "gpt2",
    ):
        self.cfg = cfg
        self.device = torch.device(
            device if device is not None else "cuda" if torch.cuda.is_available() else "cpu"
        )
        self.tokenizer = tiktoken.get_encoding(tokenizer_name)
        self.model = GPTModel(cfg).to(self.device)

        if checkpoint_path is not None:
            self.load_checkpoint(checkpoint_path)

        self.model.eval()

    def load_checkpoint(self, checkpoint_path: str) -> None:
        """
        加载模型权重。

        支持两种 checkpoint 格式：
        1. 直接保存的 state_dict；
        2. 包含 model_state_dict 字段的字典。
        """
        path = Path(checkpoint_path)
        if not path.exists():
            raise FileNotFoundError(f"checkpoint 文件不存在：{checkpoint_path}")

        checkpoint = torch.load(path, map_location=self.device)

        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            state_dict = checkpoint["model_state_dict"]
        else:
            state_dict = checkpoint

        self.model.load_state_dict(state_dict)
        self.model.eval()

    def encode(self, text: str) -> torch.Tensor:
        token_ids = self.tokenizer.encode(text)
        return torch.tensor(token_ids, dtype=torch.long, device=self.device).unsqueeze(0)

    def decode(self, token_ids: torch.Tensor) -> str:
        return self.tokenizer.decode(token_ids.squeeze(0).tolist())

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 50,
        temperature: float = 0.0,
        top_k: Optional[int] = None,
        eos_id: Optional[int] = None,
    ) -> str:
        """输入 prompt，返回生成后的完整文本。"""
        if not prompt:
            raise ValueError("prompt 不能为空")

        encoded = self.encode(prompt)
        output_ids = generate_token_ids(
            model=self.model,
            idx=encoded,
            max_new_tokens=max_new_tokens,
            context_size=self.cfg.context_length,
            temperature=temperature,
            top_k=top_k,
            eos_id=eos_id,
        )
        return self.decode(output_ids)

    def count_parameters(self) -> int:
        """统计模型总参数量。"""
        return sum(p.numel() for p in self.model.parameters())


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="从零实现的 GPT 文本生成服务模块")
    parser.add_argument("--prompt", type=str, default="Hello, I am", help="输入提示词")
    parser.add_argument("--max-new-tokens", type=int, default=30, help="最多生成的新 token 数")
    parser.add_argument("--temperature", type=float, default=0.0, help="采样温度，0 表示贪心生成")
    parser.add_argument("--top-k", type=int, default=None, help="只从概率最高的 k 个 token 中采样")
    parser.add_argument("--checkpoint", type=str, default=None, help="可选：模型 checkpoint 路径")
    parser.add_argument("--device", type=str, default=None, help="可选：cpu / cuda / mps")
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()

    service = GPTTextGenerationService(
        cfg=GPT_CONFIG_124M,
        checkpoint_path=args.checkpoint,
        device=args.device,
    )

    print(f"模型参数量：{service.count_parameters():,}")
    print("输入文本：", args.prompt)

    output_text = service.generate(
        prompt=args.prompt,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_k=args.top_k,
    )

    print("生成文本：")
    print(output_text)


if __name__ == "__main__":
    main()
```