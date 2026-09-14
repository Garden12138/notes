## 毕业设计：构建属于你的多智能体应用

> 阅读资料：[16.1 毕业设计的意义](https://datawhalechina.github.io/hello-agents/#/./chapter16/%E7%AC%AC%E5%8D%81%E5%85%AD%E7%AB%A0%20%E6%AF%95%E4%B8%9A%E8%AE%BE%E8%AE%A1?id=_161-%e6%af%95%e4%b8%9a%e8%ae%be%e8%ae%a1%e7%9a%84%e6%84%8f%e4%b9%89)、[16.2 项目选题指南](https://datawhalechina.github.io/hello-agents/#/./chapter16/%E7%AC%AC%E5%8D%81%E5%85%AD%E7%AB%A0%20%E6%AF%95%E4%B8%9A%E8%AE%BE%E8%AE%A1?id=_162-%e9%a1%b9%e7%9b%ae%e9%80%89%e9%a2%98%e6%8c%87%e5%8d%97)、[16.3 开发环境准备](https://datawhalechina.github.io/hello-agents/#/./chapter16/%E7%AC%AC%E5%8D%81%E5%85%AD%E7%AB%A0%20%E6%AF%95%E4%B8%9A%E8%AE%BE%E8%AE%A1?id=_163-%e5%bc%80%e5%8f%91%e7%8e%af%e5%a2%83%e5%87%86%e5%a4%87)、[16.4 项目开发指南](https://datawhalechina.github.io/hello-agents/#/./chapter16/%E7%AC%AC%E5%8D%81%E5%85%AD%E7%AB%A0%20%E6%AF%95%E4%B8%9A%E8%AE%BE%E8%AE%A1?id=_164-%e9%a1%b9%e7%9b%ae%e5%bc%80%e5%8f%91%e6%8c%87%e5%8d%97)
>
> 这四节不是再学一个 Agent 模块，而是把前面的知识收束成一个可运行、可检查、可展示的开源项目。

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

### 开发环境不是只有 Python 依赖

16.3 的准备工作可以分成四层。少装一个包会直接报错，远程仓库或分支配置错误则可能到提交 PR 时才暴露，因此不能只以“程序能启动”判断环境是否完成。

| 层次 | 需要准备的内容 | 解决的问题 |
| --- | --- | --- |
| Python | Python 3.10+、`hello-agents[all]` | 能否运行框架和示例 |
| 开发工具 | Git；Notebook 项目还需要 Jupyter | 能否编辑、调试和记录实验 |
| GitHub 协作 | Git 身份、Fork、`origin`、`upstream`、`feature/*` 分支 | 代码提交到哪里，如何同步官方仓库 |
| 项目交付 | `Co-creation-projects` 下的规范目录 | 是否满足共创项目的提交结构 |

按原文安装完整依赖可以写成：

~~~bash
python3 --version
python3 -m pip install "hello-agents[all]"
~~~

如果主要入口是 Notebook，再安装并启动 Jupyter：

~~~bash
python3 -m pip install jupyterlab
jupyter lab
~~~

脚本项目并不强制依赖 Jupyter。这里应该以项目的实际入口选择工具，而不是把所有可选软件都当成必装项。

### Fork、origin 与 upstream 的关系

原文采用标准的 Fork 协作流程：先在 GitHub 上 Fork 官方仓库，再克隆自己的副本，并把官方仓库登记为 `upstream`。

~~~mermaid
flowchart LR
    U["官方仓库<br/>datawhalechina/hello-agents<br/>upstream"] -->|"同步更新"| L["本地仓库"]
    F["个人 Fork<br/>用户名/hello-agents<br/>origin"] <-->|"pull / push"| L
    L --> B["feature/项目名称"]
    B -->|"Pull Request"| U
~~~

对应命令如下，其中用户名和项目名需要替换：

~~~bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"

git clone git@github.com:你的用户名/hello-agents.git
cd hello-agents
git remote add upstream https://github.com/datawhalechina/hello-agents.git
git checkout -b feature/你的项目名称
~~~

`origin` 是自己有写权限的 Fork，`upstream` 是官方仓库。开发内容先推送到 `origin` 的功能分支，再向 `upstream` 发起 PR；两者写反会让同步和提交关系变得混乱。

原文推荐用 Ed25519 SSH 密钥连接 GitHub：

~~~bash
ssh-keygen -t ed25519
ssh -T git@github.com
~~~

SSH 不是唯一方案，也可以使用 HTTPS。无论采用哪种方式，都不应把私钥、访问令牌或 `.env` 提交到项目中；`*.pub` 才是可添加到 GitHub 的公钥文件。

### 共创项目的目录边界

项目应直接放在仓库的 `Co-creation-projects` 下，目录名仍采用 `{GitHub用户名}-{项目名称}`。原文给出的推荐结构是：

~~~text
Co-creation-projects/
└── 用户名-项目名称/
    ├── README.md
    ├── requirements.txt
    ├── main.ipynb
    ├── data/                    # 可选：示例数据与测试用例
    ├── outputs/                 # 可选：报告与截图
    └── src/                     # 可选：agents、tools、utils 等模块
~~~

入口也可以是根目录 Python 脚本。`src/` 适合存放逐渐变大的实现，但 README、依赖清单和主入口应保持容易发现。这样既延续 16.1 的最低交付契约，也给后续扩展留出空间。

### 代码实践：只读的开发环境自检

原文主要给出安装和 Git 命令，没有提供可复用程序。本节新增 [environment.py](./code/HelloAgents/graduation_project/environment.py)，把这些要求整理成只读检查，并复用 16.1 的 `GraduationProjectValidator`，避免环境检查和交付检查各自维护一套规则。

~~~text
graduation_project/
├── environment.py                         # 环境、Git 与目录检查
└── submission.py                          # 复用交付物检查

examples/
├── graduation_project_environment_check.py # 实际环境 CLI
└── graduation_project_environment_demo.py  # 确定性离线演示
~~~

检查流程如下：

~~~mermaid
flowchart LR
    CLI["仓库目录 + 项目目录"] --> ENV["Python / hello-agents / Jupyter"]
    CLI --> GIT["Git 身份 / origin / upstream / 分支"]
    CLI --> DIR["Co-creation-projects 位置"]
    DIR --> CONTRACT["README / requirements / 入口 / 语法"]
    ENV --> REPORT["DevelopmentEnvironmentReport"]
    GIT --> REPORT
    CONTRACT --> REPORT
    REPORT -->|"必需项全部通过"| READY["ready = true"]
~~~

使用 [graduation_project_environment_check.py](./code/HelloAgents/examples/graduation_project_environment_check.py) 检查实际克隆的仓库：

~~~bash
cd code/HelloAgents
PYTHONPATH=. python3 examples/graduation_project_environment_check.py \
  /path/to/hello-agents \
  /path/to/hello-agents/Co-creation-projects/your-user-CodeReviewAgent \
  --github-user your-user \
  --entry-mode notebook
~~~

脚本会检查 Python 版本、发行包、Git 身份、仓库根目录、两个远程仓库、功能分支、项目位置和交付结构。Notebook 模式下 Jupyter 是必需项，脚本模式下只是提示；SSH 公钥始终是推荐项，因为 HTTPS 同样可用。加 `--json` 可以得到适合 CI 保存的结构化报告。

实现使用参数列表调用只读命令，没有经过 shell，也不会执行安装、生成密钥、克隆、推送或联网测试。Git 姓名和邮箱只报告“已设置”，不回显具体内容。

#### 本地实践结果

[graduation_project_environment_demo.py](./code/HelloAgents/examples/graduation_project_environment_demo.py) 在临时目录创建 Notebook 项目，并用固定响应模拟 Git 和 Jupyter 命令。实际输出为：

~~~text
=== 16.3 开发环境准备自检实践 ===
environment_ready: True
required_checks: 13/13
python_check: Python 3.12.1
git_branch: feature/code-review-agent
project_contract_ready: True
simulated_command_responses: 8
external_commands_executed: 0
network_calls: 0
artifacts_location: temporary_directory
~~~

这次演示验证的是检查项之间的组合逻辑，不代表当前电脑已经连接 GitHub。真实环境仍需运行 CLI，并手动确认 Fork 已创建、SSH 公钥已添加且 `ssh -T git@github.com` 能完成认证。自检器只能确认 `hello-agents` 发行包存在，不能证明 `[all]` 中每个可选依赖都可正常调用。

### README 是项目的使用入口

代码解决“怎么实现”，README 要回答“为什么做、如何运行、结果如何判断”。原文给出的模板可以整理成三组信息：

| 信息层次 | 主要内容 | 读者要解决的问题 |
| --- | --- | --- |
| 项目定位 | 项目简介、核心功能、技术栈、亮点 | 这个项目解决什么问题，为什么值得使用？ |
| 复现路径 | 环境要求、安装依赖、API 密钥、运行命令、使用示例 | 如何在自己的环境中跑起来？ |
| 项目状态 | 性能评估、未来计划、贡献、许可证、作者、致谢 | 当前效果如何，还有哪些边界？ |

快速开始部分不应只写一句“运行 Notebook”，而要给出能够顺序执行的命令：

~~~bash
python3 -m pip install -r requirements.txt
cp .env.example .env
jupyter lab
~~~

`.env.example` 只保留变量名和空值，真实密钥放在本地 `.env`，并通过 `.gitignore` 排除。使用示例最好同时包含输入与输出；只有调用代码，没有结果样例，读者仍不知道程序是否运行正确。

README 中的性能数据也必须来自实际评估。如果尚未完成测试，可以明确写“待评估”及评估方案，不能先填入 `XX%` 后把模板值当成结果。

### requirements.txt 只记录真实依赖

原文示例以 `hello-agents[all]>=0.2.7` 为核心，并按需要加入 Matplotlib、Plotly、FastAPI 和 Uvicorn。这里的“按需要”很重要：

~~~text
# 核心依赖
hello-agents[all]>=0.2.7

# 只有项目实际使用时才加入
matplotlib>=3.7.0
fastapi>=0.109.0
uvicorn>=0.27.0
~~~

依赖过少会导致他人无法复现，直接提交完整环境的 `pip freeze` 又容易混入无关包和平台专属依赖。较稳妥的做法是从代码实际导入出发维护最小清单，再在干净环境中重新安装验证。版本下界表示已知兼容的最低版本，不等于版本越新越安全；遇到兼容性敏感的项目，还需要记录经过验证的版本范围。

### Notebook 要展示完整开发链路

原文将 Notebook 分为项目介绍、环境配置、工具定义、智能体构建、功能演示、性能评估、总结与展望七部分。这个顺序对应读者理解和复现实验的路径：

~~~mermaid
flowchart LR
    INTRO["项目介绍"] --> ENV["环境配置"]
    ENV --> TOOL["工具定义"]
    TOOL --> AGENT["智能体构建"]
    AGENT --> DEMO["功能演示"]
    DEMO --> EVAL["性能评估"]
    EVAL --> REVIEW["总结与展望"]
~~~

Notebook 不是把一个 `.py` 文件拆成很多单元格。Markdown 单元负责说明目标、输入和结论，代码单元负责产生可验证结果；单元应按从上到下的顺序执行，避免依赖隐藏状态。篇幅增大后，可把 Agent、工具和通用函数放进 `src/`，Notebook 只保留编排、实验与展示。

原文中的 `CustomTool.run()`、用户输入和评估代码都是结构示意，具体项目必须替换成真实实现。16.4 尚未定义 CodeReviewAgent 的业务协议，因此这里不提前虚构工具调用逻辑，而是先保证开发结构能够被检查。

### 测试清单要区分静态检查与真实运行

提交前检查包含代码可运行、文档完整、依赖齐全、示例清晰、输出符合预期、异常得到处理、结构规范和大文件处理。它们不能全部通过读取文件自动证明：

| 检查方式 | 可以确认 | 不能确认 |
| --- | --- | --- |
| 静态检查 | 文件存在、Python 语法、Notebook JSON、README 章节、项目大小 | 外部 API 是否可用、回答质量、异常路径是否真的执行 |
| 实际运行 | 安装是否成功、示例能否完成、输出是否符合预期 | 未覆盖输入下的普遍质量 |
| 人工审查 | 文档是否清晰、注释是否有价值、结论是否可信 | 所有未来运行环境都兼容 |

因此，`compile()` 通过不能写成“项目运行成功”，Notebook 格式正确也不等于所有单元按顺序执行成功。最少要在干净环境中运行 README 的快速开始和一个完整示例，并保存输入、关键输出和失败处理记录。

### 大文件应该和代码仓库分离

Hello-Agents 共创项目总大小不能超过 5 MB，视频、大型数据集和模型文件不能直接提交。原文给出三种处理方式：

1. 上传到外部平台，在 README 中写明下载地址和放置位置；
2. 资源较多时建立独立仓库；
3. 主仓库只保留小于 1 MB 的示例数据，完整数据集使用外部链接。

~~~mermaid
flowchart TD
    FILE["项目资源"] --> Q{"适合直接提交？"}
    Q -->|"代码、小型样例、轻量截图"| REPO["共创项目仓库"]
    Q -->|"视频、大型数据集、模型"| OUT["外部平台或资源仓库"]
    OUT --> LINK["README 记录链接、版本与放置路径"]
    LINK --> REPO
~~~

外置资源不能只有一个裸链接。还应记录资源用途、版本或更新时间、下载后放到哪个目录，以及程序在资源缺失时给出什么提示。`.gitignore` 是最后一道防误提交措施，但不能代替提交前的文件大小检查。

### 代码实践：开发质量检查器

[development.py](./code/HelloAgents/graduation_project/development.py) 在前三节自检的基础上补充开发阶段检查：

~~~text
graduation_project/
├── submission.py                    # 16.1 最低交付契约
└── development.py                   # 16.4 文档、测试与大文件规则

examples/
├── graduation_project_development_check.py
├── graduation_project_development_demo.py
└── data/graduation_project/
    └── development_evidence.example.json
~~~

`ProjectDevelopmentValidator` 会检查：

- 16.1 的目录命名、README、依赖、入口和语法要求；
- README 的核心章节与建议扩展章节；
- `requirements.txt` 是否声明 `hello-agents[all]`；
- `main.ipynb` 是否按核心开发阶段组织，性能评估单独作为建议项；
- 项目是否不超过 5 MB，是否直接包含视频、模型或超过 1 MB 的数据文件；
- `.gitignore` 是否覆盖 `.env`、Python 缓存和常见大文件；
- 无法静态证明的运行、示例、输出、异常和注释检查是否有人工确认记录。

人工测试记录使用明确的布尔字段。示例文件 [development_evidence.example.json](./code/HelloAgents/examples/data/graduation_project/development_evidence.example.json) 默认全部为 `false`，完成对应检查后才能修改，避免未运行代码就得到通过报告。

~~~json
{
  "code_runs": true,
  "usage_example_verified": true,
  "output_matches_expectation": true,
  "common_exceptions_handled": true,
  "comments_reviewed": true
}
~~~

运行 [graduation_project_development_check.py](./code/HelloAgents/examples/graduation_project_development_check.py)：

~~~bash
cd code/HelloAgents
PYTHONPATH=. python3 examples/graduation_project_development_check.py \
  /path/to/your-user-CodeReviewAgent \
  --github-user your-user \
  --evidence /path/to/development_evidence.json
~~~

不提供 `--evidence` 时，静态项目即使结构完整也不会被标记为开发检查通过。加 `--json` 可输出结构化报告，但人工勾选仍是责任记录，不是测试日志本身。

#### 本地实践结果

[graduation_project_development_demo.py](./code/HelloAgents/examples/graduation_project_development_demo.py) 在临时目录构造符合原文结构的 README、依赖清单和 Notebook。第一次检查全部通过；随后加入一个内容只有占位符的 `demo.mp4`，即使文件很小也会因视频禁止直接提交而失败：

~~~text
=== 16.4 项目开发质量检查实践 ===
ready_project: True
required_checks: 7/7
readme_core_complete: True
notebook_core_complete: True
manual_evidence_complete: True
project_size_within_limit: True
video_added_ready: False
video_failed: prohibited_assets
network_calls: 0
model_calls: 0
artifacts_location: temporary_directory
~~~

本次结果只验证检查器和示例结构，没有安装 `requirements.txt`、执行 Notebook 或调用模型。README 检查依据标题，只能发现章节缺失，不能评价内容质量；依赖检查也不能自动证明清单覆盖了所有导入。这些边界正是保留人工运行记录和 Review 的原因。

### 参考资料

- [《Hello-Agents》第十六章：毕业设计](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter16/%E7%AC%AC%E5%8D%81%E5%85%AD%E7%AB%A0%20%E6%AF%95%E4%B8%9A%E8%AE%BE%E8%AE%A1.md)
- [Hello-Agents 仓库](https://github.com/datawhalechina/hello-agents)
- [Hello-Agents 共创项目目录](https://github.com/datawhalechina/hello-agents/tree/main/Co-creation-projects)

### 小结

毕业设计要把分散知识变成完整交付：先从真实问题出发，在实用性、可行性和展示性的交集中确定选题，再准备可复现的环境和协作流程。16.1 固化最低交付契约，16.2 保留选题依据，16.3 检查开发环境，16.4 继续约束 README、依赖、Notebook、测试证据和仓库大小。这些检查只能降低遗漏风险，项目价值和最终质量仍要靠真实需求、运行证据与人工 Review 判断。
