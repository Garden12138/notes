## 智能体性能评估

> 阅读资料：[《Hello-Agents》第十二章 12.1：智能体评估基础](https://datawhalechina.github.io/hello-agents/#/./chapter12/%E7%AC%AC%E5%8D%81%E4%BA%8C%E7%AB%A0%20%E6%99%BA%E8%83%BD%E4%BD%93%E6%80%A7%E8%83%BD%E8%AF%84%E4%BC%B0?id=_121-%e6%99%ba%e8%83%bd%e4%bd%93%e8%af%84%e4%bc%b0%e5%9f%ba%e7%a1%80)
>
> 本节先建立评估的基本概念和代码骨架。BFCL、GAIA、LLM Judge 与 Win Rate 只介绍定位，具体算法留到后续小节。

### 为什么需要评估

Agent 能返回答案，不代表它已经满足需求。修改 Prompt、更换模型、增加工具或调整记忆策略之后，都需要回答三个问题：

1. 预期能力是否真的提高；
2. 哪些任务和边界条件仍然薄弱；
3. 效果提升是否值得增加的时间、Token 和外部调用成本。

如果没有固定评估集，开发过程很容易变成“挑几个问题试一下”。这种观察会受到样本选择、模型随机性和主观印象影响，既不能比较版本，也无法阻止回归。系统评估要把任务、环境、推理参数、评分器和报告格式固定下来，让同一版本可以复现，不同版本可以横向比较。

~~~mermaid
flowchart LR
    V["Agent 版本<br/>模型 + Prompt + 工具 + 记忆"] --> R["评估运行器"]
    D["固定评估集<br/>输入 + 参考答案 + 分类"] --> R
    C["固定运行条件<br/>环境 + 解码参数 + 重试策略"] --> R
    R --> P["逐题预测与轨迹"]
    P --> S["任务对应的评分器"]
    S --> M["准确性、效率、鲁棒性等指标"]
    M --> B{"达到发布门槛?"}
    B -- 否 --> I["分析失败样本并迭代"]
    B -- 是 --> A["归档报告并发布"]
~~~

评估和传统单元测试有相似之处，但不能直接画等号：

| 问题 | 普通软件测试 | Agent 评估 |
| --- | --- | --- |
| 输出形式 | 多数可以精确断言 | 常有多个正确表达 |
| 执行过程 | 通常确定 | 可能受采样、检索结果和外部服务影响 |
| 判断标准 | 返回值和异常 | 任务正确性、过程、成本和安全性 |
| 依赖环境 | 相对稳定 | 网页、工具和知识可能随时间变化 |
| 执行成本 | 通常较低 | 可能包含模型 Token 和付费 API |

因此，单元测试仍用于验证解析器、工具和状态机；基准评估负责测量 Agent 在任务集合上的整体表现，两者缺一不可。

### 智能体评估的三个难点

#### 输出不确定

同一问题可能有多个正确答案，“北京”“北京市”或一段解释都可能满足任务。只做原始字符串比较会产生假阴性；完全依赖语义评分又会引入评审模型偏差。

常见处理顺序是先选择最便宜、最可解释的方法：

1. 结构化任务优先使用规则、Schema、执行结果或 AST；
2. 短答案使用归一化精确匹配或准精确匹配；
3. 开放式回答再使用 F1、语义指标、LLM Judge 或人工复核。

本地基础实现允许一条样本提供多个可接受答案，但不会把 Token F1 当成语义等价判断。

#### 标准随任务变化

天气助手、代码 Agent 和多 Agent 团队没有一个通用的“总分”。工具调用要检查工具名、参数和值；知识问答关心答案；网页任务需要在环境中验证最终状态；协作任务还要观察通信和任务分工。

因此，数据集、评分器和指标必须分离。运行器只负责投递输入、记录输出与成本，具体“怎么算正确”交给基准实现。

#### 评估本身有成本

评估规模、候选数量、重试次数和 Judge 数量都会放大调用成本。实践中可以分层：

- 日常开发运行小规模、确定性的回归集；
- 发布前运行标准评估集并比较历史基线；
- 重大版本再运行完整基准、人工抽查和压力测试。

减少样本可以降低成本，但必须保持抽样规则和随机种子稳定，不能为了得到好结果而挑题。

### 主流评估基准

原文按能力把基准分成三组。表中的规模是章节写作时的概览，实际使用前必须确认基准版本、数据划分和排行榜规则。

| 评估方向 | 基准 | 主要关注点 |
| --- | --- | --- |
| 工具调用 | BFCL | 函数选择、参数构造、多调用、并行调用和无需调用 |
| 工具调用 | ToolBench | 大规模真实 API 场景与工具使用 |
| 工具调用 | API-Bank | API 文档理解和调用 |
| 通用能力 | GAIA | 多步推理、网页、文件、工具及真实任务完成 |
| 通用能力 | AgentBench | 多种交互环境中的 Agent 能力 |
| 通用能力 | WebArena | 在可执行网站环境中完成任务 |
| 多 Agent 协作 | ChatEval | 多 Agent 对话式评审 |
| 多 Agent 协作 | SOTOPIA | 社交互动和目标完成 |
| 多 Agent 协作 | 自定义场景 | 与业务角色、协议和完成条件直接对齐 |

基准名称相同也不代表结果天然可比。模型版本、Agent 脚手架、可用工具、最大步骤、检索时间、失败重试和评估集版本都要进入实验记录。

### 常用指标

#### 准确性

若每条样本的通过结果为 $m_i\in\{0,1\}$，准确率为：

$$
\operatorname{Accuracy}
=\frac{1}{N}\sum_{i=1}^{N}m_i
$$

Exact Match 是产生 $m_i$ 的一种匹配方法，Accuracy 是聚合后的比例，两者不是同一个层级。对于多个参考答案 $G_i$，只要预测 $P_i$ 与其中一个匹配即可：

$$
m_i=\max_{g\in G_i}\operatorname{EM}(P_i,g)
$$

F1 同时考虑预测 Token 的精确率和召回率：

$$
\operatorname{Precision}=\frac{|\hat{Y}\cap Y|}{|\hat{Y}|},
\qquad
\operatorname{Recall}=\frac{|\hat{Y}\cap Y|}{|Y|}
$$

$$
F_1=\frac{2\cdot\operatorname{Precision}\cdot\operatorname{Recall}}
{\operatorname{Precision}+\operatorname{Recall}}
$$

F1 适合观察词项重合，不能证明事实正确或推理成立。工具参数、数学答案和程序执行结果应使用更直接的验证器。

#### 效率

Response Time 记录一次任务从开始到拿到最终结果的时间；Token Usage 应来自模型 SDK 或网关返回的 usage，而不是用字符数估算。只报告平均响应时间会掩盖长尾，生产评估通常还要补充 P50、P95 和超时率。

效率指标必须和任务质量一起看。一个不调用必要工具的 Agent 可能更快、Token 更少，但任务是错的。

#### 鲁棒性

“错误率”至少有两种含义：

- 任务错误率：答案未通过，包括答错和执行失败，即 $1-\operatorname{Accuracy}$；
- 执行失败率：超时、异常或外部服务失败所占比例。

把二者混在一起，就无法判断应该修改推理能力还是修复运行环境。本地实现分别记录 `task_error_rate` 和 `execution_failure_rate`。

若有 $F$ 条样本首次失败，其中 $R$ 条重试后成功，恢复率为：

$$
\operatorname{RecoveryRate}=\frac{R}{F}
$$

没有初始失败时，恢复率应为空，而不是虚构为 0% 或 100%。重试也不能掩盖故障：报告必须保留每次错误、尝试次数和是否恢复。

#### 协作

多 Agent 系统除了最终任务完成度，还可观察消息数量、无效往返、角色越界、重复工作和通信 Token。通信越少不一定越好；需要结合结果质量，判断消息是否推动了任务。

### HelloAgents 的评估体系

本章后续选择三类场景：

~~~mermaid
flowchart TB
    E["HelloAgents Evaluation System"]
    E --> BFCL["BFCL<br/>工具调用能力"]
    E --> GAIA["GAIA<br/>通用助手能力"]
    E --> DATA["数据生成质量"]
    BFCL --> AST["AST / 结构化调用匹配"]
    GAIA --> QEM["准精确匹配 + 任务证据"]
    DATA --> JUDGE["LLM Judge"]
    DATA --> WIN["Win Rate"]
    DATA --> HUMAN["人工验证"]
    AST --> REPORT["统一记录与报告"]
    QEM --> REPORT
    JUDGE --> REPORT
    WIN --> REPORT
    HUMAN --> REPORT
~~~

三类场景的“数据—执行—评分”流程相同，但评分器不同：

1. Dataset 提供输入、参考答案、分类和元数据；
2. Evaluator 运行 Agent，并保存预测、耗时、Token 和异常；
3. Metrics 根据任务规则评分和聚合；
4. Tool 再把评估能力接入 HelloAgents 的统一工具系统。

12.1 只完成前三步所需的通用底座，`benchmarks/` 暂不实现具体算法。这样后续增加 BFCL、GAIA 时不需要复制运行、重试和报告逻辑。

### 代码实践

#### 目录与接口

新增代码结构：

~~~text
hello_agents/evaluation/
├── __init__.py
├── models.py
├── metrics.py
├── runner.py
└── benchmarks/
    └── __init__.py
~~~

- [models.py](./code/HelloAgents/hello_agents/evaluation/models.py) 定义评估样本、逐题记录、Token 用量和汇总报告。
- [metrics.py](./code/HelloAgents/hello_agents/evaluation/metrics.py) 实现归一化 Exact Match、Token F1 和分类汇总。
- [runner.py](./code/HelloAgents/hello_agents/evaluation/runner.py) 负责逐题调用、计时、异常重试和使用量采集。
- [agent_evaluation_basics_demo.py](./code/HelloAgents/examples/agent_evaluation_basics_demo.py) 使用固定 Agent 验证完整流程，不调用模型或网络。

一个评估样本同时保存稳定 ID、分类和多个可接受答案：

~~~python
case = EvaluationCase(
    case_id="math_001",
    prompt="6 × 7 等于多少？",
    expected=("42", "42.0"),
    category="qa",
)
~~~

`EvaluationRunner` 接受任何 `Callable[[str], str]`，因此可以直接传入 `SimpleAgent.run`，也能使用固定函数做回归测试：

~~~python
runner = EvaluationRunner(
    predictor=agent.run,
    max_retries=1,
    usage_getter=lambda: agent.last_usage,
)
report = runner.evaluate(cases)
print(report.to_dict())
~~~

重试只处理执行异常，不会因为答案错误而让 Agent 反复作答，否则测试时计算预算会偷偷增加。`usage_getter` 也是显式接口：没有可靠统计时，报告会标记 unavailable，不填一个看似精确的估算值。

#### 实践结果

运行：

~~~bash
cd code/HelloAgents
PYTHONPATH=. python examples/agent_evaluation_basics_demo.py
~~~

控制台输出：

~~~text
=== 12.1 智能体评估基础实践 ===
samples: 4
accuracy: 75.00%
task_error_rate: 25.00%
execution_failure_rate: 0.00%
failure_recovery_rate: 100.00%
token_usage: {'available': True, 'covered_samples': 4, 'input_tokens': 34, 'output_tokens': 14, 'total_tokens': 48}
category_accuracy:
  qa: 100.00%
  robustness: 100.00%
  tool_use: 0.00%
response_time_recorded: True
token_f1_example: 0.8571
~~~

四条样本中三条通过，因此 Accuracy 为 75%。工具使用样本返回了不符合预期的回答，所以 `tool_use` 分类准确率为 0%；鲁棒性样本首次抛出超时，第二次成功，最终执行失败率为 0%，恢复率为 100%。这两个数并不矛盾：前者看最终是否仍失败，后者看初始故障能否恢复。

Token F1 示例中，`use search tool` 的三个 Token 都出现在 `use the search tool` 中，Precision 为 1，Recall 为 $3/4$，所以 $F_1=0.8571$。

### 实践边界

- 固定 Demo Agent 只用于验证评估代码，75% 不是任何真实模型的能力分数。
- 当前 Exact Match 只做 Unicode、大小写和空白归一化；它不是 BFCL AST 匹配，也不是 GAIA 准精确匹配。
- Token F1 按英文单词、数字和单个汉字切分，适合教学和回归测试，不等于模型 Tokenizer。
- 重试恢复只覆盖异常场景；内容错误不自动重试。
- 响应时间由本机单进程测量，比较不同 Agent 时仍需固定硬件、并发和外部服务条件。
- 12.1 基础实现不需要 `bfcl-eval`、`datasets` 或 Judge 模型。原文中的评估扩展依赖应在进入对应基准后再安装，避免提前引入版本冲突。

### 参考资料

- [《Hello-Agents》第十二章：智能体性能评估源文件](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter12/%E7%AC%AC%E5%8D%81%E4%BA%8C%E7%AB%A0%20%E6%99%BA%E8%83%BD%E4%BD%93%E6%80%A7%E8%83%BD%E8%AF%84%E4%BC%B0.md)
- [Gorilla / BFCL 论文](https://arxiv.org/abs/2305.15334)
- [ToolLLM / ToolBench 论文](https://arxiv.org/abs/2307.16789)
- [API-Bank 论文](https://arxiv.org/abs/2304.08244)
- [GAIA 论文](https://arxiv.org/abs/2311.12983)
- [AgentBench 论文](https://arxiv.org/abs/2308.03688)
- [WebArena 论文](https://arxiv.org/abs/2307.13854)
- [SOTOPIA 论文](https://arxiv.org/abs/2310.11667)

### 小结

Agent 评估不是给一次回答打分，而是在固定任务、环境和运行配置下，持续收集可比较的证据。不同任务需要不同评分器：工具调用看结构和执行，短答案可用精确或准精确匹配，开放式内容再考虑 Judge 和人工验证；准确性还要和响应时间、Token、执行失败及恢复能力一起分析。本节代码完成了通用样本、指标、运行和报告底座，并用确定性样例验证了准确率、分类指标、重试恢复和使用量统计，具体 BFCL、GAIA 与数据生成评估留给后续章节实现。
