## 毕业设计：构建属于你的多智能体应用

> 阅读资料：[16.1 毕业设计的意义](https://datawhalechina.github.io/hello-agents/#/./chapter16/%E7%AC%AC%E5%8D%81%E5%85%AD%E7%AB%A0%20%E6%AF%95%E4%B8%9A%E8%AE%BE%E8%AE%A1?id=_161-%e6%af%95%e4%b8%9a%e8%ae%be%e8%ae%a1%e7%9a%84%e6%84%8f%e4%b9%89)
>
> 这一节不是再学一个 Agent 模块，而是把前面的知识收束成一个可运行、可检查、可展示的开源项目。

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

### 参考资料

- [《Hello-Agents》第十六章：毕业设计](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter16/%E7%AC%AC%E5%8D%81%E5%85%AD%E7%AB%A0%20%E6%AF%95%E4%B8%9A%E8%AE%BE%E8%AE%A1.md)
- [Hello-Agents 仓库](https://github.com/datawhalechina/hello-agents)
- [Hello-Agents 共创项目目录](https://github.com/datawhalechina/hello-agents/tree/main/Co-creation-projects)

### 小结

毕业设计的价值在于把分散知识变成完整交付：从真实问题出发，选择必要的 Agent 能力，补齐错误处理和验证，最后以可运行代码、依赖、README 和 PR 接受检查。16.1 的实践代码没有提前决定选题，而是将最低交付物固化为可重复执行的结构检查，为后续项目迭代保留稳定入口。
