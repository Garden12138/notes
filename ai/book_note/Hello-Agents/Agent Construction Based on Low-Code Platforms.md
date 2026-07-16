## 基于低代码平台的智能体搭建

> 阅读资料：[《Hello-Agents》第五章](https://datawhalechina.github.io/hello-agents/#/./chapter5/%E7%AC%AC%E4%BA%94%E7%AB%A0%20%E5%9F%BA%E4%BA%8E%E4%BD%8E%E4%BB%A3%E7%A0%81%E5%B9%B3%E5%8F%B0%E7%9A%84%E6%99%BA%E8%83%BD%E4%BD%93%E6%90%AD%E5%BB%BA)
>
> 实践平台：Coze；实践项目：每日 AI 简报。截图记录于 2026 年 7 月 14 日，平台界面和功能以后可能调整。

### 低代码平台解决什么

低代码平台把模型、工具、知识库、记忆和发布渠道做成可配置节点。开发者仍要设计数据流和提示词，但不用从零处理模型接入、工具调度、状态传递与部署。

| 代码中的概念 | 低代码平台中的对应物 |
| --- | --- |
| 函数或 API | 插件、工具节点 |
| 控制流 | 工作流连线、分支、循环 |
| Prompt 与模型调用 | 大模型节点 |
| 应用入口 | Agent、聊天界面、API、发布渠道 |

本章介绍的四个平台侧重点不同：

| 平台 | 主要定位 | 更适合的场景 |
| --- | --- | --- |
| Coze | Agent、工作流与多渠道发布 | 快速制作原型和对话应用 |
| Dify | LLM 应用、工作流、RAG 与模型管理 | 需要私有化和完整应用能力的项目 |
| FastGPT | 知识库问答与 RAG | 企业文档检索、智能客服 |
| n8n | 通用业务自动化，AI 作为流程节点 | 连接大量业务系统和现有 API |

平台选择不只看模型数量，还要看数据是否允许托管、能否私有部署、工具接入方式、调试能力和发布渠道。

### Coze 的两层结构

这次实践用了工作流和 Agent 两层：

| 层级 | 职责 |
| --- | --- |
| 工作流（Workflow） | 拉取 36Kr、GitHub、arXiv 数据，交给大模型整理并返回日报 |
| Agent | 理解“每日简报”等自然语言请求，调用工作流并把结果回复给用户 |

工作流适合固定、可检查的执行步骤；Agent 负责对话入口和工具选择。把数据处理放在工作流里，问题更容易定位。

### 实践：每日 AI 简报

#### 整体流程

```mermaid
flowchart LR
    U["用户：每日简报"] --> A["每日AI简报 Agent"]
    A --> W["daily_ai_briefing 工作流"]
    W --> S["开始节点"]
    S --> R["36Kr RSS"]
    S --> G["GitHub 搜索"]
    S --> X["arXiv 搜索"]
    R --> L["大模型：筛选、分类、摘要"]
    G --> L
    X --> L
    L --> E["结束节点：output"]
    E --> A
    A --> U
```

工作流名为 `daily_ai_briefing`。开始节点同时触发三个数据源，数据准备完毕后统一交给大模型，最后通过 `output` 返回 Markdown 日报。

#### 数据源与字段

| 节点 | 输入 | 主要输出 | 本次返回量 |
| --- | --- | --- | ---: |
| rss-36kr | RSS 地址 | `entries` | 30 条 |
| github | 查询词、排序、分页参数 | `items`、`total_count` | 10 条 |
| arxiv | 查询词、数量、筛选参数 | 论文标题、摘要等字段 | 5 条 |

![工作流节点运行状态](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/hello_agents_coze_workflow_running.png)

三个节点并行执行，避免把网络请求串行叠加。需要注意的是，三个工具的返回结构不同，不能只把整个对象交给模型后期待它自行识别；关键字段应在节点映射或提示词中明确写出。

#### 大模型节点

大模型使用“豆包·1.8·深度思考”，输入为三个数据源的结果。它主要完成四件事：

1. 从原始结果中筛选与 AI 相关的内容。
2. 按技术新闻、学术论文和开源项目分类。
3. 为每条内容生成一句概述。
4. 按统一的 Markdown 模板输出标题、链接和摘要。

输出格式需要写成约束，而不是只说“生成日报”。例如：每个栏目最多多少条、字段缺失时如何处理、链接必须来自输入、禁止补造项目等。这样能降低格式漂移和内容幻觉。

#### 运行结果

![工作流完整运行结果](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/hello_agents_coze_workflow_run_result.png)

本次运行记录如下：

| 环节 | 耗时或用量 |
| --- | ---: |
| 36Kr RSS | 0.425 秒 |
| GitHub | 1 秒 |
| arXiv | 0.416 秒 |
| 大模型 | 约 2 分 31 秒 |
| 工作流总耗时 | 约 2 分 34 秒 |
| Token 用量 | 29,478 Tokens |

三个数据节点都在 1 秒左右完成，大模型节点约占总耗时的 98%。瓶颈不在数据抓取，而在一次性输入过多内容并进行长文本推理。

可以从以下几处缩减成本和等待时间：

- 在进入大模型前裁剪无关字段，只保留标题、链接、时间、摘要和必要指标。
- 每个数据源先按时间、关键词或热度过滤，再限制候选数量。
- 不需要复杂推理时换用响应更快的模型，减少深度思考开销。
- 将“筛选”和“排版”拆开，便于观察是哪一步消耗最多。

#### Agent 调用工作流

![Agent 调用每日简报工作流](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/hello_agents_coze_workflow_call.png)

“每日AI简报”Agent 采用自主规划模式，并把 `daily_ai_briefing` 配置为可调用工作流。用户输入“每日简报”后，Agent 识别意图、调用工作流，再把 `output` 作为最终回复。

工作流虽然只暴露一个 `input` 参数，也应写清它的含义和示例，例如“用户对日报日期、栏目或数量的补充要求”。参数描述含糊时，Agent 会在是否传空值、传原句还是自行改写之间反复判断。

#### 日报输出

![每日 AI 简报预览](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/hello_agents_coze_workflow_daily_brief_preview.png)

最终页面生成了标题 `AI 日报｜2026 年 07 月 14 日｜by@garden`，技术新闻部分包含 10 条内容，每条都有标题、原始链接和一句概述。

调试记录中还有一个值得保留的问题：GitHub 节点已返回 10 条记录，但 Agent 的推理过程认为“AI 开源项目部分没有内容”。这说明“工具调用成功”不等于“下游正确使用了数据”。排查顺序应为：

1. 查看 GitHub 的 `items` 是否真正传入大模型节点。
2. 检查字段路径是否与提示词中的名称一致。
3. 确认裁剪或上下文长度限制没有截掉 GitHub 数据。
4. 在大模型输出前增加数量校验，例如要求报告三个来源各接收多少条。
5. 数据为空时明确输出原因，不让模型自行猜测。

数量校验能把静默丢数变成可见错误，比只检查节点是否显示“运行成功”更可靠。

#### 发布

![Coze 发布渠道配置](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/ai/hello_agents_coze_workflow_publish_channels.png)

实践已进入发布配置页。截图中扣子商店已授权并选中，API 也已授权；飞书、微信等渠道仍需要单独授权或配置。因此这里只能确认发布入口已经配置，不能据此判断所有渠道都已上线。

### 实践结论

| 观察 | 结论 |
| --- | --- |
| 三个数据源可并行完成 | 独立的 I/O 节点应优先并行 |
| 大模型占绝大部分耗时 | 优化重点是输入裁剪、模型选择和任务拆分 |
| GitHub 有数据但栏目为空 | 节点成功之外还要检查字段映射和下游消费 |
| Agent 会犹豫如何填写 `input` | 工具参数要有明确语义、格式和示例 |
| 发布渠道状态不同 | 每个渠道都要分别检查授权、配置和发布结果 |

这次实践的核心不是把节点连起来，而是保证每条数据都能被正确传递、消费和验证。完整链路可以概括为：

`数据源 → 工作流 → 大模型 → Agent → 发布渠道`

### 参考资料

- [Hello-Agents 第五章：基于低代码平台的智能体搭建](https://datawhalechina.github.io/hello-agents/#/./chapter5/%E7%AC%AC%E4%BA%94%E7%AB%A0%20%E5%9F%BA%E4%BA%8E%E4%BD%8E%E4%BB%A3%E7%A0%81%E5%B9%B3%E5%8F%B0%E7%9A%84%E6%99%BA%E8%83%BD%E4%BD%93%E6%90%AD%E5%BB%BA)
- [Hello-Agents 第五章 GitHub 源文件](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter5/%E7%AC%AC%E4%BA%94%E7%AB%A0%20%E5%9F%BA%E4%BA%8E%E4%BD%8E%E4%BB%A3%E7%A0%81%E5%B9%B3%E5%8F%B0%E7%9A%84%E6%99%BA%E4%BD%93%E6%90%AD%E5%BB%BA.md)
- [Coze](https://www.coze.cn/)
- [Dify](https://dify.ai/)
- [FastGPT](https://fastgpt.io/)
- [n8n](https://n8n.io/)
