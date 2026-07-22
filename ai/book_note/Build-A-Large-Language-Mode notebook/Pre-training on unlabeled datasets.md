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

  ![图 5.6：提高正确目标 token 所对应的概率](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm48.png)

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

  ![图 5.7：从 logits 计算负平均对数概率](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm49.png)

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

  ![图 5.9：使用滑动窗口构建训练批次](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm50.png)

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

#### 实现训练循环

* 训练按 epoch 和 batch 两层循环进行。每个 batch 都要执行：清空梯度、计算损失、反向传播、更新权重。

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm46.png)

  图中第 3 步写的是清除上一 epoch 的梯度，更准确地说，是清除上一批次残留的梯度。PyTorch 默认累加梯度，不主动清空会把多个批次的梯度叠加在一起。

* 实现简单训练循环：

  ```python
  def train_model_simple(
      model,
      train_loader,
      val_loader,
      optimizer,
      device,
      num_epochs,
      eval_freq,
      eval_iter,
      start_context,
      tokenizer,
  ):
      train_losses = []
      val_losses = []
      track_tokens_seen = []

      tokens_seen = 0
      global_step = -1

      for epoch in range(num_epochs):
          model.train()

          for input_batch, target_batch in train_loader:
              # 1. 清空上一批次的梯度
              optimizer.zero_grad()

              # 2. 前向传播并计算当前批次的交叉熵
              loss = calc_loss_batch(
                  input_batch,
                  target_batch,
                  model,
                  device,
              )

              # 3. 反向传播，计算每个参数的梯度
              loss.backward()

              # 4. 根据梯度更新模型参数
              optimizer.step()

              tokens_seen += input_batch.numel()
              global_step += 1

              # 每隔 eval_freq 个更新步骤评估一次模型
              if global_step % eval_freq == 0:
                  train_loss, val_loss = evaluate_model(
                      model,
                      train_loader,
                      val_loader,
                      device,
                      eval_iter,
                  )

                  train_losses.append(train_loss)
                  val_losses.append(val_loss)
                  track_tokens_seen.append(tokens_seen)

                  print(
                      f"Ep {epoch + 1} (Step {global_step:06d}): "
                      f"Train loss {train_loss:.3f}, "
                      f"Val loss {val_loss:.3f}"
                  )

          # 每个 epoch 结束后生成一段文本
          generate_and_print_sample(
              model,
              tokenizer,
              device,
              start_context,
          )

      return train_losses, val_losses, track_tokens_seen
  ```

  参数更新的核心顺序：

  ```text
  optimizer.zero_grad()
          ↓
  loss = calc_loss_batch(...)
          ↓
  loss.backward()
          ↓
  optimizer.step()
  ```

  `global_step` 从 `-1` 开始，所以第一个批次更新后为 step 0。`input_batch.numel()` 是当前批次的 token 数，本例每批为 `2 × 256 = 512`。

#### 评估与生成样本

* `evaluate_model` 计算少量训练批次和验证批次的损失：

  ```python
  def evaluate_model(model, train_loader, val_loader, device, eval_iter):
      model.eval()

      with torch.no_grad():
          train_loss = calc_loss_loader(
              train_loader,
              model,
              device,
              num_batches=eval_iter,
          )
          val_loss = calc_loss_loader(
              val_loader,
              model,
              device,
              num_batches=eval_iter,
          )

      model.train()
      return train_loss, val_loss
  ```

  `model.eval()` 关闭 Dropout，`torch.no_grad()` 关闭梯度记录。评估完成后调用 `model.train()`，恢复训练模式。

  本次训练设置 `eval_iter=1`，每次只用一个批次估算损失。这样速度快，但训练集经过随机打乱，不同评估点可能取到难度不同的批次，因此曲线会有小幅波动。

* `generate_and_print_sample` 在每个 epoch 后生成 50 个 token，用于直观看模型是否进步：

  ```python
  def generate_and_print_sample(model, tokenizer, device, start_context):
      model.eval()

      # 位置嵌入表的长度就是模型支持的上下文长度
      context_size = model.pos_emb.weight.shape[0]
      encoded = text_to_token_ids(start_context, tokenizer).to(device)

      with torch.no_grad():
          token_ids = generate_text_simple(
              model=model,
              idx=encoded,
              max_new_tokens=50,
              context_size=context_size,
          )

      decoded_text = token_ids_to_text(token_ids, tokenizer)
      print(decoded_text.replace("\n", " "))

      model.train()
  ```

  损失提供数值指标，生成样本用于观察文本是否从无意义输出逐渐变得连贯。

#### 启动训练

* 使用 AdamW 训练随机初始化的 GPT 模型：

  ```python
  print("训练LLM开始...")

  torch.manual_seed(123)
  model = GPTModel(GPT_CONFIG_124M)

  device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
  model.to(device)

  optimizer = torch.optim.AdamW(
      model.parameters(),
      lr=0.0004,
      weight_decay=0.1,
  )

  num_epochs = 10
  train_losses, val_losses, tokens_seen = train_model_simple(
      model=model,
      train_loader=train_loader,
      val_loader=val_loader,
      optimizer=optimizer,
      device=device,
      num_epochs=num_epochs,
      eval_freq=5,
      eval_iter=1,
      start_context="Every effort moves you",
      tokenizer=tokenizer,
  )

  print("训练LLM结束...")
  ```

  AdamW 在 Adam 的基础上改进了权重衰减方式。`lr=0.0004` 是学习率，`weight_decay=0.1` 用于抑制权重过度增大。

  训练集每个 epoch 有 9 个批次，训练 10 个 epoch，共更新参数 90 次。`eval_freq=5` 表示每 5 个 step 评估一次，因此记录 18 组损失；每个 epoch 结束生成一次样本，共生成 10 次。

* 控制台输出节选：

  ```text
  Ep 1 (Step 000000): Train loss 9.954, Val loss 9.948
  Ep 1 (Step 000005): Train loss 8.298, Val loss 8.292
  Every effort moves you      ,        ,          ,  , , , ...

  Ep 3 (Step 000020): Train loss 5.913, Val loss 6.687
  Ep 3 (Step 000025): Train loss 5.685, Val loss 6.598
  Every effort moves you Wedding Wedding Wedding ...

  Ep 6 (Step 000045): Train loss 4.647, Val loss 6.464
  Ep 6 (Step 000050): Train loss 3.195, Val loss 6.490
  Every effort moves you know. " to "Oh, I said, in the ...

  Ep 9 (Step 000075): Train loss 1.445, Val loss 6.486
  Ep 9 (Step 000080): Train loss 1.007, Val loss 6.527
  Every effort moves you know where her " to a cheap genius ...

  Ep 10 (Step 000085): Train loss 1.188, Val loss 6.568
  Every effort moves you know where her husband, a cheap genius-- ...
  ```

  生成文本的变化大致为：标点重复 → 单词重复和乱码 → 出现常见短语 → 形成较完整的句子。

  训练损失从约 `9.954` 降到 `1.188`，说明模型越来越熟悉训练数据。验证损失降到约 `6.4` 后不再明显改善，训练与验证损失的差距持续扩大，说明模型开始过拟合这个小数据集，后期生成内容可能直接记住训练文本。

  step 80 的训练损失为 `1.007`，step 85 回升到 `1.188`，不代表整体训练退化。`eval_iter=1` 只抽取一个经过打乱的训练批次，不同批次的损失存在波动。

#### 学习率预热

> 阅读资料：[附录 D.1：学习率预热](https://skindhu.github.io/Build-A-Large-Language-Model-CN/#/./cn-Book/%E9%99%84%E5%BD%95D.%E7%BB%99%E8%AE%AD%E7%BB%83%E5%BE%AA%E7%8E%AF%E6%B7%BB%E5%8A%A0%E9%AB%98%E7%BA%A7%E6%8A%80%E5%B7%A7?id=d1-%e5%ad%a6%e4%b9%a0%e7%8e%87%e9%a2%84%e7%83%ad)

学习率预热（learning rate warmup）是指：训练开始时先使用较小的学习率，再用若干个更新 step 将它逐渐增加到正常训练使用的峰值学习率。它主要用于降低训练初期出现大幅、破坏性参数更新的风险。

##### 学习率决定参数每次迈多大一步

模型参数的基本更新可以写成：

$$
\theta_{t+1}=\theta_t-\eta_t g_t
$$

其中：

- `θ_t`：更新前的模型参数。
- `g_t`：当前梯度。
- `η_t`：当前学习率。
- `θ_(t+1)`：更新后的模型参数。

假设某个参数 `θ_t = 0.5`，梯度 `g_t = 10`：

| 学习率 | 参数更新量 `η_t × g_t` | 更新后的参数 |
| ---: | ---: | ---: |
| `0.001` | `0.001 × 10 = 0.01` | `0.5 - 0.01 = 0.49` |
| `0.1` | `0.1 × 10 = 1` | `0.5 - 1 = -0.5` |

学习率从 `0.001` 增加到 `0.1` 后，参数不再是小幅调整，而是直接从 `0.5` 跨到 `-0.5`。所以学习率越大，单次参数更新通常越大；实际幅度还同时取决于梯度、优化器状态和参数尺度。

##### 为什么训练初期更需要小步走

LLM 刚开始训练时通常存在以下情况：

- 模型参数是随机初始化的，还没有形成稳定的数据表示。
- 第一个或前几个 mini-batch 不一定能代表整体数据分布。
- 某些参数的梯度可能很大，不同层的梯度尺度也可能相差很多。
- AdamW 的一阶、二阶动量从零开始，初期统计只来自少量批次。

AdamW 虽然带有偏差修正，但前几个 step 的动量估计仍建立在很少的样本上。此时的梯度可以理解为：模型还没有站稳，就根据少量数据给出了一个粗糙方向。

如果马上使用较大的学习率，相当于方向还没判断准就先迈一大步，可能导致损失突然增大、激活异常、梯度爆炸甚至出现 `NaN`。预热则是先小步更新，等表示和优化器状态逐渐稳定后，再提高速度。

##### 线性预热

附录 D.1 使用线性预热。设初始学习率为 `η_init`、峰值学习率为 `η_peak`，预热步数为 `N_w`：

预热阶段（0 ≤ t < `N_w`）：

$$
\eta_t=\eta_{init}+\frac{t}{N_w}(\eta_{peak}-\eta_{init})
$$

预热结束后（t ≥ `N_w`）：

$$
\eta_t=\eta_{peak}
$$

因此每一步的增量为：

$$
\Delta\eta=\frac{\eta_{peak}-\eta_{init}}{N_w}
$$

在当前代码中，`step=0` 使用 `initial_lr`，到达 `warmup_steps` 后使用峰值学习率。优化器创建时配置的 `lr` 就是峰值：

```python
peak_lr = 4e-4
optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=peak_lr,
    weight_decay=0.1,
)
```

预热步数一般按总更新步数的比例计算。原文给出的经验区间是 `0.1%～20%`，示例使用 `20%`：

```python
num_epochs = 10
total_steps = len(train_loader) * num_epochs
warmup_ratio = 0.2
warmup_steps = max(1, int(warmup_ratio * total_steps))
```

这个比例是经验值，不是固定规则。数据量、batch size、模型规模和峰值学习率变化后，都应重新观察损失和梯度。若不需要预热，直接设置 `warmup_steps=0`。

##### 训练模块中的实现

[`training.py`](./code/llm_from_scratch/training.py) 新增了 `linear_warmup_lr`：

```python
def linear_warmup_lr(
    step,
    *,
    warmup_steps,
    initial_lr,
    peak_lr,
):
    if warmup_steps == 0 or step >= warmup_steps:
        return peak_lr

    progress = step / warmup_steps
    return initial_lr + progress * (peak_lr - initial_lr)
```

`train_causal_lm` 新增两个保持向后兼容的关键字参数：

```python
train_losses, val_losses, tokens_seen = train_causal_lm(
    model=model,
    train_loader=train_loader,
    val_loader=val_loader,
    optimizer=optimizer,
    device=device,
    num_epochs=num_epochs,
    eval_freq=5,
    eval_iter=1,
    start_context="Every effort moves you",
    tokenizer=tokenizer,
    warmup_steps=warmup_steps,
    initial_lr=1e-5,
)
```

- `warmup_steps=0`：关闭预热，行为与原训练循环一致。
- `warmup_steps>0`：把优化器中每个参数组原本的 `lr` 当作各自的峰值，从 `initial_lr` 线性升高。
- `initial_lr` 必须非负且不能大于峰值学习率。

学习率必须在本 step 的 `optimizer.step()` 之前写入参数组：

```python
for param_group, peak_lr in zip(optimizer.param_groups, peak_lrs):
    param_group["lr"] = linear_warmup_lr(
        global_step,
        warmup_steps=warmup_steps,
        initial_lr=initial_lr,
        peak_lr=peak_lr,
    )

optimizer.zero_grad(set_to_none=True)
loss = causal_lm_batch_loss(input_batch, target_batch, model, device)
loss.backward()
optimizer.step()
```

如果在 `optimizer.step()` 之后才修改，新的学习率只能作用于下一次更新，调度曲线会整体错开一个 step。

##### 预热能做什么，不能做什么

| 作用 | 说明 |
| --- | --- |
| 减小初期参数更新 | 避免不稳定梯度配合峰值学习率产生大跳跃 |
| 平滑进入正常训练 | 给模型表示和 AdamW 动量统计一个逐渐建立的过程 |
| 不能修复错误数据 | 数据异常、标签错误仍会产生错误梯度 |
| 不能完全替代梯度裁剪 | 预热控制学习率，梯度裁剪直接限制梯度范数 |
| 不负责训练后期减速 | 后期通常再配合余弦衰减或线性衰减 |

预热的核心不是“学习率越小越好”，而是把训练初期和正常训练阶段分开：开始时控制风险，稳定后仍要达到足够大的学习率，保证模型能够有效学习。

#### 余弦衰减

> 阅读资料：[附录 D.2：余弦衰减](https://skindhu.github.io/Build-A-Large-Language-Model-CN/#/./cn-Book/%E9%99%84%E5%BD%95D.%E7%BB%99%E8%AE%AD%E7%BB%83%E5%BE%AA%E7%8E%AF%E6%B7%BB%E5%8A%A0%E9%AB%98%E7%BA%A7%E6%8A%80%E5%B7%A7?id=d2-%e4%bd%99%e5%bc%a6%e8%a1%b0%e5%87%8f)

余弦衰减（cosine decay）用于在预热结束后逐渐降低学习率。训练前期需要较大的学习率快速学习，后期接近较低损失区域时则应减小更新步幅，降低参数在最优区域附近来回越过的风险。

完整的学习率变化分为两个阶段：

```text
warmup：       initial_lr → peak_lr
cosine decay： peak_lr    → min_lr
```

##### 从 progress 到学习率

预热结束后，先计算衰减阶段已经进行的比例：

$$
p=\frac{global\_step-warmup\_steps}
        {total\_training\_steps-warmup\_steps}
$$

代码对应为：

```python
progress = (
    (global_step - warmup_steps)
    / (total_training_steps - warmup_steps)
)
```

`progress` 表示预热结束后已经走完多少比例：刚结束预热时为 `0`，衰减阶段进行一半时约为 `0.5`，训练接近结束时约为 `1`。

然后用余弦函数生成衰减系数：

$$
c(p)=\frac{1+\cos(\pi p)}{2}
$$

| `progress` | `π × progress` | `cos(π × progress)` | `(1 + cos) / 2` |
| ---: | ---: | ---: | ---: |
| `0` | `0` | `1` | `1` |
| `0.5` | `π/2` | `0` | `0.5` |
| `1` | `π` | `-1` | `0` |

`cos(π × progress)` 本身会从 `1` 变到 `-1`，不能直接作为学习率或缩放系数。先加 `1` 再除以 `2`，就把范围从 `[-1, 1]` 映射成 `[0, 1]`，得到一个从 `1` 平滑下降到 `0` 的系数。

最终学习率为：

$$
lr=min\_lr+(peak\_lr-min\_lr)
   \frac{1+\cos(\pi\cdot progress)}{2}
$$

这里不是直接用余弦值当学习率，而是先用余弦函数生成衰减系数，再把学习率从 `peak_lr` 平滑映射到 `min_lr`：

- `(peak_lr - min_lr)` 是学习率可以衰减的范围。
- 余弦系数从 `1` 降到 `0`，使这部分从完整幅度降到 `0`。
- 最后加上 `min_lr`，保证目标下限不是 `0`。

假设 `peak_lr=1.0`、`min_lr=0.1`：

| `progress` | 余弦系数 | 学习率 |
| ---: | ---: | ---: |
| `0` | `1` | `0.1 + 0.9 × 1 = 1.0` |
| `0.5` | `0.5` | `0.1 + 0.9 × 0.5 = 0.55` |
| `1` | `0` | `0.1 + 0.9 × 0 = 0.1` |

##### `math.pi` 和三个特殊余弦值

`math.pi` 是 Python `math` 模块提供的圆周率 `π`：

```python
import math

print(math.pi)  # 3.141592653589793
```

Python 的三角函数使用弧度。`progress` 从 `0` 变到 `1` 时，`math.pi * progress` 会把它映射到 `0～π`，正好让余弦函数走半个周期：

| 弧度 | 角度 | 单位圆上的点 | `cos`，即横坐标 |
| ---: | ---: | ---: | ---: |
| `0` | `0°` | `(1, 0)` | `1` |
| `π/2` | `90°` | `(0, 1)` | `0` |
| `π` | `180°` | `(-1, 0)` | `-1` |

单位圆上角度为 `θ` 的点写成 `(cos θ, sin θ)`，因此 `cos θ` 就是该点的横坐标。点从圆的最右侧经过顶部走到最左侧，横坐标自然从 `1` 平滑变成 `0`，再变成 `-1`。

##### 训练模块中的实现

[`training.py`](./code/llm_from_scratch/training.py) 中的 `cosine_decay_lr` 负责预热后的学习率计算：

```python
def cosine_decay_lr(
    step,
    *,
    warmup_steps,
    total_training_steps,
    peak_lr,
    min_lr,
):
    progress = (step - warmup_steps) / (
        total_training_steps - warmup_steps
    )
    progress = min(progress, 1.0)
    cosine_factor = 0.5 * (
        1.0 + math.cos(math.pi * progress)
    )
    return min_lr + (peak_lr - min_lr) * cosine_factor
```

`progress` 被限制在最大值 `1`，因此即使传入超过训练终点的 step，学习率也会停在 `min_lr`，不会沿余弦曲线再次上升。

在训练循环中，通过 `min_lr` 开启余弦衰减：

```python
num_epochs = 10
total_training_steps = len(train_loader) * num_epochs
warmup_steps = max(1, int(0.2 * total_training_steps))

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=4e-4,  # peak_lr
    weight_decay=0.1,
)

train_losses, val_losses, tokens_seen = train_causal_lm(
    model=model,
    train_loader=train_loader,
    val_loader=val_loader,
    optimizer=optimizer,
    device=device,
    num_epochs=num_epochs,
    eval_freq=5,
    eval_iter=1,
    start_context="Every effort moves you",
    tokenizer=tokenizer,
    warmup_steps=warmup_steps,
    initial_lr=1e-5,
    min_lr=1e-5,
)
```

##### `train_causal_lm` 的具体修改

原来的 `train_causal_lm` 只接收 `warmup_steps` 和 `initial_lr`：预热结束后，学习率一直保持为优化器中配置的峰值。为了支持余弦衰减，函数新增了一个可选参数：

```python
def train_causal_lm(
    ...,
    warmup_steps=0,
    initial_lr=0.0,
    min_lr=None,
):
```

`min_lr=None` 是兼容开关：不传它时，已有训练代码的行为不会改变；传入具体数值时，才会在预热后启用余弦衰减。

函数内部首先计算本次训练一共包含多少次参数更新：

```python
total_training_steps = len(train_loader) * num_epochs
```

例如 DataLoader 每个 epoch 有 9 个批次，训练 10 个 epoch，则总更新次数是 `9 × 10 = 90`。余弦衰减需要这个值来计算当前进度。

然后在真正修改学习率之前，保存优化器每个参数组最初配置的学习率：

```python
peak_lrs = [
    float(group["lr"])
    for group in optimizer.param_groups
]
```

这里不能在每一步直接把当前的 `param_group["lr"]` 当作峰值，因为该值会在预热和衰减过程中不断被改写。提前保存 `peak_lrs`，后续计算始终以原始峰值为基准；多个参数组拥有不同学习率时，也可以分别调度。

如果传入了 `min_lr`，训练开始前会调用一次 `cosine_decay_lr` 检查参数：

```python
for peak_lr in peak_lrs:
    cosine_decay_lr(
        warmup_steps,
        warmup_steps=warmup_steps,
        total_training_steps=total_training_steps,
        peak_lr=peak_lr,
        min_lr=min_lr,
    )
```

这次调用不是在更新优化器，而是提前确认 `total_training_steps > warmup_steps`、`min_lr >= 0` 且 `min_lr <= peak_lr`，避免训练进行到一半才发现调度参数错误。

进入每个 batch 后，先增加 `global_step`，再根据当前阶段选择学习率：

```python
global_step += 1

if warmup_steps > 0 and global_step < warmup_steps:
    # 阶段 1：从 initial_lr 线性升到 peak_lr
    lr = linear_warmup_lr(...)

elif min_lr is not None:
    # 阶段 2：从 peak_lr 余弦衰减到 min_lr
    lr = cosine_decay_lr(...)

elif warmup_steps > 0:
    # 只启用预热：预热结束后固定为 peak_lr
    lr = peak_lr
```

三个分支分别表示：

| 条件 | 当前阶段 | 学习率变化 |
| --- | --- | --- |
| `global_step < warmup_steps` | 线性预热 | `initial_lr → peak_lr` |
| 预热结束且设置了 `min_lr` | 余弦衰减 | `peak_lr → min_lr` |
| 预热结束但 `min_lr=None` | 固定阶段 | 保持 `peak_lr` |

计算完成后，把结果写入对应的优化器参数组：

```python
for param_group, peak_lr in zip(
    optimizer.param_groups,
    peak_lrs,
):
    param_group["lr"] = lr
```

实际代码把这段赋值分别写在预热和衰减分支内，因为不同参数组可能具有不同的 `peak_lr`，每组都需要独立计算自己的学习率。

学习率调度位于本 step 的反向传播和参数更新之前：

```text
global_step += 1
→ 计算当前学习率
→ 写入 optimizer.param_groups
→ zero_grad
→ forward / loss
→ backward
→ optimizer.step
```

这样计算出的学习率会立即作用于本次 `optimizer.step()`。如果把赋值放在 `optimizer.step()` 后面，它只能影响下一个 batch，整个调度会错开一个 step。

四种参数组合的行为如下：

| `warmup_steps` | `min_lr` | 实际行为 |
| ---: | --- | --- |
| `0` | `None` | 始终使用优化器原始学习率 |
| `> 0` | `None` | 线性预热，之后保持峰值 |
| `0` | 具体数值 | 从第一个 step 开始余弦衰减 |
| `> 0` | 具体数值 | 先线性预热，再余弦衰减 |

函数原来的返回值没有改变，仍然是训练损失、验证损失和评估时累计处理的 token 数，因此已有调用代码不需要修改：

```python
return train_losses, val_losses, tokens_seen_at_eval
```

附录中的 `global_step` 从 `0` 开始，而 `total_training_steps` 是更新次数，所以最后一次实际更新的 step 是 `total_training_steps - 1`。因此训练结束时的 `progress` 通常非常接近但略小于 `1`，学习率也会非常接近但略高于 `min_lr`；在 `step == total_training_steps` 时公式才精确得到 `min_lr`。这不改变调度逻辑，`min_lr` 仍是衰减的目标下限。

##### 我的理解

总的来说，学习率衰减就是一个从大到小的过程。训练进度从 `0` 走到 `1` 时，经过转换的余弦系数

$$
\frac{1+\cos(\pi\cdot progress)}{2}
$$

刚好会从 `1` 平滑下降到 `0`。用它乘以学习率的可变化范围 `peak_lr - min_lr`，再加上最终要衰减到的目标小值 `min_lr`，就能让整个学习率逐渐变小：

```text
当前学习率
= 最低学习率
+ 可衰减范围 × 当前剩余比例
```

需要注意，原始的 `cos(π × progress)` 是从 `1` 变到 `-1`；真正从 `1` 降到 `0` 的是经过 `(1 + cos) / 2` 转换后的系数。

一句话概括：余弦衰减不是把余弦值直接当成学习率，而是用半个余弦周期生成一个从 `1` 平滑下降到 `0` 的系数，再把学习率从 `peak_lr` 平滑降到 `min_lr`。

#### 绘制损失曲线

* 将 epoch、累计 token 数、训练损失和验证损失绘制在同一张图中：

  ```python
  import matplotlib.pyplot as plt


  def plot_losses(
      epochs_seen,
      tokens_seen,
      train_losses,
      val_losses,
      output_path="losses.png",
  ):
      fig, ax1 = plt.subplots(figsize=(5, 3))

      ax1.plot(epochs_seen, train_losses, label="Training loss")
      ax1.plot(
          epochs_seen,
          val_losses,
          linestyle="-.",
          label="Validation loss",
      )
      ax1.set_xlabel("Epochs")
      ax1.set_ylabel("Loss")
      ax1.legend(loc="upper right")

      # 上方横轴显示累计处理的 token 数
      ax2 = ax1.twiny()
      ax2.plot(tokens_seen, train_losses, alpha=0)
      ax2.set_xlabel("Tokens seen")

      fig.tight_layout()
      plt.savefig(output_path, dpi=300, bbox_inches="tight")
      plt.close(fig)


  # 将 18 个评估点近似映射到 0～10 个 epoch
  epochs_tensor = torch.linspace(
      0,
      num_epochs,
      len(train_losses),
  )

  plot_losses(
      epochs_tensor,
      tokens_seen,
      train_losses,
      val_losses,
      output_path="losses.png",
  )
  ```

  `epochs_tensor` 是按评估点数量生成的近似 epoch 进度；`tokens_seen` 保存每次评估时模型累计处理的 token 数。

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm47.png)

  曲线中训练损失持续下降，而验证损失在前期下降后停留在 6.4～6.6。两条曲线逐渐分离，是过拟合的典型表现。这里的主要原因是数据集很小，却被重复训练了 10 次。

### 通过解码策略控制生成结果的随机性

* 5.2 生成样本时使用的是贪心解码：每一步都选择 logit 最大的 token。同一个模型接收相同输入时，生成结果固定，也容易复述训练文本。本节改用概率采样，并通过温度和 Top-k 控制随机程度。

#### Temperature scaling

* 先用一个小词表观察贪心解码与概率采样的区别：

  ```python
  vocab = {
      "closer": 0,
      "every": 1,
      "effort": 2,
      "forward": 3,
      "inches": 4,
      "moves": 5,
      "pizza": 6,
      "toward": 7,
      "you": 8,
  }
  inverse_vocab = {token_id: token for token, token_id in vocab.items()}

  next_token_logits = torch.tensor(
      [4.51, 0.89, -1.90, 6.75, 1.63, -1.62, -1.89, 6.28, 1.79]
  )
  probas = torch.softmax(next_token_logits, dim=0)

  # 贪心解码：固定选择概率最高的 token
  greedy_token_id = torch.argmax(probas).item()
  print(inverse_vocab[greedy_token_id])

  # 概率采样：概率越高越容易被选中，但不保证一定被选中
  torch.manual_seed(123)
  sampled_token_id = torch.multinomial(probas, num_samples=1).item()
  print(inverse_vocab[sampled_token_id])
  ```

  ```text
  forward
  forward
  ```

  这次采样仍得到 `forward`，是因为它的概率最高。区别在于 `argmax` 每次都选它，而 `multinomial` 只是更容易选它，其他 token 仍有机会被选中。

* 温度缩放是在 Softmax 前将 logits 除以温度 $T$：

  $$
  p_i=\frac{\exp(z_i/T)}{\sum_j\exp(z_j/T)}
  $$

  ```python
  def softmax_with_temperature(logits, temperature):
      scaled_logits = logits / temperature
      return torch.softmax(scaled_logits, dim=0)
  ```

  - `T=1`：logits 不变。
  - `0<T<1`：logits 的差距被放大，分布更尖锐，结果更保守。
  - `T>1`：logits 的差距被缩小，分布更平缓，结果更多样，也更可能选中不通顺的低概率 token。

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm51.png)

  公式要求 $T>0$。后面的生成函数将 `temperature=0` 单独处理为贪心解码，不会执行除以 0。

#### Top-k 采样

* 温度升高后，整个词表中的低概率 token 都可能被采样。Top-k 先把候选范围限制为 logit 最大的 k 个 token，再从这些候选中采样：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm52.png)

* 以上面 9 个 logits 为例，只保留 Top-3：

  ```python
  top_k = 3
  top_logits, top_positions = torch.topk(next_token_logits, top_k)

  print("Top logits:", top_logits)
  print("Top positions:", top_positions)

  new_logits = torch.where(
      next_token_logits < top_logits[-1],
      torch.tensor(float("-inf")),
      next_token_logits,
  )
  topk_probas = torch.softmax(new_logits, dim=0)

  print(new_logits)
  print(topk_probas)
  ```

  ```text
  Top logits: tensor([6.7500, 6.2800, 4.5100])
  Top positions: tensor([3, 7, 0])
  tensor([4.5100,   -inf,   -inf, 6.7500,   -inf,   -inf,   -inf, 6.2800,   -inf])
  tensor([0.0615, 0.0000, 0.0000, 0.5775, 0.0000, 0.0000, 0.0000, 0.3610, 0.0000])
  ```

  `exp(-inf)=0`，所以被排除的 token 经过 Softmax 后概率为 0。Top-k 只负责筛选候选，最终仍由 `multinomial` 按概率随机选择。

#### 对文本生成函数进行调整

* 将两种策略加入文本生成函数，执行顺序为：`Top-k 筛选 → 温度缩放 → Softmax → 随机采样`。

  ```python
  def generate(
      model,
      idx,
      max_new_tokens,
      context_size,
      temperature=1.0,
      top_k=None,
      eos_id=None,
  ):
      for _ in range(max_new_tokens):
          # 只保留模型支持的最后 context_size 个 token
          idx_cond = idx[:, -context_size:]

          with torch.no_grad():
              logits = model(idx_cond)

          # 最后一个位置用于预测下一个 token
          logits = logits[:, -1, :]  # [batch_size, vocab_size]

          if top_k is not None:
              top_logits, _ = torch.topk(logits, top_k)

              # [batch_size] → [batch_size, 1]，与 logits 广播比较
              min_val = top_logits[:, -1].unsqueeze(-1)
              logits = torch.where(
                  logits < min_val,
                  torch.tensor(
                      float("-inf"),
                      device=logits.device,
                      dtype=logits.dtype,
                  ),
                  logits,
              )

          if temperature > 0.0:
              logits = logits / temperature
              probs = torch.softmax(
                  logits,
                  dim=-1,
              )  # [batch_size, vocab_size]
              idx_next = torch.multinomial(probs, num_samples=1)
          else:
              # temperature <= 0 时使用贪心解码
              idx_next = torch.argmax(logits, dim=-1, keepdim=True)

          if eos_id is not None and (idx_next == eos_id).all():
              break

          idx = torch.cat((idx, idx_next), dim=1)

      return idx
  ```

  `eos_id` 判断中的 `.all()` 表示整个批次都生成结束 token 时才停止。本例 `batch_size=1`，可以直接使用；多样本生成时通常还需要分别记录每个样本是否已经结束。

* 5.3 紧接 5.2 执行，应沿用已经训练完成的 `model`，不要重新创建随机模型。为接近原文的推理环境，将模型和输入统一放到 CPU：

  ```python
  inference_device = torch.device("cpu")
  model.to(inference_device)
  model.eval()

  tokenizer = tiktoken.get_encoding("gpt2")

  # 放在 generate 前，固定本次 multinomial 采样的随机状态
  torch.manual_seed(123)

  token_ids = generate(
      model=model,
      idx=text_to_token_ids(
          "Every effort moves you",
          tokenizer,
      ).to(inference_device),
      max_new_tokens=15,
      context_size=GPT_CONFIG_124M.context_length,
      top_k=25,
      temperature=1.4,
  )

  print("Output text:\n", token_ids_to_text(token_ids, tokenizer))
  ```

  `GPT_CONFIG_124M` 已从字典转换为 `GPTConfig` 对象，因此上下文长度要用属性访问：

  ```python
  GPT_CONFIG_124M.context_length
  ```

  只有原始字典 `GPT_CONFIG_124M_DICT` 才能写成：

  ```python
  GPT_CONFIG_124M_DICT["context_length"]
  ```

* 原文同样基于 5.2 训练完成的模型，参考输出为：

  ```text
  Every effort moves you stand to work on surprise, a one of us had gone with random-
  ```

  当前实践沿用 5.2 训练完成的 `model`，得到：

  ```text
  通过温度、top-k采样增加文本生成多样性：
  Output text:
   Every effort moves you his
  between the last but I must; ority. She been fellow
  ```

  这段文本已经出现了英文句式和上下文关联，说明模型经过 5.2 训练后学到了一部分训练文本的结构；不过数据集很小，训练时间也短，再加上随机采样，语法仍可能不完整。

  与原文不一致并不代表训练或生成代码有误，主要有以下原因：

  - 本地数据的字符数、token 数、上下文长度和训练损失均与原文不同，最终得到的模型权重自然不同。
  - `temperature=1.4` 会调用 `torch.multinomial` 随机采样；随机种子只能在模型权重、随机调用顺序和运行环境都一致时复现相同结果。
  - PyTorch 版本以及 CPU/CUDA 设备的计算差异，也可能改变采样结果。

  推理时仍需调用 `model.eval()` 关闭 Dropout，否则会引入额外随机性。这里的关键不是逐字复现原文，而是确认输出来自 5.2 训练后的模型，并能随温度和 Top-k 设置产生不同结果。

### 在 PyTorch 中加载和保存模型权重

#### 保存模型权重

* PyTorch 推荐保存模型的 `state_dict`：

  ```python
  torch.save(model.state_dict(), "model.pth")
  ```

  `state_dict` 是一个从层名称映射到参数和缓冲区的字典。它只保存模型状态，不包含 `GPTModel` 类和 `GPT_CONFIG_124M` 配置，因此加载时仍需用相同配置创建模型。

  `.pth` 是 PyTorch 常用的文件扩展名，并不是强制格式。

#### 加载模型用于推理

* 加载权重前先创建结构相同的模型，再把状态复制进去：

  ```python
  device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

  model = GPTModel(GPT_CONFIG_124M).to(device)
  model_state_dict = torch.load(
      "model.pth",
      map_location=device,
      weights_only=True,
  )
  model.load_state_dict(model_state_dict)
  model.eval()
  ```

  `map_location=device` 将检查点中的张量映射到当前设备，例如把在 CUDA 上保存的权重加载到 CPU。`weights_only=True` 只允许加载保存权重所需的受支持对象；检查点仍应来自可信来源。

  `load_state_dict` 要求模型结构和参数形状匹配，否则会报告缺失键、多余键或形状不一致。用于推理时调用 `model.eval()`，关闭 Dropout。

#### 保存完整训练检查点

* 只保存模型权重适合推理。如果以后还要继续训练，还应保存优化器状态：

  ```python
  print("保存模型权重开始...")

  torch.save(
      {
          "model_state_dict": model.state_dict(),
          "optimizer_state_dict": optimizer.state_dict(),
      },
      "model_and_optimizer.pth",
  )

  print("保存模型权重结束，文件名为model_and_optimizer.pth")
  ```

  AdamW 的 `state_dict` 不仅保存学习率、权重衰减等参数组设置，还保存每个模型参数的一阶和二阶动量。只恢复模型而重新初始化优化器，模型仍可继续训练，但 AdamW 的历史统计会从头积累，训练轨迹会发生变化。

#### 恢复并继续训练

* 真正验证检查点能否恢复，应重新创建模型和优化器，模拟新的 Python 会话：

  ```python
  print("加载保存的模型权重开始...")

  device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
  checkpoint = torch.load(
      "model_and_optimizer.pth",
      map_location=device,
      weights_only=True,
  )

  # state_dict 不包含模型结构，需要先重新创建模型
  model = GPTModel(GPT_CONFIG_124M).to(device)
  model.load_state_dict(checkpoint["model_state_dict"])

  # 优化器必须绑定新模型的参数，之后再恢复状态
  optimizer = torch.optim.AdamW(
      model.parameters(),
      lr=0.0004,
      weight_decay=0.1,
  )
  optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
  model.train()

  resume_epochs = 10
  train_losses, val_losses, tokens_seen = train_model_simple(
      model=model,
      train_loader=train_loader,
      val_loader=val_loader,
      optimizer=optimizer,
      device=device,
      num_epochs=resume_epochs,
      eval_freq=5,
      eval_iter=1,
      start_context="Every effort moves you",
      tokenizer=tokenizer,
  )

  # 这是恢复后的第二阶段曲线，横轴重新从 0 计数
  resume_epochs_tensor = torch.linspace(
      0,
      resume_epochs,
      len(train_losses),
  )
  plot_losses(
      resume_epochs_tensor,
      tokens_seen,
      train_losses,
      val_losses,
      output_path="re-losses.png",
  )

  print("加载保存的模型权重结束，文件名为re-losses.png")
  ```

  创建优化器时传入的初始超参数用于构造参数组；执行 `optimizer.load_state_dict` 后，会恢复检查点中保存的学习率、权重衰减和动量状态。

  如果保存后立即把检查点加载回原来的 `model` 和 `optimizer`，而两者尚未发生变化，加载前后实际上相同，不能证明新会话可以正确恢复。在同一进程中单纯追加训练，也可以直接再次调用 `train_model_simple`，无需先保存再加载。

* 控制台输出节选：

  ```text
  Ep 1 (Step 000000): Train loss 0.753, Val loss 6.601
  Ep 1 (Step 000005): Train loss 0.865, Val loss 6.654
  Every effort moves you know where her husband, lounging in a hooded chair,
  had lit a cigar and drawn the Russian deerhound's head between his knees. ...

  Ep 3 (Step 000025): Train loss 0.251, Val loss 6.905
  Ep 6 (Step 000050): Train loss 0.101, Val loss 7.261
  Ep 9 (Step 000080): Train loss 0.057, Val loss 7.442
  Ep 10 (Step 000085): Train loss 0.032, Val loss 7.498
  Every effort moves you know where her husband, lounging in a hooded chair,
  had lit a cigar and drawn the Russian deerhound's head between his knees. ...

  损失曲线已保存到：re-losses.png
  ```

  检查点是在 5.2 完成 10 个 epoch 后保存的，所以这里打印的 `Ep 1～10` 实际是第二阶段追加的 10 个 epoch。`train_model_simple` 每次调用都会将 `global_step` 和 `tokens_seen` 重新初始化，因此日志又从 `Ep 1 / Step 0` 开始。

  当前检查点只恢复模型和优化器，没有恢复已完成 epoch、全局 step、累计 token、损失历史及随机数状态。因此它可以继续训练，但不能做到和一次不间断的 20-epoch 训练逐步完全一致。

* 追加训练的损失曲线：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm53.png)

  横轴 `0～10` 只表示加载检查点后的第二阶段训练，不表示模型总共只训练了 10 个 epoch。

  训练损失从 `0.753` 降到 `0.032`，验证损失却从 `6.601` 升到 `7.498`，两者差距进一步扩大。生成文本反复出现 `her husband, lounging in a hooded chair...` 等训练集原句，说明模型继续记忆这个小数据集，过拟合更加严重。

  `eval_iter=1` 每次只计算一个批次，单个损失点会有波动；但训练损失接近 0、验证损失持续上升的整体趋势已经很明显，继续训练不能改善模型对未见文本的表现。

### 从 OpenAI 加载预训练权重

#### 下载并读取 GPT-2 权重

* 本章前面只在一篇短篇小说上训练模型。这里加载 OpenAI 已在大规模语料上预训练好的 GPT-2 权重，不再从随机参数开始训练。

  原书的加载方式依赖 TensorFlow 和 tqdm：

  ```text
  pip install "tensorflow>=2.15.0" "tqdm>=4.66"
  ```

* 下载 `gpt_download.py`，再调用其中的 `download_and_load_gpt2`：

  ```python
  from pathlib import Path
  import urllib.request


  script_url = (
      "https://raw.githubusercontent.com/rasbt/"
      "LLMs-from-scratch/main/ch05/"
      "01_main-chapter-code/gpt_download.py"
  )
  script_path = Path("gpt_download.py")

  if not script_path.exists():
      print("开始下载gpt_download.py...")
      urllib.request.urlretrieve(script_url, script_path)
      print("gpt_download.py下载完成")
  else:
      print("gpt_download.py已存在，跳过下载")

  from gpt_download import download_and_load_gpt2

  print("开始下载并读取GPT-2 124M权重...")
  settings, params = download_and_load_gpt2(
      model_size="124M",
      models_dir="gpt2",
  )
  print("GPT-2权重读取完成")
  print("Settings:", settings)
  print("Parameter dictionary keys:", params.keys())
  ```

  `urlretrieve` 只下载约 6 KB 的 Python 脚本，并不会得到模型权重。真正创建 `params` 的是 `download_and_load_gpt2`，它会下载 7 个文件，其中权重文件约 498 MB；首次执行需要等待，并会显示 tqdm 进度条。已经完整下载的文件会被复用。

  成功后可以看到：

  ```text
  Settings: {'n_vocab': 50257, 'n_ctx': 1024, 'n_embd': 768,
             'n_head': 12, 'n_layer': 12}
  Parameter dictionary keys: dict_keys(['blocks', 'b', 'g', 'wpe', 'wte'])
  ```

  `settings` 保存 GPT-2 的结构参数；`params` 保存从 TensorFlow 检查点读取的权重。

#### 调整 GPTModel 配置

* OpenAI 提供了四种 GPT-2 规模：

  ```python
  model_configs = {
      "gpt2-small (124M)": {
          "emb_dim": 768,
          "n_layers": 12,
          "n_heads": 12,
      },
      "gpt2-medium (355M)": {
          "emb_dim": 1024,
          "n_layers": 24,
          "n_heads": 16,
      },
      "gpt2-large (774M)": {
          "emb_dim": 1280,
          "n_layers": 36,
          "n_heads": 20,
      },
      "gpt2-xl (1558M)": {
          "emb_dim": 1600,
          "n_layers": 48,
          "n_heads": 25,
      },
  }
  ```

  ![图 5.17：不同规模的 GPT-2 使用相同架构，只调整嵌入维度、层数和注意力头数](https://raw.githubusercontent.com/skindhu/Build-A-Large-Language-Model-CN/main/Image/chapter5/figure5.17.png)

* 本次加载 GPT-2 small。OpenAI 权重使用 1024-token 上下文，并且 Q、K、V 投影包含偏置，所以要覆盖这两项配置：

  ```python
  model_name = "gpt2-small (124M)"

  NEW_CONFIG_DICT = GPT_CONFIG_124M_DICT.copy()
  NEW_CONFIG_DICT.update(model_configs[model_name])
  NEW_CONFIG_DICT.update(
      {
          "context_length": 1024,
          "qkv_bias": True,
      }
  )

  # GPTModel 接收 GPTConfig 对象，而不是原始字典
  NEW_CONFIG = GPTConfig(**NEW_CONFIG_DICT)
  gpt = GPTModel(NEW_CONFIG)
  gpt.eval()
  ```

  这里不能直接把 `NEW_CONFIG_DICT` 传给当前实现的 `GPTModel`，因为模型通过 `.vocab_size`、`.context_length` 等属性读取配置。

#### 将 OpenAI 权重映射到 GPTModel

* `assign` 先检查形状，再把 OpenAI 权重转换为可训练参数：

  ```python
  import numpy as np


  def assign(left, right):
      if left.shape != right.shape:
          raise ValueError(
              f"Shape mismatch. Left: {left.shape}, Right: {right.shape}"
          )

      return torch.nn.Parameter(torch.tensor(right))
  ```

  形状检查很重要：即使配置、转置方向或层映射只错一处，也不能正确加载权重。

* OpenAI 和当前 `GPTModel` 的主要名称对应关系：

  | OpenAI 参数 | GPTModel 参数 | 处理方式 |
  | --- | --- | --- |
  | `wpe` | `pos_emb.weight` | 直接复制位置嵌入 |
  | `wte` | `tok_emb.weight`、`out_head.weight` | 复制 token 嵌入和输出层权重 |
  | `c_attn` | `W_query`、`W_key`、`W_value` | 沿最后一维三等分，权重转置 |
  | `attn.c_proj` | `att.out_proj` | 权重转置，偏置直接复制 |
  | `mlp.c_fc`、`mlp.c_proj` | 前馈网络两个线性层 | 权重转置，偏置直接复制 |
  | `ln_1`、`ln_2` | `norm1`、`norm2` | `g/b` 对应 `scale/shift` |
  | 顶层 `g/b` | `final_norm.scale/shift` | 直接复制最终归一化参数 |

  TensorFlow 线性层权重的维度顺序与 PyTorch `Linear.weight` 相反，因此注意力输出投影和前馈网络等权重需要 `.T` 转置；偏置是一维张量，不需要转置。

* 完整映射函数：

  ```python
  def load_weights_into_gpt(gpt, params):
      gpt.pos_emb.weight = assign(gpt.pos_emb.weight, params["wpe"])
      gpt.tok_emb.weight = assign(gpt.tok_emb.weight, params["wte"])

      for block_idx in range(len(params["blocks"])):
          openai_block = params["blocks"][block_idx]
          gpt_block = gpt.trf_blocks[block_idx]

          # OpenAI 把 Q、K、V 放在同一个 c_attn 张量中
          q_w, k_w, v_w = np.split(
              openai_block["attn"]["c_attn"]["w"],
              3,
              axis=-1,
          )
          gpt_block.att.W_query.weight = assign(
              gpt_block.att.W_query.weight,
              q_w.T,
          )
          gpt_block.att.W_key.weight = assign(
              gpt_block.att.W_key.weight,
              k_w.T,
          )
          gpt_block.att.W_value.weight = assign(
              gpt_block.att.W_value.weight,
              v_w.T,
          )

          q_b, k_b, v_b = np.split(
              openai_block["attn"]["c_attn"]["b"],
              3,
              axis=-1,
          )
          gpt_block.att.W_query.bias = assign(
              gpt_block.att.W_query.bias,
              q_b,
          )
          gpt_block.att.W_key.bias = assign(
              gpt_block.att.W_key.bias,
              k_b,
          )
          gpt_block.att.W_value.bias = assign(
              gpt_block.att.W_value.bias,
              v_b,
          )

          gpt_block.att.out_proj.weight = assign(
              gpt_block.att.out_proj.weight,
              openai_block["attn"]["c_proj"]["w"].T,
          )
          gpt_block.att.out_proj.bias = assign(
              gpt_block.att.out_proj.bias,
              openai_block["attn"]["c_proj"]["b"],
          )

          gpt_block.ff.layers[0].weight = assign(
              gpt_block.ff.layers[0].weight,
              openai_block["mlp"]["c_fc"]["w"].T,
          )
          gpt_block.ff.layers[0].bias = assign(
              gpt_block.ff.layers[0].bias,
              openai_block["mlp"]["c_fc"]["b"],
          )
          gpt_block.ff.layers[2].weight = assign(
              gpt_block.ff.layers[2].weight,
              openai_block["mlp"]["c_proj"]["w"].T,
          )
          gpt_block.ff.layers[2].bias = assign(
              gpt_block.ff.layers[2].bias,
              openai_block["mlp"]["c_proj"]["b"],
          )

          gpt_block.norm1.scale = assign(
              gpt_block.norm1.scale,
              openai_block["ln_1"]["g"],
          )
          gpt_block.norm1.shift = assign(
              gpt_block.norm1.shift,
              openai_block["ln_1"]["b"],
          )
          gpt_block.norm2.scale = assign(
              gpt_block.norm2.scale,
              openai_block["ln_2"]["g"],
          )
          gpt_block.norm2.shift = assign(
              gpt_block.norm2.shift,
              openai_block["ln_2"]["b"],
          )

      gpt.final_norm.scale = assign(gpt.final_norm.scale, params["g"])
      gpt.final_norm.shift = assign(gpt.final_norm.shift, params["b"])
      gpt.out_head.weight = assign(gpt.out_head.weight, params["wte"])
  ```

  `gpt.out_head.weight` 也使用 `wte`，对应 GPT-2 的 token 嵌入与输出层权重设计。所有参数先在 CPU 上完成替换，再统一把模型移动到推理设备。

#### 加载权重并生成文本

* 完成映射后进行推理：

  ```python
  print("加载gpt2-small (124M)权重，推理生成文本：")

  load_weights_into_gpt(gpt, params)

  device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
  gpt.to(device)
  gpt.eval()

  torch.manual_seed(123)
  token_ids = generate(
      model=gpt,
      idx=text_to_token_ids(
          "Every effort moves you",
          tokenizer,
      ).to(device),
      max_new_tokens=25,
      context_size=NEW_CONFIG.context_length,
      top_k=50,
      temperature=1.5,
  )

  print("Output text:\n", token_ids_to_text(token_ids, tokenizer))
  ```

  模型和输入 token 必须在同一设备。由于 `NEW_CONFIG` 是 `GPTConfig` 对象，上下文长度使用 `NEW_CONFIG.context_length`，不能再使用字典下标。

* 原文的参考输出为：

  ```text
  Every effort moves you toward finding an ideal new way to practice something!
  What makes us want to be on top of that?
  ```

  这比在小型《The Verdict》数据集上训练的模型更连贯。这里使用 `temperature=1.5` 和 Top-k 随机采样，即使权重加载正确，也不要求逐字得到相同文本。

#### 实践结果与分析

* 修正后的完整代码运行成功，控制台输出节选：

  ```text
  加载gpt2-small (124M)权重，推理生成文本：
  开始下载gpt_download.py...
  gpt_download.py下载完成：/mnt/data/llm-gpt2/gpt_download.py
  开始导入gpt_download.py...
  gpt_download.py导入完成
  开始下载并读取GPT-2 124M权重，首次运行需要下载约500 MB...

  checkpoint: 100%|██████████| 77.0/77.0
  encoder.json: 100%|██████████| 1.04M/1.04M
  hparams.json: 100%|██████████| 90.0/90.0
  model.ckpt.data-00000-of-00001: 100%|██████████| 498M/498M [12:38]
  model.ckpt.index: 100%|██████████| 5.21k/5.21k
  model.ckpt.meta: 100%|██████████| 471k/471k
  vocab.bpe: 100%|██████████| 456k/456k

  GPT-2权重读取完成
  Settings: {'n_vocab': 50257, 'n_ctx': 1024, 'n_embd': 768,
             'n_head': 12, 'n_layer': 12}
  Parameter dictionary keys: dict_keys(['blocks', 'b', 'g', 'wpe', 'wte'])
  开始创建GPTModel...
  GPTModel创建完成
  开始映射OpenAI权重到GPTModel...
  权重映射完成
  推理设备： cuda
  开始生成文本...
  Output text:
   Every effort moves you as far as the hand can go until the end of your turn
  unless something interrupts your control flow. As you may observe I
  ```

  程序之前看起来“卡住”，实际耗时主要来自 498 MB 权重文件的下载：本次用了约 12 分 38 秒。加入阶段日志后，可以区分脚本下载、TensorFlow 权重读取、参数映射和文本生成，而不是只看到第一行后一直等待。

  `settings` 和 `params` 的内容符合 GPT-2 small，模型也在 CUDA 上生成了连贯文本，说明模型配置、权重映射和输入设备已经正确衔接。再次运行时，完整下载的权重文件会被复用，不需要重新下载 498 MB。

  实践输出与原文参考文本不同是正常的。`temperature=1.5` 和 `top_k=50` 使用随机采样；即使设置相同随机种子，CPU/CUDA 设备和运行环境不同也可能产生另一条合理文本。
