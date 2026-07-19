## 用于分类任务的微调

### 不同类型的微调

* 常见的微调方式分为两类：

  * **指令微调**：使用“指令—回答”数据训练模型，使模型能够理解并完成多种自然语言任务。
  * **分类微调**：使用带类别标签的数据训练模型，使模型只能从预先定义的类别中选择结果。本章的目标是把 GPT-2 微调成二分类器，判断短信是 `spam` 还是 `not spam`。

  ![指令微调](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm54.png)

  ![分类微调](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm55.png)

* 分类模型的任务范围较窄，但所需标注数据和训练成本通常低于通用的指令微调模型。本章继续使用第 5 章加载的 GPT-2 预训练权重，只训练与分类任务关系最密切的部分参数。

### 准备数据集

* 使用 UCI 的 SMS Spam Collection 数据集。数据文件的每一行包含标签和短信正文，标签分为普通短信 `ham` 与垃圾短信 `spam`：

  ```python
  import os
  import urllib.request
  import zipfile
  from pathlib import Path

  import pandas as pd

  url = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"
  zip_path = "sms_spam_collection.zip"
  extracted_path = "sms_spam_collection"
  data_file_path = Path(extracted_path) / "SMSSpamCollection.tsv"


  def download_and_unzip_spam_data(
      url,
      zip_path,
      extracted_path,
      data_file_path,
  ):
      if data_file_path.exists():
          print(f"{data_file_path} already exists. Skipping download and extraction.")
          return

      with urllib.request.urlopen(url) as response:
          with open(zip_path, "wb") as out_file:
              out_file.write(response.read())

      with zipfile.ZipFile(zip_path, "r") as zip_ref:
          zip_ref.extractall(extracted_path)

      original_file_path = Path(extracted_path) / "SMSSpamCollection"
      os.rename(original_file_path, data_file_path)
      print(f"File downloaded and saved as {data_file_path}")


  download_and_unzip_spam_data(
      url,
      zip_path,
      extracted_path,
      data_file_path,
  )
  ```

  ```console
  File downloaded and saved as sms_spam_collection/SMSSpamCollection.tsv
  ```

* 原始数据中的普通短信远多于垃圾短信。如果直接训练，模型即使倾向于全部预测为普通短信，也可能得到看似较高的准确率。这里从普通短信中随机抽取与垃圾短信相同的数量，使两个类别各有 `747` 条数据：

  ```python
  df = pd.read_csv(
      data_file_path,
      sep="\t",
      header=None,
      names=["Label", "Text"],
  )


  def create_balanced_dataset(df):
      num_spam = df[df["Label"] == "spam"].shape[0]
      ham_subset = df[df["Label"] == "ham"].sample(
          num_spam,
          random_state=123,
      )
      return pd.concat([
          ham_subset,
          df[df["Label"] == "spam"],
      ])


  balanced_df = create_balanced_dataset(df)
  print(balanced_df["Label"].value_counts())

  # 交叉熵要求类别标签是整数索引
  balanced_df["Label"] = balanced_df["Label"].map({
      "ham": 0,
      "spam": 1,
  })
  ```

  ```console
  Label
  ham     747
  spam    747
  Name: count, dtype: int64
  ```

* 固定随机种子打乱数据，再按 `70% / 10% / 20%` 划分训练集、验证集和测试集。测试集不参与训练或超参数选择；本实践只用它记录微调前的基线和微调后的最终结果：

  ```python
  def random_split(df, train_frac, validation_frac):
      df = df.sample(frac=1, random_state=123).reset_index(drop=True)

      train_end = int(len(df) * train_frac)
      validation_end = train_end + int(len(df) * validation_frac)

      train_df = df.iloc[:train_end]
      validation_df = df.iloc[train_end:validation_end]
      test_df = df.iloc[validation_end:]
      return train_df, validation_df, test_df


  train_df, validation_df, test_df = random_split(
      balanced_df,
      train_frac=0.7,
      validation_frac=0.1,
  )

  train_df.to_csv("train.csv", index=False)
  validation_df.to_csv("validation.csv", index=False)
  test_df.to_csv("test.csv", index=False)

  print(len(train_df), len(validation_df), len(test_df))
  ```

  ```console
  1045 149 300
  ```

### 创建数据加载器

* 一批短信的长度必须一致。先用 GPT-2 分词器编码文本，再按训练集中最长文本的长度截断或填充；填充 token 使用 GPT-2 的 `<|endoftext|>`，其 token ID 为 `50256`：

  ![将短信填充到相同长度](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm56.png)

  ```python
  import tiktoken
  import torch
  from torch.utils.data import DataLoader, Dataset

  tokenizer = tiktoken.get_encoding("gpt2")


  class SpamDataset(Dataset):
      def __init__(
          self,
          csv_file,
          tokenizer,
          max_length=None,
          pad_token_id=50256,
      ):
          self.data = pd.read_csv(csv_file)
          self.encoded_texts = [
              tokenizer.encode(text)
              for text in self.data["Text"]
          ]

          if max_length is None:
              self.max_length = max(
                  len(encoded_text)
                  for encoded_text in self.encoded_texts
              )
          else:
              self.max_length = max_length
              self.encoded_texts = [
                  encoded_text[:self.max_length]
                  for encoded_text in self.encoded_texts
              ]

          self.encoded_texts = [
              encoded_text
              + [pad_token_id] * (self.max_length - len(encoded_text))
              for encoded_text in self.encoded_texts
          ]

      def __getitem__(self, index):
          encoded = self.encoded_texts[index]
          label = self.data.iloc[index]["Label"]
          return (
              torch.tensor(encoded, dtype=torch.long),
              torch.tensor(label, dtype=torch.long),
          )

      def __len__(self):
          return len(self.data)
  ```

* 训练集的最长文本包含 `120` 个 token。验证集和测试集必须沿用这个长度，不能分别计算自己的最大长度，否则三个 DataLoader 的输入规格会不一致：

  ```python
  train_dataset = SpamDataset(
      csv_file="train.csv",
      tokenizer=tokenizer,
      max_length=None,
  )
  val_dataset = SpamDataset(
      csv_file="validation.csv",
      tokenizer=tokenizer,
      max_length=train_dataset.max_length,
  )
  test_dataset = SpamDataset(
      csv_file="test.csv",
      tokenizer=tokenizer,
      max_length=train_dataset.max_length,
  )

  print("Train max length:", train_dataset.max_length)
  print("Validation max length:", val_dataset.max_length)
  print("Test max length:", test_dataset.max_length)
  ```

  ```console
  Train max length: 120
  Validation max length: 120
  Test max length: 120
  ```

* 创建 DataLoader。训练集需要打乱，并用 `drop_last=True` 丢弃不足 8 条的最后一个批次；验证集和测试集保留全部样本：

  ```python
  batch_size = 8
  num_workers = 0
  torch.manual_seed(123)

  train_loader = DataLoader(
      dataset=train_dataset,
      batch_size=batch_size,
      shuffle=True,
      num_workers=num_workers,
      drop_last=True,
  )
  val_loader = DataLoader(
      dataset=val_dataset,
      batch_size=batch_size,
      shuffle=False,
      num_workers=num_workers,
      drop_last=False,
  )
  test_loader = DataLoader(
      dataset=test_dataset,
      batch_size=batch_size,
      shuffle=False,
      num_workers=num_workers,
      drop_last=False,
  )

  print(f"{len(train_loader)} training batches")
  print(f"{len(val_loader)} validation batches")
  print(f"{len(test_loader)} test batches")

  input_batch, target_batch = next(iter(train_loader))
  print("Input batch dimensions:", input_batch.shape)
  print("Label batch dimensions:", target_batch.shape)
  ```

  ```console
  130 training batches
  19 validation batches
  38 test batches
  Input batch dimensions: torch.Size([8, 120])
  Label batch dimensions: torch.Size([8])
  ```

  每批输入的形状是 `[batch_size, num_tokens] = [8, 120]`，标签形状是 `[8]`，每条短信只有一个类别。训练集共有 `1045` 条数据，`drop_last=True` 后每个 epoch 实际使用 `130 × 8 = 1040` 条，剩余 5 条被丢弃。

### 使用预训练权重初始化模型

* 选择 GPT-2 small（124M）。加载 OpenAI 权重时必须使用 `qkv_bias=True`，并保持上下文长度、嵌入维度、注意力头数和 Transformer 层数与检查点一致：

  ```python
  from four_implement_a_GPT_model_for_text_generation_gpt_text_generation import (
      GPTConfig,
      GPTModel,
      generate_text_simple,
  )
  from five_pretraining_on_unlabeled_datasets_load_openai_model import (
      download_gpt_download_script,
      import_gpt_download,
      load_weights_into_gpt,
  )
  from five_pretraining_on_unlabeled_datasets_model_eval import (
      text_to_token_ids,
      token_ids_to_text,
  )

  CHOOSE_MODEL = "gpt2-small (124M)"

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

  base_config_dict = {
      "vocab_size": 50257,
      "context_length": 1024,
      "drop_rate": 0.0,
      "qkv_bias": True,
  }
  base_config_dict.update(model_configs[CHOOSE_MODEL])

  assert train_dataset.max_length <= base_config_dict["context_length"]

  # GPTModel 接收 GPTConfig 对象
  BASE_CONFIG = GPTConfig(**base_config_dict)
  ```

* 下载并映射 OpenAI GPT-2 124M 权重，然后先用普通文本生成验证加载结果：

  ```python
  model_size = CHOOSE_MODEL.split(" ")[-1].strip("()")

  script_path = download_gpt_download_script()
  download_and_load_gpt2 = import_gpt_download(script_path)
  settings, params = download_and_load_gpt2(
      model_size=model_size,
      models_dir="gpt2",
  )

  model = GPTModel(BASE_CONFIG)
  load_weights_into_gpt(model, params)
  model.eval()

  token_ids = generate_text_simple(
      model=model,
      idx=text_to_token_ids("Every effort moves you", tokenizer),
      max_new_tokens=15,
      context_size=BASE_CONFIG.context_length,
  )
  print(token_ids_to_text(token_ids, tokenizer))
  ```

  ```console
  Every effort moves you forward.

  The first step is to understand the importance of your work
  ```

* 直接要求基础 GPT-2 回答短信是否为垃圾短信，并不能得到分类结果：

  ```python
  text = (
      "Is the following text 'spam'? Answer with 'yes' or 'no':"
      " 'You are a winner you have been specially"
      " selected to receive $1000 cash or a $2000 award.'"
  )

  token_ids = generate_text_simple(
      model=model,
      idx=text_to_token_ids(text, tokenizer),
      max_new_tokens=23,
      context_size=BASE_CONFIG.context_length,
  )
  print(token_ids_to_text(token_ids, tokenizer))
  ```

  ```console
  Is the following text 'spam'? Answer with 'yes' or 'no': 'You are a winner
  you have been specially selected to receive $1000 cash or a $2000 award.'

  The following text 'spam'? Answer with 'yes' or 'no': 'You are a winner
  ```

  GPT-2 的预训练目标是预测下一个 token，而不是遵循分类指令。因此它只是续写提示文本；这不表示权重加载失败，后面需要用带标签的数据完成分类微调。

### 添加分类头

* 先冻结全部预训练参数，再把原来输出 `50257` 个词表 logits 的输出层替换为输出两个类别 logits 的线性层：

  ![将语言模型输出头替换为分类头](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm57.png)

  ```python
  for param in model.parameters():
      param.requires_grad = False

  torch.manual_seed(123)
  num_classes = 2
  model.out_head = torch.nn.Linear(
      in_features=BASE_CONFIG.emb_dim,
      out_features=num_classes,
  )
  ```

* 新分类头是随机初始化的。为了让模型能针对短信任务调整高层特征，同时减少训练量，只解冻最后一个 Transformer Block、最终 LayerNorm 和分类头：

  ![分类微调期间参与训练的模型层](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm58.png)

  ```python
  for param in model.trf_blocks[-1].parameters():
      param.requires_grad = True

  for param in model.final_norm.parameters():
      param.requires_grad = True
  ```

  替换后的 `model.out_head` 默认 `requires_grad=True`，所以不需要再次解冻。前面的 Transformer Block 继续提供预训练得到的通用语言特征，最后一层负责把这些特征调整到垃圾短信分类任务上。

* 检查分类头的输出。4 个输入 token 分别产生 2 个类别 logits，因此输出形状是 `[1, 4, 2]`：

  ```python
  inputs = tokenizer.encode("Do you have time")
  inputs = torch.tensor(inputs, dtype=torch.long).unsqueeze(0)

  with torch.no_grad():
      outputs = model(inputs)

  print("Inputs:", inputs)
  print("Inputs dimensions:", inputs.shape)
  print("Outputs:\n", outputs)
  print("Outputs dimensions:", outputs.shape)
  print("Last output token:", outputs[:, -1, :])
  ```

  ```console
  Inputs: tensor([[5211,  345,  423,  640]])
  Inputs dimensions: torch.Size([1, 4])
  Outputs:
   tensor([[[-1.5854,  0.9904],
           [-3.7235,  7.4548],
           [-2.2661,  6.6049],
           [-3.5983,  3.9902]]])
  Outputs dimensions: torch.Size([1, 4, 2])
  Last output token: tensor([[-3.5983,  3.9902]])
  ```

* 只用最后一个输出位置进行分类。GPT 使用因果注意力，最后一个位置可以关注它之前的全部 token，因此其输出包含整条短信的上下文信息：

  ![使用最后一个输出位置进行分类](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm59.png)

  本实践把所有短信填充到 120 个 token，所以最后一个位置通常是填充 token。由于它位于原短信之后，仍能通过因果注意力读取前面的短信内容，并为整条短信提供固定位置的分类表示。

### 计算分类损失和准确率

* 最后位置的两个 logits 分别对应 `not spam` 和 `spam`。预测类别时可以直接对 logits 使用 `argmax`；Softmax 不会改变最大值所在的位置：

  ```python
  logits = outputs[:, -1, :]
  label = torch.argmax(logits, dim=-1)
  print("Class label:", label.item())
  ```

  ```console
  Class label: 1
  ```

  此时分类头仍是随机初始化的，所以这个结果没有实际分类意义。

* 准确率统计预测正确的短信数占总短信数的比例，适合直观评估结果，但 `argmax` 不可微，不能作为训练目标：

  ```python
  def calc_accuracy_loader(data_loader, model, device, num_batches=None):
      model.eval()
      correct_predictions = 0
      num_examples = 0

      if num_batches is None:
          num_batches = len(data_loader)
      else:
          num_batches = min(num_batches, len(data_loader))

      for batch_index, (input_batch, target_batch) in enumerate(data_loader):
          if batch_index >= num_batches:
              break

          input_batch = input_batch.to(device)
          target_batch = target_batch.to(device)

          with torch.no_grad():
              logits = model(input_batch)[:, -1, :]

          predicted_labels = torch.argmax(logits, dim=-1)
          num_examples += target_batch.shape[0]
          correct_predictions += (
              predicted_labels == target_batch
          ).sum().item()

      return correct_predictions / num_examples
  ```

* 训练使用交叉熵。对每条短信只取最后位置的 `[2]` 类别 logits，并与一个整数标签比较：

  ```python
  def calc_loss_batch(input_batch, target_batch, model, device):
      input_batch = input_batch.to(device)
      target_batch = target_batch.to(device)

      # [batch_size, 120, 2] -> [batch_size, 2]
      logits = model(input_batch)[:, -1, :]
      return torch.nn.functional.cross_entropy(logits, target_batch)


  def calc_loss_loader(data_loader, model, device, num_batches=None):
      if len(data_loader) == 0:
          return float("nan")

      if num_batches is None:
          num_batches = len(data_loader)
      else:
          num_batches = min(num_batches, len(data_loader))

      total_loss = 0.0
      for batch_index, (input_batch, target_batch) in enumerate(data_loader):
          if batch_index >= num_batches:
              break

          loss = calc_loss_batch(
              input_batch,
              target_batch,
              model,
              device,
          )
          total_loss += loss.item()

      return total_loss / num_batches
  ```

* 将模型和数据移到同一设备，在未训练前取少量批次建立基线：

  ```python
  device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
  model.to(device)

  torch.manual_seed(123)
  train_accuracy = calc_accuracy_loader(
      train_loader, model, device, num_batches=10
  )
  val_accuracy = calc_accuracy_loader(
      val_loader, model, device, num_batches=10
  )
  test_accuracy = calc_accuracy_loader(
      test_loader, model, device, num_batches=10
  )

  model.eval()
  with torch.no_grad():
      train_loss = calc_loss_loader(
          train_loader, model, device, num_batches=5
      )
      val_loss = calc_loss_loader(
          val_loader, model, device, num_batches=5
      )
      test_loss = calc_loss_loader(
          test_loader, model, device, num_batches=5
      )

  print(f"Training accuracy: {train_accuracy * 100:.2f}%")
  print(f"Validation accuracy: {val_accuracy * 100:.2f}%")
  print(f"Test accuracy: {test_accuracy * 100:.2f}%")
  print(f"Training loss: {train_loss:.3f}")
  print(f"Validation loss: {val_loss:.3f}")
  print(f"Test loss: {test_loss:.3f}")
  ```

  ```console
  Training accuracy: 46.25%
  Validation accuracy: 45.00%
  Test accuracy: 48.75%
  Training loss: 2.453
  Validation loss: 2.583
  Test loss: 2.322
  ```

  两类数据已经平衡，随机分类器的准确率约为 `50%`。当前结果接近随机猜测，符合分类头尚未训练的状态。

### 使用监督数据对模型进行微调

* 分类训练循环仍采用“清空梯度 → 前向计算损失 → 反向传播 → 更新参数”的顺序。与预训练的区别是：现在每条短信只有一个分类标签，损失只使用最后一个输出位置：

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


  def train_classifier_simple(
      model,
      train_loader,
      val_loader,
      optimizer,
      device,
      num_epochs,
      eval_freq,
      eval_iter,
  ):
      train_losses, val_losses = [], []
      train_accs, val_accs = [], []
      examples_seen, global_step = 0, -1

      for epoch in range(num_epochs):
          model.train()

          for input_batch, target_batch in train_loader:
              optimizer.zero_grad()
              loss = calc_loss_batch(
                  input_batch,
                  target_batch,
                  model,
                  device,
              )
              loss.backward()
              optimizer.step()

              examples_seen += input_batch.shape[0]
              global_step += 1

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
                  print(
                      f"Ep {epoch + 1} (Step {global_step:06d}): "
                      f"Train loss {train_loss:.3f}, "
                      f"Val loss {val_loss:.3f}"
                  )

          train_accuracy = calc_accuracy_loader(
              train_loader,
              model,
              device,
              num_batches=eval_iter,
          )
          val_accuracy = calc_accuracy_loader(
              val_loader,
              model,
              device,
              num_batches=eval_iter,
          )
          train_accs.append(train_accuracy)
          val_accs.append(val_accuracy)
          print(
              f"Training accuracy: {train_accuracy * 100:.2f}% | "
              f"Validation accuracy: {val_accuracy * 100:.2f}%"
          )

      return (
          train_losses,
          val_losses,
          train_accs,
          val_accs,
          examples_seen,
      )
  ```

  `global_step=-1` 使第一次参数更新编号为 step 0。`eval_iter=5` 表示训练过程中的损失和准确率只用 5 个批次快速估算，最终评估再遍历完整数据集。

* 使用 AdamW 训练 5 个 epoch，学习率为 `5e-5`，权重衰减为 `0.1`：

  ```python
  import time

  start_time = time.time()
  torch.manual_seed(123)

  optimizer = torch.optim.AdamW(
      model.parameters(),
      lr=5e-5,
      weight_decay=0.1,
  )
  num_epochs = 5

  (
      train_losses,
      val_losses,
      train_accs,
      val_accs,
      examples_seen,
  ) = train_classifier_simple(
      model,
      train_loader,
      val_loader,
      optimizer,
      device,
      num_epochs=num_epochs,
      eval_freq=50,
      eval_iter=5,
  )

  execution_time_minutes = (time.time() - start_time) / 60
  print(f"Training completed in {execution_time_minutes:.2f} minutes.")
  ```

  ```console
  Ep 1 (Step 000000): Train loss 2.153, Val loss 2.392
  Ep 1 (Step 000050): Train loss 0.617, Val loss 0.637
  Ep 1 (Step 000100): Train loss 0.523, Val loss 0.557
  Training accuracy: 70.00% | Validation accuracy: 72.50%

  Ep 2 (Step 000250): Train loss 0.409, Val loss 0.353
  Training accuracy: 82.50% | Validation accuracy: 85.00%

  Ep 3 (Step 000350): Train loss 0.340, Val loss 0.306
  Training accuracy: 90.00% | Validation accuracy: 90.00%

  Ep 4 (Step 000500): Train loss 0.222, Val loss 0.137
  Training accuracy: 100.00% | Validation accuracy: 97.50%

  Ep 5 (Step 000600): Train loss 0.083, Val loss 0.074
  Training accuracy: 100.00% | Validation accuracy: 97.50%
  Training completed in 0.38 minutes.
  ```

  每个 epoch 有 130 个训练批次，5 个 epoch 共执行 `650` 次参数更新，处理 `5200` 个样本位置。训练损失和验证损失同步下降，验证准确率没有明显回落，当前日志未显示严重过拟合。

* 原文的损失曲线与准确率曲线可以直观看出训练过程：

  ![分类微调的训练损失和验证损失](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm60.png)

  ![分类微调的训练准确率和验证准确率](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm61.png)

  训练日志中的每个损失点只使用 5 个批次，因此单点可能波动；判断模型效果时应结合完整验证集和测试集结果。

* 训练完成后遍历三个完整数据集：

  ```python
  train_accuracy = calc_accuracy_loader(train_loader, model, device)
  val_accuracy = calc_accuracy_loader(val_loader, model, device)
  test_accuracy = calc_accuracy_loader(test_loader, model, device)

  print(f"Training accuracy: {train_accuracy * 100:.2f}%")
  print(f"Validation accuracy: {val_accuracy * 100:.2f}%")
  print(f"Test accuracy: {test_accuracy * 100:.2f}%")
  ```

  ```console
  Training accuracy: 97.21%
  Validation accuracy: 97.32%
  Test accuracy: 95.67%
  ```

  测试准确率 `95.67%` 略低于训练集和验证集，但差距不大，说明模型已经学到能泛化到未见短信的分类特征。

### 将 LLM 用于垃圾短信分类

* 新短信必须使用与训练阶段相同的预处理：GPT-2 分词、截断到训练长度、用 token ID `50256` 填充，再读取最后位置的类别 logits：

  ```python
  def classify_review(
      text,
      model,
      tokenizer,
      device,
      max_length=None,
      pad_token_id=50256,
  ):
      model.eval()
      input_ids = tokenizer.encode(text)

      # pos_emb.weight: [context_length, emb_dim]
      supported_context_length = model.pos_emb.weight.shape[0]

      if max_length is None:
          max_length = supported_context_length
      max_length = min(max_length, supported_context_length)

      input_ids = input_ids[:max_length]
      input_ids += [pad_token_id] * (max_length - len(input_ids))
      input_tensor = torch.tensor(
          input_ids,
          dtype=torch.long,
          device=device,
      ).unsqueeze(0)

      with torch.no_grad():
          logits = model(input_tensor)[:, -1, :]

      predicted_label = torch.argmax(logits, dim=-1).item()
      return "spam" if predicted_label == 1 else "not spam"
  ```

  `model.pos_emb.weight` 的形状为 `[context_length, emb_dim]`，所以模型支持的上下文长度应读取 `shape[0]`。如果使用 `shape[1]`，得到的是嵌入维度 `768`，含义不对；本实践当前的 `max_length=120` 虽未触发越界，代码仍应修正。

* 测试一条垃圾短信和一条正常短信：

  ```python
  text_1 = (
      "You are a winner you have been specially"
      " selected to receive $1000 cash or a $2000 award."
  )
  print(classify_review(
      text_1,
      model,
      tokenizer,
      device,
      max_length=train_dataset.max_length,
  ))

  text_2 = (
      "Hey, just wanted to check if we're still on"
      " for dinner tonight? Let me know!"
  )
  print(classify_review(
      text_2,
      model,
      tokenizer,
      device,
      max_length=train_dataset.max_length,
  ))
  ```

  ```console
  spam
  not spam
  ```

* 保存分类器权重。重新加载时，必须先用相同的 GPT-2 配置和二分类头恢复模型结构，再载入 `state_dict`：

  ```python
  torch.save(model.state_dict(), "review_classifier.pth")

  model_state_dict = torch.load(
      "review_classifier.pth",
      map_location=device,
      weights_only=True,
  )
  model.load_state_dict(model_state_dict)
  model.to(device)
  model.eval()
  ```

  该文件只保存参数，不包含 `GPTModel`、`GPTConfig`、分词器和 `SpamDataset`。在新进程中使用时，需要先按本章代码创建模型并替换成 `Linear(768, 2)` 分类头，然后才能加载权重。
