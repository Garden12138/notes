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

* 文本生成损失用于把模型生成文本的质量转化为一个可以计算和优化的数值。训练 GPT 时，不是直接判断最终生成的字符串是否完全正确，而是检查模型在每个位置为“正确的下一个 token”分配了多大的概率：正确 token 的概率越高，损失越小；正确 token 的概率越低，损失越大。

* 首先创建两个输入样本及其目标。`targets` 是 `inputs` 向后错开一个 token 得到的序列：

  ```text
  输入： every  -> effort -> moves
  目标： effort -> moves  -> you

  输入： I      -> really -> like
  目标： really -> like   -> chocolate
  ```

  这种错位使模型在每个位置执行“根据当前及之前的 token 预测下一个 token”的任务。例如，当输入位置是 `every` 时，正确目标是 `effort`；当输入位置是 `every effort moves` 的最后一个 token 时，正确目标是 `you`。

  ```python
  # 实践文本生成损失的计算
  print("实践文本生成损失的计算：")

  print("创建 input 以及对应的 target 两个输入样本：")
  inputs = torch.tensor([
      [16833, 3626, 6100],
      [40, 1107, 588]
  ])

  print("inputs：['every effort moves', \n'I really like']\n", inputs)

  targets = torch.tensor([
      [3626, 6100, 345],
      [1107, 588, 11311]
  ])

  print("targets：[' effort moves you', \n' really like chocolate']\n", targets)
  ```

  输出：

  ```text
  创建 input 以及对应的 target 两个输入样本：
  inputs：['every effort moves',
  'I really like']
   tensor([[16833,  3626,  6100],
          [   40,  1107,   588]])
  targets：[' effort moves you',
  ' really like chocolate']
   tensor([[ 3626,  6100,   345],
          [ 1107,   588, 11311]])
  ```

  `inputs` 和 `targets` 的形状都是 `[2, 3]`：`2` 是批次中的文本数量，`3` 是每条文本包含的 token 数量。

* 将输入送入随机初始化的 GPT 模型。模型为每条文本的每个位置输出一个长度为 `50257` 的 logit 向量，再通过 Softmax 将 logits 转换成词表上的概率分布：

  ```python
  print("创建 GPT 模型：")
  model = GPTModel(GPT_CONFIG_124M)

  print("计算 logit 向量，应用 Softmax 转换为概率得分：")

  # 评估/推理模式会关闭 Dropout，但不会关闭梯度跟踪
  model.eval()

  # 当前只评估模型输出，不更新参数，因此禁用梯度跟踪
  with torch.no_grad():
      logits = model(inputs)

  print("logits shape:", logits.shape)
  print(logits)

  # 在词表维度上执行 Softmax，使每个位置的 50257 个概率之和为 1
  probas = torch.softmax(logits, dim=-1)
  print("probas shape:", probas.shape)
  print(probas)
  ```

  输出：

  ```text
  logits shape: torch.Size([2, 3, 50257])
  tensor([[[-0.5674,  0.5365, -0.1212,  ..., -0.1641, -0.0188, -0.4796],
           [ 0.2166,  0.9475, -0.0563,  ...,  0.0443,  0.3628, -0.3648],
           [-0.0564,  0.4534, -1.0238,  ..., -0.1265,  0.5788,  0.2558]],

          [[-0.1174, -0.0511, -0.4544,  ...,  0.5887, -0.1215,  0.3770],
           [-0.0154,  1.0483, -0.1088,  ..., -0.6011,  0.4666,  0.7810],
           [ 0.3686,  0.0096, -0.4947,  ..., -0.4710,  0.1680,  0.6011]]])
  probas shape: torch.Size([2, 3, 50257])
  tensor([[[    0.0000,     0.0000,     0.0000,  ...,     0.0000,
                0.0000,     0.0000],
           [    0.0000,     0.0000,     0.0000,  ...,     0.0000,
                0.0000,     0.0000],
           [    0.0000,     0.0000,     0.0000,  ...,     0.0000,
                0.0000,     0.0000]],

          [[    0.0000,     0.0000,     0.0000,  ...,     0.0000,
                0.0000,     0.0000],
           [    0.0000,     0.0000,     0.0000,  ...,     0.0000,
                0.0000,     0.0000],
           [    0.0000,     0.0000,     0.0000,  ...,     0.0000,
                0.0000,     0.0000]]])
  ```

  `logits` 和 `probas` 的形状都是 `[2, 3, 50257]`：

  - 第 0 维 `2`：批次中有两条文本。
  - 第 1 维 `3`：每条文本有三个输入位置。
  - 第 2 维 `50257`：每个位置都要为词表中的所有 token 给出预测分数或概率。

  `probas` 中显示的 `0.0000` 并不表示概率真的等于 0，而是因为 PyTorch 默认显示的小数位有限。实际概率通常在 `10^-5` 附近，所以后面对这些概率取对数时仍能得到有限的负数，而不是负无穷。

  当前模型使用随机初始化权重，因此具体的 logits、预测 token 和损失值会受到随机种子、此前随机数生成器状态及运行设备影响。实践输出与原书示例数值不同是正常现象，重要的是张量形状和损失计算过程一致。

* 使用 `argmax` 可以查看模型在每个输入位置最终会选择哪个 token ID：

  ```python
  print("获取概率得分最高的token ID：")
  token_ids = torch.argmax(probas, dim=-1, keepdim=True)
  print("Token IDs:\n", token_ids)
  ```

  输出：

  ```text
  Token IDs:
   tensor([[[12887],
           [15721],
           [ 5679]],

          [[  126],
           [34728],
           [32247]]])
  ```

  `argmax` 只是为了观察模型实际会选择什么 token，并不直接参与交叉熵损失的计算。直接比较 argmax 得到的 token ID 与目标 ID 只能产生“对或错”的离散结果，而且 `argmax` 不可微，无法为模型参数提供有效的梯度。训练时需要使用完整概率分布中目标 token 对应的概率。

* 模型训练的目标，是提高正确目标 token 所对应的概率。图 5.6 使用一个只有 7 个 token 的简化词表展示了这个过程；实际模型的词表大小为 `50257`。

  ![图 5.6：提高正确目标 token 所对应的概率](https://raw.githubusercontent.com/skindhu/Build-A-Large-Language-Model-CN/main/Image/chapter5/figure5.6.png)

* 使用 PyTorch 高级索引，分别取得两条文本中三个正确目标 token 的概率：

  ```python
  print("获取两个输入文本目标token对应的概率得分：")

  text_idx = 0
  target_probas_1 = probas[text_idx, [0, 1, 2], targets[text_idx]]
  print("Text 1:", target_probas_1)

  text_idx = 1
  target_probas_2 = probas[text_idx, [0, 1, 2], targets[text_idx]]
  print("Text 2:", target_probas_2)
  ```

  输出：

  ```text
  Text 1: tensor([    0.0000,     0.0000,     0.0000])
  Text 2: tensor([    0.0000,     0.0000,     0.0000])
  ```

  可以先把 `probas` 的三个索引槽记成：

  ```text
  probas[文本编号, 序列位置, 词表中的 token ID]
  ```

  以第一条文本为例，`text_idx = 0` 表示固定读取第 0 条文本；`targets[text_idx]` 则给出这条文本在三个位置上的正确目标 token ID：

  ```python
  text_idx = 0

  targets[text_idx]
  # tensor([3626, 6100, 345])

  target_probas_1 = probas[text_idx, [0, 1, 2], targets[text_idx]]
  ```

  为了便于记忆，可以把这行高级索引逐项展开。这里使用 `torch.stack` 将三个标量概率重新组合成一个张量：

  ```python
  target_probas_1 = torch.stack([
      probas[text_idx, 0, targets[text_idx][0]],
      probas[text_idx, 1, targets[text_idx][1]],
      probas[text_idx, 2, targets[text_idx][2]],
  ])
  ```

  也就是分别取：

  ```text
  第 0 个序列位置，正确目标 token 的概率
  第 1 个序列位置，正确目标 token 的概率
  第 2 个序列位置，正确目标 token 的概率
  ```

  将实际 token ID 代入后，又等价于：

  ```python
  target_probas_1 = torch.stack([
      probas[0, 0, 3626],  # 输入 every  后，正确目标 effort 的概率
      probas[0, 1, 6100],  # 输入 effort 后，正确目标 moves  的概率
      probas[0, 2, 345],   # 输入 moves  后，正确目标 you    的概率
  ])
  ```

  所以 `[0, 1, 2]` 与 `targets[text_idx]` 中的 `[3626, 6100, 345]` 是逐元素配对的：位置 0 配目标 3626，位置 1 配目标 6100，位置 2 配目标 345；它们不会组合出所有可能的索引。

  可以用一句话记忆这行代码：**固定一条文本，依次走过每个序列位置，再用该位置对应的目标 token ID 到词表维取出正确答案的概率。**

  六个目标概率与索引坐标的对应关系如下：

  | 文本编号 | 序列位置 | 当前输入 token | 正确目标 token | 从 `probas` 选择的元素 |
  | --- | ---: | --- | --- | --- |
  | 0 | 0 | `every` | `effort`（3626） | `probas[0, 0, 3626]` |
  | 0 | 1 | `effort` | `moves`（6100） | `probas[0, 1, 6100]` |
  | 0 | 2 | `moves` | `you`（345） | `probas[0, 2, 345]` |
  | 1 | 0 | `I` | `really`（1107） | `probas[1, 0, 1107]` |
  | 1 | 1 | `really` | `like`（588） | `probas[1, 1, 588]` |
  | 1 | 2 | `like` | `chocolate`（11311） | `probas[1, 2, 11311]` |

  也可以使用 `gather` 一次性取得整个批次的目标概率。该写法只是帮助理解等价的向量化操作，不替换上面的实践代码：

  ```python
  # targets.unsqueeze(-1): [2, 3] -> [2, 3, 1]
  target_probas = probas.gather(
      dim=-1,
      index=targets.unsqueeze(-1),
  ).squeeze(-1)

  print(target_probas.shape)
  # torch.Size([2, 3])
  ```

  `gather` 在最后一个词表维度中，根据 `targets` 提供的 token ID，为批次中的每条文本和每个序列位置各取一个概率。

* 得到六个目标概率后，将它们合并并取自然对数：

  ```python
  print("合并两个输入文本目标token对应的概率得分并取对数：")
  log_probas = torch.log(torch.cat((target_probas_1, target_probas_2)))
  print(log_probas)
  ```

  输出：

  ```text
  tensor([-11.3422, -10.9906, -10.9056, -10.1789, -11.1665, -11.2905])
  ```

* 为什么需要对概率取对数：

  GPT 对一个目标序列给出的联合概率，可以写成每个位置条件概率的乘积。假设六个正确目标 token 的概率分别是 $p_1,p_2,\ldots,p_6$，那么：

  $$P(\text{目标序列})=p_1p_2p_3p_4p_5p_6$$

  对数公式可以把完整的概率乘法转换成加法：

  $$\ln(a\times b\times c)=\ln(a)+\ln(b)+\ln(c)$$

  需要特别注意：**对数累加的数值并不等于概率累乘的数值。对数累加得到的是“概率乘积的对数”，两者是在不同尺度上表示同一个结果。**

  例如，三个正确目标 token 的概率分别为 `0.2`、`0.1` 和 `0.05`，它们的概率乘积是：

  $$0.2\times0.1\times0.05=0.001$$

  先计算乘积再取自然对数：

  $$\ln(0.001)\approx-6.9078$$

  分别取自然对数再相加：

  $$\ln(0.2)+\ln(0.1)+\ln(0.05)\approx-6.9078$$

  其中：

  $$\ln(0.2)\approx-1.6094,\qquad\ln(0.1)\approx-2.3026,\qquad\ln(0.05)\approx-2.9957$$

  三项相加后约为 `-6.9078`。

  因此：

  $$\ln(0.2\times0.1\times0.05)=\ln(0.2)+\ln(0.1)+\ln(0.05)$$

  概率乘积是 `0.001`，对数累加结果是 `-6.9078`，它们本身并不相等；`-6.9078` 正好是 `0.001` 的自然对数。对对数累加结果执行指数运算，可以还原原来的概率乘积：

  $$e^{-6.9078}\approx0.001$$

  可以把这个转换过程记成：

  ```text
  概率累乘
      ↓ 取 ln
  对数累加
      ↓ 取 exp
  恢复概率累乘
  ```

  为什么转换到对数尺度后，不会改变“哪个结果更好”？因为自然对数函数在正数范围内单调递增，会保留原来的大小顺序。例如：

  $$P_1=0.001,\qquad P_2=0.0001$$

  原始概率满足：

  $$P_1>P_2$$

  取自然对数后：

  $$\ln(0.001)\approx-6.9078$$

  $$\ln(0.0001)\approx-9.2103$$

  仍然满足：

  $$-6.9078>-9.2103$$

  所以，寻找最大的概率乘积，等价于寻找最大的对数概率之和：

  $$\arg\max\left(\prod_i p_i\right)=\arg\max\left(\sum_i\ln p_i\right)$$

  对数转换主要带来两个好处：

  1. 把大量小概率的连乘转换成加法，避免乘积接近计算机所能表示的最小数而产生数值下溢。
  2. 对很低的正确目标概率施加更大的惩罚。例如，$-\ln(0.1)\approx2.303$，而 $-\ln(0.01)\approx4.605$。

  | 正确目标概率 $p$ | $-\ln(p)$ |
  | ---: | ---: |
  | 1 | 0 |
  | 0.5 | 0.693 |
  | 0.1 | 2.303 |
  | 0.01 | 4.605 |
  | 0.00001 | 11.513 |

  因此，模型越不相信正确答案，损失越大；模型为正确答案分配的概率越接近 1，损失越接近 0。

* 对六个目标 token 的对数概率求平均：

  ```python
  print("计算两个输入文本目标token对应的概率得分取对数后的平均值：")
  avg_log_probas = torch.mean(log_probas)
  print(avg_log_probas)
  ```

  输出：

  ```text
  tensor(-10.9791)
  ```

  求平均不是改变优化目标，而是对 token 数量进行归一化。若直接求和，序列越长或批次越大，损失的绝对值通常越大；取平均后，不同批次大小和序列长度得到的损失更容易比较。这里一共有 `2 × 3 = 6` 个目标 token，因此平均对数概率为：

  $$\frac{1}{6}\sum_{i=1}^{6}\log p_i=-10.9791$$

* 图 5.7 总结了从 logits 到损失的完整过程：

  ![图 5.7：从 logits 计算负平均对数概率](https://raw.githubusercontent.com/skindhu/Build-A-Large-Language-Model-CN/main/Image/chapter5/figure5.7.png)

* 最后对平均对数概率乘以 `-1`，得到负平均对数概率：

  ```python
  print("计算两个输入文本目标token对应的概率得分取对数后的平均值的正数：")
  avg_log_probas = torch.mean(log_probas)
  neg_avg_log_probas = avg_log_probas * -1
  print(neg_avg_log_probas)
  ```

  输出：

  ```text
  tensor(10.9791)
  ```

  这里并不是对平均值“取绝对值”，而是根据负对数似然的定义乘以 `-1`。因为任意概率都满足 $0<p\leq1$，所以 $\log p\leq0$；训练希望最大化平均对数概率，使其趋近于最大值 0。但深度学习优化器通常执行最小化，因此将目标改写为最小化它的相反数：

  $$L=-\frac{1}{B\times T}\sum_{b=1}^{B}\sum_{t=1}^{T}\log p_\theta\left(y_{b,t}\mid x_{b,\leq t}\right)$$

  其中：

  - $B$ 是批次大小，本例为 2。
  - $T$ 是每条文本的目标 token 数量，本例为 3。
  - $y_{b,t}$ 是第 $b$ 条文本在位置 $t$ 的正确目标 token。
  - $p_\theta(y_{b,t}\mid x_{b,\leq t})$ 是模型根据当前位置及之前上下文，为正确目标 token 分配的概率。

  在本例中，`abs(avg_log_probas)` 与 `-avg_log_probas` 的数值碰巧相同，是因为对数概率不会大于 0。但损失的数学定义是负对数似然，而不是绝对值；使用负号能直接表达“最大化似然”等价于“最小化损失”的关系。

* 当真实目标在词表中用 one-hot 分布表示时，交叉熵就等于正确目标 token 的负对数概率。因此，本例的负平均对数似然也就是 token 级别的平均交叉熵损失。

  PyTorch 的 `cross_entropy` 期望接收二维 logits `[样本数量, 类别数量]` 和一维目标 ID `[样本数量]`。所以需要先将批次维和序列维合并：

  ```python
  print("使用cross_entropy计算两个输入文本目标的负的平均对数概率：")

  # [2, 3, 50257] -> [6, 50257]
  logits_flat = logits.flatten(0, 1)

  # [2, 3] -> [6]
  targets_flat = targets.flatten()

  loss = torch.nn.functional.cross_entropy(logits_flat, targets_flat)
  print(loss)
  ```

  输出：

  ```text
  tensor(10.9791)
  ```

  `flatten` 后两者仍保持相同顺序：`logits_flat[i]` 对应 `targets_flat[i]`。`cross_entropy` 默认使用 `reduction="mean"`，因此会对这 6 个 token 位置的损失求平均，结果与手工计算的 `neg_avg_log_probas` 相同。

  `cross_entropy` 应直接接收未经 Softmax 的 logits。它会在内部以数值更稳定的方式组合 `log_softmax` 和负对数似然损失，避免先计算很小的概率、再对概率取对数可能造成的精度问题。前面的显式 `softmax -> 选择目标概率 -> log -> mean -> 取负` 适合用来理解原理，实际训练时直接使用 `cross_entropy(logits, targets)`。

* 困惑度（Perplexity）是语言模型中常与交叉熵一起使用的指标，计算方式是对平均交叉熵取指数：

  ```python
  perplexity = torch.exp(loss)
  print(perplexity)
  ```

  使用控制台中已四舍五入的 `loss = 10.9791` 估算：

  ```text
  perplexity ≈ 58635.76
  ```

  实际运行结果应以张量中未四舍五入的 loss 为准。困惑度越低，表示模型为正确的下一个 token 分配的平均概率越高。均匀预测 `50257` 个 token 时，交叉熵约为 $\log(50257)=10.8249$；当前损失 `10.9791` 更高、困惑度也高于词表大小，说明这个随机初始化模型为正确 token 分配的几何平均概率甚至低于均匀分布。此时不应把 `58635.76` 机械理解为“模型在 58636 个 token 中选择”，它主要用于比较模型训练前后的相对不确定性。

* 完整损失计算流程可以总结为：

  ```text
  inputs、targets
        ↓
  GPT 输出 logits：[2, 3, 50257]
        ↓ Softmax（手工理解时使用）
  每个位置在词表上的概率分布
        ↓ 根据 targets 选择正确 token 的概率
  6 个 target probabilities
        ↓ log → mean → 乘以 -1
  负平均对数似然 / 平均交叉熵：10.9791
  ```

#### 计算训练集和验证集的损失

### 训练 LLM

### 通过解码策略控制生成结果的随机性

#### Temperature scaling

#### Top-k 采样

#### 对文本生成函数进行调整

### 在 PyTorch 中加载和保存模型权重

### 从 OpenAI 加载预训练权重
