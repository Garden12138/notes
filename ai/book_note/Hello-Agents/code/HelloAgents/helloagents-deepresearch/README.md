# HelloAgents 自动化深度研究助手

这是第十四章的持续实践目录。14.1 实现前后端工程骨架、四层架构契约和 SSE 通道；14.2 补全 TODO 草案、任务编号及三阶段顺序流程；14.3 实现规划、总结、报告三个 Agent 服务，以及工具调用监听和事件桥接；14.4 接入多后端 `SearchTool`、`NoteTool` 和 `ToolRegistry`。

## 当前结构

```text
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
```

## 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
export PYTHONPATH=../..
python src/main.py
```

可用接口：

- `GET /`：项目入口；
- `GET /healthz`：配置存在性与工作流装配状态；
- `GET /architecture`：四层架构、Agent、工具和数据流；
- `POST /research/stream`：SSE 通道。

当前尚未在全局应用中装配真实 LLM 和各角色服务，因此直接调用研究接口仍会明确返回 `503`，不会生成没有来源的占位报告。14.4 已提供 `build_research_toolset()`：它根据配置创建搜索、笔记和注册表，并提供协调器所需的 `Searcher`、`NoteWriter` 与 `ReportStore` 适配对象；完整组合根留到服务层小节。

搜索后端可选 `duckduckgo`、`tavily`、`perplexity`、`searxng` 和 `advanced`。`advanced` 会调用当前可用的多个来源，按轮转顺序合并结果，再按 URL 去重和限制摘要长度。结构化返回固定包含 `results`、`backend`、`answer`、`notices`。

任务记录保存到 `NOTES_WORKSPACE/notes/`，最终报告原子写入 `NOTES_WORKSPACE/reports/final_report.md`。`NoteTool` 自己生成稳定笔记 ID，并回填到 `TodoItem.note_id`；文件名不依赖模型输出的任务编号。

离线验证：

```bash
PYTHONDONTWRITEBYTECODE=1 python architecture_demo.py
PYTHONDONTWRITEBYTECODE=1 python workflow_demo.py
PYTHONDONTWRITEBYTECODE=1 python agent_system_demo.py
PYTHONDONTWRITEBYTECODE=1 python tool_system_demo.py
```

`workflow_demo.py` 验证 14.2 的 TODO 数据流；`agent_system_demo.py` 验证三个角色的结构化交接；`tool_system_demo.py` 使用四个固定搜索适配器和临时目录，验证 Advanced 合并、URL 去重、摘要限长、工具注册、三条任务笔记与最终报告。所有 Demo 都不会访问模型或真实搜索服务，临时笔记不会写入仓库。

`ToolAwareSimpleAgent` 位于同级 HelloAgents 框架的 `hello_agents/agents/tool_aware_simple_agent.py`，在 `SimpleAgent` 原有行为上增加完成后监听，不改变工具执行协议。`PYTHONPATH=../..` 让后端优先使用这份随章节持续完善的本地框架代码。

## 前端

```bash
cd frontend
npm install
npm run dev
```

默认访问 <http://localhost:5174>。前端通过 `fetch()` 发送带请求体的 `POST /research/stream`，再从响应体逐帧解析 `text/event-stream`；这与只能发起 GET 的原生 `EventSource` 不同。

构建和依赖审计：

```bash
npm run build
npm audit
```

当前实践中两条命令均通过，审计结果为 0 个已知漏洞。

`.env` 中只填写本地配置，不要提交真实密钥。
