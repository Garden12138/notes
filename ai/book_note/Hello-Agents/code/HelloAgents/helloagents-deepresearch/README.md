# HelloAgents 自动化深度研究助手

这是第十四章的持续实践目录。14.1 实现前后端工程骨架、四层架构契约和 SSE 通道；14.2 在此基础上补全 TODO 草案、任务编号、三阶段状态以及“搜索—总结—记录”的顺序执行流程。真实模型、搜索、笔记与报告服务将在后续小节逐步接入。

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
```

## 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
python src/main.py
```

可用接口：

- `GET /`：项目入口；
- `GET /healthz`：配置存在性与工作流装配状态；
- `GET /architecture`：四层架构、Agent、工具和数据流；
- `POST /research/stream`：SSE 通道。

当前尚未装配真实服务，因此直接调用全局应用的研究接口会明确返回 `503`，不会生成没有来源的占位报告。后续只需在组合根提供 `DeepResearchAgent` 工厂，无需修改 API 和前端协议。

离线验证：

```bash
PYTHONDONTWRITEBYTECODE=1 python architecture_demo.py
PYTHONDONTWRITEBYTECODE=1 python workflow_demo.py
```

`workflow_demo.py` 使用确定性测试替身验证规划日期、系统编号、搜索后端传递、任务状态、来源保留、失败状态和调用顺序，不访问模型、搜索引擎或文件系统。

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
