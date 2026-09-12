## 智能体性能评估

> 阅读资料：[《Hello-Agents》第十二章 12.1：智能体评估基础](https://datawhalechina.github.io/hello-agents/#/./chapter12/%E7%AC%AC%E5%8D%81%E4%BA%8C%E7%AB%A0%20%E6%99%BA%E8%83%BD%E4%BD%93%E6%80%A7%E8%83%BD%E8%AF%84%E4%BC%B0?id=_121-%e6%99%BA%E8%83%BD%E4%BD%93%E8%AF%84%E4%BC%B0%E5%9F%BA%E7%A1%80)、[12.2：BFCL——工具调用能力评估](https://datawhalechina.github.io/hello-agents/#/./chapter12/%E7%AC%AC%E5%8D%81%E4%BA%8C%E7%AB%A0%20%E6%99%BA%E8%83%BD%E4%BD%93%E6%80%A7%E8%83%BD%E8%AF%84%E4%BC%B0?id=_122-bfcl%ef%bc%9a%e5%b7%a5%e5%85%b7%e8%b0%83%e7%94%a8%e8%83%bd%e5%8a%9b%e8%af%84%e4%bc%b0)
>
> 补充阅读：[12.3：GAIA——通用 AI 助手能力评估](https://datawhalechina.github.io/hello-agents/#/./chapter12/%E7%AC%AC%E5%8D%81%E4%BA%8C%E7%AB%A0%20%E6%99%BA%E8%83%BD%E4%BD%93%E6%80%A7%E8%83%BD%E8%AF%84%E4%BC%B0?id=_123-gaia%ef%bc%9a%e9%80%9a%e7%94%a8-ai-%e5%8a%a9%e6%89%8b%e8%83%bd%e5%8a%9b%e8%af%84%e4%bc%b0)、[12.4：数据生成质量评估](https://datawhalechina.github.io/hello-agents/#/./chapter12/%E7%AC%AC%E5%8D%81%E4%BA%8C%E7%AB%A0%20%E6%99%BA%E8%83%BD%E4%BD%93%E6%80%A7%E8%83%BD%E8%AF%84%E4%BC%B0?id=_124-%e6%95%b0%e6%8d%ae%e7%94%9f%e6%88%90%e8%b4%a8%e9%87%8f%e8%af%84%e4%bc%b0)
>
> 本文先建立评估底座，再实现 BFCL 工具调用评估、GAIA 通用任务评估和 AIME 风格数据生成质量评估。

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

基础部分先完成前三步所需的通用底座；BFCL 再在 `benchmarks/` 中实现自己的数据结构和评分规则。后续增加 GAIA 时仍可复用通用的运行、计时和报告模型。

### 基础代码实践

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

### 基础实践边界

- 固定 Demo Agent 只用于验证评估代码，75% 不是任何真实模型的能力分数。
- 当前 Exact Match 只做 Unicode、大小写和空白归一化；它不是 BFCL AST 匹配，也不是 GAIA 准精确匹配。
- Token F1 按英文单词、数字和单个汉字切分，适合教学和回归测试，不等于模型 Tokenizer。
- 重试恢复只覆盖异常场景；内容错误不自动重试。
- 响应时间由本机单进程测量，比较不同 Agent 时仍需固定硬件、并发和外部服务条件。
- 12.1 基础实现不需要 `bfcl-eval`、`datasets` 或 Judge 模型。原文中的评估扩展依赖应在进入对应基准后再安装，避免提前引入版本冲突。

### BFCL：工具调用能力评估

BFCL（Berkeley Function Calling Leaderboard）不评价工具执行后的自然语言答案，而是检查模型能否把请求转换成正确的函数调用。核心链路是：理解请求、选择函数、填写参数、在复杂场景中决定调用数量和顺序。

#### 四类基础任务

| 类别 | 要解决的问题 | 典型错误 |
| --- | --- | --- |
| Simple | 已给出一个函数，构造一次正确调用 | 函数名或参数值错误 |
| Multiple | 给出多个候选函数，选择正确的一个 | 选错功能相近的函数 |
| Parallel | 同一请求需要多个互相独立的调用 | 漏调用、重复调用或参数串位 |
| Irrelevance | 判断请求是否根本不需要现有函数 | 为了调用而调用 |

这四类可以理解为难度递进，而不是四套互不相关的测试。Simple 先检查“会不会填”，Multiple 增加“会不会选”，Parallel 增加“会不会拆”，Irrelevance 再检查“会不会停”。当前 BFCL V4 还包含不同语言、Live、Multi-turn 和 Agentic 等更细类别；学习本节时先掌握上述单轮主线。

#### 数据和 Ground Truth

官方文件虽然使用 `.json` 后缀，实际采用 JSONL：每行是一条完整 JSON 记录。问题文件与 `possible_answer/` 下的答案文件通过 `id` 对齐：

~~~text
bfcl_eval/data/
├── BFCL_v4_simple_python.json
└── possible_answer/
    └── BFCL_v4_simple_python.json
~~~

问题记录同时给出对话和函数 Schema：

~~~json
{
  "id": "simple_python_0",
  "question": [[{
    "role": "user",
    "content": "Find the area of a triangle with a base of 10 units and height of 5 units."
  }]],
  "function": [{
    "name": "calculate_triangle_area",
    "parameters": {
      "type": "dict",
      "properties": {
        "base": {"type": "integer"},
        "height": {"type": "integer"}
      },
      "required": ["base", "height"]
    }
  }]
}
~~~

对应答案不是普通的 `name + arguments`，而是“函数名映射到参数可接受值集合”：

~~~json
{
  "id": "simple_python_0",
  "ground_truth": [{
    "calculate_triangle_area": {
      "base": [10],
      "height": [5],
      "unit": ["units", ""]
    }
  }]
}
~~~

数组表示多个可接受值，不是让模型把参数传成数组；空字符串表示这个可选参数可以省略。因此，Ground Truth 不能直接和预测字典做字符串比较。加载器还要检查两边 ID 是否唯一且一一对应，否则少一行答案也可能让后面的样本错位。

#### 评估流程

~~~mermaid
flowchart LR
    D["BFCL 问题 JSONL"] --> L["Dataset 按 ID 合并"]
    G["possible_answer JSONL"] --> L
    L --> P["问题 + 函数 Schema<br/>构造 Prompt"]
    P --> A["Agent 生成调用"]
    A --> X["抽取 JSON / Python / TOOL_CALL"]
    X --> N["统一为 name + arguments"]
    N --> M["结构匹配"]
    M --> R["准确率、分类结果<br/>参数诊断与报告"]
    N --> E["导出官方 JSONL envelope"]
    E --> O["BFCL 官方评估器"]
~~~

每条 BFCL 样本彼此独立。若复用 `SimpleAgent` 实例，历史对话会不断累积，使后面的样本看到前面的题目。本地评估器因此会在每题前调用 `clear_history()`；它只重置会话，不重建模型客户端。

#### AST 匹配在匹配什么

这里的重点不是比较源码字符串，而是先把不同输出归一化为结构：

~~~python
{
    "name": "calculate_triangle_area",
    "arguments": {"height": 5, "base": 10},
}
~~~

本地实现支持三类教学输出：

~~~text
{"name":"get_weather","arguments":{"city":"Beijing"}}
get_weather(city="Beijing")
[TOOL_CALL:get_weather:city=Beijing]
~~~

匹配规则如下：

- 函数名必须准确，`get_weather` 和 `get_temperature` 不等价；
- 关键字参数按名称比较，不受书写顺序影响；
- Ground Truth 中同一参数的多个候选值任选其一；
- 参数候选值包含空字符串时，允许省略该参数；
- Parallel 的调用列表按无序多重集合匹配，但调用数必须一致；
- Irrelevance 的正确结果是没有抽取到任何调用；
- Python 调用中的常量算术会在受限 AST 内求值，所以 `x=2+3` 可与 `x=5` 匹配；不会执行函数、变量访问或任意代码。

最后一条不能用 Python `eval()` 实现。评估数据和模型输出都属于外部输入，直接执行会把评分器变成代码执行入口。本地解析器只接受字面量以及有限的加减乘除、取模和幂运算。

若第 $i$ 个样本的结构匹配结果为 $m_i\in\{0,1\}$，则：

$$
\operatorname{Accuracy}
=\operatorname{ASTMatchRate}
=\frac{1}{N}\sum_{i=1}^{N}m_i
$$

分类准确率用于定位 Simple、Multiple、Parallel、Irrelevance 中哪一层出了问题；加权准确率用于汇总类别，但必须同时保存权重。`parameter_accuracy`、函数名准确率和调用级 F1 是本地诊断指标，能区分“选对函数但填错参数”和“完全选错函数”，不应冒充 BFCL 官方榜单指标。

### BFCL 代码实践

#### 实现结构

~~~text
hello_agents/evaluation/benchmarks/bfcl/
├── dataset.py
├── ast_matcher.py
├── metrics.py
└── evaluator.py

hello_agents/tools/builtin/
└── bfcl_evaluation_tool.py
~~~

- [dataset.py](./code/HelloAgents/hello_agents/evaluation/benchmarks/bfcl/dataset.py) 同时兼容 JSON 数组和官方 JSONL，按 ID 合并问题与答案。
- [ast_matcher.py](./code/HelloAgents/hello_agents/evaluation/benchmarks/bfcl/ast_matcher.py) 抽取 JSON、Python 调用和 HelloAgents 文本协议，并执行安全的结构匹配。
- [metrics.py](./code/HelloAgents/hello_agents/evaluation/benchmarks/bfcl/metrics.py) 汇总整体、分类、函数名、参数和调用级 F1。
- [evaluator.py](./code/HelloAgents/hello_agents/evaluation/benchmarks/bfcl/evaluator.py) 负责构造 Prompt、隔离样本、调用 Agent、计时、导出 JSONL 和生成报告。
- [bfcl_evaluation_tool.py](./code/HelloAgents/hello_agents/tools/builtin/bfcl_evaluation_tool.py) 把完整流程接入统一 `Tool` 接口。
- [bfcl_evaluation_demo.py](./code/HelloAgents/examples/bfcl_evaluation_demo.py) 使用五条本地样例覆盖四类任务，不调用模型或网络。
- [bfcl_evaluate.py](./code/HelloAgents/examples/bfcl_evaluate.py) 从环境变量创建真实 `SimpleAgent`，用于显式运行小样本或完整评估。

获取完整数据时仍以官方仓库为准：

~~~bash
git clone https://github.com/ShishirPatil/gorilla.git temp_gorilla
cd temp_gorilla/berkeley-function-call-leaderboard
ls bfcl_eval/data/BFCL_v4_*.json
ls bfcl_eval/data/possible_answer/BFCL_v4_*.json
~~~

加载一个类别：

~~~python
from hello_agents import BFCLDataset

dataset = BFCLDataset(
    bfcl_data_dir="./temp_gorilla/berkeley-function-call-leaderboard/bfcl_eval/data",
    category="simple_python",
)
samples = dataset.load(max_samples=5)
print(dataset.get_available_categories())
~~~

直接使用评估器：

~~~python
from hello_agents import BFCLEvaluator

evaluator = BFCLEvaluator(dataset, category="simple_python")
result = evaluator.evaluate(agent, max_samples=5)
print(result["overall_accuracy"])
~~~

也可以通过 Tool 一次完成本地评估、结果导出和报告生成。当前 `Tool.run()` 的统一接口接收参数字典，因此不是 `run(agent=...)`：

~~~python
from hello_agents import BFCLEvaluationTool

tool = BFCLEvaluationTool(
    "./temp_gorilla/berkeley-function-call-leaderboard/bfcl_eval/data"
)
result = tool.run({
    "agent": agent,
    "category": "simple_python",
    "max_samples": 5,
    "output_dir": "./evaluation_results",
    "run_official_eval": False,
})
~~~

真实模型入口会读取现有 LLM 环境变量；只有执行这条命令才会调用模型：

~~~bash
PYTHONPATH=. python examples/bfcl_evaluate.py \
  --data-dir ./temp_gorilla/berkeley-function-call-leaderboard/bfcl_eval/data \
  --category simple_python \
  --max-samples 5
~~~

导出文件仍采用 `.json` 后缀，但内容是官方结果 envelope 的 JSONL：

~~~json
{"id":"simple_python_0","result":"calculate_triangle_area(base=10, height=5)","latency":0.12}
~~~

`result` 保留 Agent 的原始响应，由官方的模型 Handler 负责解码。不同模型的原生 Function Calling 返回结构并不完全相同，因此导出成功只表示文件结构可交接，不等于已经得到官方分数。

#### 本地实践结果

运行：

~~~bash
cd code/HelloAgents
PYTHONPATH=. python examples/bfcl_evaluation_demo.py
~~~

控制台输出：

~~~text
=== 12.2 BFCL 工具调用评估实践 ===
available_categories: ['demo']
samples: 5
accuracy: 80.00%
ast_match_rate: 80.00%
weighted_accuracy: 87.50%
function_name_accuracy: 100.00%
parameter_accuracy: 85.71%
call_f1: 80.00%
category_accuracy:
  irrelevance: 100.00%
  multiple: 100.00%
  parallel: 100.00%
  simple: 50.00%
constant_arithmetic_match: True
official_jsonl_records: 5
report_generated: True
official_evaluation: not_run
~~~

五条样本中故意保留一条错误：题目要求查询 Beijing，固定 Agent 却传入 Shanghai，所以总体准确率为 80%，Simple 为 50%。其余样本验证了参数换序、从候选函数中选择、并行调用换序以及无需调用。四个类别默认等权，因此加权准确率是 $(50\%+100\%+100\%+100\%)/4=87.5\%$，它和按五条样本计算的微平均 80% 含义不同。

函数名准确率仍为 100%，说明错误样本选对了 `get_weather`；参数准确率下降到 85.71%，把问题定位到了参数值。`constant_arithmetic_match: True` 则确认 `2+3` 与 `5` 能在安全常量表达式范围内匹配。

#### 本地评分与官方评分的边界

本地 Matcher 用于理解算法、调试输出格式和做小规模回归，不是官方 BFCL Evaluator 的等价重写。官方实现还会结合函数 Schema、语言、模型 Handler、类别和版本执行更完整的类型转换及判定。要报告可与排行榜比较的成绩，必须固定 Gorilla 仓库提交、模型 Handler、数据版本和生成参数，并使用该版本自带的官方评估器。

`BFCLEvaluationTool` 因此默认 `run_official_eval=False`。只有显式提供 `model_name`、官方仓库目录并确认本机已安装对应 CLI 时，才会复制结果并运行原文章节所示命令：

~~~bash
bfcl evaluate \
  --model Qwen/Qwen3-8B \
  --test-category simple_python \
  --partial-eval
~~~

`--partial-eval` 只对结果文件中已有的样本评分，适合冒烟测试，不能与完整类别分数混用。CLI 参数和支持的模型名会随 BFCL 版本变化，运行前应查看当前检出版本的 README 与 `bfcl evaluate --help`。

本地 Dataset、Matcher 和 Metrics 不新增第三方依赖；完整官方评分环境应按所检出 Gorilla/BFCL 版本的安装说明配置，不把某个时期的包名或参数写死到 HelloAgents 中。

实践时可以按以下顺序推进：先用 5 条样本检查输出能否解析，再扩大到 50 条定位主要错误类型，最后运行完整类别；类别顺序从 Simple、Multiple 到 Parallel、Irrelevance。比较两个 Agent 时，除模型和 Prompt 外，还要固定数据提交、最大步骤、工具 Schema、温度、重试和样本数。

原文使用 `SimpleAgent` 复现文本调用协议，这适合观察 Prompt 和解析器。若改用原生 Function Calling，不能只调用当前 `FunctionCallAgent.run()`：它会执行工具并返回最终文本，原始 `tool_calls` 已不在返回值中。正式适配时应在执行前捕获 SDK 的结构化调用，再交给 BFCL 对应模型 Handler，避免把“工具执行后的回答”当成“待评分的函数调用”。

### GAIA：通用 AI 助手能力评估

BFCL 把能力范围收窄到“能否生成正确的函数调用”；GAIA 关注的是 Agent 能否在真实问题中组合推理、检索、网页浏览、文件处理和工具调用，并给出一个可核验的短答案。GAIA 论文共设计了 466 道题，问题对人类通常不难，但对需要自行选择工具和组织步骤的系统更有区分度。

| 对比项 | BFCL | GAIA |
| --- | --- | --- |
| 主要对象 | 一次或多次函数调用 | 完整问题解决过程 |
| 输入 | 用户请求、函数 Schema | 问题，部分题目带附件 |
| 关键能力 | 选函数、填参数、判断是否调用 | 推理、搜索、文件处理、工具协作 |
| 核心输出 | 结构化调用 | 简短最终答案 |
| 主要评分 | AST / 结构匹配 | 准精确匹配与分级准确率 |

#### 三个难度级别

| Level | 特征 | 对 Agent 的要求 |
| --- | --- | --- |
| 1 | 路径直接，步骤少 | 理解问题并完成少量检索或计算 |
| 2 | 需要多步信息组合 | 拆解问题，协调多个工具，处理中间结果 |
| 3 | 路径长、附件或信息源复杂 | 自主规划、纠错、跨模态处理与证据核验 |

Level 不是按题目文字长度划分。一个问题可能只有一句话，却要先定位网页、再读取表格、换算单位并交叉验证。真正增加的是工具选择和状态管理难度。章节使用的 2023 版验证集共有 165 条，Level 1、2、3 分别为 53、62、50 条；测试集答案不公开，用于排行榜评估。

#### 数据结构与受限访问

每条记录的主干字段是：

~~~text
task_id              稳定样本 ID
Question             问题
Level                难度 1 / 2 / 3
Final answer         验证集参考答案；测试集可能为空
file_name/file_path  可选附件
Annotator Metadata   标注步骤、耗时和所需工具
~~~

GAIA 是 Gated Dataset。使用前要在 Hugging Face 接受数据条款并配置 `HF_TOKEN`，验证集和测试集内容不能复制到公开仓库。本次代码只提交自编的五条固定样例，不包含 GAIA 原题。

原文章节按 `2023/{validation,test}/metadata.jsonl` 讲解。官方仓库在 2025 年 10 月增加了 `metadata.parquet` 及各 Level 的 Parquet 文件，列名和附件相对路径保持不变。因此 [dataset.py](./code/HelloAgents/hello_agents/evaluation/benchmarks/gaia/dataset.py) 同时支持旧 JSONL 和当前 Parquet；后者需要 `pandas` 与 `pyarrow`。

下载不会在构造对象时自动发生。这样本地 Demo 和模块导入不会意外访问受限数据；只有 `auto_download=True` 或命令行显式传入 `--download` 时，加载器才调用 `snapshot_download`。

#### 评估流程

~~~mermaid
flowchart LR
    D["GAIA metadata<br/>问题 + Level + 参考答案"] --> L["GAIADataset<br/>加载、过滤、解析附件路径"]
    F["可选附件<br/>PDF / 图片 / 表格等"] --> L
    L --> P["构造问题与附件提示"]
    P --> A["Agent<br/>规划 + 浏览 + 文件工具 + 计算"]
    A --> X["提取最后一个<br/>FINAL ANSWER"]
    X --> N["按参考答案类型归一化"]
    N --> M["准精确匹配"]
    M --> R["整体与分级指标"]
    R --> O["JSONL + Markdown 报告"]
~~~

加载器只负责把附件解析为受数据目录约束的绝对路径，并标记文件是否存在。真正的图片识别、PDF 阅读或表格分析仍要由被测 Agent 的工具完成；把路径拼进 Prompt 不等于已经读取附件。

每条题目相互独立，评估器在运行前调用 `clear_history()`，避免上一题污染下一题。Agent 最终应输出：

~~~text
FINAL ANSWER: [answer]
~~~

评估器取最后一个 `FINAL ANSWER`，防止模型在推理说明中先复述格式模板。没有该标记时，才尝试“最终答案”“Answer”等备用标记，最后退回到末尾非空行。

#### 准精确匹配

准精确匹配不是模糊语义判断，而是先归一化，再做严格相等。令 $\mathcal{N}$ 为归一化函数，则第 $i$ 条样本的得分可写为：

$$
m_i=\mathbf{1}\!\left[\mathcal{N}(A_{\mathrm{pred},i})
=\mathcal{N}(A_{\mathrm{true},i})\right]
$$

| 答案类型 | 归一化规则 | 示例 |
| --- | --- | --- |
| 数字 | 去千位分隔符、货币符号和百分号，统一小数尾零 | `$1,234.50` → `1234.5` |
| 字符串 | Unicode 归一化、转小写、去开头冠词、多余空白和末尾标点 | `The Pacific Ocean.` → `pacific ocean` |
| 列表 | 逗号切分，逐项归一化，再排序 | `Paris, Berlin, London` → `berlin,london,paris` |

这里有一个容易漏掉的边界：`$1,234.56` 含逗号，但它是数字，不是列表。如果先执行“见逗号就切分”，会得到错误结果。[quasi_exact_match.py](./code/HelloAgents/hello_agents/evaluation/benchmarks/gaia/quasi_exact_match.py) 会根据参考答案确定类型，并优先尝试数字解析。

准精确匹配便宜、确定、可复现，适合 GAIA 的短答案设计；它不会把“42”和“四十二”自动视为相同，也不能判断较长解释是否语义等价。代码额外提供了列表项或文本 Token 的 `partial_match_score`，仅用于定位“部分正确”的本地诊断，不能当作 GAIA 官方分数。

#### 指标与边界

可评分样本的整体匹配率为：

$$
\operatorname{ExactMatchRate}
=\frac{1}{N}\sum_{i=1}^{N}m_i
$$

各 Level 分别计算准确率。难度递进下降率用于观察能力随难度增加的衰减：

$$
\operatorname{DropRate}_{\ell\rightarrow\ell+1}
=\frac{\operatorname{Accuracy}_{\ell}
-\operatorname{Accuracy}_{\ell+1}}
{\operatorname{Accuracy}_{\ell}}
$$

若较低 Level 没有样本或准确率为 0，分母无意义，代码返回 `None`。下降率也可能为负，表示当前样本上高 Level 的准确率反而更高，不应强行截断为 0。

平均推理步骤只统计回答正确且 Agent 明确暴露 `last_run_steps` 的样本。`Annotator Metadata` 中的步骤是人工给出的参考路径，不是模型实际走过的步骤，用它冒充 Agent 步数会让效率指标失真。没有实际轨迹时，该指标和覆盖率保持为空。

测试集参考答案可能不可见。[metrics.py](./code/HelloAgents/hello_agents/evaluation/benchmarks/gaia/metrics.py) 会把这类记录标为不可评分，仍允许生成预测文件，但不会把空答案算成错误或产生一个假的 0 分。

### GAIA 代码实践

#### 实现结构

~~~text
hello_agents/evaluation/benchmarks/gaia/
├── dataset.py
├── quasi_exact_match.py
├── metrics.py
└── evaluator.py

hello_agents/tools/builtin/
└── gaia_evaluation_tool.py

examples/
├── gaia_evaluation_demo.py
├── gaia_evaluate.py
└── data/gaia/2023/validation/
    ├── metadata.jsonl
    └── sample_notes.txt
~~~

- [evaluator.py](./code/HelloAgents/hello_agents/evaluation/benchmarks/gaia/evaluator.py) 负责样本隔离、Prompt 构造、答案提取、匹配、导出和报告。
- [gaia_evaluation_tool.py](./code/HelloAgents/hello_agents/tools/builtin/gaia_evaluation_tool.py) 把 `Dataset → Evaluator → Metrics → Artifacts` 接入统一 `Tool.run(parameters)` 接口。
- [gaia_evaluation_demo.py](./code/HelloAgents/examples/gaia_evaluation_demo.py) 使用本地固定 Agent 和原创样例验证流程，不调用模型和网络。
- [gaia_evaluate.py](./code/HelloAgents/examples/gaia_evaluate.py) 是真实模型入口，网络调用和受限数据下载都由命令行显式触发。

直接使用加载器和评估器：

~~~python
from hello_agents import GAIADataset, GAIAEvaluator

dataset = GAIADataset(
    split="validation",
    level=1,
    local_data_dir="./data/gaia",
    auto_download=False,
)
result = GAIAEvaluator(dataset, level=1).evaluate(agent, max_samples=5)
print(result["exact_match_rate"])
~~~

通过 Tool 运行完整流程：

~~~python
from hello_agents import GAIAEvaluationTool

result_json = GAIAEvaluationTool("./data/gaia").run({
    "agent": agent,
    "split": "validation",
    "level": 1,
    "max_samples": 5,
    "output_dir": "./evaluation_results",
    "download": False,
})
~~~

首次获取官方数据时，先在 Hugging Face 页面接受条款，再显式下载：

~~~bash
pip install huggingface_hub pandas pyarrow
# 官方当前的 Parquet 数据还需要：pip install pandas pyarrow
export HF_TOKEN="your_huggingface_token"
PYTHONPATH=. python examples/gaia_evaluate.py \
  --data-dir ./data/gaia \
  --split validation \
  --level 1 \
  --max-samples 5 \
  --download
~~~

`HF_TOKEN` 只放在运行环境，不写入代码或提交到仓库。当前真实入口使用 `SimpleAgent` 演示评估管线，本身没有配置浏览器、文件解析器和搜索工具，因此不能代表一个完整 GAIA Agent；正式测评前还要按任务需求接入这些工具，并固定最大步骤、超时和重试策略。

#### 本地实践结果

运行确定性 Demo：

~~~bash
cd code/HelloAgents
PYTHONPATH=. python examples/gaia_evaluation_demo.py
~~~

控制台输出：

~~~text
=== 12.3 GAIA 通用助手评估实践 ===
samples: 5
attachments: 1
exact_match_rate: 80.00%
partial_match_rate: 80.00%
level_accuracy:
  level_1: 100.00%
  level_2: 100.00%
  level_3: 0.00%
difficulty_drop_rates:
  level_1_to_2: 0.00%
  level_2_to_3: 100.00%
average_reasoning_steps: 1.50
numeric_comma_match: True
normalized_list: berlin,london,paris
gaia_jsonl_records: 5
report_generated: True
submission_guide_generated: True
official_submission: not_run
~~~

五条样例覆盖数字、短文本、无序列表和附件路径，并故意让一条 Level 3 样例答错，因此整体为 4/5。Level 1 与 Level 2 都通过，Level 3 为 0%，所以两级之间的下降率分别为 0% 和 100%。`average_reasoning_steps=1.50` 来自固定 Agent 为四条正确样例记录的实际步骤数 $1、1、2、2$。

`numeric_comma_match=True` 验证带千位分隔符的数字不会误判为列表。Demo 生成五条 JSONL、Markdown 报告和提交检查说明，但全部写入系统临时目录，不污染仓库。

#### 本地结果与官方成绩

这次 80% 只说明本地实现的加载、附件传递、答案抽取、归一化、分级统计和导出能连通，不是任何真实模型的 GAIA 成绩。导出的章节兼容格式为：

~~~json
{"task_id":"demo_gaia_001","model_answer":"$1,234.50","reasoning_trace":"..."}
~~~

生成文件不等于已向排行榜提交。提交前仍应查看当前 [GAIA 官方排行榜](https://huggingface.co/spaces/gaia-benchmark/leaderboard) 的格式和流程，记录数据版本、模型版本、Prompt、全部工具、搜索日期、最大步骤及失败处理，并遵守数据集不可公开转发的条款。

### 数据生成质量评估

前面的 BFCL 和 GAIA 都在评估 Agent 做题或调用工具的能力，12.4 换了一个对象：模型生成的数据本身。章节以 AIME 风格数学题为例，希望生成可用于训练或评测的新题。此时“JSON 能解析”只是格式合格，还要继续检查题目是否正确、清楚、达到目标难度，解答能否支撑答案。

AIME 的最终答案是 $0$ 到 $999$ 的整数。实践把目标难度设在 AIME 第 6～9 题附近，主题限定为 Algebra、Geometry、Number Theory、Combinatorics 和 Probability。生成时可从历年题目中取一题作为风格参考，评估时则换用独立的 AIME 2025 参考集，避免用同一批样本既引导生成又判断质量。

#### 三层评估闭环

单一评分很难覆盖数据质量，因此原文组合了三种方法：LLM Judge 负责规模化绝对评分，Win Rate 负责相对比较，人工审核处理高风险和有争议的样本。

~~~mermaid
flowchart LR
    H["历年 AIME 参考题<br/>仅提供风格与难度"] --> G["AIMEGenerator<br/>生成全新题目"]
    G --> V["Schema 校验<br/>题目 + 整数答案 + 解答 + 主题"]
    V --> D["生成数据集"]
    D --> J["LLM Judge<br/>四维绝对评分"]
    D --> W["Win Rate<br/>与 AIME 2025 成对比较"]
    R["独立真实参考集"] --> W
    D --> U["人工审核<br/>通过 / 驳回 / 待修改"]
    J --> C["综合报告"]
    W --> C
    U --> C
~~~

这三层回答的问题不同：

| 方法 | 主要问题 | 优点 | 主要风险 |
| --- | --- | --- | --- |
| LLM Judge | 单题在各维度达到什么水平 | 快，能给理由，适合批量筛查 | 评分尺度、模型偏好和 Prompt 会影响结果 |
| Win Rate | 生成题相对真实题哪一个更好 | 相对判断通常比绝对打分稳定 | 位置偏差、配对抽样和字段不对称 |
| 人工审核 | 这条数据最终能否进入下游 | 能发现隐蔽数学错误与歧义 | 慢、成本高，也存在评审差异 |

LLM Judge 和 Win Rate 都只是筛查证据，不是数学证明；要进入高质量训练集，关键样本仍需人工或确定性验证器复核。

#### AIME 风格题目生成

[aime_generator.py](./code/HelloAgents/hello_agents/evaluation/benchmarks/data_generation/aime_generator.py) 保留原文的生成逻辑：随机抽取参考题、要求模型生成完全不同的新题、解析 JSON、定期保存检查点，最后输出完整数据集。生成结果统一为：

~~~json
{
  "problem_id": "gen_aime_0001",
  "problem": "...",
  "answer": "207",
  "solution": "...",
  "topic": "Probability",
  "reference_problem_id": "real_0042",
  "generated_at": "2026-09-11T10:00:00+08:00"
}
~~~

完整实现增加了几项必要约束：

- `answer` 必须能解析成 $[0,999]$ 内的整数；
- 四个核心字段不能为空，`topic` 必须属于指定主题；
- 每道题生成前清空 Agent 历史，避免上一题进入下一题上下文；
- 参考集下载默认关闭，只有显式传入 `download_reference=True` 才访问网络；
- 检查点只属于本次输出文件，不清理其他运行留下的数据；
- 时间使用包含时区的 RFC 3339 格式。

数学表达式还会暴露一个工程问题：模型可能在 JSON 字符串里直接输出 `\frac`、`\theta`，单反斜杠会被 JSON 当成转义符。[解析器](./code/HelloAgents/hello_agents/evaluation/benchmarks/data_generation/aime_generator.py) 在解码前识别这类 LaTeX 命令并补齐转义，同时保留合法的 JSON 转义。修复解析只保证文本不损坏，并不验证公式推导正确。

[dataset.py](./code/HelloAgents/hello_agents/evaluation/benchmarks/data_generation/dataset.py) 将本地 JSON、JSONL 和 Parquet 统一成同一结构。构造对象不会自动下载数据；真实运行可显式使用 `TianHongZXY/aime-1983-2025` 作为生成参考，使用 `math-ai/aime25` 作为相对评估参考。

#### LLM Judge 绝对评分

[llm_judge.py](./code/HelloAgents/hello_agents/evaluation/benchmarks/data_generation/llm_judge.py) 按原文从四个维度给出 1～5 分：

| 维度 | 检查内容 |
| --- | --- |
| `correctness` | 题目、答案和推导是否正确 |
| `clarity` | 条件和问题是否清楚、无歧义 |
| `difficulty_match` | 是否接近目标 AIME 难度 |
| `completeness` | 解答是否完整并可复核 |

第 $i$ 道题的平均分为：

$$
S_i=\frac{1}{4}\sum_{d=1}^{4}s_{i,d}
$$

设样本数为 $N$，章节采用 $3.5$ 作为通过阈值、$4.5$ 作为优秀阈值：

$$
\operatorname{PassRate}
=\frac{1}{N}\sum_{i=1}^{N}\mathbf{1}[S_i\ge 3.5]
$$

$$
\operatorname{ExcellentRate}
=\frac{1}{N}\sum_{i=1}^{N}\mathbf{1}[S_i\ge 4.5]
$$

这两个阈值是当前实践规则，不是所有数据生成任务的通用标准。实现会分别记录成功评分和解析失败；如果所有 Judge 响应都失败，均分和比例返回空值，不用 0 冒充质量得分。

[llm_judge_tool.py](./code/HelloAgents/hello_agents/tools/builtin/llm_judge_tool.py) 将加载、评分、JSON 结果和 Markdown 报告接入 `Tool.run(parameters)`。绝对评分只需要生成题，不再加载一份实际没有参与计算的参考数据。

#### Win Rate 成对比较

[win_rate.py](./code/HelloAgents/hello_agents/evaluation/benchmarks/data_generation/win_rate.py) 将生成题记为 A、真实参考题记为 B，Judge 返回 `A`、`B` 或 `Tie`。在成功完成的 $M$ 组比较中：

$$
\operatorname{WinRate}=\frac{N_A}{M},\qquad
\operatorname{LossRate}=\frac{N_B}{M},\qquad
\operatorname{TieRate}=\frac{N_{Tie}}{M}
$$

胜率接近 50% 可以作为“与参考题大致相当”的信号，但前提是 Judge、抽样、Prompt 和位置策略固定。胜率很高也不一定更好，可能是生成题偏简单、Judge 偏好某种表达，或 A/B 顺序造成位置偏差。当前实现明确保留原文的“生成题固定为 A”策略，并在报告中记录，正式实验应再交换位置复评。

`math-ai/aime25` 的记录可能只有题目和答案，没有官方解答。成对 Prompt 会明确说明该字段未提供，避免仅因 B 缺少 `solution` 就判它较差。缺失字段仍会降低完整性维度的可比性，必要时应补齐同源解答或把比较范围收窄到双方共有字段。

[win_rate_tool.py](./code/HelloAgents/hello_agents/tools/builtin/win_rate_tool.py) 负责加载两组数据、固定随机种子、配对、汇总和生成报告。参考数据缺失时直接报错，除非调用者显式允许下载。

#### 人工验证

[human_verification.py](./code/HelloAgents/hello_agents/evaluation/benchmarks/data_generation/human_verification.py) 保存相同四维评分、审核状态、备注和时间：

~~~json
{
  "problem_id": "gen_aime_0001",
  "scores": {
    "correctness": 5,
    "clarity": 5,
    "difficulty_match": 4,
    "completeness": 4
  },
  "average_score": 4.5,
  "status": "approved",
  "comments": "答案和推导可以复核。",
  "verified_at": "2026-09-11T10:00:00+08:00"
}
~~~

状态只能是 `approved`、`rejected` 或 `needs_revision`。同一 `problem_id` 再次提交会更新记录，结果默认写入 `<原数据名>_verifications.json`。[human_verification_ui.py](./code/HelloAgents/examples/human_verification_ui.py) 提供可选的 Gradio 逐题审核界面；存储逻辑独立于界面，也可以在其他应用中直接调用。

### 数据生成评估代码实践

#### 实现结构

~~~text
hello_agents/evaluation/benchmarks/data_generation/
├── dataset.py
├── aime_generator.py
├── llm_judge.py
├── win_rate.py
└── human_verification.py

hello_agents/tools/builtin/
├── llm_judge_tool.py
└── win_rate_tool.py

examples/
├── data_generation_evaluation_demo.py
├── data_generation_evaluate.py
├── human_verification_ui.py
└── data/data_generation/reference_aime.json
~~~

- [data_generation_evaluation_demo.py](./code/HelloAgents/examples/data_generation_evaluation_demo.py) 使用原创固定样例验证完整闭环，不调用模型和网络；
- [data_generation_evaluate.py](./code/HelloAgents/examples/data_generation_evaluate.py) 是真实生成与评估入口，结果按运行时间写入独立目录；
- [reference_aime.json](./code/HelloAgents/examples/data/data_generation/reference_aime.json) 只用于离线回归，不包含 AIME 原题。

真实流程需要模型配置；参考集下载由命令行单独授权：

~~~bash
cd code/HelloAgents
pip install huggingface_hub
PYTHONPATH=. python examples/data_generation_evaluate.py \
  --num-problems 10 \
  --download-generation-reference \
  --download-evaluation-reference
~~~

这会发生真实模型调用和 Hugging Face 下载。若参考数据已在本地，应改传 `--generation-reference-path` 与 `--evaluation-reference-path`，便于固定数据版本。
可通过 `--judge-model` 指定独立评审模型；未指定时沿用生成模型，但评审温度固定为 0。

生成人工审核页面需要额外安装 Gradio：

~~~bash
pip install gradio
PYTHONPATH=. python examples/human_verification_ui.py \
  ./data_generation_results/<运行时间>/generated_data/generated_aime.json
~~~

#### 本地实践结果

确定性 Demo 的运行方式：

~~~bash
cd code/HelloAgents
PYTHONPATH=. python examples/data_generation_evaluation_demo.py
~~~

控制台输出：

~~~text
=== 12.4 数据生成质量评估实践 ===
generated: 3/3
llm_judge_average: 4.00/5
llm_judge_pass_rate: 66.67%
llm_judge_excellent_rate: 33.33%
pairwise_win_rate: 33.33%
pairwise_loss_rate: 33.33%
pairwise_tie_rate: 33.33%
human_verification_progress: 1/3
latex_json_escape_repaired: True
network_calls: 0
real_model_calls: 0
artifacts_location: temporary_directory
~~~

固定 Judge 分别给三题 $5、4、3$ 分，因此总均分为 $4$；两题达到 $3.5$，一题达到 $4.5$。三组成对结果固定为一胜、一负、一平，用来验证聚合分母和字段映射。人工部分只审核第一题，所以进度为 $1/3$。所有产物写入系统临时目录，以上数字只是实现回归结果，不代表真实模型的数据生成质量。

#### 真实评估边界

- 生成参考集与评估参考集要分开，并记录数据版本，避免泄漏和训练集污染；
- Judge 模型、温度、Prompt、阈值、随机种子和 A/B 位置都属于实验条件；
- 同一 Judge 既生成又评分容易自我偏好，条件允许时应换模型或使用多 Judge；
- 数学正确性最好增加符号计算、数值代入或独立求解器验证，LLM 分数不能代替证明；
- 先用小批量检查 JSON、成本和评分稳定性，再扩大样本；
- 报告应保留失败响应和人工修改意见，不能只保留最终均分。

章节中展示的平均分、通过率和胜率是流程示例，不能当作本项目的实测结果。本次真实模型和官方数据评估没有运行，也没有据此生成成绩。

### 参考资料

- [《Hello-Agents》第十二章：智能体性能评估源文件](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter12/%E7%AC%AC%E5%8D%81%E4%BA%8C%E7%AB%A0%20%E6%99%BA%E8%83%BD%E4%BD%93%E6%80%A7%E8%83%BD%E8%AF%84%E4%BC%B0.md)
- [Gorilla / BFCL 论文](https://arxiv.org/abs/2305.15334)
- [Gorilla / BFCL 官方仓库](https://github.com/ShishirPatil/gorilla)
- [BFCL 数据目录说明](https://github.com/ShishirPatil/gorilla/blob/main/berkeley-function-call-leaderboard/bfcl_eval/data/README.md)
- [BFCL 官方 AST Checker](https://github.com/ShishirPatil/gorilla/blob/main/berkeley-function-call-leaderboard/bfcl_eval/eval_checker/ast_eval/ast_checker.py)
- [ToolLLM / ToolBench 论文](https://arxiv.org/abs/2307.16789)
- [API-Bank 论文](https://arxiv.org/abs/2304.08244)
- [GAIA 论文](https://arxiv.org/abs/2311.12983)
- [GAIA 官方数据集与格式说明](https://huggingface.co/datasets/gaia-benchmark/GAIA)
- [GAIA 官方排行榜](https://huggingface.co/spaces/gaia-benchmark/leaderboard)
- [TianHongZXY/aime-1983-2025 数据集](https://huggingface.co/datasets/TianHongZXY/aime-1983-2025)
- [math-ai/aime25 数据集](https://huggingface.co/datasets/math-ai/aime25)
- [AgentBench 论文](https://arxiv.org/abs/2308.03688)
- [WebArena 论文](https://arxiv.org/abs/2307.13854)
- [SOTOPIA 论文](https://arxiv.org/abs/2310.11667)

### 小结

Agent 评估要在固定任务、环境和运行配置下收集可比较的证据，具体基准负责定义“什么算正确”。BFCL 检查函数调用结构，GAIA 评估完整问题解决，数据生成评估则组合四维绝对评分、成对胜率和人工审核。本章代码补齐了三类场景的数据加载、样本隔离、匹配、指标、报告和导出，并用确定性样例验证流程。所有 Demo 分数都只是本地回归结果；对外比较仍要固定官方数据版本、模型、Prompt、工具和评分规则。
