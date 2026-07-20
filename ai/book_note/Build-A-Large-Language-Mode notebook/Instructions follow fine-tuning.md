## 指令遵循微调

### 指令遵循微调简介

* 预训练只教模型预测下一个 token。模型可以续写文本，却不一定能理解“改写句子”“回答问题”等任务要求。监督式指令微调（Supervised Fine-Tuning，SFT）继续使用下一个 token 预测目标，但训练文本改成统一的“指令、可选输入、参考回答”格式。

  ![指令微调的输入和目标回答](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm62.png)

* 本章流程：

  ```text
  指令数据 → 提示词格式化 → 分词与动态填充 → 加载预训练模型
          → 监督微调 → 生成测试集回答 → 人工或 LLM 评估
  ```

  第 6 章的分类微调只输出固定类别；指令微调仍然生成任意长度的文本，因此损失需要覆盖回答中的多个 token。

### 为监督指令微调准备数据集

* 下载包含 `1100` 条记录的 JSON 数据集。每条记录有三个字段：

  * `instruction`：要完成的任务；
  * `input`：完成任务所需的补充内容，可以为空；
  * `output`：期望模型生成的参考回答。

  ```python
  import json
  import os
  import urllib.request


  def download_and_load_file(file_path, url):
      if not os.path.exists(file_path):
          with urllib.request.urlopen(url) as response:
              text_data = response.read().decode("utf-8")
          with open(file_path, "w", encoding="utf-8") as file:
              file.write(text_data)

      with open(file_path, "r", encoding="utf-8") as file:
          return json.load(file)


  file_path = "instruction-data.json"
  url = (
      "https://raw.githubusercontent.com/rasbt/"
      "LLMs-from-scratch/main/ch07/01_main-chapter-code/"
      "instruction-data.json"
  )

  data = download_and_load_file(file_path, url)
  print("Number of entries:", len(data))
  print("Example entry:\n", data[50])
  ```

  ```console
  Number of entries: 1100
  Example entry:
  {'instruction': 'Identify the correct spelling of the following word.',
   'input': 'Ocassion',
   'output': "The correct spelling is 'Occasion.'"}
  ```

* 指令数据必须使用固定的提示词模板。本章采用 Alpaca 风格；`input` 为空时省略 `### Input`，但始终保留 `### Instruction` 和 `### Response`：

  ![Alpaca 与 Phi-3 的提示词格式](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm63.png)

  ```python
  def format_input(entry):
      instruction_text = (
          "Below is an instruction that describes a task. "
          "Write a response that appropriately completes the request."
          f"\n\n### Instruction:\n{entry['instruction']}"
      )
      input_text = (
          f"\n\n### Input:\n{entry['input']}"
          if entry["input"]
          else ""
      )
      return instruction_text + input_text


  def format_data(entry):
      desired_response = f"\n\n### Response:\n{entry['output']}"
      return format_input(entry) + desired_response


  print(format_data(data[50]))
  ```

  ```text
  Below is an instruction that describes a task. Write a response that appropriately completes the request.

  ### Instruction:
  Identify the correct spelling of the following word.

  ### Input:
  Ocassion

  ### Response:
  The correct spelling is 'Occasion.'
  ```

  训练和推理必须使用同一模板，否则模型在推理时看到的是训练中没有学过的输入分布。

* 按 `85% / 5% / 10%` 划分训练集、验证集和测试集：

  ```python
  train_portion = int(len(data) * 0.85)
  test_portion = int(len(data) * 0.10)
  val_portion = len(data) - train_portion - test_portion

  train_data = data[:train_portion]
  test_data = data[train_portion:train_portion + test_portion]
  val_data = data[train_portion + test_portion:]

  print("Training set length:", len(train_data))
  print("Validation set length:", len(val_data))
  print("Test set length:", len(test_data))
  ```

  ```console
  Training set length: 935
  Validation set length: 55
  Test set length: 110
  ```

### 将数据组织成训练批次

* `InstructionDataset` 在初始化时完成格式化和分词，`__getitem__` 返回一条完整的 token ID 序列：

  ```python
  import torch
  from torch.utils.data import Dataset


  class InstructionDataset(Dataset):
      def __init__(self, data, tokenizer):
          self.data = data
          self.encoded_texts = [
              tokenizer.encode(format_data(entry))
              for entry in data
          ]

      def __getitem__(self, index):
          return self.encoded_texts[index]

      def __len__(self):
          return len(self.data)
  ```

* 不把整个数据集一次性填充到相同长度，而是在每个批次内以最长样本为准。这样不同批次可以具有不同的序列长度，减少无意义的填充和计算：

  ![按批次动态填充序列](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm64.png)

* 输入和目标仍然错开一个 token。假设原序列为 `[0, 1, 2, 3, 4]`，先在末尾追加 `<|endoftext|>`，再分别删除末尾和开头：

  ```text
  完整序列：[0, 1, 2, 3, 4, 50256]
  inputs：  [0, 1, 2, 3, 4]
  targets： [1, 2, 3, 4, 50256]
  ```

  ![输入 token 与目标 token 错开一个位置](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm65.png)

  每个输入位置负责预测右侧的下一个 token。目标中保留第一个 `50256`，让模型学习回答结束后应生成 `<|endoftext|>`。

* 同一批次内，较短样本会出现多个填充 token。除了第一个结束 token，其余填充位置在 `targets` 中改成 `-100`：

  ![保留首个结束 token 并屏蔽额外填充位置](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm66.png)

  PyTorch 的 `cross_entropy` 默认使用 `ignore_index=-100`，这些位置不参与平均损失，避免模型把大量精力用于预测填充 token。

* 完整的批处理函数：

  ```python
  def custom_collate_fn(
      batch,
      pad_token_id=50256,
      ignore_index=-100,
      allowed_max_length=None,
      device="cpu",
  ):
      # 多预留一个结束 token，再生成错开一位的 inputs 和 targets
      batch_max_length = max(len(item) + 1 for item in batch)
      inputs_lst, targets_lst = [], []

      for item in batch:
          new_item = item.copy()
          new_item.append(pad_token_id)
          padded = new_item + [pad_token_id] * (
              batch_max_length - len(new_item)
          )

          inputs = torch.tensor(padded[:-1], dtype=torch.long)
          targets = torch.tensor(padded[1:], dtype=torch.long)

          # 保留第一个结束 token，忽略后续填充位置
          pad_indices = torch.nonzero(
              targets == pad_token_id,
              as_tuple=True,
          )[0]
          if pad_indices.numel() > 1:
              targets[pad_indices[1:]] = ignore_index

          if allowed_max_length is not None:
              inputs = inputs[:allowed_max_length]
              targets = targets[:allowed_max_length]

          inputs_lst.append(inputs)
          targets_lst.append(targets)

      inputs_tensor = torch.stack(inputs_lst).to(device)
      targets_tensor = torch.stack(targets_lst).to(device)
      return inputs_tensor, targets_tensor
  ```

* 使用三个短序列检查输入、目标、填充和掩码的对应关系：

  ```python
  batch = (
      [0, 1, 2, 3, 4],
      [5, 6],
      [7, 8, 9],
  )

  inputs, targets = custom_collate_fn(batch)
  print(inputs)
  print(targets)
  ```

  ```console
  tensor([[    0,     1,     2,     3,     4],
          [    5,     6, 50256, 50256, 50256],
          [    7,     8,     9, 50256, 50256]])
  tensor([[    1,     2,     3,     4, 50256],
          [    6, 50256,  -100,  -100,  -100],
          [    8,     9, 50256,  -100,  -100]])
  ```

  第二条序列的第一个目标是 `6`，随后保留一个 `50256` 作为结束标记，剩余三个填充位置改成 `-100`。

* 本章没有屏蔽指令和输入部分，因此模型会对“提示词 + 回答”的所有有效 token 计算损失。另一种做法是把 `### Response` 之前的目标也设为 `-100`，让损失只关注回答；两种方法的效果需要结合数据集实验判断。

### 为指令数据集创建数据加载器

* 使用 `partial` 固定批处理函数的设备和最大上下文长度。`allowed_max_length=1024` 与 GPT-2 的位置嵌入长度一致：

  ```python
  from functools import partial

  import tiktoken
  from torch.utils.data import DataLoader

  device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
  tokenizer = tiktoken.get_encoding("gpt2")

  customized_collate_fn = partial(
      custom_collate_fn,
      device=device,
      allowed_max_length=1024,
  )
  ```

* 创建三个 DataLoader：

  ```python
  batch_size = 8
  num_workers = 0
  torch.manual_seed(123)

  train_dataset = InstructionDataset(train_data, tokenizer)
  train_loader = DataLoader(
      train_dataset,
      batch_size=batch_size,
      collate_fn=customized_collate_fn,
      shuffle=True,
      drop_last=True,
      num_workers=num_workers,
  )

  val_dataset = InstructionDataset(val_data, tokenizer)
  val_loader = DataLoader(
      val_dataset,
      batch_size=batch_size,
      collate_fn=customized_collate_fn,
      shuffle=False,
      drop_last=False,
      num_workers=num_workers,
  )

  test_dataset = InstructionDataset(test_data, tokenizer)
  test_loader = DataLoader(
      test_dataset,
      batch_size=batch_size,
      collate_fn=customized_collate_fn,
      shuffle=False,
      drop_last=False,
      num_workers=num_workers,
  )

  print(len(train_loader), len(val_loader), len(test_loader))
  ```

  ```console
  116 7 14
  ```

  训练集有 935 条数据，`drop_last=True` 后每轮使用 `116 × 8 = 928` 条；验证集最后一批有 7 条，测试集最后一批有 6 条。

* 动态填充使不同批次的第二维不同，但同一批次的 inputs 和 targets 始终同形：

  ```text
  Train loader（节选）：
  torch.Size([8, 61]) torch.Size([8, 61])
  torch.Size([8, 76]) torch.Size([8, 76])
  torch.Size([8, 73]) torch.Size([8, 73])

  Validation loader（最后一批）：
  torch.Size([7, 59]) torch.Size([7, 59])

  Test loader（最后一批）：
  torch.Size([6, 76]) torch.Size([6, 76])
  ```

  `calc_loss_batch` 会把 logits 和 targets 展平。标签为 `-100` 的位置被交叉熵忽略，所以第 5 章的损失函数和训练循环可以直接复用。

### 加载预训练的 LLM

* 指令微调使用 GPT-2 medium（355M）。它的容量大于前一章的 124M 模型，更适合学习不同类型的指令；对应权重文件约为 `1.42 GB`：

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

  CHOOSE_MODEL = "gpt2-medium (355M)"

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
  BASE_CONFIG = GPTConfig(**base_config_dict)

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
  ```

  配置字典只需要合并一次模型规模参数。由于当前 `GPTModel` 接收 `GPTConfig` 对象，后续读取上下文长度应写成 `BASE_CONFIG.context_length`。

* 微调前先让模型处理验证集第一条指令：

  ```python
  torch.manual_seed(123)
  input_text = format_input(val_data[0])

  token_ids = generate_text_simple(
      model=model,
      idx=text_to_token_ids(input_text, tokenizer),
      max_new_tokens=35,
      context_size=BASE_CONFIG.context_length,
  )
  generated_text = token_ids_to_text(token_ids, tokenizer)
  response_text = generated_text[len(input_text):].strip()
  print(response_text)
  ```

  ```text
  The chef cooks the meal every day.

  ### Instruction:

  Convert the active sentence to passive: 'The chef cooks the
  ```

  预训练模型只是延续文本，没有把主动语态正确改成被动语态，说明它尚未学会当前提示格式和指令遵循任务。

### 指令微调 LLM

* 将模型移到计算设备，并先计算 5 个批次的基线损失：

  ```python
  from five_pretraining_on_unlabeled_datasets_model_eval import calc_loss_loader

  model.to(device)
  model.eval()

  torch.manual_seed(123)
  with torch.no_grad():
      train_loss = calc_loss_loader(
          train_loader,
          model,
          device,
          num_batches=5,
      )
      val_loss = calc_loss_loader(
          val_loader,
          model,
          device,
          num_batches=5,
      )

  print("Training loss:", train_loss)
  print("Validation loss:", val_loss)
  ```

  ```console
  Training loss: 3.8259091854095457
  Validation loss: 3.761933708190918
  ```

* 复用第 5 章的 `train_model_simple` 进行全参数微调。本章没有冻结 Transformer 层；AdamW 会更新 GPT-2 medium 的全部可训练参数：

  ```python
  import time

  from five_pretraining_on_unlabeled_datasets_llm_train import (
      train_model_simple,
  )

  start_time = time.time()
  torch.manual_seed(123)

  optimizer = torch.optim.AdamW(
      model.parameters(),
      lr=5e-5,
      weight_decay=0.1,
  )
  num_epochs = 2

  train_losses, val_losses, tokens_seen = train_model_simple(
      model,
      train_loader,
      val_loader,
      optimizer,
      device,
      num_epochs=num_epochs,
      eval_freq=5,
      eval_iter=5,
      start_context=format_input(val_data[0]),
      tokenizer=tokenizer,
  )

  execution_time_minutes = (time.time() - start_time) / 60
  print(f"Training completed in {execution_time_minutes:.2f} minutes.")
  ```

* 控制台日志较长，保留几个关键节点：

  ```console
  Ep 1 (Step 000000): Train loss 2.637, Val loss 2.626
  Ep 1 (Step 000005): Train loss 1.174, Val loss 1.102
  Ep 1 (Step 000050): Train loss 0.663, Val loss 0.783
  Ep 1 (Step 000115): Train loss 0.508, Val loss 0.663

  ### Response: The meal is prepared every day by the chef.<|endoftext|>...

  Ep 2 (Step 000120): Train loss 0.435, Val loss 0.672
  Ep 2 (Step 000195): Train loss 0.329, Val loss 0.635
  Ep 2 (Step 000210): Train loss 0.367, Val loss 0.630
  Ep 2 (Step 000230): Train loss 0.294, Val loss 0.656

  ### Response: The meal is cooked every day by the chef.<|endoftext|>...
  Training completed in 1.26 minutes.
  ```

  训练损失从约 `3.83` 降至 `0.29`，验证损失从约 `3.76` 降至 `0.63～0.66`，模型已经能正确完成验证样例。第二个 epoch 后半段训练损失继续下降，而验证损失大致持平并略有回升，继续增加 epoch 可能开始过拟合。

  ![指令微调的训练损失和验证损失](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm67.png)

* 训练样例在 `<|endoftext|>` 后仍出现下一段提示，是因为 `train_model_simple` 内部使用 `generate_text_simple`：它不会根据 EOS 提前停止，只会生成固定数量的 token。这不影响训练损失，但正式提取回答时应使用第 5 章实现的 `generate(..., eos_id=50256)`。

### 提取并保存响应

* 对 110 条测试指令逐条生成回答，并把结果写入每个字典的 `model_response` 字段。这里复用第 5 章支持 EOS 的 `generate`，生成结束 token 后立即停止：

  ```python
  import re

  from tqdm import tqdm

  # generate 为第 5.3 节实现的解码函数
  model.eval()
  torch.manual_seed(123)

  for index, entry in tqdm(
      enumerate(test_data),
      total=len(test_data),
  ):
      input_text = format_input(entry)
      input_ids = text_to_token_ids(input_text, tokenizer).to(device)

      token_ids = generate(
          model=model,
          idx=input_ids,
          max_new_tokens=256,
          context_size=BASE_CONFIG.context_length,
          temperature=0.0,
          eos_id=50256,
      )

      # 只解码输入之后新增的 token，避免按字符长度切片
      response_ids = token_ids[:, input_ids.shape[1]:]
      response_text = token_ids_to_text(
          response_ids,
          tokenizer,
      ).strip()
      test_data[index]["model_response"] = response_text

  with open(
      "instruction-data-with-response.json",
      "w",
      encoding="utf-8",
  ) as file:
      json.dump(test_data, file, indent=4, ensure_ascii=False)
  ```

  相比实践代码中的 `generated_text[len(input_text):]`，按 token 数量截取不依赖字符与 token 的对应关系；同时 `eos_id=50256` 避免把 EOS 后面的续写混入回答。

* 本地生成 110 条回答的耗时：

  ```console
  100%|██████████████████████████████████████████████████| 110/110 [11:23<00:00, 6.21s/it]
  ```

* 保存微调后的模型权重：

  ```python
  file_name = f"{re.sub(r'[ ()]', '', CHOOSE_MODEL)}-sft.pth"
  torch.save(model.state_dict(), file_name)
  print(f"Model saved as {file_name}")
  ```

  ```console
  Model saved as gpt2-medium355M-sft.pth
  ```

  `state_dict` 只保存参数。重新加载时，需要先创建相同配置的 GPT-2 medium，再加载权重：

  ```python
  state_dict = torch.load(
      "gpt2-medium355M-sft.pth",
      map_location=device,
      weights_only=True,
  )
  model.load_state_dict(state_dict)
  model.to(device)
  model.eval()
  ```

* 实践代码没有打印测试集中的具体回答，因此当前只能确认 110 条回答和模型权重已经成功保存。定性检查时可同时查看指令、参考回答和模型回答：

  ```python
  for entry in test_data[:3]:
      print(format_input(entry))
      print("\nCorrect response:")
      print(entry["output"])
      print("\nModel response:")
      print(entry["model_response"])
      print("-" * 40)
  ```

### 评估指令微调后的 LLM

* 指令回答通常存在多个合理写法，不能像垃圾短信分类那样只比较一个标签。常见评估方式包括：

  * 在问答或多项选择基准上计算客观分数；
  * 由人工比较回答的正确性、相关性和表达质量；
  * 使用能力更强的 LLM，根据参考回答给模型回答打分。

  ![使用另一个 LLM 评估模型回答](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm68.png)

* **本节 Ollama 评估未实践。** 以下只记录原文流程，不记录为本地运行结果：

  1. 安装并启动 Ollama，在另一个终端运行书中使用的 Llama 3 8B 指令模型。
  2. 通过本地 REST API 把“指令、参考回答、待评估回答”交给评估模型。
  3. 要求评估模型只返回 `0～100` 的整数，最后计算 110 条回答的平均分。

* 原文启动命令：

  ```bash
  ollama run llama3
  ```

  Ollama 只负责本地模型推理，不用于训练本章的 GPT-2。模型名称、下载体积和硬件需求可能随 Ollama 版本变化，真正实践时应以 Ollama 当前模型库为准。

* 原文通过流式 REST API 查询本地模型：

  ```python
  def query_model(
      prompt,
      model="llama3",
      url="http://localhost:11434/api/chat",
  ):
      data = {
          "model": model,
          "seed": 123,
          "temperature": 0,
          "messages": [
              {"role": "user", "content": prompt},
          ],
      }

      payload = json.dumps(data).encode("utf-8")
      request = urllib.request.Request(
          url,
          data=payload,
          method="POST",
      )
      request.add_header("Content-Type", "application/json")

      response_text = ""
      with urllib.request.urlopen(request) as response:
          while True:
              line = response.readline().decode("utf-8")
              if not line:
                  break
              response_json = json.loads(line)
              response_text += response_json["message"]["content"]

      return response_text
  ```

* 批量评分函数要求只返回整数，无法转换的结果跳过并提示：

  ```python
  def generate_model_scores(
      json_data,
      json_key,
      model="llama3",
  ):
      scores = []

      for entry in tqdm(json_data, desc="Scoring entries"):
          prompt = (
              f"Given the input `{format_input(entry)}` "
              f"and correct output `{entry['output']}`, "
              f"score the model response `{entry[json_key]}` "
              "on a scale from 0 to 100, where 100 is the best score. "
              "Respond with the integer number only."
          )
          score = query_model(prompt, model)

          try:
              scores.append(int(score))
          except ValueError:
              print(f"Could not convert score: {score}")

      return scores
  ```

  原文使用该流程得到 `110 / 110` 个分数，平均分为 `54.16`；这是书中的参考结果，不是本次实践结果。即使设置种子和 `temperature=0`，不同模型版本和运行环境也可能产生不同评分。LLM-as-a-judge 适合批量比较实验，但仍会受评估提示词、评估模型偏好和参考答案质量影响。

### 结语

* 本章完成了从基础 GPT-2 到指令模型的完整路径：

  ```text
  预训练 GPT-2 medium
      ↓
  1100 条 Alpaca 格式指令数据
      ↓
  动态填充、错位目标、屏蔽额外 PAD
      ↓
  2 个 epoch 全参数监督微调
      ↓
  导出 110 条测试回答和模型权重
      ↓
  人工评估或 LLM 自动评分
  ```

  ![从模型实现到指令微调的完整流程](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/ballm69.png)

* 关键不是修改 GPT 架构，而是把高质量的任务和回答组织成一致的文本格式，再继续执行下一个 token 预测。数据格式、回答质量和损失掩码方式会直接影响模型最终行为。
