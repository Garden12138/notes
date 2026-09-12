# HelloAgents 智能旅行助手

这是第十三章持续实践目录。13.1 完成前后端骨架，13.2 增加统一数据模型，13.3 实现四个 Agent 的固定协作流程，13.4 接入共享的高德 MCP 工具和 Unsplash 图片服务，13.5 完成需求表单、行程结果、地图和导出页面。

## 目录

```text
helloagents-trip-planner/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── prompts.py
│   │   │   └── trip_planner.py
│   │   ├── api/routes/trip.py
│   │   ├── models/schemas.py
│   │   ├── services/
│   │   │   ├── agent_runtime.py
│   │   │   ├── architecture.py
│   │   │   ├── mcp_integration.py
│   │   │   └── unsplash.py
│   │   └── config.py
│   ├── architecture_demo.py
│   ├── collaboration_demo.py
│   ├── mcp_integration_demo.py
│   ├── model_demo.py
│   ├── requirements.txt
│   └── run.py
└── frontend/
    ├── package-lock.json
    ├── src/
    │   ├── router/
    │   ├── services/
    │   │   ├── api.ts
    │   │   ├── trip-storage.ts
    │   │   └── trip.ts
    │   ├── types/trip.ts
    │   └── views/
    │       ├── HomeView.vue
    │       └── ResultView.vue
    └── package.json
```

## 离线架构验证

```bash
cd backend
python architecture_demo.py
```

该命令不需要模型或外部服务的密钥与网络。

## 离线数据模型验证

本机安装 Pydantic 2 后可运行：

```bash
cd backend
python model_demo.py
```

脚本会构造一次两日旅行计划，验证日期、坐标、温度、预算、嵌套模型和 JSON 往返，并主动捕获三类非法输入。它不会调用 Agent 或外部 API。

## 离线协作流程验证

```bash
cd backend
python collaboration_demo.py
```

脚本使用四个确定性测试 Agent，验证景点、天气和酒店结果确实被传给规划 Agent，最终 JSON 经过 `TripPlan` 和规划规则校验。无效输出会明确失败，不会回退到虚构行程。

## 离线 MCP 集成验证

```bash
cd backend
python mcp_integration_demo.py
```

脚本使用假的 MCP Tool 与 HTTP 响应，验证高德 Server 启动参数、工具自动展开、必要工具检查、三个检索 Agent 共享同一工具，以及 Unsplash 图片补全。它不会启动 `uvx` 子进程，也不会访问高德、Unsplash 或模型 API。

## 启动后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
PYTHONPATH=../.. python run.py
```

`PYTHONPATH=../..` 指向同一 `code/HelloAgents/` 目录下持续实现的本地 `hello_agents` 框架，避免改用另一套旅行 Agent 实现。

启动后可访问：

- API 文档：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/api/system/health>
- 架构快照：<http://127.0.0.1:8000/api/system/architecture>
- 请求校验：`POST http://127.0.0.1:8000/api/trip/validate`
- 行程规划：`POST http://127.0.0.1:8000/api/trip/plan`

首次请求 `/api/trip/plan` 时，后端会启动 `uvx amap-mcp-server` 完成工具发现，并检查 `amap_maps_text_search` 与 `amap_maps_weather` 是否可用。LLM 或高德配置缺失、Server 启动失败、必要工具缺失时返回 `503`；Agent 输出无法通过 `TripPlan` 校验时返回 `502`。规划成功后再调用 Unsplash 补全景点图片，图片失败不会伪造 URL，也不会让有效行程失败。

## 启动前端

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

浏览器访问 <http://127.0.0.1:5173>。`src/types/trip.ts` 定义了与后端一致的旅行数据契约。

首页会把目的地、日期、出行方式和偏好转换为 `TripRequest`，调用 `POST /api/trip/plan`。成功后结果保存到 `sessionStorage` 并跳转 `/result`，展示行程、预算、天气和地图，也可导出 PNG 或 PDF。

`.env` 中的 `VITE_API_BASE_URL` 默认指向本地后端；如需地图，还要填写高德 JS API 使用的 `VITE_AMAP_WEB_KEY`。它与后端 MCP 的 `AMAP_MAPS_API_KEY` 用途不同，不要混用。

生产构建与依赖检查：

```bash
npm run build
npm audit
```

13.5 实践中两条命令均通过，审计结果为 0 个已知漏洞。行程编辑与路线联动保留给 13.6。

`.env` 只保存在本地，不要提交真实密钥。运行真实规划需要配置 `LLM_API_KEY`、`LLM_MODEL_ID`、`LLM_BASE_URL` 和 `AMAP_MAPS_API_KEY`；`UNSPLASH_ACCESS_KEY` 可选，未配置时只是不补充景点图片。三个检索 Agent 共享一个 `MCPTool` 门面，行程规划 Agent 不注册外部工具。
