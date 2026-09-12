## 智能旅行助手

> 阅读资料：[《Hello-Agents》第十三章 13.1：项目概述与架构设计](https://datawhalechina.github.io/hello-agents/#/./chapter13/%E7%AC%AC%E5%8D%81%E4%B8%89%E7%AB%A0%20%E6%99%BA%E8%83%BD%E6%97%85%E8%A1%8C%E5%8A%A9%E6%89%8B?id=_131-%e9%a1%b9%e7%9b%ae%e6%a6%82%e8%bf%b0%e4%b8%8e%e6%9e%b6%e6%9e%84%e8%ae%be%e8%ae%a1)
>
> 本节先确定产品范围、技术分层和模块边界。数据模型、真实 Agent、MCP 服务和完整页面在后续小节中逐步实现。

### 从原型走向完整应用

第一章的旅行助手主要用来理解 Thought—Action—Observation 循环，第十三章则要求把前面学过的框架接口、工具、记忆、MCP 和评估方法组合成一个 Web 应用。变化不只是代码增多，而是需要处理三个工程问题：

- 信息来自地图、天气、图片和 LLM 等不同服务，格式与可用性并不一致；
- 行程必须结合日期、偏好、预算和住宿要求，通用攻略无法直接复用；
- 删除景点或调整顺序后，路线、时间和预算都可能跟着变化。

旅行助手的价值在于把“跨网站查资料—筛选—安排—计算—反复调整”收敛为一个可编辑的计划，而不是让模型一次性写一篇看似完整的攻略。

### 功能范围

原文定义了五项核心能力：

| 功能 | 输入或操作 | 预期结果 |
| --- | --- | --- |
| 智能行程规划 | 目的地、日期、偏好、预算 | 包含景点、餐饮和酒店的每日安排 |
| 地图可视化 | 景点坐标、游览顺序 | 地图标记与路线 |
| 预算计算 | 门票、住宿、餐饮、交通 | 分类明细与总预算 |
| 行程编辑 | 添加、删除、排序景点 | 重新计算后的行程、地图和预算 |
| 导出 | 已确认的最终计划 | PDF 或图片 |

这些功能存在依赖关系。地图和预算不是独立的装饰模块，而是行程变化后的派生结果；编辑操作完成后，相关结果也需要重新计算。

### 四层技术架构

系统采用前后端分离架构，分为前端、后端、智能体和外部服务四层：

~~~mermaid
flowchart TB
    subgraph F["前端层 · Vue 3 + TypeScript"]
        FORM["旅行需求表单"]
        RESULT["行程 / 预算 / 天气"]
        MAP["地图与路线"]
        EDIT["编辑与导出"]
    end

    subgraph B["后端层 · FastAPI"]
        API["API 路由"]
        VALIDATE["数据验证"]
        SERVICE["业务编排"]
    end

    subgraph A["智能体层 · HelloAgents"]
        ATTRACTION["景点搜索 Agent"]
        WEATHER["天气查询 Agent"]
        HOTEL["酒店推荐 Agent"]
        PLANNER["行程规划 Agent"]
    end

    subgraph E["外部服务层"]
        AMAP["高德地图 API / MCP"]
        UNSPLASH["Unsplash API"]
        LLM["LLM API"]
    end

    FORM --> API --> VALIDATE --> SERVICE
    SERVICE --> ATTRACTION & WEATHER & HOTEL
    ATTRACTION --> AMAP & UNSPLASH
    WEATHER --> AMAP
    HOTEL --> AMAP
    ATTRACTION & WEATHER & HOTEL --> PLANNER
    PLANNER --> LLM
    PLANNER --> SERVICE --> RESULT
    RESULT --> MAP & EDIT
~~~

| 层次 | 负责什么 | 不应该负责什么 |
| --- | --- | --- |
| 前端 | 收集输入、调用 API、渲染和编辑 | 保存后端密钥、直接编排 Agent |
| 后端 | 验证数据、暴露 API、组织业务流程 | 把第三方原始响应直接交给页面 |
| 智能体 | 理解需求、分解任务、使用工具、整合结果 | 绕过后端直接控制页面状态 |
| 外部服务 | 提供地图、天气、图片和模型能力 | 决定完整旅行计划的数据结构 |

分层的重点不是目录好看，而是建立稳定边界。高德地图的字段变化应由服务层适配；更换 Agent Prompt 不应要求修改 Vue 页面；前端也不应知道 MCP 工具的调用细节。

### 四个 Agent 的分工

13.1 只给出总体角色，具体提示词与调用方式留到后续章节：

| Agent | 主要输入 | 主要输出 |
| --- | --- | --- |
| 景点搜索 Agent | 城市、偏好 | 候选景点及位置、费用、图片 |
| 天气查询 Agent | 城市、开始日期、结束日期 | 日期范围内的天气和出行提示 |
| 酒店推荐 Agent | 城市、预算、住宿偏好 | 酒店候选及区域、价格 |
| 行程规划 Agent | 用户需求与前三类结果 | 每日行程、预算和地图点位 |

前三个 Agent 负责收集各自领域的信息，行程规划 Agent 负责整合。这样可以缩小每个角色的 Prompt 和工具范围，也便于判断错误究竟发生在检索、天气、住宿还是最终规划阶段。

### 一次规划请求如何流转

~~~mermaid
sequenceDiagram
    actor U as 用户
    participant V as Vue 前端
    participant F as FastAPI 后端
    participant S as 景点/天气/酒店 Agent
    participant X as MCP 与外部 API
    participant P as 行程规划 Agent

    U->>V: 填写目的地、日期、偏好和预算
    V->>F: POST 旅行规划请求
    F->>F: 校验并规范化数据
    F->>S: 分发检索任务
    S->>X: 查询 POI、天气、酒店和图片
    X-->>S: 返回不同格式的外部数据
    S-->>F: 返回结构化候选结果
    F->>P: 提交需求与候选结果
    P-->>F: 返回完整旅行计划
    F-->>V: 返回统一 JSON
    V-->>U: 展示行程、预算、地图和天气
~~~

前端请求和后端响应需要稳定的数据协议，外部响应则要先转换后再进入规划环节。原文把这部分放在 13.2 的数据模型设计中，因此本节代码不提前定义一个可能与后文冲突的 `TripPlan`。

### 技术选型与运行条件

| 部分 | 技术 | 选择原因 |
| --- | --- | --- |
| 前端 | Vue 3、TypeScript、Vite | 组件化页面、静态类型和独立构建 |
| 后端 | FastAPI | Pydantic 验证、异步接口和自动 OpenAPI 文档 |
| Agent | HelloAgents | 复用已有 Agent、工具、MCP 和 LLM 抽象 |
| 地图与天气 | 高德地图 | POI、天气和路线数据 |
| 图片 | Unsplash | 目的地与景点图片 |

原文的最低环境是 Python 3.10、Node.js 16 和 npm 8。实际安装时还要以项目锁定的依赖版本为准，尤其不能只看 Node.js 主版本而忽略构建工具要求。

密钥应放在本地 `.env`，后端只向前端暴露“是否已配置”，不能返回密钥内容。高德 Web 服务 Key、浏览器端 JS Key 的权限和暴露范围不同，也不应混用。

### 代码实践

#### 工程结构

本节在 `code/HelloAgents/` 下建立与原文一致的独立项目：

~~~text
helloagents-trip-planner/
├── backend/
│   ├── app/
│   │   ├── agents/registry.py
│   │   ├── api/
│   │   │   ├── main.py
│   │   │   └── routes/system.py
│   │   ├── models/
│   │   ├── services/architecture.py
│   │   └── config.py
│   ├── architecture_demo.py
│   ├── requirements.txt
│   └── run.py
└── frontend/
    ├── src/
    │   ├── router/
    │   ├── services/api.ts
    │   ├── types/architecture.ts
    │   └── views/HomeView.vue
    └── package.json
~~~

- [项目 README](./code/HelloAgents/helloagents-trip-planner/README.md) 记录离线验证与前后端启动方式；
- [registry.py](./code/HelloAgents/helloagents-trip-planner/backend/app/agents/registry.py) 声明四个 Agent 的输入、输出、职责和外部能力；
- [architecture.py](./code/HelloAgents/helloagents-trip-planner/backend/app/services/architecture.py) 生成前后端共用的架构快照；
- [main.py](./code/HelloAgents/helloagents-trip-planner/backend/app/api/main.py) 创建 FastAPI、配置 CORS 并注册路由；
- [HomeView.vue](./code/HelloAgents/helloagents-trip-planner/frontend/src/views/HomeView.vue) 调用后端接口并展示分层、角色、数据流和配置状态。

后端提供三个基础入口：

| 地址 | 作用 |
| --- | --- |
| `GET /` | 服务入口和文档地址 |
| `GET /api/system/health` | 进程状态与外部服务配置状态 |
| `GET /api/system/architecture` | 四层架构、Agent 注册表和数据流 |

`health` 只返回布尔状态：

~~~python
def integration_status(self) -> dict[str, bool]:
    return {
        "llm": bool(self.llm_api_key and self.llm_model_id),
        "amap": bool(self.amap_maps_api_key),
        "unsplash": bool(self.unsplash_access_key),
    }
~~~

这一接口适合页面启动时检查环境，但“密钥存在”不等于服务真实可用。联网探测、超时和降级策略应在接入外部服务时再实现。

#### 离线实践结果

架构 Demo 不依赖 FastAPI、模型或网络：

~~~bash
cd code/HelloAgents/helloagents-trip-planner/backend
python architecture_demo.py
~~~

控制台输出：

~~~text
=== 13.1 智能旅行助手架构实践 ===
layers: 4
agents: 4
  attraction_search: 景点搜索 Agent
  weather_query: 天气查询 Agent
  hotel_recommendation: 酒店推荐 Agent
  trip_planning: 行程规划 Agent
data_flow_steps: 8
frontend_backend_contract: ready
external_api_calls: 0
trip_plan_generation: deferred_to_later_sections
~~~

这次结果验证的是目录、四层结构、角色数量和数据流契约。`external_api_calls: 0` 与 `trip_plan_generation: deferred_to_later_sections` 明确表示没有调用真实服务，也没有把固定文本伪装成旅行计划。

#### 启动前后端

后端：

~~~bash
cd code/HelloAgents/helloagents-trip-planner/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
~~~

API 文档位于 `http://127.0.0.1:8000/docs`。前端另开终端启动：

~~~bash
cd code/HelloAgents/helloagents-trip-planner/frontend
cp .env.example .env
npm install
npm run dev
~~~

访问 `http://127.0.0.1:5173` 后，页面会请求 `/api/system/architecture`。当前页面用于验证前后端分离和接口契约；旅行表单、地图、编辑、预算和导出不会在 13.1 中提前实现。

### 实践边界

- 配置状态只是凭据存在性检查，不会验证额度、权限和网络；
- 四个 Agent 当前是职责注册表，还没有创建 LLM 或 MCP 客户端；
- 规划数据不能继续用随意拼接的字典，需要在 13.2 建立统一模型；
- Agent 调用顺序、失败恢复与结果整合属于 13.3 的协作实现；
- 地图、页面编辑和导出分别留给服务与前端章节。

按章节顺序保留这些边界，可以让当前代码直接成为后续实现的基线，而不是先写一套新方案，再随着阅读反复推倒。

### 参考资料

- [《Hello-Agents》第十三章：智能旅行助手源文件](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter13/%E7%AC%AC%E5%8D%81%E4%B8%89%E7%AB%A0%20%E6%99%BA%E8%83%BD%E6%97%85%E8%A1%8C%E5%8A%A9%E6%89%8B.md)
- [HelloAgents 智能旅行助手参考项目](https://github.com/datawhalechina/hello-agents/tree/main/code/chapter13/helloagents-trip-planner)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Vue 3 官方文档](https://vuejs.org/)
- [高德开放平台](https://lbs.amap.com/)
- [Unsplash Developers](https://unsplash.com/developers)

### 小结

智能旅行助手把分散的信息查询、个性化规划和联动调整放进同一应用。13.1 的重点是先固定前端、后端、智能体和外部服务四层边界，再明确景点、天气、酒店和行程规划四个 Agent 的职责。本节实践完成了可启动的前后端骨架、架构接口和离线验证，但不伪造尚未接入的数据；后续可以在这个目录中按章节逐步补上数据模型、协作流程、MCP 服务和完整页面。
