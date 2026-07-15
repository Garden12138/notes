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

* 文本生成损失衡量模型为正确的下一个 token 分配了多少概率。概率越高，损失越小。

* `targets` 是 `inputs` 向后错开一个 token 得到的序列：

  ```text
  输入： every  -> effort -> moves
  目标： effort -> moves  -> you

  输入： I      -> really -> like
  目标： really -> like   -> chocolate
  ```

  每个输入位置都对应一个下一个 token：`every` 预测 `effort`，`moves` 预测 `you`。

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

  两个张量的形状都是 `[2, 3]`：2 条文本，每条 3 个 token。

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
  probas shape: torch.Size([2, 3, 50257])
  ```

  形状依次对应 `[批次, 序列位置, 词表]`。概率打印成 `0.0000` 是显示精度造成的，实际值约为 `10^-5`。模型尚未训练，具体数值与随机状态有关。

* `argmax` 取出每个位置概率最高的 token ID：

  ```python
  print("获取概率得分最高的token ID：")
  token_ids = torch.argmax(probas, dim=-1, keepdim=True)
  print("Token IDs:\n", token_ids)
  ```

  `argmax` 只用于查看结果，不参与损失计算。它不可微，训练时要使用完整概率分布中目标 token 对应的概率。

* 训练的目标是提高正确目标 token 的概率。图 5.6 使用 7 个 token 的简化词表，实际词表大小为 `50257`。

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

  三个索引分别是：

  ```text
  probas[文本编号, 序列位置, 词表中的 token ID]
  ```

  第一条文本的目标是：

  ```python
  targets[0]
  # tensor([3626, 6100, 345])
  ```

  因此，高级索引可以展开为：

  ```python
  target_probas_1 = torch.stack([
      probas[0, 0, targets[0][0]],  # probas[0, 0, 3626]：effort 的概率
      probas[0, 1, targets[0][1]],  # probas[0, 1, 6100]：moves 的概率
      probas[0, 2, targets[0][2]],  # probas[0, 2,  345]：you 的概率
  ])
  ```

  `[0, 1, 2]` 和 `[3626, 6100, 345]` 逐项配对：位置 0 取目标 3626，位置 1 取目标 6100，位置 2 取目标 345。

  记忆：**固定文本 → 遍历序列位置 → 用对应的目标 token ID 在词表维取概率。**

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

* 对数把概率连乘转换为加法：

  $$\ln\left(\prod_i p_i\right)=\sum_i\ln p_i$$

  以 `0.2`、`0.1`、`0.05` 为例：

  $$
  \begin{aligned}
  0.2\times0.1\times0.05 &= 0.001 \\
  \ln(0.001) &\approx -6.9078 \\
  \ln(0.2)+\ln(0.1)+\ln(0.05) &\approx -6.9078 \\
  e^{-6.9078} &\approx 0.001
  \end{aligned}
  $$

  `0.001` 与 `-6.9078` 不相等；后者是前者的对数。取 `exp` 可以还原概率乘积。

  `ln` 单调递增，所以不会改变大小顺序：

  $$0.001>0.0001\quad\Longleftrightarrow\quad-6.9078>-9.2103$$

  因而最大化概率乘积，等价于最大化对数概率之和：

  $$\arg\max\prod_i p_i=\arg\max\sum_i\ln p_i$$

  取对数还能避免大量小概率连乘造成数值下溢。正确 token 的概率越低，$-\ln(p)$ 越大，例如 $-\ln(0.1)\approx2.303$、$-\ln(0.01)\approx4.605$。

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

  平均值用于消除 token 数量对损失大小的影响。本例有 `2 × 3 = 6` 个目标 token：

  $$\frac{1}{6}\sum_{i=1}^{6}\log p_i=-10.9791$$

* 图 5.7 展示了从 logits 到损失的过程：

  ![图 5.7：从 logits 计算负平均对数概率](https://raw.githubusercontent.com/skindhu/Build-A-Large-Language-Model-CN/main/Image/chapter5/figure5.7.png)

* 对平均对数概率乘以 `-1`：

  ```python
  print("计算两个输入文本目标token对应的概率得分取对数后的平均值的正数：")
  neg_avg_log_probas = avg_log_probas * -1
  print(neg_avg_log_probas)
  ```

  输出：

  ```text
  tensor(10.9791)
  ```

  这一步不是取绝对值。因为 $0<p\leq1$，所以 $\log p\leq0$。训练原本要最大化平均对数概率；乘以 `-1` 后，就变成优化器熟悉的最小化问题：

  $$L=-\frac{1}{B\times T}\sum_{b=1}^{B}\sum_{t=1}^{T}\log p_\theta\left(y_{b,t}\mid x_{b,\leq t}\right)$$

  $B$ 是批次大小，$T$ 是序列长度。`abs(avg_log_probas)` 在这里数值相同，只是因为对数概率非正；损失的定义仍是负对数似然。

* 对 one-hot 目标，交叉熵等于正确 token 的负对数概率。`cross_entropy` 需要二维 logits 和一维 targets，因此先合并批次维与序列维：

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

  展平后，`logits_flat[i]` 仍对应 `targets_flat[i]`。`cross_entropy` 默认对 6 个位置求平均，结果与手工计算相同。

  函数直接接收 logits，内部完成数值稳定的 `log_softmax + negative log-likelihood`。手工步骤用于理解，训练时使用 `cross_entropy`。

* 困惑度（Perplexity）是平均交叉熵的指数：

  ```python
  perplexity = torch.exp(loss)
  print(perplexity)
  ```

  ```text
  perplexity ≈ 58635.76
  ```

  该值由四舍五入后的 `10.9791` 估算。均匀预测时的损失约为 $\ln(50257)=10.8249$；当前损失更高，说明随机模型给正确 token 的平均概率低于均匀分布。困惑度主要用于比较训练前后的相对变化。

* 整体流程：

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

* 训练损失衡量模型对训练数据的拟合程度，验证损失衡量模型在未参与训练的数据上的表现。训练前先计算两者，作为后续比较的基线。

* 加载《判决》（The Verdict）文本并统计字符数和 token 数：

  ```python
  print("实现文本生成损失的计算：")
  print("加载数据集：")

  file_path = "the-verdict.txt"
  with open(file_path, "r", encoding="utf-8") as file:
      text_data = file.read()

  total_characters = len(text_data)
  tokenizer = tiktoken.get_encoding("gpt2")
  total_tokens = len(tokenizer.encode(text_data))

  print("Characters:", total_characters)
  print("Tokens:", total_tokens)
  ```

  输出：

  ```text
  Characters: 20445
  Tokens: 5489
  ```

  字符数和 token 数不同，因为 GPT-2 分词器使用 BPE，一个 token 可能对应一个字符、多个字符或单词片段。这个数据集只用于验证训练流程，规模不足以训练出实用的语言模型。

* 按字符位置连续切分数据，前 90% 用于训练，后 10% 用于验证：

  ```python
  print("数据集划分为90%训练集和10%验证集：")

  train_ratio = 0.90
  split_idx = int(train_ratio * len(text_data))
  train_data = text_data[:split_idx]
  val_data = text_data[split_idx:]

  print("训练集长度：", len(train_data))
  print("验证集长度：", len(val_data))
  ```

  输出：

  ```text
  训练集长度： 18400
  验证集长度： 2045
  ```

  先切分文本，再分别创建滑动窗口，可以避免同一个窗口同时跨入训练集和验证集。

* 图 5.9 展示了 `max_length` 和 `stride` 如何控制文本窗口。代码中两者都为 256，因此每次向后移动 256 个 token，窗口之间不重叠。

  ![图 5.9：使用滑动窗口构建训练批次](https://raw.githubusercontent.com/skindhu/Build-A-Large-Language-Model-CN/main/Image/chapter5/figure5.9.png)

* 创建训练集和验证集 DataLoader：

  ```python
  print("创建训练集加载器：")
  train_loader = create_dataloader_v1(
      train_data,
      batch_size=2,
      max_length=256,
      stride=256,
      drop_last=True,
      shuffle=True,
      num_workers=0,
  )

  print("创建验证集加载器：")
  val_loader = create_dataloader_v1(
      val_data,
      batch_size=2,
      max_length=256,
      stride=256,
      drop_last=False,
      shuffle=False,
      num_workers=0,
  )

  print("Train loader:")
  for x, y in train_loader:
      print(x.shape, y.shape)

  print("\nValidation loader:")
  for x, y in val_loader:
      print(x.shape, y.shape)
  ```

  输出汇总：

  ```text
  Train loader:      9 个批次，每个 x、y 均为 torch.Size([2, 256])
  Validation loader: 1 个批次，x、y 均为 torch.Size([2, 256])
  ```

  参数含义：

  - `batch_size=2`：每批包含 2 个文本窗口。
  - `max_length=256`：每个窗口包含 256 个 token，小于模型支持的 1024。
  - `stride=256`：每次移动一个完整窗口，窗口之间不重叠。
  - `shuffle=True`：训练时打乱窗口顺序；验证时保持固定顺序。
  - `drop_last=True`：训练集丢弃最后一个不足 2 个样本的批次；验证集保留。

  `x` 和 `y` 形状相同，但内容错开一个 token：`x` 是模型输入，`y` 是每个位置的下一个 token。

* `calc_loss_batch` 计算单个批次的平均交叉熵：

  ```python
  print("实现计算训练和验证加载器返回的批量数据的损失值方法：")

  def calc_loss_batch(input_batch, target_batch, model, device):
      # 数据和模型必须位于同一设备
      input_batch = input_batch.to(device)
      target_batch = target_batch.to(device)

      logits = model(input_batch)
      loss = torch.nn.functional.cross_entropy(
          logits.flatten(0, 1),
          target_batch.flatten(),
      )
      return loss
  ```

  形状变化：

  ```text
  input_batch、target_batch: [2, 256]
  logits:                    [2, 256, 50257]
  logits.flatten(0, 1):      [512, 50257]
  target_batch.flatten():    [512]
  loss:                      标量
  ```

  一个批次共有 `2 × 256 = 512` 个目标位置，返回值是这些位置的平均交叉熵。

* `calc_loss_loader` 计算指定 DataLoader 中若干批次的平均损失：

  ```python
  print("实现计算指定数据加载器中的指定数据批次的损失值方法：")

  def calc_loss_loader(data_loader, model, device, num_batches=None):
      total_loss = 0.0

      if len(data_loader) == 0:
          return float("nan")

      if num_batches is None:
          num_batches = len(data_loader)
      else:
          num_batches = min(num_batches, len(data_loader))

      for i, (input_batch, target_batch) in enumerate(data_loader):
          if i >= num_batches:
              break

          loss = calc_loss_batch(
              input_batch,
              target_batch,
              model,
              device,
          )

          # 调试信息，正式训练时可以移除
          print("批次：", i)
          print("loss：", loss)

          # 将标量张量转换为 Python 数值后累加
          total_loss += loss.item()

      return total_loss / num_batches
  ```

  `num_batches=None` 表示遍历全部批次；指定批次数可以减少评估开销。若指定值超过 DataLoader 的长度，使用实际批次数。空 DataLoader 返回 `nan`，避免除以 0。

* 将模型和数据放到同一设备，在评估模式下计算基线损失：

  ```python
  device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
  model.to(device)
  model.eval()

  with torch.no_grad():
      train_loss = calc_loss_loader(train_loader, model, device)
      val_loss = calc_loss_loader(val_loader, model, device)

  print("Training loss:", train_loss)
  print("Validation loss:", val_loss)
  ```

  `model.eval()` 关闭 Dropout，`torch.no_grad()` 关闭梯度记录；两者作用不同。

  输出汇总：

  ```text
  Train batch losses:
  [11.0307, 10.9937, 11.0069, 11.0117, 11.0029,
   10.9994, 11.0199, 11.0337, 10.9971]

  Validation batch losses:
  [11.0442]

  Training loss:   11.01067140367296
  Validation loss: 11.044153213500977
  ```

  训练损失是 9 个训练批次损失的平均值。验证集只有一个批次，所以验证损失等于该批次的损失。

  上面列出的批次损失只显示 4 位小数，直接平均约为 `11.01066667`；程序使用未舍入的 `loss.item()`，因此得到 `11.01067140367296`。

  模型尚未训练，两项损失都接近 11，且差距很小。此时它们只是随机初始化模型的基线；后续训练应使训练损失和验证损失下降。

* 整体流程：

  ```text
  文本切分
      ↓
  创建训练集、验证集 DataLoader
      ↓
  calc_loss_batch：计算单批次平均交叉熵
      ↓
  calc_loss_loader：计算多个批次的平均值
      ↓
  得到训练损失与验证损失基线
  ```

### 训练 LLM

### 通过解码策略控制生成结果的随机性

#### Temperature scaling

#### Top-k 采样

#### 对文本生成函数进行调整

### 在 PyTorch 中加载和保存模型权重

### 从 OpenAI 加载预训练权重
