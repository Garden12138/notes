# 《Build a Large Language Model From Scratch》实践代码

本目录把七章笔记中的代码整理成一套可复用实现。算法和训练参数仍以书中实践为基准，主要调整了文件职责、命名、重复定义和导入关系。

## 目录

```text
code/
├── llm_from_scratch/
│   ├── config.py          # GPTConfig 与 GPT-2 规格
│   ├── data.py            # 分词、滑动窗口和语言模型 DataLoader
│   ├── attention.py       # 因果多头注意力
│   ├── model.py           # LayerNorm、GELU、TransformerBlock、GPTModel
│   ├── generation.py      # 编解码、贪心/温度/Top-k/EOS 生成
│   ├── training.py        # 损失、评估、线性预热、余弦衰减与训练
│   ├── checkpoint.py      # 模型权重与训练检查点
│   ├── openai_weights.py  # OpenAI GPT-2 权重下载与映射
│   ├── classification.py  # 短信分类数据、损失、训练与推理
│   ├── instruction.py     # 指令数据、动态批处理与回答导出
│   └── ollama_eval.py     # 可选的本地 LLM 自动评分
├── examples/              # 按章节组装的可执行实践入口
├── tests/                 # 不下载大模型的轻量测试
├── pyproject.toml
└── requirements.txt
```

依赖方向保持单向：

```text
data → attention → model → generation/training/checkpoint/openai_weights
                                      ├→ classification
                                      └→ instruction → ollama_eval（可选）
```

第 6、7 章复用同一个 GPT 核心，不再复制模型、生成和损失代码。

## 安装

建议先安装基础依赖和测试工具：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
```

需要运行 OpenAI GPT-2 权重下载与映射时，再安装 TensorFlow：

```bash
python -m pip install -e '.[openai-weights]'
```

## 运行章节实践

在 `code/` 目录执行：

```bash
python examples/chapter02_text_data.py /path/to/the-verdict.txt
python examples/chapter03_attention.py
python examples/chapter04_gpt_model.py
python examples/chapter05_pretraining.py --text-file /path/to/the-verdict.txt
python examples/chapter05_openai_weights.py
python examples/chapter06_classification.py
python examples/chapter07_instruction_tuning.py
```

第 1 章用于建立 LLM 的整体概念，没有独立的 Python 实践入口；代码主线从第 2 章的数据处理开始。

`the-verdict.txt` 不在本目录重复保存；运行第 2、5 章示例时传入你从原书下载的本地文件路径。

从第 5 章保存的模型与优化器检查点继续训练：

```bash
python examples/chapter05_pretraining.py \
  --text-file /path/to/the-verdict.txt \
  --resume-checkpoint model_and_optimizer.pth
```

第 5～7 章会下载数据或 GPT-2 权重并执行训练，耗时与显存需求远高于前三个示例。所有下载、训练和保存操作都在 `main()` 中，导入模块不会自动启动任务。

Ollama 自动评分属于第 7 章未实践部分，不在默认入口中执行。需要时先启动 Ollama，再单独调用 `llm_from_scratch.ollama_eval`。

## 命名整理

核心公开 API 使用能够直接表达任务的名称：

| 笔记中的名称 | 整理后的名称 |
| --- | --- |
| `GPTDatasetV1` | `GPTDataset` |
| `create_dataloader_v1` | `create_text_dataloader` |
| `calc_loss_batch`（语言模型） | `causal_lm_batch_loss` |
| `calc_loss_loader`（语言模型） | `causal_lm_loader_loss` |
| `train_model_simple` | `train_causal_lm` |
| `calc_loss_batch`（分类） | `classification_batch_loss` |
| `calc_loss_loader`（分类） | `classification_loader_loss` |
| `SpamDataset` | `SpamDataset`（语义已经明确） |
| `classify_review` | `classify_message` |
| `format_input` | `format_instruction_prompt` |
| `format_data` | `format_instruction_example` |
| `custom_collate_fn` | `collate_instruction_batch` |
| `assign` | `assign_parameter` |

`GPTDatasetV1`、`create_dataloader_v1` 和 `generate_text_simple` 作为书中代码的兼容入口保留；新代码优先使用规范名称。

模型内部仍保留书中的 `tok_emb`、`pos_emb`、`trf_blocks`、`W_query`、`W_key`、`W_value` 等属性名。它们不仅是命名风格问题，也是 OpenAI GPT-2 权重映射的路径，直接改名会使现有映射和检查点失效。

## 验证

轻量测试使用很小的词表、嵌入维度和层数，不下载 GPT-2 权重：

```bash
python -m pytest
```

也可以只检查所有 Python 文件是否能通过语法编译：

```bash
python -m compileall llm_from_scratch examples tests
```

真实 GPT-2 权重下载、完整预训练、分类微调、指令微调和 Ollama 评分属于手动集成测试，不放进默认测试套件。
