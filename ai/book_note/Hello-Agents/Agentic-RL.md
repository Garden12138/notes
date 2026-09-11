## Agentic-RL

> 阅读资料：[《Hello-Agents》第十一章 11.1：从 LLM 训练到 Agentic-RL](https://datawhalechina.github.io/hello-agents/#/./chapter11/%E7%AC%AC%E5%8D%81%E4%B8%80%E7%AB%A0%20Agentic-RL?id=_111-%e4%bb%8e-llm-%e8%ae%ad%e7%bb%83%e5%88%b0-agentic-rl)、[11.2：数据集与奖励函数](https://datawhalechina.github.io/hello-agents/#/./chapter11/%E7%AC%AC%E5%8D%81%E4%B8%80%E7%AB%A0%20Agentic-RL?id=_112-%e6%95%b0%e6%8d%ae%e9%9b%86%e4%b8%8e%e5%a5%96%e5%8a%b1%e5%87%bd%e6%95%b0)、[11.3：SFT 训练](https://datawhalechina.github.io/hello-agents/#/./chapter11/%E7%AC%AC%E5%8D%81%E4%B8%80%E7%AB%A0%20Agentic-RL?id=_113-sft-%e8%ae%ad%e7%bb%83)、[11.4：GRPO 训练](https://datawhalechina.github.io/hello-agents/#/./chapter11/%E7%AC%AC%E5%8D%81%E4%B8%80%E7%AB%A0%20Agentic-RL?id=_114-grpo-%e8%ae%ad%e7%bb%83)、[11.5：模型评估与分析](https://datawhalechina.github.io/hello-agents/#/./chapter11/%E7%AC%AC%E5%8D%81%E4%B8%80%E7%AB%A0%20Agentic-RL?id=_115-%e6%a8%a1%e5%9e%8b%e8%af%84%e4%bc%b0%e4%b8%8e%e5%88%86%e6%9e%90)、[11.6：完整训练流程实战](https://datawhalechina.github.io/hello-agents/#/./chapter11/%E7%AC%AC%E5%8D%81%E4%B8%80%E7%AB%A0%20Agentic-RL?id=_116-%e5%ae%8c%e6%95%b4%e8%ae%ad%e7%bb%83%e6%b5%81%e7%a8%8b%e5%ae%9e%e6%88%98)
>
> 本节先梳理预训练、SFT、RLHF/RLAIF 与 Agentic-RL 的关系，再依次整理数据、奖励、LoRA SFT、GRPO 和模型评估。这里的 GRPO 仍以单轮数学回答为训练对象，还不等同于完整的多步 Agentic-RL。

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

11.5 和 11.6 在四层训练底座之外增加了 [evaluation.py](./code/HelloAgents/hello_agents/rl/evaluation.py)、[pipeline.py](./code/HelloAgents/hello_agents/rl/pipeline.py) 与 [deployment.py](./code/HelloAgents/hello_agents/rl/deployment.py)，分别负责指标聚合、阶段编排和验收后的模型服务化，不把这些职责塞回训练器。

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

### SFT 训练

#### SFT 是强化学习前的行为起点

预训练模型已经会续写文本，但不一定会稳定输出 Step 1、Step 2 和 Final Answer。SFT 用标准解题轨迹建立三件事：任务格式、基本推理路径和明确的结束位置。后续强化学习才能可靠提取答案、计算奖励，并在一个合理策略附近探索。

对于 Prompt $x$ 和标准回答 $y=(y_1,\ldots,y_T)$，SFT 最小化目标 Token 的负对数似然：

$$
\mathcal{L}_{\text{SFT}}(\theta)
=-\sum_{t=1}^{T}\log p_{\theta}(y_t\mid x,y_{<t})
$$

Prompt 负责提供条件，不应成为主要监督目标。当前 TRL 支持 prompt-completion 数据时，默认只在 Completion Token 上计算损失；兼容旧版 TRL 时，本地封装仍保留 text 字段作为回退。Padding Token 则统一屏蔽，不参与损失。

~~~mermaid
flowchart LR
    RAW["GSM8K<br/>question + answer"] --> FORMAT["应用 Chat Template<br/>补 EOS"]
    FORMAT --> TOKEN["Tokenizer<br/>截断与 Padding"]
    TOKEN --> LOSS["Completion Token<br/>交叉熵损失"]
    LOSS --> BACK["反向传播"]
    BACK --> LORA["只更新 LoRA<br/>A、B 矩阵"]
    LORA --> CKPT["保存 Adapter<br/>与 Tokenizer"]
    CKPT --> EVAL["GSM8K test<br/>准确率与回答质量"]
~~~

#### LoRA 为什么能降低训练成本

对原权重 $W\in\mathbb{R}^{d\times k}$，LoRA 冻结 $W$，只学习低秩增量：

$$
W'=W+\Delta W
$$

$$
\Delta W=\frac{\alpha}{r}BA
$$

其中 $A\in\mathbb{R}^{r\times k}$、$B\in\mathbb{R}^{d\times r}$，可训练参数量由 $dk$ 降为 $r(d+k)$。当 $d=k=4096$、$r=8$ 时，一个投影层从 16,777,216 个参数降到 65,536 个，约为原来的 $1/256$。

rank 决定增量矩阵的表达容量，alpha 通过 $\alpha/r$ 控制更新尺度。默认只改 q_proj 和 v_proj；完整训练示例扩展到 q_proj、k_proj、v_proj、o_proj。目标模块越多、rank 越大，可训练参数和显存占用也越高。

LoRA 必须以 LoraConfig 传入 SFTTrainer 的 peft_config。仅在外层参数中设置 use_lora=True，并不会自动冻结原模型或创建 Adapter。

#### 训练参数如何进入更新循环

| 参数 | 作用 | 实践中的处理 |
| --- | --- | --- |
| max_samples | 控制训练样本量 | 100 条用于链路测试，None 使用全部 7,473 条训练数据 |
| num_epochs | 遍历数据集的次数 | 从 1—3 轮开始，根据训练集与验证集曲线调整 |
| batch_size | 单设备一次前向的样本数 | 显存不足时先减小，再用梯度累积补足有效批量 |
| learning_rate | 每次参数更新的步长 | 普通 SFT 可从 $5\times10^{-5}$ 起步，LoRA 可比较 $10^{-4}$ |
| warmup_ratio | 预热步数占总步数的比例 | 默认 0.1；若 warmup_steps 大于 0，则固定步数优先 |
| weight_decay | AdamW 的权重衰减 | 默认 0.01，用于抑制过拟合 |
| logging_steps | 指标记录间隔 | 观察 loss、grad_norm 和 learning_rate |
| save_steps | 检查点间隔 | 与总更新步数匹配，避免小数据实验从不保存中间状态 |
| eval_steps | 训练中验证间隔 | 只有同时提供验证集才生效 |

单进程的有效批量为：

$$
B_{\text{effective}}
=B_{\text{device}}\times N_{\text{accumulation}}
$$

多进程训练还要再乘进程数。有效批量增大通常让更新更平稳，但也会减少每个 Epoch 的参数更新次数。

训练时主要观察 loss、grad_norm 和 learning_rate。loss 持续不降需要同时检查数据、学习率和监督掩码；grad_norm 突增可能意味着更新不稳定，但“正常范围”依赖模型、精度和批量，不能把固定阈值当作通用结论。

#### SFTTrainerWrapper 的职责

封装层不重新实现优化算法，只负责把数据、模型、训练参数和 LoRA 配置接到 TRL：

~~~python
config = TrainingConfig(
    model_name="Qwen/Qwen3-0.6B",
    output_dir="./output/sft_quick",
    num_train_epochs=1,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=5e-5,
    warmup_ratio=0.1,
    weight_decay=0.01,
    use_lora=True,
    lora_r=8,
    lora_alpha=16,
)
trainer = SFTTrainerWrapper(config, train_dataset, eval_dataset)
trainer.train()
trainer.save_model()
~~~

完整实现见 [trainers.py](./code/HelloAgents/hello_agents/rl/trainers.py)。它会设置 Pad Token、按 TRL 版本选择 processing_class 或 tokenizer、传入 LoRA、保存 Adapter 和 Tokenizer，并返回总参数量、可训练参数量与训练指标。

#### 训练后怎样评估

训练 loss 下降只表示模型更贴合训练文本，不等于数学能力一定提高。至少需要比较：

- 准确率：从 Final Answer 提取答案后，与 ground_truth 做数值比较。
- 平均奖励：使用当前奖励函数汇总生成结果；只有准确率奖励时，它与准确率相同。
- 推理质量：检查步骤是否连贯、是否只是碰巧答对，通常需要抽样人工审阅。

比较基础模型和 SFT 模型时，必须固定 GSM8K test 子集、Prompt 模板、解码参数和最大生成长度。原文给出的准确率区间只能作为示例，不能替代本机实际评估。

### GRPO 训练

#### 从 PPO 到 GRPO

SFT 让模型模仿标准解法，GRPO 则让当前模型对同一道题采样多个回答，根据奖励提高较优回答的概率。两者不是替代关系：SFT 提供稳定的初始策略，GRPO 在此基础上探索。

PPO 需要 Value Model 估计优势，GRPO 直接用同组回答的相对奖励代替，因此省去了价值模型：

| 对比项 | PPO | GRPO |
| --- | --- | --- |
| 优势估计 | 奖励与 Value Model | 同一 Prompt 下的组内奖励 |
| 训练模型 | Policy、Reference、Value，奖励还可能来自 Reward Model | Policy；启用 KL 时还需 Reference |
| 每个 Prompt 的输出 | 通常采样一个或少量回答 | 必须采样一组回答 |
| 主要成本 | 多模型前向与价值学习 | 多候选生成与奖励计算 |

在 GSM8K 中，奖励来自可验证的最终答案，不必再训练 Reward Model。GRPO 减少了模型数量，但一次要生成多个 Completion，显存和时间开销仍明显高于 SFT。

#### 组内相对优势

对同一个 Prompt 生成 $G$ 个回答，奖励为 $r_1,\ldots,r_G$。原文先计算组内均值：

$$
\bar{r}=\frac{1}{G}\sum_{i=1}^{G}r_i
$$

再把每个回答转换为相对优势：

$$
\hat{A}_i=r_i-\bar{r}
$$

例如奖励为 $[1.0,1.0,0.0,0.8]$，均值为 $0.7$，相对优势就是 $[0.3,0.3,-0.7,0.1]$。更新后，前两个回答的生成概率应提高，错误回答的概率应降低，第四个回答虽然正确，但增幅较小。

当前 TRL 默认还会除以组内标准差：

$$
\hat{A}_i=\frac{r_i-\bar{r}}{\sigma_r+\varepsilon}
$$

这能统一不同组的更新尺度，但也可能引入题目难度偏差，可通过 `scale_rewards=False` 关闭。更直接的问题是：如果一组回答全部正确或全部错误，$\sigma_r=0$，所有相对优势都为 0，这个 Prompt 本轮不会提供区分信号。因此要同时关注平均奖励和 `frac_reward_zero_std`，不能只看 loss。

#### 一次 GRPO 更新发生了什么

~~~mermaid
flowchart LR
    P["一批 Prompt"] --> SAMPLE["当前策略采样<br/>每题 G 个回答"]
    SAMPLE --> REWARD["奖励函数<br/>逐个回答打分"]
    REWARD --> ADV["组内中心化<br/>得到相对优势"]
    ADV --> RATIO["计算新旧策略<br/>概率比"]
    RATIO --> CLIP["裁剪策略更新<br/>限制变化幅度"]
    CLIP --> KL["可选 KL 惩罚<br/>约束参考策略"]
    KL --> UPDATE["反向传播<br/>更新 LoRA"]
    UPDATE --> SAMPLE
~~~

设 Token 级策略概率比为：

$$
\rho_{i,t}(\theta)
=\frac{\pi_{\theta}(o_{i,t}\mid q,o_{i,<t})}
{\pi_{\theta_{\mathrm{old}}}(o_{i,t}\mid q,o_{i,<t})}
$$

核心损失可简化理解为：

$$
\mathcal{L}_{\mathrm{GRPO}}
=-\mathbb{E}\left[
\min\left(
\rho\hat{A},
\mathrm{clip}(\rho,1-\epsilon,1+\epsilon)\hat{A}
\right)
-\beta D_{\mathrm{KL}}
\right]
$$

`clip_range` 对应 $\epsilon$，限制一次更新改变策略的幅度；`kl_coef` 对应 TRL 的 `beta`，控制当前策略与参考策略之间的距离。原文采用 `kl_coef=0.05`，会启用参考策略的 KL 计算：训练完整模型时通常需要独立的 Reference Model，使用 PEFT 时则可将关闭适配器后的基础模型作为参考。当前 TRL 默认 `beta=0`，此时不使用 KL 项，也不需要参考策略。两种设置都可以训练，但监控项不同：`beta=0` 时没有 KL 指标，不能再用“KL 是否合理”判断训练状态。

#### 参数怎样接入 TRL

| 原文参数 | 本地配置 | TRL 参数 | 说明 |
| --- | --- | --- | --- |
| num_generations | num_generations | num_generations | 每个 Prompt 的候选数 |
| max_new_tokens | max_completion_length | max_completion_length | 单个回答的最大生成长度 |
| temperature、top_p | 同名 | 同名 | 保留采样多样性 |
| kl_coef | kl_coef | beta | KL 惩罚系数 |
| clip_range | clip_range | epsilon | 策略概率比裁剪范围 |
| lora_rank | lora_r | LoraConfig.r | LoRA 秩，两个参数名均兼容 |

单进程下必须满足：

$$
B_{\mathrm{device}}\times N_{\mathrm{accumulation}}
\quad\text{能被}\quad G\quad\text{整除}
$$

多进程时还要乘进程数。这里检查的是有效批量，不是只检查 `batch_size`。候选数、生成长度和批量都会直接放大生成成本；显存不足时应先减小 `max_new_tokens`、`num_generations` 或设备批量，再考虑梯度检查点和混合精度。

`reward_type="combined"` 不能只写在参数里却仍使用准确率奖励。本地实现会解析 `reward_config.components`，以准确率为基础，只对正确答案施加加权的长度惩罚和步骤奖励。这样避免重复叠加三次准确率基线，也避免模型靠错误但很短、步骤很多的回答获得正奖励。

#### 训练监控

GRPO 至少需要观察以下指标：

- `reward` 与各奖励分量：判断策略是否真的得到更高任务回报。
- `reward_std`、`frac_reward_zero_std`：判断同组回答是否有足够差异。
- `kl`：仅在 `kl_coef>0` 时存在；持续增大表示策略正在远离参考模型。
- `clip_ratio/region_mean`：过高说明大量更新被裁剪，应检查学习率和奖励尺度。
- `completions/mean_length`、`completions/clipped_ratio`：判断回答是否越来越冗长，或频繁撞到长度上限。

平均奖励上升不等于泛化能力提高。训练后仍要在固定的 GSM8K test 子集上比较 SFT 与 GRPO，并抽查答案格式和推理连贯性。原文日志与准确率是示例，不能当作本地训练结果。

### 模型评估与分析

#### 为什么准确率不够

训练 loss 和训练奖励描述的是优化过程，最终能力必须在未参与训练的测试集上重新测量。单看准确率只能回答“第一条回答是否答对”，不能说明模型能否通过多次采样找到答案、输出成本有多高、推理格式是否稳定，也无法定位错误来自计算、推理还是题意理解。

原文把指标分为准确性、效率和质量三类：

| 维度 | 指标 | 回答的问题 |
| --- | --- | --- |
| 准确性 | Accuracy | 首个回答完全正确的比例是多少 |
| 准确性 | Accuracy@K | 每题采样 K 个候选后，至少答对一次的比例是多少 |
| 准确性 | Numerical Error | 可解析数值答案距离标准答案有多远 |
| 效率 | Average Length | 每个首选回答平均生成多少 Token |
| 效率 | Average Steps | 回答平均包含多少个推理步骤 |
| 效率 | Inference Time | 每个问题完成生成平均耗时多久 |
| 质量 | Format Correctness | 回答是否同时包含显式步骤和最终答案标记 |
| 质量 | Coherence、Explainability | 推理是否连贯、易懂且可以复核 |

设共有 $N$ 道题，第一条回答是否正确记为 $c_i\in\{0,1\}$，则：

$$
\mathrm{Accuracy}=\frac{1}{N}\sum_{i=1}^{N}c_i
$$

若第 $i$ 道题采样 $K$ 个候选，候选正确性记为 $c_{i,j}$，则：

$$
\mathrm{Accuracy@K}
=\frac{1}{N}\sum_{i=1}^{N}\max_{1\le j\le K}c_{i,j}
$$

Accuracy@K 衡量的是模型的搜索潜力，不等于单次作答能力。单独测量 Accuracy 时通常使用贪心解码，Accuracy@K 则必须采样多个不同回答；比较模型时要固定 $K$、温度、`top_p`、随机种子和最大生成长度。

对能解析为数值的回答，平均绝对误差为：

$$
\mathrm{MAE}=\frac{1}{N_{\mathrm{num}}}
\sum_{i=1}^{N_{\mathrm{num}}}|\hat{y}_i-y_i|
$$

这里的分母是成功解析出预测值和标准值的样本数 $N_{\mathrm{num}}$。无法解析的回答不能悄悄按 0 误差处理，因此实现会同时返回 `numerical_error_samples`，并通过格式正确率暴露缺失答案标记的问题。

`average_reward` 衡量的是模型对当前奖励函数的适配程度。默认只使用准确率奖励，所以它与 Accuracy 相同；若训练使用组合奖励，评估时也要传入相同的 `reward_type` 和 `reward_config`，否则训练奖励与评估奖励没有可比性。组合奖励仍只计算每题的首个回答，Accuracy@K 另行衡量候选覆盖率。

#### 一次评估如何流转

~~~mermaid
flowchart LR
    D["固定 GSM8K test 子集"] --> P["按同一模板构造 Prompt"]
    P --> G["模型生成<br/>Greedy 或 K 次采样"]
    G --> X["提取最终答案"]
    X --> M["准确率 / Accuracy@K<br/>误差 / 长度 / 步骤 / 耗时"]
    G --> F["检查步骤与 Final Answer 格式"]
    M --> E["收集错误样本"]
    F --> E
    E --> A["错误类型与难度分组"]
    A --> I["调整数据、奖励或训练参数"]
    I --> D
~~~

基础模型、SFT 和 GRPO 的横向比较必须使用同一批题、同一 Prompt、同一解码配置和同一答案提取规则。还要记录硬件与推理参数，否则推理时间没有可比性。若训练阶段看过 test 划分，评估结果已经发生数据泄漏，不能作为泛化结论。

平均长度按生成 Token 数计算，而不是 Python 字符数；中文文本尤其不能用 `len(text)` 代替 Token 数。平均步骤数只能反映回答结构，不是越多越好。格式正确率也只是可自动检查的代理指标，推理连贯性和可解释性仍需人工抽查或独立评审模型，不能从是否出现 `Step 1` 推断出来。

#### 错误分析

原文将错误分成四类：

| 类型 | 典型表现 | 优先改进方向 |
| --- | --- | --- |
| 计算错误 | 解题路径合理，但等式内部算错 | 增加计算样本或接入计算器 |
| 推理错误 | 有步骤、有最终答案，但推导关系不成立 | 改善推理示范和过程奖励 |
| 理解错误 | 没有形成可用步骤，遗漏题目条件 | 增加题意改写与难例训练 |
| 格式错误 | 缺少 `Final Answer:` 等约定标记 | 加强格式 SFT 或格式奖励 |

这四类并不能只靠字符串规则准确判断。本地实现保持原文的规则分析思路：缺少最终答案标记归为格式错误；发现 `48/2=25` 这类内部不一致等式归为计算错误；有显式步骤但答案错误归为推理错误；其余暂归为理解错误。它适合快速筛查，不应替代人工复核，返回结果也只能称为“规则性诊断”。

GSM8K 的标准解答使用 `<<表达式=结果>>` 标注计算步骤，可据此将题目分为简单（1—2 步）、中等（3—4 步）和困难（5 步及以上）。按难度统计准确率时，分组依据必须来自标准答案，不能用模型自己生成了多少步定义题目难度，否则模型的冗长回答会改变评估分组。

#### 原文接口需要补齐的地方

原文示例传入了 `metrics`、`k` 和 `return_details`，后续又读取 `errors`、`details`、`ground_truth_steps`，但说明代码没有实现这些字段。本地 `RLTrainingTool` 现已补齐：

- `metrics` 支持 Accuracy、Accuracy@K、数值误差、平均生成长度、平均步骤数、平均推理时间和格式正确率。
- `average_reward` 始终返回；默认等于 Accuracy，也可复用训练时的组合奖励配置。
- 只有请求 `accuracy_at_k` 时才为每道题采样 K 个候选；普通 Accuracy 仍使用贪心解码，避免无谓增加推理成本。
- `return_details=True` 返回逐题候选、正确性、数值误差、Token 数、步骤数、格式状态和标准答案步骤数。
- `errors` 只收录首个回答错误的样本，并附带规则性错误类型；同时汇总 `error_distribution`。
- `accuracy_by_difficulty` 按标准答案的标注步骤统计，空分组不会伪造 0% 准确率。
- `evaluate` 中的 `use_lora` 不再决定加载逻辑：工具通过目录内是否存在 `adapter_config.json` 自动区分完整模型和 LoRA Adapter。
- 原文模型对比示例遗漏了 `json.loads()`；`tool.run()` 返回 JSON 字符串，参与数值格式化前必须先解析。

指标聚合与规则分析集中在 [evaluation.py](./code/HelloAgents/hello_agents/rl/evaluation.py)，模型加载和生成仍由 [rl_training_tool.py](./code/HelloAgents/hello_agents/tools/builtin/rl_training_tool.py) 负责，避免把可测试的指标逻辑绑死在 GPU 推理流程里。

### 完整训练流程实战

#### 从分散脚本到阶段流水线

前几节分别实现了数据、奖励、SFT、GRPO 和评估，11.6 的重点不是再写一种训练算法，而是把这些能力接成一条可中断、可检查、可复现的流水线。

~~~mermaid
flowchart TD
    C["读取并校验配置"] --> D["1. 加载与检查数据"]
    D --> S["2. LoRA SFT"]
    S --> SE["3. SFT 固定测试集评估"]
    SE --> GATE{"Accuracy 达到门槛?"}
    GATE -- 否 --> F["停止并保存失败报告"]
    GATE -- 是 --> G["4. 从 SFT Adapter 执行 GRPO"]
    G --> GE["5. GRPO 固定测试集评估"]
    GE --> R["6. 保存训练报告"]
    R --> A{"人工验收通过?"}
    A -- 否 --> T["调整数据、奖励或超参数"]
    T --> C
    A -- 是 --> M["合并 Adapter 或直接加载"]
    M --> API["部署推理服务"]
~~~

原文总览把模型部署列为训练链路的最后一步，但示例 `AgenticRLPipeline` 的第六个可执行阶段实际是保存结果。这里保留这个边界：主流水线只负责训练、评估和落盘；合并模型、量化和启动 API 必须在结果验收后显式执行，不能因脚本正常退出就自动上线。

每个阶段都要有稳定的输入、输出和失败条件：

| 阶段 | 关键输入 | 可交给下一阶段的结果 | 失败时的处理 |
| --- | --- | --- | --- |
| 数据准备 | 数据集、格式、样本上限 | 格式化后的样本和质量报告 | 缺字段、空值或重复 Prompt 时停止 |
| SFT | 基础模型、SFT 数据、LoRA 配置 | SFT Adapter 路径 | 保留错误信息，不进入评估 |
| SFT 评估 | Adapter、固定测试集、生成配置 | 指标报告 | 低于门槛时不启动 GRPO |
| GRPO | SFT Adapter、RL 数据、奖励函数 | GRPO Adapter 路径 | 保存前面已完成的阶段结果 |
| GRPO 评估 | GRPO Adapter、同一测试设置 | 可比较的最终指标 | 标记失败，不伪造评估结果 |
| 结果保存 | 全部阶段状态和时间 | JSON 报告 | 返回独立的保存错误 |

这种接法解决了原文示例中的几个断点：工具返回的是 JSON 字符串，流水线必须先解析并检查 `status`；GRPO 的 `model_name` 必须来自 SFT 返回的 `model_path`；配置中的 `sft_accuracy_threshold` 要真正成为门禁；任一阶段失败后都不能继续消耗算力，同时仍要保存已获得的信息。开始与结束时间使用带时区的 RFC 3339 格式，便于跨机器比对运行记录。

数据质量检查只能发现结构问题，不能判断推理是否正确。重复 Prompt、空答案和字段缺失可以自动拦截；答案错误、题目歧义和难度分布仍要抽样审核。数据增强也不是越多越好，改写题目时必须保持数值关系和标准答案不变。

#### 超参数调优

| 方法 | 做法 | 适合场景 | 主要代价 |
| --- | --- | --- | --- |
| 网格搜索 | 枚举有限候选的笛卡尔积 | 参数少、范围明确 | 组合数增长快 |
| 随机搜索 | 从给定分布抽取若干组参数 | 搜索空间较大 | 结果受预算和随机种子影响 |
| 贝叶斯优化 | 根据已完成试验选择下一组参数 | 单次训练昂贵 | 需要额外调优框架和持久化试验状态 |

网格搜索只能找到“给定网格中的最优组合”，不能称为连续空间的全局最优。每次试验要使用独立输出目录和完整配置快照，否则后一次训练会覆盖前一次检查点。选参应读取验证集指标，测试集只在方案确定后使用一次；若反复根据 test Accuracy 改参数，最终结果已经泄漏测试信息。

实用的调优顺序是先固定数据和评估方式，再调整 SFT 学习率、批量与 Epoch；得到稳定起点后，再调整 GRPO 的候选数、学习率、KL 系数、裁剪范围和奖励权重。一次只改变少数参数，更容易解释指标变化。

#### 分布式训练

分布式启动并不会改变训练脚本的业务阶段，`accelerate launch` 负责创建多个进程，TRL 和 Transformers 负责把模型、批次及梯度接入 DDP、DeepSpeed 或其他后端。配置里的 `batch_size` 是单设备批量，全局有效批量为：

$$
B_{\text{global}}
=B_{\text{device}}\times N_{\text{accum}}\times N_{\text{process}}
$$

GRPO 每道题要生成 $G$ 个候选，因此还要满足：

$$
B_{\text{global}}\bmod G=0
$$

本地实现已把 `WORLD_SIZE` 纳入校验。单卡配置中 $4\times1\times1=4$，可容纳 4 个候选；两进程时若每设备批量为 2，则 $2\times1\times2=4$ 也成立。只检查单进程批量会错误拒绝后一种有效配置。

DDP 会在每张 GPU 保存一份模型副本，适合模型能够放入单卡、主要想提升吞吐的情况；显存不足时再考虑 DeepSpeed ZeRO 或 FSDP。多机还要统一代码、依赖、数据和配置，并正确设置主节点地址与各机器 rank。流水线中的所有进程都会参加训练，公共 `training_results.json` 只由 rank 0 写入，避免多个进程同时覆盖同一个临时文件。

硬件拓扑不同，不应直接复制原文 YAML；先运行 `accelerate config`，再用配置文件启动：

~~~bash
accelerate launch --config_file accelerate_config.yaml \
  examples/agentic_rl_pipeline_demo.py --run
~~~

#### 从训练产物到服务

LoRA 训练保存的是 Adapter，体积小，但加载时仍需要基础模型。部署有两种常见方式：直接加载基础模型与 Adapter，便于切换多个任务；或用 `merge_and_unload()` 合并权重，得到普通 Transformers 模型。合并后文件更大，也会失去禁用、切换和拆分 Adapter 的能力，因此原 Adapter 应单独保留。

量化能降低推理显存，但会改变数值精度和运行依赖，量化后的服务需要重新跑离线评估。API 层只负责请求校验与推理，不应返回原文示例中固定写死的 `confidence=0.8`；没有校准方法就不提供置信度。Prompt 也应通过 Tokenizer 的 Chat Template 构造，避免手写模板与训练格式不一致。

本地实现把部署拆为两步：[deployment.py](./code/HelloAgents/hello_agents/rl/deployment.py) 负责合并 Adapter、加载普通或量化模型及生成回答，[agentic_rl_api.py](./code/HelloAgents/examples/agentic_rl_api.py) 提供 `/health` 和 `/solve`。服务不会被训练脚本自动启动。

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

11.3 的入口见 [agentic_rl_sft_demo.py](./code/HelloAgents/examples/agentic_rl_sft_demo.py)。先查看并校验快速配置，不会下载模型：

~~~bash
PYTHONPATH=. python examples/agentic_rl_sft_demo.py
~~~

确认配置后再显式开始训练；需要复现原文的完整配置时切换 full，并可在训练结束后评估固定数量的测试样本：

~~~bash
PYTHONPATH=. python examples/agentic_rl_sft_demo.py --run

PYTHONPATH=. python examples/agentic_rl_sft_demo.py \
  --profile full --run --evaluate-samples 100
~~~

11.4 的入口见 [agentic_rl_grpo_demo.py](./code/HelloAgents/examples/agentic_rl_grpo_demo.py)。默认只校验原文参数并计算一组相对优势，不加载 SFT 模型：

~~~bash
PYTHONPATH=. python examples/agentic_rl_grpo_demo.py
~~~

训练必须从 SFT 输出继续。快速配置使用 100 条样本与准确率奖励；完整配置使用全部训练集和原文的组合奖励：

~~~bash
PYTHONPATH=. python examples/agentic_rl_grpo_demo.py \
  --model-name ./output/sft_full --run

PYTHONPATH=. python examples/agentic_rl_grpo_demo.py \
  --profile full --model-name ./output/sft_full \
  --run --evaluate-samples 100
~~~

11.5 的入口见 [agentic_rl_evaluation_demo.py](./code/HelloAgents/examples/agentic_rl_evaluation_demo.py)。默认使用五条固定记录验证指标聚合、四类错误诊断和难度分组，不加载模型：

~~~bash
PYTHONPATH=. python examples/agentic_rl_evaluation_demo.py
~~~

确认模型路径后，可以在同一批 200 条 GSM8K test 样本上比较基础模型、SFT Adapter 和 GRPO Adapter：

~~~bash
PYTHONPATH=. python examples/agentic_rl_evaluation_demo.py --run \
  --model "预训练模型=Qwen/Qwen3-0.6B" \
  --model "SFT模型=./output/sft_full" \
  --model "GRPO模型=./output/grpo_full" \
  --max-samples 200 --k 3 --max-new-tokens 256
~~~

实际执行会为每个模型重新生成答案。只请求 Accuracy 时使用贪心解码；同一次调用还请求 Accuracy@3 时会生成三条采样候选，Accuracy 使用其中第一条，Accuracy@3 检查三条。三个模型共享测试集、种子和生成上限，但单样本准确率与候选覆盖率的含义仍不同。

11.6 的配置文件见 [agentic_rl_pipeline_config.json](./code/HelloAgents/examples/agentic_rl_pipeline_config.json)，编排入口见 [agentic_rl_pipeline_demo.py](./code/HelloAgents/examples/agentic_rl_pipeline_demo.py)。默认只校验配置并打印阶段，不下载数据：

~~~bash
PYTHONPATH=. python examples/agentic_rl_pipeline_demo.py
~~~

预览输出如下：

~~~text
=== 11.6 完整训练流水线预览 ===
base_model: Qwen/Qwen3-0.6B
train_samples: 1000
evaluation_samples: 200
sft_accuracy_threshold: 40.00%
grpo_group_check: global_effective_batch=4, world_size=1, num_generations=4
stage_1: prepare_data
stage_2: sft_training
stage_3: sft_evaluation
stage_4: grpo_training
stage_5: grpo_evaluation
stage_6: save_results
results_path: ./output/agentic_rl/training_results.json
pipeline_started: False (add --run after checking the config)
~~~

确认模型、显存、数据和输出目录后，才执行真实训练：

~~~bash
PYTHONPATH=. python examples/agentic_rl_pipeline_demo.py \
  --config examples/agentic_rl_pipeline_config.json --run
~~~

该命令会下载数据和模型、执行两轮训练与两轮评估，运行时会占用较多显存、磁盘和时间。当前没有执行重型训练，因此笔记不记录 Accuracy、Loss 或 Reward 等虚构结果。流水线实现见 [pipeline.py](./code/HelloAgents/hello_agents/rl/pipeline.py)；它会在失败时停止后续阶段，并将已完成阶段和错误写入 `training_results.json`。

通过人工验收后，可先预览再合并 GRPO Adapter：

~~~bash
PYTHONPATH=. python examples/agentic_rl_merge_adapter.py

PYTHONPATH=. python examples/agentic_rl_merge_adapter.py --run \
  --adapter-path ./output/agentic_rl/grpo_model \
  --output-dir ./output/agentic_rl/merged_model
~~~

安装 `fastapi`、`uvicorn` 后可以启动服务；4-bit 或 8-bit 模式还需要与当前硬件兼容的 `bitsandbytes`：

~~~bash
PYTHONPATH=. python examples/agentic_rl_api.py \
  --model-path ./output/agentic_rl/merged_model \
  --quantization none --host 127.0.0.1 --port 8000
~~~

原有 [agentic_rl_quickstart.py](./code/HelloAgents/examples/agentic_rl_quickstart.py) 保留为最小串联入口。默认只运行奖励冒烟测试：

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
PYTHONPATH=. python examples/agentic_rl_quickstart.py \
  --stage grpo --model-path ./output/quick_test/sft
PYTHONPATH=. python examples/agentic_rl_quickstart.py \
  --stage evaluate --model-path ./output/quick_test/grpo
~~~

这些步骤会下载 GSM8K 和 Qwen3-0.6B，并在 output/ 写入检查点。`--stage all` 会把 SFT 返回的 Adapter 路径传给 GRPO；单独执行 GRPO 时必须用 `--model-path` 指定初始策略。10 条样本、1 个 Epoch 只能验证链路，不能说明模型能力得到稳定提升；快速流水线使用较保守的 $10^{-6}$，11.4 复现脚本则保留原文的 $10^{-5}$，应根据奖励、KL 和裁剪比例调整。

#### 统一工具接口

RLTrainingTool 保留原文的四种动作：

~~~python
import json

from hello_agents import RLTrainingTool

tool = RLTrainingTool()
result = json.loads(tool.run({
    "action": "train",
    "algorithm": "sft",
    "model_name": "Qwen/Qwen3-0.6B",
    "output_dir": "./output/sft_model",
    "max_samples": 100,
    "num_epochs": 3,
    "batch_size": 4,
    "gradient_accumulation_steps": 4,
    "learning_rate": 5e-5,
    "warmup_ratio": 0.1,
    "weight_decay": 0.01,
    "use_lora": True,
    "lora_rank": 8,
    "lora_alpha": 16,
}))
~~~

GRPO 的统一入口沿用同一个工具，但初始模型应指向 SFT 输出，并显式传入原文的策略和奖励配置：

~~~python
result = json.loads(tool.run({
    "action": "train",
    "algorithm": "grpo",
    "model_name": "./output/sft_full",
    "output_dir": "./output/grpo_full",
    "num_epochs": 3,
    "batch_size": 4,
    "num_generations": 4,
    "max_new_tokens": 512,
    "learning_rate": 1e-5,
    "temperature": 0.8,
    "kl_coef": 0.05,
    "clip_range": 0.2,
    "use_lora": True,
    "lora_rank": 16,
    "reward_type": "combined",
    "reward_config": {
        "components": [
            {"type": "accuracy", "weight": 1.0},
            {"type": "length_penalty", "weight": 0.5,
             "target_length": 200},
            {"type": "step", "weight": 0.3,
             "step_bonus": 0.1},
        ]
    },
}))
~~~

模型评估仍使用同一个工具。`return_details` 会明显增大返回 JSON，只在错误分析时打开：

~~~python
evaluation = json.loads(tool.run({
    "action": "evaluate",
    "model_path": "./output/grpo_full",
    "max_samples": 200,
    "metrics": [
        "accuracy",
        "accuracy_at_k",
        "numerical_error",
        "average_length",
        "average_steps",
        "inference_time",
        "format_correctness",
    ],
    "k": 3,
    "max_new_tokens": 256,
    "temperature": 0.7,
    "top_p": 0.9,
    "return_details": True,
    "seed": 42,
}))
~~~

实现中做了几处必要补全：

- 对外以 format 为正式参数，同时兼容章节快速脚本出现的 format_type。
- 创建奖励函数不依赖 TRL；只有数据下载、训练和评估才检查重型依赖。
- SFT 与 GRPO 都真正传入 LoRA 配置并保存 Tokenizer。
- lora_r 和原文章节中的 lora_rank 都可使用；warmup_ratio、weight_decay、优化器、目标模块、日志及保存间隔都会进入 TRL 配置。
- 新旧 Transformers 分别使用 warmup_ratio 或小于 1 的 warmup_steps 表示预热比例，封装层会按构造参数自动映射。
- max_new_tokens、kl_coef 和 clip_range 分别映射到 TRL 的 max_completion_length、beta 和 epsilon，不再是未生效的展示参数。
- combined 奖励会解析 components、权重和 target_length；显式 reward_type 优先于同名数据集的默认奖励。
- 从本地 SFT Adapter 继续训练时直接加载已有 LoRA 参数，不会在外层再创建一套 Adapter。
- 训练返回 model_path、num_samples、num_epochs、final_loss 和可训练参数占比，不再只有一个输出目录。
- GRPO 还从训练日志提取最后一次 average_reward、kl 和 clip_ratio；某项没有被当前配置记录时返回 null，不伪造数值。
- eval_steps 只有在提供 custom_eval_dataset 或 eval_samples 时才启用，避免把“设置了间隔”误解成“已经执行验证”。
- GRPO 在训练前校验有效批量与候选组数，避免开始训练后才报错。
- 奖励函数统一使用 ground_truth，并兼容 TRL 可能传入的对话式 Completion。
- 评估阶段识别普通模型目录与 LoRA Adapter 目录，使用贪心解码计算准确率。
- 评估指标列表、Top-K 采样、逐题明细、错误分布和难度分组均已接入，不再返回只有准确率的占位结果。

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

#### SFT 配置实践结果

运行 11.3 实践脚本的默认配置：

~~~text
=== SFT 配置预览 ===
profile: quick
model: Qwen/Qwen3-0.6B
samples: 100
epochs: 1
effective_batch_size (single process): 16
warmup: ratio=0.1, fixed_steps=0
LoRA: r=8, alpha=16, targets=['q_proj', 'v_proj']
estimated LoRA parameters (hidden=4096, square projections): 131,072
output_dir: ./output/sft_quick
training_requested: False (add --run to start training)
~~~

有效批量 $4\times4=16$；131,072 是假设 q_proj、v_proj 都为 $4096\times4096$ 时的结构估算，用于理解 $r(d+k)$，不是 Qwen3-0.6B 的实际 Adapter 参数总数。真实数量会在训练完成后由模型参数直接统计并写入结果。

#### GRPO 配置实践结果

运行 11.4 实践脚本的默认配置：

~~~text
=== GRPO 配置预览 ===
profile: quick
initial_policy: ./output/sft_full
samples: 100
epochs: 3
effective_batch_size (single process): 4
num_generations: 4
generation: max_new_tokens=256, temperature=0.7, top_p=0.9
policy: kl_coef=0.05, clip_range=0.2
reward_type: accuracy
example_group_rewards: [1.0, 1.0, 0.0, 0.8]
example_group_mean: 0.7
example_centered_advantages: [0.3, 0.3, -0.7, 0.1]
output_dir: ./output/grpo_quick
training_requested: False (add --run to start training)
~~~

有效批量和候选数都是 4，满足分组约束。相对优势是原文按均值中心化后的结果，用来检查符号和组内比较逻辑；真正训练时由 TRL 按安装版本的 GRPOConfig 计算，并可能继续按标准差缩放。

#### 评估逻辑实践结果

运行 11.5 实践脚本的固定样例：

~~~text
=== 11.5 评估逻辑预览 ===
samples: 5
accuracy: 20.00%
accuracy@3: 40.00%
numerical_error: 4.25
average_length: 8.80
average_steps: 1.20
average_inference_time: 0.11s
format_correctness: 60.00%
error_distribution: {'计算错误': 1, '推理错误': 1, '理解错误': 1, '格式错误': 1}
accuracy_by_difficulty: {'简单(1-2步)': {'num_samples': 3, 'accuracy': 0.3333333333333333}, '中等(3-4步)': {'num_samples': 1, 'accuracy': 0.0}, '困难(5+步)': {'num_samples': 1, 'accuracy': 0.0}}
model_loaded: False (add --run to evaluate real checkpoints)
~~~

五条记录是专门构造的测试夹具：只有一个首选回答正确，第二题的另外两个候选中有一个正确，所以 Accuracy 为 20%，Accuracy@3 为 40%；四个错误回答分别命中四种规则类型。这个输出验证的是评估代码，不代表 Qwen、SFT 或 GRPO 模型的实际能力。

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
- SFT 的职责是学习示范，不会自行探索比数据更好的策略；训练 loss 降低也不等于测试准确率一定提高。
- LoRA 节省的是可训练参数和优化器状态，基础模型权重仍需加载，不能把 Adapter 大小等同于全部显存占用。
- 完整流水线只编排阶段，不保证参数适合当前硬件；真实运行前仍要核对显存、磁盘、分布式配置和监控依赖。
- SFT 门槛只能阻止明显不合格的模型进入 GRPO，不能代替 GRPO 前后的多指标比较与人工抽查。
- 本文没有运行 Qwen3 的完整训练，配置预览不会产生模型指标，因此不报告 Accuracy、Loss 或 Reward 等数值。

因此，这里的四层架构更像训练底座。后续要把 prompt → completion → reward 扩展为 state → action → environment → observation → next state，训练目标才真正落到多步智能体行为上。

### 参考资料

- [《Hello-Agents》第十一章：Agentic-RL 源文件](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter11/%E7%AC%AC%E5%8D%81%E4%B8%80%E7%AB%A0%20Agentic-RL.md)
- [Hugging Face TRL 文档](https://huggingface.co/docs/trl/index)
- [TRL SFT Trainer](https://huggingface.co/docs/trl/sft_trainer)
- [PEFT LoRA API](https://huggingface.co/docs/peft/main/en/package_reference/lora)
- [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685)
- [TRL GRPO Trainer](https://huggingface.co/docs/trl/grpo_trainer)
- [Accelerate：启动分布式训练脚本](https://huggingface.co/docs/accelerate/en/basic_tutorials/launch)
- [PEFT：Checkpoint 与 Adapter 合并](https://huggingface.co/docs/peft/en/developer_guides/checkpoint)
- [Transformers 文本生成配置](https://huggingface.co/docs/transformers/main_classes/text_generation)
- [GSM8K 数据集](https://huggingface.co/datasets/openai/gsm8k)
- [Training Verifiers to Solve Math Word Problems](https://arxiv.org/abs/2110.14168)
- [Hello-Agents：数据集加载示例](https://github.com/datawhalechina/hello-agents/blob/main/code/chapter11/01_dataset_loading.py)
- [Hello-Agents：奖励函数示例](https://github.com/datawhalechina/hello-agents/blob/main/code/chapter11/02_reward_functions.py)
- [Hello-Agents：LoRA 配置示例](https://github.com/datawhalechina/hello-agents/blob/main/code/chapter11/03_lora_configuration.py)
- [Hello-Agents：SFT 训练示例](https://github.com/datawhalechina/hello-agents/blob/main/code/chapter11/04_sft_training.py)
- [Qwen3-0.6B 模型说明](https://huggingface.co/Qwen/Qwen3-0.6B)
- [DeepSeekMath：GRPO 的论文来源](https://arxiv.org/abs/2402.03300)

### 小结

传统 LLM 训练主要优化 Token 预测和单次回答，Agentic-RL 则把模型视为环境中的策略，关注多步状态、动作、观察与长期回报。SFT 数据提供完整解法，LoRA SFT 让模型先掌握稳定格式；GRPO 数据只保留问题和标准答案，通过同题多候选的相对奖励优化策略。评估要固定测试集与生成条件，同时观察 Accuracy、Accuracy@K、成本、格式和错误分布，不能用训练奖励代替泛化结果。完整流水线进一步把数据质量、SFT、评估门禁、GRPO、再次评估和结果保存串联起来，失败即停止并保留报告；模型合并、量化和 API 部署放在人工验收之后。当前数学实践仍是单轮回答训练，后续还要接入环境、工具与多步轨迹才能成为完整的 Agentic-RL。
