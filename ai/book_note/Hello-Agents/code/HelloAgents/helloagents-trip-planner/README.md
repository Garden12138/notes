# HelloAgents 智能旅行助手

这是第十三章持续实践目录。当前完成 13.1 的工程初始化：前后端可以连通，后端提供四层架构、四个 Agent 职责和外部服务配置状态；旅行数据模型、真实 Agent、MCP 调用、地图和导出将在后续小节中继续补充。

## 目录

```text
helloagents-trip-planner/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── api/
│   │   ├── models/
│   │   ├── services/
│   │   └── config.py
│   ├── architecture_demo.py
│   ├── requirements.txt
│   └── run.py
└── frontend/
    ├── src/
    │   ├── router/
    │   ├── services/
    │   ├── types/
    │   └── views/
    └── package.json
```

## 离线架构验证

```bash
cd backend
python architecture_demo.py
```

该命令不需要依赖、密钥或网络。

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

## 启动前端

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

浏览器访问 <http://127.0.0.1:5173>。页面会调用后端架构接口，展示四层架构、Agent 分工、数据流和配置状态。

`.env` 只保存在本地，不要提交真实密钥。当前页面不会调用 LLM、高德地图或 Unsplash，也不会生成虚构的旅行计划。

