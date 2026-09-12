# HelloAgents 智能旅行助手

这是第十三章持续实践目录。13.1 完成前后端骨架，13.2 增加统一的请求、行程、天气、预算、POI 与路线模型。真实 Agent、MCP 调用、地图和导出仍按后续小节逐步补充。

## 目录

```text
helloagents-trip-planner/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── api/routes/trip.py
│   │   ├── models/schemas.py
│   │   ├── services/
│   │   └── config.py
│   ├── architecture_demo.py
│   ├── model_demo.py
│   ├── requirements.txt
│   └── run.py
└── frontend/
    ├── src/
    │   ├── router/
    │   ├── services/trip.ts
    │   ├── types/trip.ts
    │   └── views/
    └── package.json
```

## 离线架构验证

```bash
cd backend
python architecture_demo.py
```

该命令不需要依赖、密钥或网络。

## 离线数据模型验证

本机安装 Pydantic 2 后可运行：

```bash
cd backend
python model_demo.py
```

脚本会构造一次两日旅行计划，验证日期、坐标、温度、预算、嵌套模型和 JSON 往返，并主动捕获三类非法输入。它不会调用 Agent 或外部 API。

## 启动后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

启动后可访问：

- API 文档：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/api/system/health>
- 架构快照：<http://127.0.0.1:8000/api/system/architecture>
- 请求校验：`POST http://127.0.0.1:8000/api/trip/validate`

## 启动前端

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

浏览器访问 <http://127.0.0.1:5173>。页面会调用后端架构接口，展示四层架构、Agent 分工、数据流和配置状态。`src/types/trip.ts` 已定义与后端一致的旅行数据契约，后续页面可以直接复用。

`.env` 只保存在本地，不要提交真实密钥。当前页面不会调用 LLM、高德地图或 Unsplash，也不会生成虚构的旅行计划。`/api/trip/validate` 只负责规范化和校验请求，真正的 `/plan` 接口留给 Agent 协作章节。
