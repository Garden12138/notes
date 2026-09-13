## 毕业设计：构建属于你的多智能体应用

> 阅读资料：[16.1 毕业设计的意义](https://datawhalechina.github.io/hello-agents/#/./chapter16/%E7%AC%AC%E5%8D%81%E5%85%AD%E7%AB%A0%20%E6%AF%95%E4%B8%9A%E8%AE%BE%E8%AE%A1?id=_161-%e6%af%95%e4%b8%9a%e8%ae%be%e8%ae%a1%e7%9a%84%e6%84%8f%e4%b9%89)、[16.2 项目选题指南](https://datawhalechina.github.io/hello-agents/#/./chapter16/%E7%AC%AC%E5%8D%81%E5%85%AD%E7%AB%A0%20%E6%AF%95%E4%B8%9A%E8%AE%BE%E8%AE%A1?id=_162-%e9%a1%b9%e7%9b%ae%e9%80%89%e9%a2%98%e6%8c%87%e5%8d%97)
>
> 这两节不是再学一个 Agent 模块，而是把前面的知识收束成一个可运行、可检查、可展示的开源项目。

### 毕业设计检验的是综合能力

教程中的单个练习通常已经给定了问题、输入和参考代码，重点是理解某个知识点。毕业设计没有这些预设，需要自己回答：

1. 要解决的真实问题是什么；
2. 什么结果算是完成；
3. 哪些步骤适合交给 Agent，哪些必须由确定性代码约束；
4. 如何处理错误、超时、格式偏离和外部服务失败；
5. 如何用文档、测试和演示证明它真的可用。

因此，完成一个毕业项目不等于写出一段能调用模型的代码。它要把需求、架构、实现、验证和交付连成闭环。

~~~mermaid
flowchart LR
    P["真实问题"] --> S["范围与验收标准"]
    S --> D["Agent、工具与状态设计"]
    D --> I["可运行实现"]
    I --> V["测试与评估"]
    V --> DOC["README 与演示材料"]
    DOC --> PR["Pull Request 与社区 Review"]
    PR -->|"需要修改"| I
~~~

### 不需要堆满前面所有技术

原文强调的是“选择性整合”。项目不需要为了显得复杂，同时加入 ReAct、RAG、长期记忆、MCP、多 Agent 和强化学习。每个组件都应对应一个具体需求：

| 需求 | 可选能力 | 使用前要回答的问题 |
| --- | --- | --- |
| 任务需要多步外部操作 | ReAct 或工具调用 | 工具结果如何校验？ |
| 回答必须依据私有文档 | RAG | 来源如何引用，无证据时如何处理？ |
| 需要跨轮保留用户状态 | 记忆系统 | 保存什么，何时失效，如何隔离用户？ |
| 子任务需要不同专业角色 | 多 Agent 协作 | 分工是否比单 Agent 更清晰？ |
| 需要接入外部标准服务 | MCP 等协议 | 协议带来的复用性是否值得增加复杂度？ |
| 需要比较版本效果 | 评估体系 | 是否有固定数据、指标和基线？ |

能用单 Agent 和两个工具稳定解决的问题，没有必要强行拆成五个角色。架构的价值在于降低问题复杂度，而不是增加模块数量。

### 开源项目是毕业设计的交付形式

毕业设计需要放入 Hello-Agents 的 `Co-creation-projects` 目录，项目名使用 `{GitHub用户名}-{项目名称}` 格式。最低交付物是：

| 内容 | 是否必需 | 证明什么 |
| --- | --- | --- |
| 可运行的 `.py` 或 `.ipynb` | 是 | 核心流程不只停留在设计图 |
| `requirements.txt` | 是 | 别人知道如何复原环境 |
| `README.md` | 是 | 项目目标、安装、运行和示例可被理解 |
| 截图、演示视频、数据集 | 否 | 降低评审和试用成本 |
| GitHub Pull Request | 是 | 项目进入可 review 的开源协作流程 |

“有文件”只是最低要求。一份可用的 README 至少还应说清问题、范围、架构、环境变量、运行命令、输入输出示例、验证结果和已知边界。只放一张效果图，但不说如何运行，仍然不算可复现。

### 我的理解

前面章节中的实践是“跟着建”，毕业设计要转向“自己做决定”。最重要的不是代码量，而是每个决定都能回到问题本身：为什么要用 Agent，为什么需要多角色，为什么保存记忆，失败后如何恢复，以及用什么证据评价效果。

毕业设计也不是一次性写完后就结束。PR Review 把它变成一个迭代过程：提交者给出实现和证据，评审者检查正确性、可复现性和边界，修改后再验证。这比“本机能跑”更接近真实工程。

### 代码实践：把交付要求变成可执行检查

16.1 没有定义具体选题，也没有 Agent 实现片段。因此这里不提前构造一个毕业项目，而是把本节的交付规则实现为标准库自检器。

~~~text
graduation_project/
├── __init__.py
└── submission.py                    # 交付物数据模型与校验器

examples/
├── graduation_project_check.py      # 通用 CLI
└── graduation_project_readiness_demo.py
                                          # 确定性离线实践
~~~

[submission.py](./code/HelloAgents/graduation_project/submission.py) 将每项规则表示为 `ProjectCheck`，再聚合成 `GraduationProjectReport`。只有必需项失败才会使 `ready=False`；截图、视频和数据集等可选材料只提示，不会阻止提交。

~~~python
report = GraduationProjectValidator(
    project_root,
    github_username="your-github-name",
).validate()

if not report.ready:
    print(report.failed_required_codes)
~~~

校验器会检查：

- 目录和 `{GitHub用户名}-{项目名}` 命名；
- `README.md`、`requirements.txt` 和根目录运行入口；
- 全部 Python 文件的内存语法编译；
- Notebook 是否为有效 JSON，并且至少包含一个代码单元；
- 是否提供了可选的演示或数据材料。

使用 [graduation_project_check.py](./code/HelloAgents/examples/graduation_project_check.py) 检查实际项目：

~~~bash
cd code/HelloAgents
PYTHONPATH=. python examples/graduation_project_check.py \
  /path/to/your-github-name-AgentProject \
  --github-user your-github-name
~~~

在 CI 中可加 `--json` 保存结构化结果。必需项全部通过时进程返回 `0`，否则返回 `1`。

#### 本地实践结果

[graduation_project_readiness_demo.py](./code/HelloAgents/examples/graduation_project_readiness_demo.py) 在临时目录生成一个完整项目和一个缺失交付物的项目，不调用模型或网络：

~~~bash
cd code/HelloAgents
PYTHONPATH=. python examples/graduation_project_readiness_demo.py
~~~

实际输出：

~~~text
=== 16.1 毕业设计交付自检实践 ===
valid_project_ready: True
required_checks: 7/7
optional_materials_required: False
incomplete_project_ready: False
incomplete_failed: project_name,requirements_file,runnable_entry
network_calls: 0
model_calls: 0
artifacts_location: temporary_directory
~~~

这个结果只证明校验逻辑能区分完整和缺失交付物的目录。它不会执行用户项目，也不能判断 Agent 效果、README 的解释质量或 PR 是否能通过人工 Review。这些仍需要单元测试、任务评估和真实评审。

### 好选题是三个条件的交集

原文给出了三个直接标准：解决真实问题，能在有限时间和资源内完成，能清楚展示自己的技术能力。三者少一个，项目都容易失控：

| 标准 | 要回答的问题 | 常见偏差 |
| --- | --- | --- |
| 实用性 | 谁在什么场景下遇到什么问题？ | 先决定技术栈，再为它寻找用途 |
| 可行性 | 在给定周期和每周时间内能交付哪些核心能力？ | 把所有想法都放进第一版 |
| 展示性 | 如何用输入、输出和指标证明效果？ | 只能演示一段对话，无法验收 |

~~~mermaid
flowchart TB
    U["实用性<br/>真实用户与问题"]
    F["可行性<br/>时间、资源与范围"]
    D["展示性<br/>可演示与可评估"]
    U --> T["值得实现的选题"]
    F --> T
    D --> T
    T --> MVP["先交付最小完整闭环"]
~~~

这三项不适合用总分完全互相抵消。一个项目即使看起来很酷，只要无法在现有资源内完成，仍应缩小范围，而不是用展示性的高分掩盖可行性的低分。

### 五类方向只是起点

原文将参考选题分为五类：

| 方向 | 参考选题 | 更适合展示的能力 |
| --- | --- | --- |
| 生产力工具 | 代码审查、文档生成、会议、邮件助手 | 工具调用、结构化输出、工作流 |
| 学习辅助 | 学习伙伴、论文助手、编程导师、语言学习 | RAG、记忆、个性化反馈 |
| 创意娱乐 | 故事生成、游戏 NPC、音乐推荐、菜谱助手 | 角色 Prompt、多轮状态、内容生成 |
| 数据分析 | 数据分析师、股票分析、舆情监控、竞品分析 | 检索、代码执行、可视化和报告 |
| 生活服务 | 健康、理财、购物、智能家居助手 | 外部 API、约束处理和安全边界 |

分类本身不会产生好选题。“智能学习伙伴”仍然太宽；“根据一组 LangGraph 笔记生成每周练习，并按错题安排复习”才同时指向用户、输入、任务和结果。

### 如何拆解 CodeReviewAgent 示例

原文的选题示例是智能代码审查助手。它不是从“我想用 LLM 审查代码”开始，而是先描述人工审查耗时、容易遗漏，传统静态分析又难以理解业务语义的问题。

核心功能可分为五类：

1. 检查代码风格、命名和注释；
2. 发现逻辑错误、边界条件和资源泄漏；
3. 识别性能瓶颈并给出优化建议；
4. 检查 SQL 注入、XSS 等常见安全风险；
5. 结合语言特性和设计模式提供最佳实践。

预期交付物是可运行的 Python 脚本或 Notebook，最终支持 Python 和 JavaScript，生成带问题分类、定位、原因、修改建议和代码示例的 Markdown 报告。若时间受限，可先以 Python 完成从输入到报告的整个闭环，再扩展 JavaScript；这是分阶段交付，不是删掉原文的最终目标。

~~~mermaid
flowchart LR
    CODE["Python / JavaScript 代码"] --> REVIEW["代码审查流程"]
    REVIEW --> QUALITY["质量与规范"]
    REVIEW --> BUG["潜在 Bug"]
    REVIEW --> PERF["性能"]
    REVIEW --> SECURITY["安全"]
    REVIEW --> PRACTICE["最佳实践"]
    QUALITY --> REPORT["结构化 Markdown 报告"]
    BUG --> REPORT
    PERF --> REPORT
    SECURITY --> REPORT
    PRACTICE --> REPORT
~~~

### 代码实践：选题方案与评估规则

本节没有进入 CodeReviewAgent 的具体 Agent 实现，因此代码聚焦在选题阶段：先用 `TopicProposal` 完整表达问题、用户、功能、预期成果和时间盒，再记录三项评分及其证据。

~~~text
graduation_project/
├── submission.py
└── topic_selection.py                  # 选题模型、评分与排序

examples/
├── graduation_project_topic_check.py   # JSON 选题检查 CLI
├── graduation_project_topic_demo.py    # 确定性对比实践
└── data/graduation_project/
    └── code_review_topic.json           # 原文示例的结构化方案
~~~

[topic_selection.py](./code/HelloAgents/graduation_project/topic_selection.py) 使用下面的本地 rubric：

$$
S=20\times(0.35P+0.35F+0.30D)
$$

其中 $P$、$F$、$D$ 分别代表实用性、可行性和展示性，每项取 1～5 分。总分达到 80 且三项都不低于 3 时标记为 `recommended`；总分不足时建议 `narrow_scope`；任意一项低于 3 则返回 `rework`。

权重、80 分门槛和 3 分下限是本地实践规则，不是原文或 Hello-Agents 社区的官方评审标准。每个分数必须附证据，它的作用是迫使提案者说清判断依据，而不是用公式代替人工决策。

用 [code_review_topic.json](./code/HelloAgents/examples/data/graduation_project/code_review_topic.json) 运行命令行评估：

~~~bash
cd code/HelloAgents
PYTHONPATH=. python examples/graduation_project_topic_check.py \
  examples/data/graduation_project/code_review_topic.json
~~~

输出：

~~~text
项目：CodeReviewAgent
类别：生产力工具
总分：86.0/100
  practicality: 5/5
  feasibility: 3/5
  demonstrability: 5/5
预计投入：48 小时
建议：recommended
~~~

`feasibility` 只有 3 分，原因是六周内同时支持两种语言和五类检查存在范围风险。它仍然达到最低下限，但这个证据会直接提醒开发时采用分阶段交付。

#### 本地实践结果

[graduation_project_topic_demo.py](./code/HelloAgents/examples/graduation_project_topic_demo.py) 还加入了一个“为所有人解决所有日常任务”的宽泛方案，用于验证单项下限和排序：

~~~text
=== 16.2 毕业设计选题评估实践 ===
code_review_score: 86.0
code_review_recommendation: recommended
code_review_feature_count: 5
broad_idea_score: 33.0
broad_idea_recommendation: rework
broad_idea_risks: practicality_below_floor,feasibility_below_floor,demonstrability_below_floor
ranking_first: CodeReviewAgent
network_calls: 0
model_calls: 0
~~~

这里的 86 分是对示例中人工填写分数的确定性汇总，不是模型自动判断，也不代表 CodeReviewAgent 已经实现或质量达标。真正开发前还需要与目标用户确认问题，并把功能拆成可验收的里程碑。

### 参考资料

- [《Hello-Agents》第十六章：毕业设计](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter16/%E7%AC%AC%E5%8D%81%E5%85%AD%E7%AB%A0%20%E6%AF%95%E4%B8%9A%E8%AE%BE%E8%AE%A1.md)
- [Hello-Agents 仓库](https://github.com/datawhalechina/hello-agents)
- [Hello-Agents 共创项目目录](https://github.com/datawhalechina/hello-agents/tree/main/Co-creation-projects)

### 小结

毕业设计要把分散知识变成完整交付：从真实问题出发，在实用性、可行性和展示性的交集中确定选题，再选择必要的 Agent 能力。16.1 的交付自检器固化文件契约；16.2 的结构化方案和评分器则保留选题依据。分数只辅助暴露范围风险，最终选择仍要回到用户需求、实际资源和可验收结果。
