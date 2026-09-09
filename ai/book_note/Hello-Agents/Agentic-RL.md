## Agentic-RL

> 阅读资料：[《Hello-Agents》第十一章 11.1：从 LLM 训练到 Agentic-RL](https://datawhalechina.github.io/hello-agents/#/./chapter11/%E7%AC%AC%E5%8D%81%E4%B8%80%E7%AB%A0%20Agentic-RL?id=_111-%e4%bb%8e-llm-%e8%ae%ad%e7%bb%83%e5%88%b0-agentic-rl)、[11.2：数据集与奖励函数](https://datawhalechina.github.io/hello-agents/#/./chapter11/%E7%AC%AC%E5%8D%81%E4%B8%80%E7%AB%A0%20Agentic-RL?id=_112-%e6%95%b0%e6%8d%ae%e9%9b%86%e4%b8%8e%e5%a5%96%e5%8a%b1%e5%87%bd%e6%95%b0)
>
> 本节先梳理预训练、SFT、RLHF/RLAIF 与 Agentic-RL 的关系，再按原文的四层结构补齐代码。SFT 和单轮 GRPO 是训练基础，还不等同于完整的多步 Agentic-RL。

### 从语言模型训练到 Agentic-RL

#### 一个数学题如何变成强化学习问题

以“Janet 的鸭子每天产 16 个蛋，她早餐吃 3 个、用 4 个烤松饼，其余每个卖 2 美元，一天收入多少”为例，模型需要完成可验证的推理：

1. 可出售鸭蛋：$16-3-4=9$。
2. 当天收入：$9\times2=18$。

映射到强化学习后，各元素含义如下：

| 强化学习元素 | 数学推理任务中的对应内容 |
| --- | --- |
| Agent | 负责推理和作答的语言模型 |
| Environment | 题目、答案校验器以及可能使用的工具 |
| State | 原始问题和截至当前的推理、观察历史 |
| Action | 下一步推理文本、工具调用或最终回答 |
| Reward | 答案正确、步骤有效、工具使用合理等反馈 |

监督学习会告诉模型“正确答案应该怎么写”，强化学习则让模型尝试不同路径，再根据结果调整策略。两者不是替代关系：通常先用 SFT 建立基本能力和输出格式，再用奖励信号优化行为。

~~~mermaid
flowchart LR
    S["状态 s_t<br/>问题 + 已有推理 + 观察"] --> P["策略 πθ"]
    P --> A["动作 a_t<br/>生成文本或调用工具"]
    A --> E["环境执行与验证"]
    E --> O["新观察 o_{t+1}"]
    E --> R["奖励 r_t"]
    O --> NS["新状态 s_{t+1}"]
    NS --> P
    R --> U["更新策略参数 θ"]
~~~

#### 为什么只做监督微调还不够

SFT 依赖人工或强模型给出的标准答案，优点是稳定，局限也很明确：

- 能力上限受到示范数据质量限制，模型主要学习已有解法。
- 训练目标是模仿答案，不会主动探索更好的策略。
- 单条回答的似然不能直接表达“最终任务是否完成”。
- 工具调用、失败恢复和长程规划需要多步反馈，仅靠输入—输出对很难描述。

Agentic-RL 将 LLM 放进持续交互的环境中。模型不仅生成文字，还可能选择工具、读取观察、修正计划，训练目标由“一次回答像不像标准答案”扩展为“一整条轨迹能否完成任务”。

### LLM 的训练链路

#### 预训练：学习语言分布

自回归预训练根据前文预测下一个 Token：

$$
\mathcal{L}_{\text{pretrain}}
= -\sum_{t=1}^{T}\log P_{\theta}(x_t\mid x_{<t})
$$

它让模型获得语言、知识和模式识别能力，但没有直接教模型遵循指令，也没有定义任务完成标准。

#### SFT：学习如何回答

监督微调使用指令与标准回答 $(x_i,y_i)$：

$$
\mathcal{L}_{\text{SFT}}
= -\sum_{i=1}^{N}\log P_{\theta}(y_i\mid x_i)
$$

在本章数学任务中，SFT 数据同时保留推理过程与最终答案，使模型先学会逐步作答的基本格式。

#### RLHF 与 RLAIF：用偏好调整行为

RLHF 先收集人类对多个回答的偏好，再训练奖励模型。若 $y_w$ 优于 $y_l$，奖励模型常用成对排序目标：

$$
\mathcal{L}_{\text{RM}}
= -\mathbb{E}\left[
\log \sigma\left(r_{\phi}(x,y_w)-r_{\phi}(x,y_l)\right)
\right]
$$

随后使用 PPO 等算法提高期望奖励，同时通过 KL 约束避免策略偏离参考模型过远：

$$
J_{\text{PPO}}
= \mathbb{E}[r_{\phi}(x,y)]
- \beta D_{\text{KL}}(\pi_{\theta}\parallel\pi_{\text{ref}})
$$

RLAIF 将偏好标注者换成 AI，流程仍是“生成候选—比较质量—形成奖励—优化策略”。它能降低人工标注成本，但评价质量受评审模型和评价准则影响。

~~~mermaid
flowchart LR
    P["预训练<br/>预测下一个 Token"] --> S["SFT<br/>学习指令与回答格式"]
    S --> R["RLHF / RLAIF<br/>学习人类或 AI 偏好"]
    R --> A["Agentic-RL<br/>优化多步交互轨迹"]
~~~

这条图表示训练目标逐步扩展，不代表每个系统都必须重新完成全部阶段。实际开发通常从一个已经预训练、已经指令微调的模型继续训练。

### PBRFT 与 Agentic-RL 的区别

原文将偏好强化微调记作 PBRFT（Preference-Based Reinforcement Fine-Tuning）。它仍以一次生成作为基本单元，是从 RLHF 到 Agentic-RL 的中间形态。

| 维度 | PBRFT | Agentic-RL |
| --- | --- | --- |
| 交互步数 | 单轮生成 | 多轮决策与环境交互 |
| 状态 | 主要是初始 Prompt | Prompt、历史动作、工具结果和环境状态 |
| 动作 | 一次文本生成 | 文本、工具调用、计划修改等 |
| 状态转移 | 生成结束即终止 | 环境执行动作后产生新观察 |
| 奖励 | 多为最终答案奖励 | 可包含过程奖励与终局奖励 |
| 优化目标 | 单个回答的期望奖励 | 整条轨迹的长期累积回报 |

Agentic-RL 可以建模为马尔可夫决策过程：

$$
\mathcal{M}=(\mathcal{S},\mathcal{A},P,R,\gamma)
$$

其中 $\mathcal{S}$ 是状态空间，$\mathcal{A}$ 是动作空间，$P$ 是环境的状态转移，$R$ 是奖励函数，$\gamma$ 是折扣因子。第 $t$ 步状态可以写成：

$$
s_t=(x,o_1,o_2,\ldots,o_t)
$$

一条轨迹为 $\tau=(s_0,a_0,r_0,\ldots,s_T)$，其折扣回报是：

$$
G(\tau)=\sum_{t=0}^{T}\gamma^t r(s_t,a_t)
$$

训练目标不再只评价最终文本，而是最大化轨迹的期望回报：

$$
J_{\text{Agentic}}(\theta)
=\mathbb{E}_{\tau\sim\pi_{\theta}}[G(\tau)]
$$

例如“分析代码仓库质量并生成报告”可以分配过程奖励：获取仓库 $+0.1$、读取文件 $+0.1$、完成分析 $+0.2$、提交报告 $+0.6$。奖励总和是 $1.0$，但真正重要的是每一步都会改变后续可用信息；顺序错误、调用失败和无效重复也应有明确反馈。

#### Agentic-RL 要训练什么能力

| 能力 | 奖励与环境需要观察的行为 |
| --- | --- |
| 推理 | 中间步骤是否有效，结论能否验证 |
| 工具使用 | 工具选择、参数和调用时机是否正确 |
| 记忆 | 是否写入重要信息，并在需要时准确检索 |
| 规划 | 子任务顺序是否合理，失败后能否调整 |
| 自我改进 | 是否能利用反馈修正下一次行为 |
| 感知 | 是否正确读取网页、文件或其他环境观察 |

最终奖励最容易定义，却可能造成信用分配困难：任务失败时，不清楚是哪一步导致。过程奖励能缓解这个问题，但设计不当会让模型钻规则漏洞。因此奖励函数本身也需要测试和审计。

### HelloAgents 的强化学习模块

原文使用 [TRL](https://huggingface.co/docs/trl/index) 承担训练循环，以 [Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B) 作为轻量实践模型，并通过 LoRA 降低可训练参数量。模块分成四层：

~~~mermaid
flowchart TB
    TOOL["统一工具层<br/>RLTrainingTool"]
    TRAINER["训练器层<br/>SFTTrainerWrapper / GRPOTrainerWrapper"]
    REWARD["奖励层<br/>Accuracy / LengthPenalty / Step"]
    DATA["数据层<br/>GSM8KDataset<br/>SFT / RL 格式"]
    HF["TRL + Transformers + PEFT"]

    TOOL --> TRAINER
    TOOL --> REWARD
    TOOL --> DATA
    TRAINER --> REWARD
    TRAINER --> DATA
    TRAINER --> HF
~~~

| 层 | 本次实现 | 职责 |
| --- | --- | --- |
| 数据层 | [datasets.py](./code/HelloAgents/hello_agents/rl/datasets.py) | 加载 GSM8K，拆分推理与答案，生成 SFT/RL 格式 |
| 奖励层 | [rewards.py](./code/HelloAgents/hello_agents/rl/rewards.py) | 提取数值答案，计算准确率、长度惩罚和步骤奖励 |
| 训练器层 | [trainers.py](./code/HelloAgents/hello_agents/rl/trainers.py) | 配置 TRL 的 SFTTrainer、GRPOTrainer 和 LoRA |
| 工具层 | [rl_training_tool.py](./code/HelloAgents/hello_agents/tools/builtin/rl_training_tool.py) | 统一 train、load_dataset、create_reward、evaluate 四个动作 |

### 数据集与奖励函数

#### 为什么选择 GSM8K

[GSM8K](https://huggingface.co/datasets/openai/gsm8k) 包含 7,473 条训练数据和 1,319 条测试数据，题目是需要 2—8 步推理的小学数学应用题。它适合用来学习强化微调，原因不是题目简单，而是训练闭环清楚：

- 最终答案唯一，可以由程序自动校验。
- 解题过程包含多个中间步骤，便于观察推理格式。
- 不需要再训练一个主观评分模型，奖励噪声较小。

典型答案会保存推理过程，并用 #### 分隔最终结果：

~~~text
Natalia sold 48/2 = 24 clips in May.
Natalia sold 48+24 = 72 clips altogether.
#### 72
~~~

数据处理使用最后一个 #### 分隔符：前半部分作为推理过程，后半部分作为 ground_truth。这样即使推理文本中出现额外标记，也不会错误截断最终答案。

~~~mermaid
flowchart LR
    RAW["原始数据<br/>question + answer"] --> SPLIT["拆分推理过程与最终答案"]
    SPLIT --> SFT["SFT 格式<br/>prompt + completion + text"]
    SPLIT --> RL["RL 格式<br/>prompt + ground_truth<br/>question + full_answer"]
    TOKENIZER["模型 Tokenizer<br/>apply_chat_template"] --> SFT
    TOKENIZER --> RL
    SFT --> ST["监督微调"]
    RL --> GT["生成候选 + 奖励计算"]
~~~

#### 数据格式为什么分成两种

同一条 GSM8K 数据在两个阶段承担的职责不同：

~~~python
# SFT：标准推理过程直接进入训练文本
{
    "prompt": "<|im_start|>user ... <|im_start|>assistant",
    "completion": "... Final Answer: 72<|im_end|>",
    "text": "prompt 与 completion 拼接后的完整文本",
}

# GRPO：只给模型问题，ground_truth 留给奖励函数
{
    "prompt": "<|im_start|>user ... <|im_start|>assistant",
    "ground_truth": "72",
    "question": "原始问题",
    "full_answer": "数据集中的完整参考解法",
}
~~~

两种格式的 Prompt 都要通过当前模型的 `apply_chat_template` 生成，不能手写并假设所有模型都使用 Qwen 的特殊标记。SFT 的 Completion 还要补上 `eos_token`，模型才能学到回答终止位置。

如果把参考答案混进 GRPO 的 Prompt，就会泄漏标签；如果 SFT 只保留最终数字，模型又学不到推理格式。完整转换和字段校验见 [`datasets.py`](./code/HelloAgents/hello_agents/rl/datasets.py)。

#### 奖励函数必须能处理训练器的真实输入

MathRewardFunction 依次执行：

1. 将纯字符串或对话消息统一为文本。
2. 从 Final Answer、####、中文“答案”等格式中提取结果。
3. 清理千位分隔符、货币符号和百分号。
4. 对数值使用容差比较，无法数值化时才使用字符串比较。
5. 返回与 completions 等长的奖励列表。

准确率奖励最适合有确定答案的数学题。设模型答案为 $a$、标准答案为 $a^*$：

$$
r_{\text{acc}}(a,a^*)=1 \quad \text{当 } a=a^*
$$

$$
r_{\text{acc}}(a,a^*)=0 \quad \text{当 } a\ne a^*
$$

数值比较需要处理 72 与 72.0、千位分隔符、货币符号和浮点容差。当前实现没有把 seventy-two 或 1k 转换成数值，这类单位和自然语言归一化应由任务专用解析器负责，不能只靠宽松正则猜测。

#### 长度惩罚和步骤奖励

长度惩罚只对“答案正确但超过目标长度”的部分扣分：

$$
r_{\text{length}}
=r_{\text{acc}}-\alpha\max(0,l-l_{\text{target}})
$$

若答案错误，奖励仍为 0。代码按字符数计算 $l$，默认 $\alpha=0.001$；如果训练目标按 Token 计费，就应改用 Tokenizer 统计，不能把字符数直接当作 Token 数。

步骤奖励同样以正确答案为前提：

$$
r_{\text{step}}
=r_{\text{acc}}+\beta s
$$

其中 $s$ 是识别出的 Step N、步骤 N 或编号行数量。实现设置 max_steps 上限，避免模型仅靠重复空洞步骤无限加分。错误答案即使写了很多步骤也不会获得步骤奖励。

| 奖励 | 优点 | 主要风险 |
| --- | --- | --- |
| 准确率 | 客观、简单、易验证 | 信号稀疏，无法区分接近正确与完全错误 |
| 长度惩罚 | 控制冗余和生成成本 | 权重过大时会压缩必要推理 |
| 步骤奖励 | 鼓励结构化、可检查的过程 | 模型可能堆砌无效步骤 |

三者组合后为：

$$
r
=r_{\text{acc}}
-\alpha\max(0,l-l_{\text{target}})
+\beta s
$$

组合并不是把三个已经计算过的奖励再次相加，否则准确率基线可能被重复计算。代码中的 CompositeReward 只计算一次准确率，再分别加入长度项与步骤项；答案错误时两个塑形项都不生效。

#### 自定义数据集和奖励函数

自定义原始数据至少要包含 question 和 answer，format_math_dataset 会把它转换成训练格式。训练前的字段约束如下：

| 格式 | 必需字段 | 可选字段 |
| --- | --- | --- |
| SFT | prompt、completion | text；缺少时由两者拼接 |
| RL | question、prompt、ground_truth、full_answer | 其他供奖励函数使用的元数据 |

直接传入适合一次实验；需要反复使用时，可以注册到工具：

~~~python
rl_tool.register_dataset("my_math_dataset", rl_dataset)
rl_tool.register_reward_function("my_math_dataset", tolerant_reward)

result = rl_tool.run({
    "action": "train",
    "algorithm": "grpo",
    "dataset": "my_math_dataset",
})
~~~

当 custom_reward 未显式传入时，RLTrainingTool 会先查找与 dataset 同名的已注册奖励，再回退到准确率奖励。这补齐了原文“同名自动匹配”的调用约定。

自定义奖励函数必须接收 completions 和关键字参数，返回等长的奖励列表。除了数值范围，还要保证确定性、异常可解释、不会修改输入，并对无答案、非法数字和批量长度不一致做处理。实践中的 tolerant_reward 按误差给 1.0、0.8、0.5 或 0.0，再对有效推理格式增加少量奖励。

### 训练器与 LoRA

训练器封装没有重新实现优化算法，只负责把统一配置传给 TRL：

~~~python
config = TrainingConfig(
    model_name="Qwen/Qwen3-0.6B",
    output_dir="./output/quick_test/grpo",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    num_generations=8,
    learning_rate=1e-6,
    use_lora=True,
    lora_r=8,
    lora_alpha=16,
)
trainer = GRPOTrainerWrapper(config, dataset, reward_fn)
trainer.train()
trainer.save_model()
~~~

单进程时，GRPO 的有效批量为：

$$
B_{\text{effective}}
=B_{\text{device}}\times N_{\text{accumulation}}
$$

它必须能按 num_generations 分组。示例中 $2\times4=8$，刚好容纳每个 Prompt 的 8 个候选回答；不是要求单个 batch_size=2 被 8 整除。

LoRA 配置通过 TRL 的 peft_config 交给训练器，实际作用于注意力层的 q_proj 和 v_proj。只在参数字典里写 use_lora=True、却没有把 LoraConfig 传给训练器，并不会产生 LoRA 训练。

### 代码实践

#### 安装与入口

原文使用固定版本安装可选依赖：

~~~bash
python -m pip install "hello-agents[rl]==0.2.5"
~~~

本地源码仍会优先从 code/HelloAgents 导入；Qwen3 模型要求较新的 Transformers，若单独安装依赖，应保证 transformers>=4.51，并包含 torch、datasets、trl、peft 与 accelerate。

11.2 的数据转换与奖励实践见 [agentic_rl_data_rewards_demo.py](./code/HelloAgents/examples/agentic_rl_data_rewards_demo.py)。默认使用固定样例和一个只负责渲染模板的 DemoTokenizer，不下载模型：

~~~bash
cd code/HelloAgents
PYTHONPATH=. python examples/agentic_rl_data_rewards_demo.py
~~~

安装 datasets 与 transformers 后，可让脚本创建 Hugging Face Dataset、加载真实模型模板，并验证数据集和同名奖励注册：

~~~bash
PYTHONPATH=. python examples/agentic_rl_data_rewards_demo.py \
  --with-huggingface --model-name Qwen/Qwen3-0.6B
~~~

完整训练入口见 [agentic_rl_quickstart.py](./code/HelloAgents/examples/agentic_rl_quickstart.py)。默认只运行奖励冒烟测试：

~~~bash
cd code/HelloAgents
PYTHONPATH=. python examples/agentic_rl_quickstart.py --stage reward
~~~

执行与原文相同的“10 条 SFT、5 条 GRPO、10 条评估”流程：

~~~bash
PYTHONPATH=. python examples/agentic_rl_quickstart.py --stage all
~~~

也可以分阶段运行：

~~~bash
PYTHONPATH=. python examples/agentic_rl_quickstart.py --stage dataset
PYTHONPATH=. python examples/agentic_rl_quickstart.py --stage sft
PYTHONPATH=. python examples/agentic_rl_quickstart.py --stage grpo
PYTHONPATH=. python examples/agentic_rl_quickstart.py \
  --stage evaluate --model-path ./output/quick_test/grpo
~~~

这些步骤会下载 GSM8K 和 Qwen3-0.6B，并在 output/ 写入检查点。10 条样本、1 个 Epoch 只能验证链路，不能说明模型能力得到稳定提升；GRPO 对学习率也较敏感，因此实践入口显式使用 $10^{-6}$，不沿用 SFT 的默认学习率。

#### 统一工具接口

RLTrainingTool 保留原文的四种动作：

~~~python
from hello_agents import RLTrainingTool

tool = RLTrainingTool()
result = tool.run({
    "action": "train",
    "algorithm": "grpo",
    "model_name": "Qwen/Qwen3-0.6B",
    "max_samples": 5,
    "num_epochs": 1,
    "batch_size": 2,
    "gradient_accumulation_steps": 4,
    "num_generations": 8,
    "learning_rate": 1e-6,
    "use_lora": True,
})
~~~

实现中做了几处必要补全：

- 对外以 format 为正式参数，同时兼容章节快速脚本出现的 format_type。
- 创建奖励函数不依赖 TRL；只有数据下载、训练和评估才检查重型依赖。
- SFT 与 GRPO 都真正传入 LoRA 配置并保存 Tokenizer。
- GRPO 在训练前校验有效批量与候选组数，避免开始训练后才报错。
- 奖励函数统一使用 ground_truth，并兼容 TRL 可能传入的对话式 Completion。
- 评估阶段识别普通模型目录与 LoRA Adapter 目录，使用贪心解码计算准确率。

#### 数据与奖励实践结果

运行 11.2 实践脚本得到：

~~~text
=== 数据格式 ===
SFT fields: ['prompt', 'completion', 'text']
SFT prompt uses chat template: True
RL fields: ['prompt', 'ground_truth', 'question', 'full_answer']
RL ground_truth: 72

=== 准确率奖励 ===
[1.0, 1.0, 0.0]

=== 长度惩罚 ===
length= 16, reward=1.000
length=500, reward=0.700
length= 16, reward=0.000

=== 步骤奖励 ===
steps=0, reward=1.000
steps=2, reward=1.200
steps=2, reward=0.000

=== 组合奖励 ===
reward=1.191
tolerant: [0.9, 0.5]
~~~

这组输出对应几条关键规则：72 和 72.0 视为相同；500 字符的正确答案在目标长度 200、惩罚系数 0.001 时得到 $1-0.001\times300=0.7$；两步正确推理得到 1.2，而两步错误推理仍为 0。组合奖励 1.191 只计算一次准确率基线，再扣除超长部分、增加步骤奖励。

未安装训练依赖时，工具会在下载模型前返回明确错误：

~~~text
{
  "status": "error",
  "action": "train",
  "message": "缺少 Agentic-RL 依赖：torch, transformers, datasets, trl, peft, accelerate。..."
}
~~~

这不是训练失败，而是依赖预检。真实训练结果必须在安装依赖并实际完成 SFT/GRPO 后记录。

### 实践中的边界

本节代码实现的是 Agentic-RL 的训练基础设施，不应把一次 GSM8K GRPO 直接称为完整 Agentic-RL：

- SFT 仍是监督学习，用于建立推理格式和初始策略。
- 当前 GRPO 根据最终数学答案给单轮 Completion 打分，属于 PBRFT。
- 真正的 Agentic-RL 还需要环境在每一步执行工具、返回观察，并保存完整轨迹。
- 奖励还要覆盖工具选择、参数正确性、过程成本、失败恢复和最终任务质量。
- 格式转换不是简单拼接字符串：Prompt 必须服从当前模型的对话模板，SFT Completion 还要有明确的终止标记。
- 奖励塑形必须建立在任务成功之上，否则模型可能靠写长答案或堆砌步骤获得高分。

因此，这里的四层架构更像训练底座。后续要把 prompt → completion → reward 扩展为 state → action → environment → observation → next state，训练目标才真正落到多步智能体行为上。

### 参考资料

- [《Hello-Agents》第十一章：Agentic-RL 源文件](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter11/%E7%AC%AC%E5%8D%81%E4%B8%80%E7%AB%A0%20Agentic-RL.md)
- [Hugging Face TRL 文档](https://huggingface.co/docs/trl/index)
- [TRL SFT Trainer](https://huggingface.co/docs/trl/sft_trainer)
- [TRL GRPO Trainer](https://huggingface.co/docs/trl/grpo_trainer)
- [GSM8K 数据集](https://huggingface.co/datasets/openai/gsm8k)
- [Training Verifiers to Solve Math Word Problems](https://arxiv.org/abs/2110.14168)
- [Hello-Agents：数据集加载示例](https://github.com/datawhalechina/hello-agents/blob/main/code/chapter11/01_dataset_loading.py)
- [Hello-Agents：奖励函数示例](https://github.com/datawhalechina/hello-agents/blob/main/code/chapter11/02_reward_functions.py)
- [Qwen3-0.6B 模型说明](https://huggingface.co/Qwen/Qwen3-0.6B)
- [DeepSeekMath：GRPO 的论文来源](https://arxiv.org/abs/2402.03300)

### 小结

传统 LLM 训练主要优化 Token 预测和单次回答，Agentic-RL 则把模型视为环境中的策略，关注多步状态、动作、观察与长期回报。SFT 数据提供完整解法，RL 数据只向奖励函数保留标准答案；准确率负责定义任务成功，长度与步骤奖励负责塑形，但都不能凌驾于正确性之上。本次代码按照原文补齐了数据格式化、字段校验、答案解析、三类奖励、组合奖励、自定义注册和同名匹配，并保留了从单轮 GRPO 继续演进到多步环境训练的接口边界。
