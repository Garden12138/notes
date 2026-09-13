## 自动化深度研究智能体

> 阅读资料：[14.1 项目概述与架构设计](https://datawhalechina.github.io/hello-agents/#/./chapter14/%E7%AC%AC%E5%8D%81%E5%9B%9B%E7%AB%A0%20%E8%87%AA%E5%8A%A8%E5%8C%96%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6%E6%99%BA%E8%83%BD%E4%BD%93?id=_141-%e9%a1%b9%e7%9b%ae%e6%a6%82%e8%bf%b0%e4%b8%8e%e6%9e%b6%e6%9e%84%e8%ae%be%e8%ae%a1)、[14.2 TODO 驱动的研究范式](https://datawhalechina.github.io/hello-agents/#/./chapter14/%E7%AC%AC%E5%8D%81%E5%9B%9B%E7%AB%A0%20%E8%87%AA%E5%8A%A8%E5%8C%96%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6%E6%99%BA%E8%83%BD%E4%BD%93?id=_142-todo-%e9%a9%b1%e5%8a%a8%e7%9a%84%e7%a0%94%e7%a9%b6%e8%8c%83%e5%bc%8f)、[14.3 智能体系统设计](https://datawhalechina.github.io/hello-agents/#/./chapter14/%E7%AC%AC%E5%8D%81%E5%9B%9B%E7%AB%A0%20%E8%87%AA%E5%8A%A8%E5%8C%96%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6%E6%99%BA%E8%83%BD%E4%BD%93?id=_143-%e6%99%ba%e8%83%bd%e4%bd%93%e7%b3%bb%e7%bb%9f%e8%ae%be%e8%ae%a1)、[14.4 工具系统集成](https://datawhalechina.github.io/hello-agents/#/./chapter14/%E7%AC%AC%E5%8D%81%E5%9B%9B%E7%AB%A0%20%E8%87%AA%E5%8A%A8%E5%8C%96%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6%E6%99%BA%E8%83%BD%E4%BD%93?id=_144-%e5%b7%a5%e5%85%b7%e7%b3%bb%e7%bb%9f%e9%9b%86%e6%88%90)
>
> 14.1 确定产品目标、四层架构和数据流；14.2 用 TODO 组织研究过程；14.3 把三类产物交给三个窄职责 Agent；14.4 统一搜索、笔记和工具调用边界。

### 深度研究不等于多搜几次

普通搜索解决的是“找到相关网页”，深度研究还要回答三个问题：应该查哪些方面、证据是否足以支撑结论、怎样把分散材料组织成可核验的报告。

因此，系统不能把搜索结果直接拼给用户，而要完成一条研究链：

1. 把开放主题拆成可检索的子问题；
2. 围绕子问题持续收集资料并去重；
3. 总结阶段结果，保留事实、数据和来源；
4. 发现信息缺口后决定是否继续检索；
5. 合并所有阶段结论，生成结构化报告。

原文把价值归纳为节省时间、提高覆盖度、保留来源和方便扩展。这里的“将一两个小时压缩到几分钟”是产品目标，不是固定性能承诺；实际耗时取决于子任务数量、搜索后端、页面抓取范围和模型速度。

### 三项核心能力

| 能力 | 解决的问题 | 可检查的输出 |
| --- | --- | --- |
| 问题剖析 | 主题太宽，无法直接检索 | 3–5 个边界清楚的 TODO，每项都有 `title`、`intent`、`query` |
| 多轮信息采集 | 单次搜索覆盖不足，结果重复 | 结构化搜索结果、去重后的 URL、来源摘要 |
| 反思与总结 | 信息很多但缺少结论，或关键问题尚未回答 | 阶段总结、知识缺口、继续或停止的判断、最终报告 |

深度研究的核心产物不是篇幅，而是“结论—证据—来源”之间的对应关系。报告写得再流畅，如果无法回到原始来源核对，也只能算自动生成的综述草稿。

### 四层技术架构

系统继续采用前后端分离，并把研究流程放在后端和 Agent 层：

~~~mermaid
flowchart TB
    subgraph F["前端层 · Vue 3 + TypeScript"]
        INPUT["研究主题与搜索引擎"]
        MODAL["全屏研究面板"]
        VIEW["任务 / 日志 / Markdown 报告"]
    end

    subgraph B["后端层 · FastAPI"]
        API["POST /research/stream"]
        STATE["研究状态与事件"]
        COORDINATOR["流程协调器"]
    end

    subgraph A["智能体层 · HelloAgents"]
        PLANNER["TODO Planner"]
        SUMMARIZER["Task Summarizer"]
        WRITER["Report Writer"]
        SEARCH["SearchTool"]
        NOTE["NoteTool"]
    end

    subgraph E["外部服务层"]
        SEARCH_API["搜索引擎"]
        LLM["LLM 提供商"]
    end

    INPUT --> API --> STATE --> COORDINATOR
    COORDINATOR --> PLANNER
    COORDINATOR --> SEARCH --> SEARCH_API
    COORDINATOR --> SUMMARIZER
    COORDINATOR --> NOTE
    COORDINATOR --> WRITER
    PLANNER & SUMMARIZER & WRITER --> LLM
    COORDINATOR --> API --> MODAL --> VIEW
~~~

| 层次 | 主要职责 | 边界 |
| --- | --- | --- |
| 前端 | 收集主题、发起请求、呈现实时进度与报告 | 不保存模型和搜索密钥，不编排 Agent |
| 后端 | 校验输入、创建状态、调度研究流程、推送 SSE | 不把内部异常堆栈直接暴露给页面 |
| Agent | 规划、总结、写报告，决定如何使用工具 | 不处理 HTTP、DOM 和页面状态 |
| 外部服务 | 提供检索数据和模型推理 | 不决定内部 TODO 和报告数据结构 |

分层的意义是隔离变化。更换搜索引擎只影响搜索服务；调整规划 Prompt 不应修改 SSE 协议；前端也不需要知道某次总结调用了哪个模型。

### 三个 Agent 与两个工具

| 组件 | 输入 | 输出 | 关注点 |
| --- | --- | --- | --- |
| TODO Planner | 研究主题、当前日期 | 3–5 个研究任务 | 覆盖范围和查询质量 |
| Task Summarizer | 单个 TODO、搜索结果 | 带引用的阶段总结 | 事实提取、合并重复信息 |
| Report Writer | 主题、全部已完成 TODO | Markdown 报告 | 结构、去重、统一引用 |
| SearchTool | 查询词、搜索后端 | 标题、URL、摘要等 | 统一不同搜索 API 的返回格式 |
| NoteTool | 任务、总结、来源 | 可持久化笔记 | 中间状态、恢复和审计 |

`SearchTool` 负责获取证据，`NoteTool` 负责保留证据处理后的阶段成果。两者都不应代替 Agent 做研究判断。

### TODO 是研究过程的中间协议

一次性让模型“搜索并写报告”，规划、检索和写作会混在一个黑盒里：漏查了什么难以发现，失败后也只能整段重来。TODO 驱动把研究拆成三个阶段：

~~~mermaid
flowchart LR
    TOPIC["研究主题 + 当前日期"] --> PLAN["规划阶段<br/>生成 3–5 个 TODO 草案"]
    PLAN --> EXEC["执行阶段<br/>逐项搜索、总结、记录"]
    EXEC --> REPORT["报告阶段<br/>整合已完成任务"]
    REPORT --> RESULT["Markdown 报告 + 参考资料"]

    PLAN -. 输出 .-> DRAFT["title / intent / query"]
    EXEC -. 输出 .-> EVIDENCE["summary / sources / note_id"]
~~~

Planner 只负责生成任务草案：

| 字段 | 含义 | 示例 |
| --- | --- | --- |
| `title` | 页面展示和报告分节使用的任务名 | 行业现状与主要参与者 |
| `intent` | 解释为什么要查，约束总结重点 | 识别市场格局与代表案例 |
| `query` | 交给搜索工具的检索词 | 2026 深度研究智能体 市场 案例 |

`id`、`status`、`summary`、`sources` 和 `note_id` 属于执行状态，不应让 LLM 在规划时生成。由系统统一编号和维护，既避免模型给出重复或不稳定的 ID，也让状态变化有可靠依据。

### 规划阶段：把主题变成可搜索的问题

Planner 同时接收研究主题和当前日期。日期不是装饰：查询“最新进展”“当前政策”时，模型需要明确时间基准。一个可执行计划至少满足四点：

- 覆盖主题的主要方面，各任务之间尽量少重叠；
- 每项任务的目标明确，能判断是否已经回答；
- `query` 可以直接用于搜索，而不是宽泛的写作标题；
- 数量控制在 3–5 个，避免计划过粗或任务爆炸。

当前实现还会拒绝重复的规范化查询，并在 Planner 返回后按顺序生成稳定 ID。这里的校验不能替代规划质量判断，但能挡住数量错误、重复查询和编号漂移等确定性问题。

### 执行阶段：一个 TODO 是最小审计单元

每个 TODO 都执行同一条链路：

~~~mermaid
stateDiagram-v2
    [*] --> pending
    pending --> in_progress: 开始处理
    in_progress --> in_progress: 搜索并保存结构化来源
    in_progress --> in_progress: 总结并写入笔记
    in_progress --> completed: 结果完整
    in_progress --> failed: 任一步骤异常
    completed --> [*]
    failed --> [*]
~~~

搜索器接收 `query`、用户选择的搜索后端和 `max_results=5`，返回标题、URL、摘要等结构化结果。Summarizer 结合任务意图提炼阶段结论，NoteTool 再保存任务、总结和来源。来源保留为结构化数据，而不是只在正文里留下 `[1]`；否则后续无法去重、重排引用或核验链接。

执行期间会依次推送“开始任务”“正在搜索”“正在总结”“任务完成”等事件。若任一步骤抛出异常，当前任务会先变为 `failed` 并发送状态事件，然后终止本次线性流程，避免报告把未完成任务当成有效结论。

### 报告阶段：整合已有证据

Report Writer 的输入是研究主题和全部已完成 TODO，而不是重新从主题自由发挥。报告通常包含标题、概述、各任务分析、总结和参考资料。它要完成的是跨任务去重、结构调整和引用统一，不能引入阶段总结与来源中没有的新事实。

这种线性流程容易理解和调试，任务状态也很清楚；代价是规划质量决定了研究上限，而且前一任务失败会阻断后续任务。动态补充查询、失败重试、并行执行和断点恢复都很有价值，但不属于 14.2 当前描述的流程，因此本次代码没有提前加入。

### 智能体系统设计：按产物拆分角色

`SimpleAgent` 足以处理一次问答，但深度研究同时存在三种差异明显的输出：机器可解析的计划、带局部引用的任务总结，以及跨任务整合的报告。让一个 Agent 反复切换身份，会让 Prompt 越来越长，也容易把某一阶段的格式带入下一阶段。

14.3 因此按产物拆成三个 Agent，而不是笼统地设置“研究员、专家、审核员”等称号：

| Agent | 必须关注 | 明确不负责 |
| --- | --- | --- |
| TODO Planner | 主题覆盖、任务边界、查询可执行性、JSON 格式 | 搜索资料、撰写正文 |
| Task Summarizer | 当前任务意图、搜索结果、关键数据、局部引用 | 修改计划、推断其他任务结论 |
| Report Writer | 跨任务排序、去重、统一结构和参考资料 | 重新搜索、补写无来源事实 |

职责边界最终要落实到输入和输出。Planner 的输出是 `TodoDraft`；Summarizer 的输出写回对应 `TodoItem.summary`；Report Writer 只接收状态为 `completed` 的任务。三个 Agent 不直接互发自然语言消息，协调器才是状态和执行顺序的唯一管理者。

#### Prompt 是角色之间的接口契约

三个 Prompt 的侧重点不同：

- Planner 注入当前日期和研究主题，要求只返回包含 `title`、`intent`、`query` 的 JSON；
- Summarizer 同时看到任务标题、意图、查询和编号后的来源，使用 `[1]`、`[2]` 建立局部引用；
- Report Writer 接收按任务组织的总结与来源，输出标题、概述、详细分析、总结和参考资料。

只在 Prompt 里写“必须返回 JSON”仍不够。代码还要解析和校验模型输出：规划服务寻找第一个有效 JSON 对象或数组，再用 `TodoDraft` 检查字段；协调器继续检查数量和重复查询。格式要求由 Prompt 引导，确定性约束由程序兜底。

每个角色完成一次调用后都会清空自己的会话历史。本次请求需要的上下文已经完整写入 Prompt，不应让上一个研究主题悄悄影响下一个主题。三个 Agent 可以共享同一个 LLM 客户端，但不能共享对话历史。

### ToolAwareSimpleAgent：为工具调用增加观察点

`ToolAwareSimpleAgent` 不是第四种研究角色，也没有改变 `SimpleAgent` 的思考与工具调用协议。它只重写 `_execute_tool_call()`：先解析参数，复用父类完成工具调用，再把 Agent 名称、工具名、参数和结果交给监听器，最后原样返回结果。

~~~mermaid
sequenceDiagram
    participant A as ToolAwareSimpleAgent
    participant R as ToolRegistry
    participant T as Tool
    participant L as tool_call_listener
    participant C as DeepResearchAgent
    participant V as 前端

    A->>R: get_tool(tool_name)
    R-->>A: Tool
    A->>T: run(parameters)
    T-->>A: result
    A->>L: agent / tool / parameters / result
    L->>C: 暂存调用元数据
    C-->>V: SSE · tool_call
~~~

监听发生在工具执行之后，因此拿到的是实际结果，不是模型“准备调用工具”的意图。监听数据适合调试、过程日志、行为分析和进度展示，但需要控制暴露范围：本次 SSE 只发送 Agent、工具和参数，不把可能很长或含敏感信息的工具结果直接推给前端。

回调本身不能 `yield` SSE 事件，所以代码使用共享的 `ToolCallRecorder` 暂存调用元数据；协调器在规划、总结和报告完成后依次排空记录器。它仍是顺序协作，没有引入后台线程或并发队列。

### 工具系统集成：统一接口，保留来源差异

研究 Agent 不应该知道不同搜索 API 的字段名、认证方式和失败格式。14.4 将这些差异收进 `SearchTool`，对上层只暴露一种调用方式：输入查询、后端、结果数和返回模式，输出统一的来源结构。

| 后端 | 接入条件 | 返回特点 | 更适合 |
| --- | --- | --- | --- |
| DuckDuckGo | 安装 `ddgs`，无需 API Key | 标题、URL、摘要 | 本地体验和普通网页检索 |
| Tavily | `TAVILY_API_KEY` | 面向研究任务的搜索结果 | 需要较规整来源的检索 |
| Perplexity | `PERPLEXITY_API_KEY` | 来源外还可返回 `answer` | 需要带检索上下文的直接回答 |
| SearXNG | 可访问的 `SEARXNG_URL` | 聚合自建实例配置的搜索源 | 自托管和数据控制 |
| Advanced | 至少一个可用后端 | 组合多个来源后统一处理 | 单一搜索源覆盖不足时 |

第七章的 `SerpApi` 与 `hybrid` 仍作为兼容能力保留：`hybrid` 按 Tavily、SerpApi 顺序降级；本章新增的 `advanced` 不是降级，而是调用所有当前可用来源并合并结果。页面只列出本章配置枚举中的五种模式。

#### 统一搜索协议

结构化调用如下：

~~~python
payload = search_tool.run({
    "input": task.query,
    "backend": "advanced",
    "mode": "structured",
    "max_results": 5,
    "max_tokens_per_source": 2000,
})
~~~

返回值固定包含四个字段：

~~~json
{
  "results": [
    {"title": "...", "url": "https://...", "snippet": "..."}
  ],
  "backend": "advanced",
  "answer": null,
  "notices": ["组合来源：tavily、duckduckgo"]
}
~~~

`answer` 只承载 Perplexity 的直接回答，不能代替 `results` 中可核验的来源；配置缺失、单个后端失败和组合信息进入 `notices`。文本模式供 Agent 阅读，结构化模式供协调器和服务层消费，两种模式共用同一套检索与清洗逻辑。

~~~mermaid
flowchart LR
    Q["query / backend / max_results"] --> SELECT{"选择模式"}
    SELECT -->|单后端| ONE["调用指定适配器"]
    SELECT -->|hybrid| FALLBACK["Tavily 失败后尝试 SerpApi"]
    SELECT -->|advanced| MANY["调用全部可用适配器"]
    ONE --> NORMALIZE["统一 title / url / snippet"]
    FALLBACK --> NORMALIZE
    MANY --> MERGE["轮转合并来源"] --> NORMALIZE
    NORMALIZE --> DEDUP["按 URL 保留首次出现"]
    DEDUP --> LIMIT["限制每条摘要长度"]
    LIMIT --> OUT["results / backend / answer / notices"]
~~~

Advanced 使用轮转合并，避免某个后端先返回很多结果，把其他来源全部挤出 `max_results`。随后按 URL 去重，保留第一次出现的版本。原文用“一个 Token 约等于四个字符”截断摘要：

~~~python
max_characters = max_tokens_per_source * 4
if len(snippet) > max_characters:
    snippet = snippet[:max_characters] + "..."
~~~

这是控制上下文规模的近似规则，不是真实分词。中英文、代码和 URL 的 Token 密度不同；若后续需要精确预算，应改用与模型一致的 tokenizer。

#### NoteTool：把研究过程落到磁盘

每个 TODO 完成后，`NotesService` 将任务信息、结构化搜索结果和总结写入 `NoteTool`；报告生成后，再把最终 Markdown 原子写入固定路径：

~~~text
workspace/
├── notes/
│   ├── note_*.md
│   └── notes_index.json
└── reports/
    └── final_report.md
~~~

原文示意图使用 `1.md`、`2.md` 表示任务文件。当前框架的 `NoteTool` 会生成稳定的 `note_id`，所以实际文件名是 `note_*.md`，协调器再把 ID 写回 `TodoItem.note_id`。任务编号仍用于标题和标签，不参与路径拼接。这样既沿用第九章的 NoteTool，也避免模型输出直接决定文件名。

笔记正文保持固定结构：任务标题、意图、查询、逐条来源和总结。若任务已经有 `note_id`，再次记录会更新原笔记；最终报告则覆盖 `reports/final_report.md`，临时文件写完后再替换正式文件，避免只写入半份报告。

持久化不等于断点恢复。现在磁盘上已有可审计的中间产物，但协调器还没有读取索引、重建 TODO 状态和恢复 SSE 游标；这些状态恢复逻辑不能只靠“文件存在”推断。

#### ToolRegistry：统一发现和调用

`SearchTool` 与 `NoteTool` 在 Agent 创建前注册到同一个 `ToolRegistry`，三个角色因此可以共享工具描述和调用入口：

~~~python
registry = ToolRegistry()
registry.register_tool(search_tool)
registry.register_tool(note_tool)

agent = ToolAwareSimpleAgent(
    name="研究助手",
    llm=llm,
    tool_registry=registry,
)
~~~

原文把整条链路概括为“生成、解析、查找、执行、返回”。结合当前 HelloAgents 实现，边界更具体：`SimpleAgent` 解析 `[TOOL_CALL:工具名:参数]` 文本协议和 JSON 参数；`ToolRegistry` 负责按名称找到工具；工具的 `run()` 负责业务执行；`ToolAwareSimpleAgent` 在执行后记录调用信息。

注册名取自 `SearchTool.name`，当前值是 `search`，所以调用标记应写成 `[TOOL_CALL:search:{...}]`；类名 `SearchTool` 不是注册表中的键。

~~~mermaid
sequenceDiagram
    participant L as LLM
    participant A as SimpleAgent
    participant R as ToolRegistry
    participant T as SearchTool / NoteTool

    L-->>A: [TOOL_CALL:search:{...}]
    A->>A: 解析名称与参数
    A->>R: get_tool("search")
    R-->>A: SearchTool
    A->>T: run(parameters)
    T-->>A: 结构化结果
    A-->>L: 格式化后的工具结果
~~~

把解析职责写清楚很重要：注册表不是 Prompt 解析器，也不决定研究流程；它只是工具对象的目录和执行边界。

### 一次研究请求怎样流转

~~~mermaid
sequenceDiagram
    actor U as 用户
    participant V as Vue 前端
    participant F as FastAPI
    participant P as TODO Planner
    participant S as SearchTool
    participant T as Task Summarizer
    participant N as NoteTool
    participant R as Report Writer

    U->>V: 输入研究主题
    V->>F: POST /research/stream
    F->>F: 校验请求并创建状态
    F->>P: 分解研究主题
    P-->>F: TODO 列表
    F-->>V: SSE · tasks
    loop 每个 TODO
        F->>S: 执行 query
        S-->>F: 搜索结果与来源
        F->>T: 总结当前任务
        T-->>F: 阶段总结
        F->>N: 保存总结和来源
        F-->>V: SSE · task
    end
    F->>R: 整合全部任务
    R-->>F: Markdown 报告
    F-->>V: SSE · report / done
    V-->>U: 更新任务、日志和报告
~~~

这条链路有两个不同的数据面：

- 研究状态保存 TODO、搜索结果、总结和引用，是后续步骤的输入；
- SSE 事件只负责可观测性，把 `status`、`tasks`、`task`、`report`、`done` 等变化推给页面。

状态不能只存在于日志里，否则页面能显示“完成”，报告生成器却拿不到真正的任务总结。

### 为什么使用 SSE

研究任务通常持续数分钟。如果前端等待一个普通 JSON 响应，期间无法知道是在规划、检索还是总结，也很难提供取消操作。SSE 让后端在同一 HTTP 响应中持续写入事件：

~~~text
data: {"type":"status","message":"正在规划研究任务","progress":0}

data: {"type":"tasks","tasks":[...],"progress":10}

data: {"type":"tool_call","message":"研究助手调用工具：example_tool"}

data: {"type":"report","report_markdown":"# ...","progress":98}

data: {"type":"done","message":"研究完成","progress":100}
~~~

本项目需要在请求体中提交主题和搜索后端，因此前端使用 `fetch()` 发起 POST，再读取 `ReadableStream`；原生 `EventSource` 只适合 GET，不能直接承载这里的 JSON 请求体。

### 代码实践

#### 当前工程结构

实践代码放在 `code/HelloAgents/helloagents-deepresearch/`，保留原文的前后端边界：

~~~text
helloagents-deepresearch/
├── backend/
│   ├── src/
│   │   ├── agent.py
│   │   ├── architecture.py
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── prompts.py
│   │   ├── streaming.py
│   │   ├── tool_events.py
│   │   ├── tooling.py
│   │   └── services/
│   │       ├── notes.py
│   │       ├── planner.py
│   │       ├── summarizer.py
│   │       ├── reporter.py
│   │       └── factory.py
│   ├── .env.example
│   ├── agent_system_demo.py
│   ├── architecture_demo.py
│   ├── tool_system_demo.py
│   ├── workflow_demo.py
│   └── pyproject.toml
└── frontend/
    ├── src/
    │   ├── components/ResearchModal.vue
    │   ├── composables/useResearch.ts
    │   ├── types/research.ts
    │   ├── App.vue
    │   ├── main.ts
    │   └── style.css
    ├── index.html
    ├── package.json
    ├── tsconfig.json
    └── vite.config.ts
~~~

- [项目 README](./code/HelloAgents/helloagents-deepresearch/README.md) 记录运行方式与当前边界；
- [architecture.py](./code/HelloAgents/helloagents-deepresearch/backend/src/architecture.py) 定义四层架构、Agent、工具和八步数据流；
- [models.py](./code/HelloAgents/helloagents-deepresearch/backend/src/models.py) 区分 Planner 生成的 `TodoDraft` 与系统维护的 `TodoItem`，并固定搜索、阶段和 SSE 事件结构；
- [agent.py](./code/HelloAgents/helloagents-deepresearch/backend/src/agent.py) 校验规划结果并执行“规划—逐项搜索、总结、记录—报告”；
- [search_tool.py](./code/HelloAgents/hello_agents/tools/builtin/search_tool.py) 实现多搜索后端、统一返回、Advanced 合并、去重和摘要限长；
- [tooling.py](./code/HelloAgents/helloagents-deepresearch/backend/src/tooling.py) 创建工具注册表，并把结构化搜索结果转换成协调器的数据模型；
- [notes.py](./code/HelloAgents/helloagents-deepresearch/backend/src/services/notes.py) 通过 NoteTool 保存任务笔记，并写入最终报告；
- [tool_system_demo.py](./code/HelloAgents/helloagents-deepresearch/backend/tool_system_demo.py) 用固定搜索响应验证工具层，不调用外部 API；
- [prompts.py](./code/HelloAgents/helloagents-deepresearch/backend/src/prompts.py) 定义三个角色的输入、输出和事实边界；
- [services](./code/HelloAgents/helloagents-deepresearch/backend/src/services/) 实现规划 JSON 解析、来源格式化和报告上下文组装；
- [tool_aware_simple_agent.py](./code/HelloAgents/hello_agents/agents/tool_aware_simple_agent.py) 在框架层扩展工具调用监听；
- [tool_events.py](./code/HelloAgents/helloagents-deepresearch/backend/src/tool_events.py) 将监听回调桥接为协调器可以发送的事件；
- [main.py](./code/HelloAgents/helloagents-deepresearch/backend/src/main.py) 暴露健康检查、架构信息和流式研究入口；
- [useResearch.ts](./code/HelloAgents/helloagents-deepresearch/frontend/src/composables/useResearch.ts) 解析 POST 返回的 SSE 数据帧；
- [ResearchModal.vue](./code/HelloAgents/helloagents-deepresearch/frontend/src/components/ResearchModal.vue) 展示任务、日志、进度和报告。

#### 用接口固定协作边界

14.2 先固定组件协议，14.3 用三个 Agent 服务实现规划、总结和报告，14.4 再用适配器实现搜索与持久化协议。协调器仍不绑定具体 Agent、搜索供应商或文件工具：

~~~python
class Planner(Protocol):
    def plan(self, topic: str, current_date: str) -> list[TodoDraft]: ...

class Searcher(Protocol):
    def search(
        self,
        query: str,
        *,
        backend: SearchAPI | None,
        max_results: int,
    ) -> list[SearchResult]: ...

class Reporter(Protocol):
    def write(self, topic: str, tasks: Sequence[TodoItem]) -> str: ...

class ReportStore(Protocol):
    def save_report(self, topic: str, report_markdown: str) -> str: ...
~~~

Planner 返回草案后，协调器再补充系统字段并逐项执行：

~~~python
drafts = self._planner.plan(normalized_topic, current_date)
if not 3 <= len(drafts) <= 5:
    raise ValueError("TODO Planner 必须生成 3–5 个子任务")

tasks = [
    TodoItem(id=index, **draft.model_dump())
    for index, draft in enumerate(drafts, start=1)
]

results = self._searcher.search(
    task.query,
    backend=search_api,
    max_results=self._max_results,
)
~~~

这样既保留原文的顺序工作流，也确保前端选择的搜索后端真正传到 Searcher。`SearchToolAdapter` 负责把工具字典校验成 `SearchResult`，`NotesService` 同时实现 `NoteWriter` 和 `ReportStore`。FastAPI 通过 `runner_factory` 注入协调器；全局应用没有装配完整服务时，`POST /research/stream` 返回 `503`，而不是生成没有搜索来源的占位报告。

工具层的组合入口只做创建和注册：

~~~python
toolset = build_research_toolset(settings)
roles = build_role_services(llm, tool_registry=toolset.registry)

coordinator = DeepResearchAgent(
    planner=roles.planner,
    searcher=toolset.searcher,
    summarizer=roles.summarizer,
    note_writer=toolset.notes,
    reporter=roles.reporter,
    report_store=toolset.notes,
)
~~~

#### 三个角色服务与监听扩展

`PlanningService`、`SummarizationService`、`ReportingService` 分别实现协调器的三个协议。`build_role_services()` 为它们创建独立的 `ToolAwareSimpleAgent`，共享 LLM、工具注册表和监听器：

~~~python
return RoleServices(
    planner=PlanningService(
        create_agent("TODO Planner", TODO_PLANNER_SYSTEM_PROMPT)
    ),
    summarizer=SummarizationService(
        create_agent("Task Summarizer", TASK_SUMMARIZER_SYSTEM_PROMPT)
    ),
    reporter=ReportingService(
        create_agent("Report Writer", REPORT_WRITER_SYSTEM_PROMPT)
    ),
)
~~~

监听扩展仍然复用父类的工具执行逻辑：

~~~python
def _execute_tool_call(self, tool_name: str, parameters: str) -> str:
    parsed_parameters = self._parse_listener_parameters(tool_name, parameters)
    result = super()._execute_tool_call(tool_name, parameters)
    if self._tool_call_listener is not None:
        self._tool_call_listener({
            "agent_name": self.name,
            "tool_name": tool_name,
            "parsed_parameters": parsed_parameters,
            "result": result,
        })
    return result
~~~

这里没有把规划、总结和报告塞回协调器，也没有为三个角色各写一套 LLM 客户端。服务负责准备上下文和解析输出，Agent 负责模型交互，协调器只负责顺序与状态。

#### 配置只报告是否存在

[.env.example](./code/HelloAgents/helloagents-deepresearch/backend/.env.example) 包含模型、搜索后端、跨域和工作区配置，所有密钥保持为空。`/healthz` 只检查配置是否存在，不访问外部服务，也不会返回密钥内容：

~~~python
return {
    "llm": bool(self.llm_model_id and self.llm_api_key),
    "search": search_ready,
    "notes": bool(self.notes_workspace.strip()),
}
~~~

“已填写”不等于“调用成功”。真实连通性、额度、超时与重试要在对应服务接入后验证。

#### 运行方式

后端要求 Python 3.10+：

~~~bash
cd code/HelloAgents/helloagents-deepresearch/backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
export PYTHONPATH=../..
python src/main.py
~~~

不配置密钥也可以先验证 14.4 工具链：

~~~bash
PYTHONDONTWRITEBYTECODE=1 python tool_system_demo.py
~~~

前端要求 Node.js 16+ 和 npm 8+；实际还要满足当前 Vite 版本的 Node.js 要求：

~~~bash
cd code/HelloAgents/helloagents-deepresearch/frontend
npm install
npm run dev
~~~

默认前端地址为 `http://localhost:5174`，后端为 `http://localhost:8000`，接口文档位于 `http://localhost:8000/docs`。

#### 实践结果

架构 Demo 验证四层、三个 Agent、两个工具、八个数据流步骤和 TODO 工作流契约：

~~~text
=== 14.1–14.4 深度研究助手架构实践 ===
layers: 4
agents: 3
tools: 2
data_flow_steps: 8
stream_endpoint: POST /research/stream
architecture_contract: ready
todo_research_workflow: ready
agent_system_design: ready
tool_system_integration: ready
external_api_calls: 0
~~~

TODO 流程使用固定测试替身，实际验证了日期传递、系统编号、搜索后端与结果上限、状态变化、来源保留、失败状态、SSE 分帧和报告收集：

~~~text
=== 14.2 TODO 驱动研究离线验证 ===
todo_tasks: 3
stream_events: 17
todo_drafts_numbered: ready
planning_date_forwarded: ready
selected_search_backend: ready
task_state_transitions: ready
source_preservation: ready
failure_state: ready
sse_frames: ready
fastapi_stream_route: ready
report_collection: ready
external_api_calls: 0
~~~

这 17 个事件由 1 个规划状态、1 个任务列表、每项任务 4 个事件、1 个报告状态、1 个报告事件和 1 个完成事件组成。测试替身只验证编排逻辑，输出不是一次真实研究结果。

14.3 的 Agent 服务验证继续使用固定响应，但走过真实的 Prompt 组装、JSON 解析、角色历史清理、协调器交接和工具事件排空逻辑：

~~~text
=== 14.3 智能体系统设计离线验证 ===
role_agents: 3
todo_tasks: 3
stream_events: 22
planner_json_contract: ready
summarizer_source_context: ready
reporter_task_handoff: ready
role_history_isolation: ready
tool_call_listener_bridge: ready
sequential_collaboration: ready
external_api_calls: 0
~~~

为了验证监听桥接，测试替身分别模拟了 Planner 1 次、Summarizer 3 次和 Report Writer 1 次工具调用，所以比 14.2 多出 5 个事件。这里用脚本化 Agent 代替真实 LLM，验证的是角色协作和观察链路，不是报告内容质量。

14.4 使用四个固定搜索适配器和临时工作区，执行了 Advanced 搜索以及完整的三任务协调流程：

~~~text
=== 14.4 工具系统集成离线验证 ===
registered_tools: search, note
search_backends: tavily, duckduckgo, perplexity, searxng
advanced_results: 5
deduplicated_urls: ready
source_token_limit: ready
task_notes: 3
final_report: ready
coordinator_persistence: ready
external_api_calls: 0
~~~

四个适配器中有两个返回同一 URL，最终只保留一条；40 个字符的测试摘要在 5 个近似 Token 的限制下截为 20 个字符加省略号。协调器随后为三个 TODO 分别创建笔记，并把报告写入临时目录中的 `reports/final_report.md`。这验证的是工具协议、清洗和落盘链路，不代表真实搜索质量。

前端 `vue-tsc` 与 Vite 生产构建通过，共转换 14 个模块；入口脚本为 73.02 kB（gzip 后 29.56 kB）。上一次依赖审计返回 `found 0 vulnerabilities`；本节没有变更前端依赖。

### 实践边界

- 当前完成 14.1 的架构基线、14.2 的 TODO 工作流、14.3 的三个 Agent 服务，以及 14.4 的搜索与笔记工具集成；
- `DeepResearchAgent` 已实现三阶段编排、任务状态、工具调用事件与失败事件，但全局 FastAPI 应用尚未注入生产服务；
- Prompt 约束不能保证模型始终按格式输出；规划结果仍会经过 JSON、Pydantic、数量和重复查询四层检查；
- 当前任务按顺序执行；失败后不自动重试、跳过或重新规划；
- NoteTool 已保存任务产物，SSE 也能展示进度，但断线恢复仍需要重建任务状态和事件游标；
- 搜索摘要不是原文全文，关键结论仍应回到来源核验；
- 配置检查不发起联网请求，不能证明模型或搜索 API 可用；
- 没有使用真实密钥，也没有调用收费模型或搜索服务；
- 前端目前按纯文本保留 Markdown，安全渲染、引用跳转和报告导出留给后续界面实现。

### 参考资料

- [《Hello-Agents》第十四章：自动化深度研究智能体](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter14/%E7%AC%AC%E5%8D%81%E5%9B%9B%E7%AB%A0%20%E8%87%AA%E5%8A%A8%E5%8C%96%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6%E6%99%BA%E8%83%BD%E4%BD%93.md)
- [官方深度研究助手项目](https://github.com/datawhalechina/hello-agents/tree/main/code/chapter14/helloagents-deepresearch)
- [官方搜索调度代码](https://github.com/datawhalechina/hello-agents/blob/main/code/chapter14/helloagents-deepresearch/backend/src/services/search.py)
- [官方 FastAPI 入口](https://github.com/datawhalechina/hello-agents/blob/main/code/chapter14/helloagents-deepresearch/backend/src/main.py)
- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [MDN：使用可读流](https://developer.mozilla.org/zh-CN/docs/Web/API/Streams_API/Using_readable_streams)
- [Vue 3 官方文档](https://vuejs.org/)

### 小结

深度研究助手不是搜索框外面再套一层 LLM，而是一条可观测、可落盘的研究流水线。14.1 固定四层边界和 SSE 协议，14.2 用 TODO 串起规划、执行和报告，14.3 把三类产物交给三个独立 Agent，14.4 再以统一协议接入多种搜索后端、NoteTool 和 ToolRegistry。Agent 只处理研究判断，工具处理外部能力，协调器维护状态与顺序。当前版本已经能保存任务证据和最终报告，但生产服务装配、缓存及真正的断点恢复仍需后续完成。
