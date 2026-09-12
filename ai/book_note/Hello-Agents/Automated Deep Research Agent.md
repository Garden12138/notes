## 自动化深度研究智能体

> 阅读资料：[14.1 项目概述与架构设计](https://datawhalechina.github.io/hello-agents/#/./chapter14/%E7%AC%AC%E5%8D%81%E5%9B%9B%E7%AB%A0%20%E8%87%AA%E5%8A%A8%E5%8C%96%E6%B7%B1%E5%BA%A6%E7%A0%94%E7%A9%B6%E6%99%BA%E8%83%BD%E4%BD%93?id=_141-%e9%a1%b9%e7%9b%ae%e6%a6%82%e8%bf%b0%e4%b8%8e%e6%9e%b6%e6%9e%84%e8%ae%be%e8%ae%a1)
>
> 14.1 先确定产品目标、四层架构和数据流。TODO 规划、搜索适配、任务总结与报告生成将在后续小节逐步实现。

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
- [models.py](./code/HelloAgents/helloagents-deepresearch/backend/src/models.py) 固定请求、TODO、搜索结果和 SSE 事件结构；
- [agent.py](./code/HelloAgents/helloagents-deepresearch/backend/src/agent.py) 根据依赖注入的服务执行“规划—逐项搜索与总结—记录—报告”；
- [main.py](./code/HelloAgents/helloagents-deepresearch/backend/src/main.py) 暴露健康检查、架构信息和流式研究入口；
- [useResearch.ts](./code/HelloAgents/helloagents-deepresearch/frontend/src/composables/useResearch.ts) 解析 POST 返回的 SSE 数据帧；
- [ResearchModal.vue](./code/HelloAgents/helloagents-deepresearch/frontend/src/components/ResearchModal.vue) 展示任务、日志、进度和报告。

#### 用接口隔离后续实现

14.1 尚未讲解 Planner、搜索器和报告器的具体实现，所以协调器只依赖清晰的协议：

~~~python
class Planner(Protocol):
    def plan(self, topic: str) -> list[TodoItem]: ...

class Searcher(Protocol):
    def search(self, query: str) -> list[SearchResult]: ...

class Reporter(Protocol):
    def write(self, topic: str, tasks: Sequence[TodoItem]) -> str: ...
~~~

`DeepResearchAgent` 已完整实现数据流和事件顺序，但不在这一节伪造真实服务。FastAPI 通过 `runner_factory` 注入协调器；全局应用没有装配服务时，`POST /research/stream` 返回明确的 `503`，而不是生成没有搜索来源的占位报告。

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

#### 离线实践结果

架构 Demo 验证四层、三个 Agent、两个工具和八个数据流步骤：

~~~text
=== 14.1 深度研究助手架构实践 ===
layers: 4
agents: 3
tools: 2
data_flow_steps: 8
stream_endpoint: POST /research/stream
architecture_contract: ready
external_api_calls: 0
~~~

协调器 Demo 使用固定测试替身，验证 TODO 数量、搜索—总结—笔记顺序、SSE 分帧和报告收集，不把输出当作真实研究结果：

~~~text
=== 14.1 研究数据流离线验证 ===
todo_tasks: 3
stream_events: 11
search_summary_note_cycle: ready
sse_frames: ready
report_collection: ready
external_api_calls: 0
~~~

前端 `vue-tsc` 与 Vite 生产构建通过，共转换 14 个模块；入口脚本为 72.96 kB（gzip 后 29.52 kB）。`npm audit` 返回 `found 0 vulnerabilities`。

### 实践边界

- 当前完成的是 14.1 架构基线，不包含后续小节的真实 Prompt、搜索适配和 NoteTool 持久化；
- `DeepResearchAgent` 的编排逻辑可以用测试替身完整运行，但全局 FastAPI 应用尚未注入生产服务；
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

深度研究助手不是搜索框外面再套一层 LLM，而是一条可观测的研究流水线：TODO Planner 决定查什么，SearchTool 获取证据，Task Summarizer 形成阶段结论，NoteTool 保存中间成果，Report Writer 负责最终组织。14.1 的实践先固定四层边界、数据模型和 SSE 事件协议，并用依赖注入保留后续扩展位置；没有真实服务时明确拒绝生成报告，避免把流程演示误认为研究结论。
