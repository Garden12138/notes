## 自动化深度研究智能体

> 阅读资料：[14.1 项目概述与架构设计](https://datawhalechina.github.io/hello-agents/#/./chapter14/%E7%AC%AC%E5%8D%81%E5%9B%9B%E7%AB%A0%20%E8%87%AA%E5%8A%A8%E5%8C%96%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6%E6%99%BA%E8%83%BD%E4%BD%93?id=_141-%e9%a1%b9%e7%9b%ae%e6%a6%82%e8%bf%b0%e4%b8%8e%e6%9e%b6%e6%9e%84%e8%ae%be%e8%ae%a1)、[14.2 TODO 驱动的研究范式](https://datawhalechina.github.io/hello-agents/#/./chapter14/%E7%AC%AC%E5%8D%81%E5%9B%9B%E7%AB%A0%20%E8%87%AA%E5%8A%A8%E5%8C%96%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6%E6%99%BA%E8%83%BD%E4%BD%93?id=_142-todo-%e9%a9%b1%e5%8a%a8%e7%9a%84%e7%a0%94%e7%a9%b6%e8%8c%83%e5%bc%8f)
>
> 14.1 确定产品目标、四层架构和数据流；14.2 用 TODO 把开放问题转成可执行、可跟踪、可整合的研究任务。

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
│   │   └── streaming.py
│   ├── .env.example
│   ├── architecture_demo.py
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
- [main.py](./code/HelloAgents/helloagents-deepresearch/backend/src/main.py) 暴露健康检查、架构信息和流式研究入口；
- [useResearch.ts](./code/HelloAgents/helloagents-deepresearch/frontend/src/composables/useResearch.ts) 解析 POST 返回的 SSE 数据帧；
- [ResearchModal.vue](./code/HelloAgents/helloagents-deepresearch/frontend/src/components/ResearchModal.vue) 展示任务、日志、进度和报告。

#### 用接口固定协作边界

14.2 讲清了组件怎样协作，但真实模型 Prompt、搜索适配器和 NoteTool 会在后续小节展开。当前协调器依赖协议，不绑定具体供应商：

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

这样既保留原文的顺序工作流，也确保前端选择的搜索后端真正传到 Searcher。FastAPI 通过 `runner_factory` 注入协调器；全局应用没有装配具体服务时，`POST /research/stream` 返回 `503`，而不是生成没有搜索来源的占位报告。

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
python src/main.py
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
=== 14.1–14.2 深度研究助手架构实践 ===
layers: 4
agents: 3
tools: 2
data_flow_steps: 8
stream_endpoint: POST /research/stream
architecture_contract: ready
todo_research_workflow: ready
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

前端 `vue-tsc` 与 Vite 生产构建通过，共转换 14 个模块；入口脚本为 72.96 kB（gzip 后 29.52 kB）。`npm audit` 返回 `found 0 vulnerabilities`。

### 实践边界

- 当前完成 14.1 的架构基线和 14.2 的 TODO 顺序工作流，不包含后续小节的真实 Prompt、搜索适配和 NoteTool 持久化；
- `DeepResearchAgent` 已实现三阶段编排、任务状态与失败事件，但全局 FastAPI 应用尚未注入生产服务；
- 当前任务按顺序执行；失败后不自动重试、跳过或重新规划；
- SSE 保证进度可见，不保证任务断线后自动恢复；恢复需要持久化研究状态和事件游标；
- 搜索摘要不是原文全文，关键结论仍应回到来源核验；
- 配置检查不发起联网请求，不能证明模型或搜索 API 可用；
- 没有使用真实密钥，也没有调用收费模型或搜索服务；
- 前端目前按纯文本保留 Markdown，安全渲染、引用跳转和报告导出留给后续界面实现。

### 参考资料

- [《Hello-Agents》第十四章：自动化深度研究智能体](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter14/%E7%AC%AC%E5%8D%81%E5%9B%9B%E7%AB%A0%20%E8%87%AA%E5%8A%A8%E5%8C%96%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6%E6%99%BA%E8%83%BD%E4%BD%93.md)
- [官方深度研究助手项目](https://github.com/datawhalechina/hello-agents/tree/main/code/chapter14/helloagents-deepresearch)
- [官方 FastAPI 入口](https://github.com/datawhalechina/hello-agents/blob/main/code/chapter14/helloagents-deepresearch/backend/src/main.py)
- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [MDN：使用可读流](https://developer.mozilla.org/zh-CN/docs/Web/API/Streams_API/Using_readable_streams)
- [Vue 3 官方文档](https://vuejs.org/)

### 小结

深度研究助手不是搜索框外面再套一层 LLM，而是一条可观测的研究流水线。14.1 固定四层边界、数据模型和 SSE 协议，14.2 再用 TODO 串起规划、执行和报告三个阶段。Planner 只生成 `title`、`intent`、`query`，系统负责编号和状态；每项任务都留下总结与结构化来源，Report Writer 只整合已完成任务。这个线性版本简单、可审计，也暴露了规划上限、失败阻断和无法动态补查等边界，为后续服务实现和流程增强留下了清楚的扩展点。
