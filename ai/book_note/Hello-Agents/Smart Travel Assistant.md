## 智能旅行助手

> 阅读资料：[13.1 项目概述与架构设计](https://datawhalechina.github.io/hello-agents/#/./chapter13/%E7%AC%AC%E5%8D%81%E4%B8%89%E7%AB%A0%20%E6%99%BA%E8%83%BD%E6%97%85%E8%A1%8C%E5%8A%A9%E6%89%8B?id=_131-%e9%a1%b9%e7%9b%ae%e6%a6%82%e8%bf%b0%e4%b8%8e%e6%9e%b6%e6%9e%84%e8%ae%be%e8%ae%a1)、[13.2 数据模型设计](https://datawhalechina.github.io/hello-agents/#/./chapter13/%E7%AC%AC%E5%8D%81%E4%B8%89%E7%AB%A0%20%E6%99%BA%E8%83%BD%E6%97%85%E8%A1%8C%E5%8A%A9%E6%89%8B?id=_132-%e6%95%b0%e6%8d%ae%e6%a8%a1%e5%9e%8b%e8%ae%be%e8%ae%a1)、[13.3 多智能体协作设计](https://datawhalechina.github.io/hello-agents/#/./chapter13/%E7%AC%AC%E5%8D%81%E4%B8%89%E7%AB%A0%20%E6%99%BA%E8%83%BD%E6%97%85%E8%A1%8C%E5%8A%A9%E6%89%8B?id=_133-%e5%a4%9a%e6%99%ba%e8%83%bd%e4%bd%93%e5%8d%8f%e4%bd%9c%e8%ae%be%e8%ae%a1)、[13.4 MCP 工具集成详解](https://datawhalechina.github.io/hello-agents/#/./chapter13/%E7%AC%AC%E5%8D%81%E4%B8%89%E7%AB%A0%20%E6%99%BA%E8%83%BD%E6%97%85%E8%A1%8C%E5%8A%A9%E6%89%8B?id=_134-mcp-%e5%b7%a5%e5%85%b7%e9%9b%86%e6%88%90%e8%af%a6%e8%a7%a3)、[13.5 前端开发详解](https://datawhalechina.github.io/hello-agents/#/./chapter13/%E7%AC%AC%E5%8D%81%E4%B8%89%E7%AB%A0%20%E6%99%BA%E8%83%BD%E6%97%85%E8%A1%8C%E5%8A%A9%E6%89%8B?id=_135-%e5%89%8d%e7%ab%af%e5%bc%80%e5%8f%91%e8%af%a6%e8%a7%a3)
>
> 13.1 确定产品边界，13.2 固定数据协议，13.3 实现四个 Agent 的协作流程，13.4 接入高德 MCP 和 Unsplash，13.5 完成需求表单、结果展示、地图与导出。

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

13.1 先确定总体角色，13.3 再实现提示词和调用流程：

| Agent | 主要输入 | 主要输出 |
| --- | --- | --- |
| 景点搜索 Agent | 城市、偏好 | 候选景点及位置、费用、图片 |
| 天气查询 Agent | 城市、开始日期、结束日期 | 日期范围内的天气和出行提示 |
| 酒店推荐 Agent | 城市、住宿偏好 | 酒店候选及区域、价格 |
| 行程规划 Agent | 用户需求与前三类结果 | 每日行程、天气和预算 |

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

前端请求和后端响应需要稳定的数据协议，外部响应则要先转换后再进入规划环节。13.2 用 Pydantic 建立这套协议，使后续 Agent 和服务都围绕同一组对象工作。

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
│   │   ├── agents/
│   │   │   ├── prompts.py
│   │   │   ├── registry.py
│   │   │   └── trip_planner.py
│   │   ├── api/
│   │   │   ├── main.py
│   │   │   └── routes/
│   │   │       ├── system.py
│   │   │       └── trip.py
│   │   ├── models/schemas.py
│   │   ├── services/architecture.py
│   │   ├── services/agent_runtime.py
│   │   ├── services/mcp_integration.py
│   │   ├── services/unsplash.py
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
    │   ├── types/
    │   │   ├── architecture.ts
    │   │   └── trip.ts
    │   └── views/
    │       ├── HomeView.vue
    │       └── ResultView.vue
    └── package.json
~~~

- [项目 README](./code/HelloAgents/helloagents-trip-planner/README.md) 记录离线验证与前后端启动方式；
- [registry.py](./code/HelloAgents/helloagents-trip-planner/backend/app/agents/registry.py) 声明四个 Agent 的输入、输出、职责和外部能力；
- [prompts.py](./code/HelloAgents/helloagents-trip-planner/backend/app/agents/prompts.py) 保存四个角色各自的系统提示词；
- [trip_planner.py](./code/HelloAgents/helloagents-trip-planner/backend/app/agents/trip_planner.py) 实现固定顺序的协作、查询构建和结果校验；
- [architecture.py](./code/HelloAgents/helloagents-trip-planner/backend/app/services/architecture.py) 生成前后端共用的架构快照；
- [schemas.py](./code/HelloAgents/helloagents-trip-planner/backend/app/models/schemas.py) 定义旅行请求、领域对象和 API 响应；
- [main.py](./code/HelloAgents/helloagents-trip-planner/backend/app/api/main.py) 创建 FastAPI、配置 CORS 并注册路由；
- [trip.ts](./code/HelloAgents/helloagents-trip-planner/frontend/src/types/trip.ts) 提供与后端对应的 TypeScript 类型；
- [HomeView.vue](./code/HelloAgents/helloagents-trip-planner/frontend/src/views/HomeView.vue) 收集目的地、日期、出行方式和偏好；
- [ResultView.vue](./code/HelloAgents/helloagents-trip-planner/frontend/src/views/ResultView.vue) 展示行程、预算、天气、地图，并支持图片与 PDF 导出。

13.1 的后端骨架提供三个基础入口：

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
collaboration_workflow: ready
mcp_integration: ready
frontend_trip_workflow: ready
external_api_calls: 0
production_trip_plan_generation: configured_when_credentials_exist
~~~

这次结果验证的是目录、四层结构、角色数量、数据流契约和模块装配状态。`configured_when_credentials_exist` 表示生产入口已经接好，但这条离线命令仍然没有调用模型或外部服务。

#### 启动前后端

后端：

~~~bash
cd code/HelloAgents/helloagents-trip-planner/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
PYTHONPATH=../.. python run.py
~~~

`PYTHONPATH=../..` 让后端复用同一 `code/HelloAgents/` 目录中的本地框架。API 文档位于 `http://127.0.0.1:8000/docs`。前端另开终端启动：

~~~bash
cd code/HelloAgents/helloagents-trip-planner/frontend
cp .env.example .env
npm install
npm run dev
~~~

访问 `http://127.0.0.1:5173` 后，首页把表单转换为 `TripRequest` 请求 `/api/trip/plan`，成功后进入 `/result`。13.5 已实现地图与导出，行程编辑按原文章节留给 13.6。

### 为什么需要统一数据模型

如果各模块直接传递字典，同一个值很容易出现多种写法：经纬度可能是字符串、列表或两个字段，温度可能是 `16`、`"16"` 或 `"16°C"`，日期也可能缺少统一格式。字典本身不会阻止漏字段、拼写错误和类型漂移，问题通常要到页面渲染或预算计算时才暴露。

Pydantic 模型把数据边界前移：输入进入业务逻辑前先完成解析与校验，输出也必须满足约定结构。

~~~mermaid
flowchart LR
    FORM["前端表单 JSON"] --> REQUEST["TripRequest<br/>校验日期与旅行天数"]
    REQUEST --> SERVICE["服务与 Agent"]
    API["地图 / 天气 API"] --> ADAPTER["外部数据转换"]
    ADAPTER --> SERVICE
    SERVICE --> DOMAIN["Location / Attraction / Hotel<br/>DayPlan / WeatherInfo / Budget"]
    DOMAIN --> PLAN["TripPlan"]
    PLAN --> RESPONSE["统一响应模型"]
    RESPONSE --> TS["TypeScript 类型<br/>页面渲染"]
~~~

数据模型不是数据库表，也不负责调用 API。它解决的是各层如何准确表达同一份旅行数据。

### 模型分层

实践代码补齐了原文和官方示例中的 18 个模型，并按用途分成四组：

| 分组 | 模型 | 作用 |
| --- | --- | --- |
| 请求 | `TripRequest`、`POISearchRequest`、`RouteRequest` | 接收旅行需求、POI 检索和路线规划参数 |
| 基础对象 | `Location`、`Attraction`、`Meal`、`Hotel`、`WeatherInfo`、`POIInfo`、`RouteInfo` | 统一外部服务与业务层的数据形状 |
| 聚合对象 | `DayPlan`、`Budget`、`TripPlan` | 从单日安排逐层组成完整行程 |
| 响应 | `TripPlanResponse`、`POISearchResponse`、`RouteResponse`、`WeatherResponse`、`ErrorResponse` | 为 API 提供稳定的成功与失败结构 |

对象之间是组合关系：

~~~mermaid
flowchart BT
    LOCATION["Location"] --> ATTRACTION["Attraction"]
    LOCATION --> MEAL["Meal"]
    LOCATION --> HOTEL["Hotel"]
    LOCATION --> POI["POIInfo"]
    ATTRACTION & MEAL & HOTEL --> DAY["DayPlan"]
    DAY --> PLAN["TripPlan"]
    WEATHER["WeatherInfo"] --> PLAN
    BUDGET["Budget"] --> PLAN
    PLAN --> PLAN_RESPONSE["TripPlanResponse"]
    POI --> POI_RESPONSE["POISearchResponse"]
    ROUTE["RouteInfo"] --> ROUTE_RESPONSE["RouteResponse"]
~~~

这种自底向上的结构让 `TripPlan` 不必重复描述景点、酒店和坐标字段，也方便前端按日渲染。

### 请求模型与业务一致性

原文片段把旅行请求称为 `TripPlanRequest`，官方项目最终使用 `TripRequest`，本地实现跟随后者，避免同一概念出现两个名称。字段包括城市、起止日期、旅行天数、交通、住宿、偏好和自由文本。

类型约束只能保证 `travel_days` 是 1 到 30 的整数，还不能保证它与日期相符，因此增加模型级校验：

~~~python
@model_validator(mode="after")
def validate_date_range(self) -> "TripRequest":
    start = date.fromisoformat(self.start_date)
    end = date.fromisoformat(self.end_date)
    if end < start:
        raise ValueError("end_date 不能早于 start_date")
    expected_days = (end - start).days + 1
    if self.travel_days != expected_days:
        raise ValueError(f"travel_days 应为 {expected_days}")
    return self
~~~

旅行天数按首尾日期都计入，例如 9 月 20 日到 9 月 21 日是两天。偏好列表在校验后去除空字符串和重复项，防止后续 Prompt 重复强调同一偏好。

### 基础模型的规范化

`Location` 是景点、餐饮、酒店和 POI 的共同依赖。模型对经度使用 `[-180, 180]`、纬度使用 `[-90, 90]` 的范围约束，并把高德常见的 `"经度,纬度"` 字符串以及 `lng`、`lon`、`lat` 别名统一成两个浮点数字段：

~~~python
Location.model_validate("116.397128,39.916527")
Location.model_validate({"lng": 116.397128, "lat": 39.916527})
~~~

`WeatherInfo` 保留原文的温度转换逻辑：去掉 `°C`、`℃` 等单位后转为整数，转换失败时回退为 `0`。这个策略适合作为演示中的容错，但 `0°C` 本身也是合法温度，正式接入时应同时记录解析告警，否则无法区分真实零度与脏数据。

可选列表字段都使用 `Field(default_factory=list)`，完整行程的 `days` 则保持必填且至少包含一天。这比直接写 `[]` 更清楚，也延续了普通 Python 数据类处理可变默认值的安全习惯。公共基类还启用了 `extra="forbid"`，字段拼错时直接报错，而不是悄悄丢弃输入。

### 行程、预算与响应

`DayPlan` 聚合当天的酒店、景点和餐饮，`TripPlan` 再组合日期范围内的每日安排、天气、预算和总体建议。除了嵌套类型，本地实现还检查：

- `days` 必须覆盖完整旅行日期，每日日期不能越界或重复；
- `day_index` 从 `0` 开始，并与日期相对开始日的偏移一致；
- 天气日期不能越界或重复；
- `Budget.total` 为零时按四个分项自动汇总，显式给出的非零总额必须与分项一致；
- `TripPlanResponse.success=True` 时必须包含 `data`。

这些规则属于数据本身的一致性，不依赖 LLM，也不应该交给 Prompt 反复提醒。

### 前后端共用契约

后端模型位于 [schemas.py](./code/HelloAgents/helloagents-trip-planner/backend/app/models/schemas.py)，前端对应类型位于 [trip.ts](./code/HelloAgents/helloagents-trip-planner/frontend/src/types/trip.ts)。两边保持相同字段名和嵌套关系，避免页面使用 `camelCase`、后端返回 `snake_case` 时再维护一层隐式映射。

[trip.py](./code/HelloAgents/helloagents-trip-planner/backend/app/api/routes/trip.py) 在 13.2 先提供请求校验入口：

~~~python
@router.post("/validate", response_model=TripRequest)
def validate_trip_request(request: TripRequest) -> TripRequest:
    return request
~~~

请求经过 FastAPI 后会自动转换为 `TripRequest`，校验成功就返回规范化结果。校验失败时，FastAPI 默认返回 `422 Unprocessable Entity`，并不是原文示例描述的 `400`。13.3 再为 `/plan` 接入协作接口。

### 数据模型实践结果

[model_demo.py](./code/HelloAgents/helloagents-trip-planner/backend/model_demo.py) 不依赖网络，用固定数据构造请求、两天行程、天气和预算，再完成 JSON 序列化与反序列化：

~~~bash
cd code/HelloAgents/helloagents-trip-planner/backend
python3 model_demo.py
~~~

实际输出：

~~~text
=== 13.2 旅行助手数据模型实践 ===
schema_models: 18
travel_days: 2
preferences: 历史文化, 美食
location: 116.397128,39.916527
weather_temperature: 16
budget_total: 960
trip_days: 2
json_round_trip: True
validation_failures_caught: 3
external_api_calls: 0
~~~

三次失败分别来自越界经度、日期范围与旅行天数不一致、预算总额与分项不一致。`json_round_trip: True` 表示序列化后重新解析得到的 `TripPlan` 与原对象一致；它验证了数据契约，不代表 Agent 已生成过真实行程。

### 为什么拆成多个 Agent

一个 Agent 也能完成景点、天气、酒店和行程规划，但它需要同时理解多套工具参数、输出格式和业务规则。提示词会越来越长，某一步出错时也难以判断问题来自检索、工具调用还是最终整合。

原文还以“`SimpleAgent.run()` 一次只能执行一个工具”为拆分理由。当前仓库里的 `SimpleAgent` 已支持有限次数的“模型—工具—模型”循环，因此这不再是硬限制。多 Agent 仍有价值，主要体现在职责隔离：

- 景点、天气和酒店 Agent 只接触各自需要的输入与工具；
- 规划 Agent 不调用外部工具，只整合已有结果；
- 每一步都能单独记录、替换和测试；
- 某个搜索策略变化时，不必修改完整规划提示词。

这套设计并不是让四个 Agent 自由讨论，而是由一个协调器按固定流程调度。

### 角色边界

| Agent | 输入 | 工具 | 输出 |
| --- | --- | --- | --- |
| `AttractionSearchAgent` | 城市、偏好 | `amap_maps_text_search` | 景点候选文本 |
| `WeatherQueryAgent` | 城市、日期范围 | `amap_maps_weather` | 天气预报文本 |
| `HotelAgent` | 城市、住宿偏好 | `amap_maps_text_search` | 酒店候选文本 |
| `PlannerAgent` | 原始请求与前三项结果 | 无 | `TripPlan` JSON |

前三个角色负责获取事实，最后一个角色负责组合事实。规划 Agent 不再查询数据，可以避免它一边补资料、一边安排路线时混淆信息来源。

### 固定协作流程

`MultiAgentTripPlanner` 是协调器，整个过程分为五步：搜索景点、查询天气、推荐酒店、生成计划、解析并校验结果。

~~~mermaid
sequenceDiagram
    participant O as MultiAgentTripPlanner
    participant A as 景点搜索 Agent
    participant W as 天气查询 Agent
    participant H as 酒店推荐 Agent
    participant P as 行程规划 Agent
    participant M as TripPlan 模型

    O->>A: 城市 + 第一个偏好
    A-->>O: 景点检索结果
    O->>W: 城市 + 起止日期
    W-->>O: 天气检索结果
    O->>H: 城市 + 住宿偏好
    H-->>O: 酒店检索结果
    O->>P: 原始请求 + 三份结果
    P-->>O: TripPlan JSON
    O->>M: 解析并验证
    M-->>O: 结构化旅行计划
~~~

核心代码保持原文的顺序编排：

~~~python
def plan_trip(self, request: TripRequest) -> TripPlan:
    attraction_response = self._run_agent(
        step="attraction_search",
        agent=self.attraction_agent,
        query=self._build_attraction_query(request),
    )
    weather_response = self._run_agent(...)
    hotel_response = self._run_agent(...)
    planner_response = self._run_agent(
        step="trip_planning",
        agent=self.planner_agent,
        query=self._build_planner_query(
            request,
            attraction_response,
            weather_response,
            hotel_response,
        ),
    )
    return self._parse_trip_plan(planner_response, request)
~~~

前三项查询目前仍按原文串行执行，没有擅自改成并行。它们在数据上彼此独立，后续确实可以并发优化，但要同时处理超时、部分失败和共享工具的并发安全。

### 消息如何投递和消费

这里没有消息队列，Agent 之间也不直接发送消息。协调器持有四个 Agent，并通过 `run(query)` 完成一次同步投递：

1. 协调器构造景点查询，景点 Agent 消费该字符串并返回文本；
2. 天气和酒店阶段采用相同方式，各自结果先回到协调器；
3. `_build_planner_query()` 把 `TripRequest` 和三份结果组装成一个新查询；
4. 规划 Agent 消费这个聚合查询，返回 JSON 文本；
5. 协调器解析 JSON，并交给 `TripPlan` 校验。

因此，真正负责上下文传递的是 `MultiAgentTripPlanner`。`AgentStepTrace` 会保存每一步的 Agent 名称、查询和响应，便于确认某份数据是否真的传到了下一阶段。每次规划开始前还会清理 Agent 历史，避免不同 Web 请求串入彼此的对话内容。

聚合查询使用显式区块区分数据来源：

~~~text
<user_request>...</user_request>
<attraction_results>...</attraction_results>
<weather_results>...</weather_results>
<hotel_results>...</hotel_results>
~~~

提示词同时要求把检索结果当作数据，而不是新的系统指令。这不能彻底解决提示词注入，但比直接拼接几段无边界文本更容易识别和处理。

### 查询字段与现有模型对齐

原文的查询构建示例使用了 `request.days` 和 `request.budget`，但 13.2 的实际请求模型只有 `travel_days`，也没有单独的预算字段。实践代码按现有 `TripRequest` 修正：

- 天数读取 `request.travel_days`；
- 不虚构 `request.budget`；
- 如果用户在 `free_text_input` 中填写预算要求，它会随完整请求一起交给规划 Agent；
- 若后续需要结构化预算上限，应先扩展 `TripRequest`，再同步前端类型和规划逻辑。

这种处理没有改变原文流程，只是让示意代码与上一节已经确定的数据协议一致。

### 提示词与工具边界

[prompts.py](./code/HelloAgents/helloagents-trip-planner/backend/app/agents/prompts.py) 分别保存四个系统提示词。景点、天气和酒店提示词都要求调用工具、不得自行编造；规划提示词则明确禁用工具，只允许使用输入中的事实。

`build_simple_agent_team()` 负责创建四个 `SimpleAgent`。前三个 Agent 复用同一个高德 MCP 工具，规划 Agent 不注册工具：

~~~python
for agent in (attraction_agent, weather_agent, hotel_agent):
    agent.add_tool(amap_tool)

planner_agent = SimpleAgent(
    name="行程规划专家",
    llm=llm,
    system_prompt=PLANNER_AGENT_PROMPT,
    enable_tool_calling=False,
)
~~~

这里接收已经创建好的 `llm` 和 `amap_tool`，不在 13.3 内部启动 MCP Server。这样既保留了原文“共享一个 MCP 工具”的结构，也把 MCP 创建、发现和连接细节留给 13.4。

### JSON 解析与结果验收

模型回复可能是纯 JSON，也可能被包在 `json` 代码围栏里。解析器兼容这两种形式，但解析成功不等于计划可用，结果还要经过三层检查：

1. `TripPlan` 验证字段、类型、日期、预算分项和嵌套对象；
2. 城市、开始日期、结束日期必须与原始请求一致；
3. 每天必须有 2 至 3 个景点、早中晚三餐和酒店，天气覆盖全部日期，预算不能为空。

任何阶段返回空文本、抛出异常或产生无效 JSON，都会统一转换为 `TripPlanningError`。官方完整项目带有一个固定景点名称和坐标的备用计划，但这与角色提示词中的“不得编造信息”相冲突，因此本地实现选择明确失败，让 API 返回错误，而不是把占位内容冒充真实行程。

### 协作接口

[trip_planner.py](./code/HelloAgents/helloagents-trip-planner/backend/app/agents/trip_planner.py) 实现协作流程，[trip.py](./code/HelloAgents/helloagents-trip-planner/backend/app/api/routes/trip.py) 增加 `POST /api/trip/plan`，前端 [trip.ts](./code/HelloAgents/helloagents-trip-planner/frontend/src/services/trip.ts) 提供对应调用函数。接口通过 FastAPI 依赖注入获取协调器，便于测试和后续装配。

13.4 完成后，默认依赖会装配 LLM 和高德 MCP。配置缺失、MCP Server 无法启动或必要工具未发现时返回 `503 Service Unavailable`；Agent 输出无效时返回 `502 Bad Gateway`。这两个状态分别表示“运行时不可用”和“上游结果不可用”，不会返回虚构的成功响应。

### 多智能体协作实践结果

[collaboration_demo.py](./code/HelloAgents/helloagents-trip-planner/backend/collaboration_demo.py) 使用四个确定性测试 Agent，验证调用顺序、上下文传递、JSON 解析和无效结果拒绝逻辑：

~~~bash
cd code/HelloAgents/helloagents-trip-planner/backend
python3 collaboration_demo.py
~~~

实际输出：

~~~text
=== 13.3 多智能体协作实践 ===
workflow_steps: attraction_search -> weather_query -> hotel_recommendation -> trip_planning -> response_parsing
agent_calls: 4
attraction_context_forwarded: True
weather_context_forwarded: True
hotel_context_forwarded: True
shared_tool_reused: True
planner_without_tools: True
trip_city: 北京
trip_days: 2
budget_total: 960
invalid_plan_rejected: True
external_api_calls: 0
~~~

三个 `context_forwarded` 均为 `True`，说明前三个 Agent 的返回值确实进入了规划 Agent 的输入。`shared_tool_reused` 与 `planner_without_tools` 验证了工具边界，`invalid_plan_rejected` 验证了无效输出会失败；示例地点和金额只用于离线测试，不代表真实旅行推荐。

### 为什么在旅行助手中引入 MCP

直接调用高德 HTTP API 并非不能实现，但每增加一种能力，都要重新处理请求参数、认证、响应格式、错误码和工具注册。MCP 在 Agent 与外部服务之间增加一层统一协议：Server 负责封装高德 API，Client 负责连接，`MCPTool` 再把 Server 暴露的能力转换成 HelloAgents 能注册的工具。

| 对比项 | 直接调用 HTTP API | 通过 MCP 调用 |
| --- | --- | --- |
| 接口适配 | 每个 API 单独编写 | Server 统一暴露工具描述和参数 Schema |
| 工具发现 | 代码中手工注册 | Client 通过 `list_tools` 动态发现 |
| Agent 侧调用 | 了解具体 URL 与响应 | 只面对工具名和参数 |
| 适合场景 | 调用时机固定、逻辑简单 | 多工具需要被 Agent 选择和组合 |
| 额外成本 | 较低 | 需要管理 Client、Server 和传输会话 |

MCP 解决的是能力接入和调用协议，不负责判断结果是否真实，也不会自动让工具选择变得可靠。当前旅行助手仍通过 Prompt 约束工具名，并在景点查询中直接给出调用标记；是否调用以及参数是否正确，仍受模型输出和协调器逻辑影响。

### 高德 MCP Server 的装配

[mcp_integration.py](./code/HelloAgents/helloagents-trip-planner/backend/app/services/mcp_integration.py) 创建一个高德 `MCPTool`：

~~~python
tool = MCPTool(
    name="amap",
    description="高德地图 MCP 服务",
    server_command=["uvx", "amap-mcp-server"],
    env={"AMAP_MAPS_API_KEY": amap_key},
    auto_expand=True,
)
expanded_tools = tool.get_expanded_tools()
~~~

原文章节中的 JavaScript 示例使用 `npx`，官方参考项目实际采用 `uvx amap-mcp-server`。当前本地 `MCPTool` 的构造参数也不是示例里的 `command` 和 `args`，而是完整的 `server_command` 列表，因此实践代码沿用参考项目的 Python Server 方案。两种方案选一种即可，启动命令、包名和环境变量不能混着写。

这里的 `AMAP_MAPS_API_KEY` 作为 MCP 子进程环境变量传入，不会进入 Agent Prompt，也不会返回前端。`AmapMCPConfig` 还将密钥字段标记为不参与 `repr`，避免调试输出直接带出凭据。

工具发现完成后，装配器会检查下面两个实际依赖：

- `amap_maps_text_search`：景点搜索和酒店搜索共用；
- `amap_maps_weather`：天气 Agent 使用。

Server 能启动但缺少必要工具，同样属于不可用状态。与其等模型执行到一半才得到“工具不存在”，不如在装配时列出实际发现的工具并返回 `503`。

### `auto_expand` 如何把 MCP 能力交给 Agent

高德 MCP Server 返回的原始工具名是 `maps_text_search`、`maps_weather` 等。`MCPTool(name="amap", auto_expand=True)` 会为它们增加 `amap_` 前缀，并生成独立的 `MCPWrappedTool`：

~~~text
maps_text_search  -> amap_maps_text_search
maps_weather      -> amap_maps_weather
~~~

前缀能减少多个 MCP Server 出现同名工具时的冲突。`SimpleAgent.add_tool(amap_tool)` 交给 `ToolRegistry` 注册时，注册表会展开这些子工具，所以 Prompt 中使用的是展开后的名字，而真正发给 Server 的仍是原始工具名。

一次天气调用的链路如下：

~~~mermaid
sequenceDiagram
    participant L as LLM
    participant A as SimpleAgent
    participant R as ToolRegistry
    participant W as MCPWrappedTool
    participant M as MCPTool / MCPClient
    participant S as 高德 MCP Server
    participant H as 高德 HTTP API

    L-->>A: [TOOL_CALL:amap_maps_weather:city=北京]
    A->>R: 解析工具名与参数
    R->>W: run({city: 北京})
    W->>M: call_tool(maps_weather, arguments)
    M->>S: stdio JSON-RPC 请求
    S->>H: 调用天气接口
    H-->>S: 天气响应
    S-->>M: MCP 调用结果
    M-->>A: Observation 文本
    A->>L: 工具结果 + 回答要求
    L-->>A: 整理后的天气信息
~~~

这条链路有两个名称空间：Agent 看到带 `amap_` 前缀的本地工具名，MCP Server 只接收自己的原始工具名。包装器负责在两者之间转换，业务代码不需要手写 JSON-RPC。

### 三个 Agent 共享同一个 MCP 工具

[agent_runtime.py](./code/HelloAgents/helloagents-trip-planner/backend/app/services/agent_runtime.py) 将 LLM 和高德 MCP 工具作为共享资源缓存，只执行一次工具发现；每个 `/api/trip/plan` 请求再围绕这些资源创建一组新的 Agent：

~~~mermaid
flowchart LR
    CACHE["共享运行时<br/>LLM + Amap MCPTool"]
    REQ1["请求 A"] --> TEAM1["四个请求内 Agent"]
    REQ2["请求 B"] --> TEAM2["四个请求内 Agent"]
    CACHE --> TEAM1
    CACHE --> TEAM2
    TEAM1 --> A1["景点 / 天气 / 酒店"]
    TEAM2 --> A2["景点 / 天气 / 酒店"]
    A1 --> TOOL["同一个 MCPTool 门面"]
    A2 --> TOOL
~~~

这种划分保留了原文“景点、天气、酒店 Agent 共享一个 MCP 工具”的结构，同时避免把 Agent 对话历史也做成全局单例。行程规划 Agent 不注册工具，只消费前三个角色返回的资料。

这里共享的是 `MCPTool` 门面和已发现的工具元数据。当前框架的 `MCPClient` 在每次发现或调用时通过异步上下文管理器打开并关闭 stdio 会话，因此不能把“一个共享工具对象”简单理解成“永远只有一个常驻操作系统进程”。真正需要常驻连接时，还要另外设计连接池、并发控制和应用关闭钩子。

### Unsplash 保持直接调用

图片补全没有做成 Agent 工具。[unsplash.py](./code/HelloAgents/helloagents-trip-planner/backend/app/services/unsplash.py) 在 `TripPlan` 已通过校验后，按“景点名 + 城市”搜索第一张图片，并写入 `image_url`：

~~~python
for day in plan.days:
    for attraction in day.attractions:
        if attraction.image_url:
            continue
        image_url = service.get_photo_url(
            f"{attraction.name} {plan.city}"
        )
        if image_url:
            attraction.image_url = image_url
~~~

这一步的触发条件和参数都已经确定，不需要模型选择；直接 HTTP 调用更短，也不会额外消耗 Token。服务会规范化图片 ID、常规图、缩略图、描述和摄影师字段。未配置 `UNSPLASH_ACCESS_KEY`、请求失败或响应结构异常时返回空结果，保留有效行程但不伪造图片 URL。

因此，MCP 并不是所有外部请求的默认答案：高德包含多种可选能力，适合以 MCP 工具集交给 Agent；Unsplash 只是规划后的固定增强步骤，保留普通服务更合适。

### 规划接口的完整执行顺序

13.4 没有重写 13.3 的协调流程，只补上外部依赖和图片后处理：

~~~mermaid
flowchart TD
    REQUEST["POST /api/trip/plan"] --> VALIDATE["TripRequest 校验"]
    VALIDATE --> RUNTIME{"共享运行时已创建?"}
    RUNTIME -- 否 --> DISCOVER["创建 LLM 与 MCPTool<br/>发现并检查必要工具"]
    RUNTIME -- 是 --> TEAM["创建请求内四 Agent"]
    DISCOVER --> TEAM
    TEAM --> WORKFLOW["景点 → 天气 → 酒店 → 规划"]
    WORKFLOW --> CHECK["解析 TripPlan 并验收业务规则"]
    CHECK --> IMAGE["Unsplash 补全景点图片"]
    IMAGE --> RESPONSE["TripPlanResponse"]

    DISCOVER -. 失败 .-> E503["503 运行时不可用"]
    CHECK -. 失败 .-> E502["502 Agent 结果不可用"]
~~~

运行真实规划需要在 `backend/.env` 填写：

~~~dotenv
LLM_API_KEY=""
LLM_MODEL_ID=""
LLM_BASE_URL=""
AMAP_MAPS_API_KEY=""
UNSPLASH_ACCESS_KEY=""
~~~

安装依赖后以 `PYTHONPATH=../.. python run.py` 启动。`fastmcp` 提供 MCP Client 与 stdio 传输，`uv` 提供 `uvx`，`httpx` 用于 Unsplash 请求。真实调用会产生模型费用，并受高德、Unsplash 的网络、权限和额度限制。

### MCP 集成实践结果

[mcp_integration_demo.py](./code/HelloAgents/helloagents-trip-planner/backend/mcp_integration_demo.py) 使用假的 MCP Tool 和 HTTP 响应验证装配逻辑，不启动子进程，也不访问外部网络：

~~~bash
cd code/HelloAgents/helloagents-trip-planner/backend
python3 mcp_integration_demo.py
~~~

实际输出：

~~~text
=== 13.4 MCP 工具集成实践 ===
server_command: uvx amap-mcp-server
api_key_forwarded: True
secret_redacted: True
auto_expand: True
expanded_tools: amap_maps_text_search, amap_maps_weather, amap_maps_geo
required_tools_ready: True
shared_amap_tool: True
planner_without_tools: True
unsplash_query: 故宫 北京
unsplash_image_attached: True
missing_tools_rejected: True
mcp_server_processes_started: 0
external_api_calls: 0
~~~

这次结果覆盖启动参数、环境变量传递、密钥脱敏、工具展开、必要工具检查、共享关系和图片后处理。`amap_maps_geo` 只用于证明 Server 可以提供更多能力，当前三个检索 Agent 实际依赖的仍是文本搜索和天气两个工具。图片地址来自假的 HTTP 响应，只验证字段写入，不是一次真实图片搜索结果。

### 前端的职责与技术栈

13.5 将前面的数据协议和规划接口落到浏览器。前端不参与 Agent 编排，只负责四件事：收集需求、发起请求、呈现结果和处理页面交互。

| 技术 | 在项目中的作用 |
| --- | --- |
| Vue 3 Composition API | 组织表单、派生状态和页面生命周期 |
| TypeScript | 复用后端数据契约，提前暴露字段错误 |
| Vue Router | 分离需求表单和行程结果页 |
| Ant Design Vue | 提供表单、日期、折叠面板和反馈组件 |
| Axios | 统一 API 基址、超时和错误转换 |
| 高德 JS API | 在结果页标记每日景点 |
| html2canvas、jsPDF | 导出长图和分页 PDF |

`App.vue` 提供共用页头和页脚，路由仅保留 `/` 与 `/result` 两个业务页面。结果页、地图加载器和导出库都采用动态导入，避免用户刚进入表单时就下载全部功能。

### 数据契约要以当前后端为准

原文个别片段中出现过 `days`、单个字符串形式的 `preferences` 和 `budget`，但本项目 13.2 已经确定了完整契约。因此页面发送的是 `travel_days`，偏好保持为 `string[]`，后端则返回 `TripPlanResponse` 包装：

~~~typescript
interface TripRequest {
  city: string;
  start_date: string;
  end_date: string;
  travel_days: number;
  transportation: string;
  accommodation: string;
  preferences?: string[];
  free_text_input?: string | null;
}

interface TripPlanResponse {
  success: boolean;
  message: string;
  data: TripPlan | null;
}
~~~

这个调整没有改变文章的前端流程，只是让 13.5 与前面已实现的 Pydantic 模型保持一致。类型集中在 [trip.ts](./code/HelloAgents/helloagents-trip-planner/frontend/src/types/trip.ts)，请求逻辑集中在 [api.ts](./code/HelloAgents/helloagents-trip-planner/frontend/src/services/api.ts) 和 [services/trip.ts](./code/HelloAgents/helloagents-trip-planner/frontend/src/services/trip.ts)。

Agent 规划可能需要较长时间，Axios 超时设为 120 秒。超时、后端 `detail` 错误和 FastAPI 字段校验错误都会转换成用户可读的消息，不直接把 Axios 异常对象显示在页面上。

### 首页表单与请求状态

[HomeView.vue](./code/HelloAgents/helloagents-trip-planner/frontend/src/views/HomeView.vue) 将表单分成目的地与日期、旅行方式、兴趣偏好和补充需求四组。日期区间改变时，页面自动计算包含起止日的 `travel_days`，并限制在 1–30 天；过去日期、早于开始日的结束日不可选。

~~~mermaid
flowchart LR
    INPUT["填写城市、日期与偏好"] --> CHECK["表单校验<br/>计算 travel_days"]
    CHECK --> REQUEST["POST /api/trip/plan"]
    REQUEST --> WAIT["显示等待阶段"]
    WAIT --> RESPONSE{"success 且 data 存在?"}
    RESPONSE -- 否 --> ERROR["保留表单并显示错误"]
    RESPONSE -- 是 --> STORE["写入 sessionStorage"]
    STORE --> RESULT["跳转 /result"]
~~~

等待时的进度条只是前端反馈：它在请求返回前最多走到 90%，成功后才到 100%。这不是后端任务的实时进度，页面中也明确写出了这一点。组件卸载时会清理计时器，避免离开页面后继续更新状态。

### 结果页的状态交接

规划结果保存在 `sessionStorage`，而不是只放在路由 `state` 中。这样用户刷新 `/result` 时仍能看到本次会话的行程，关闭标签页后又不会把临时结果当成长期数据。[trip-storage.ts](./code/HelloAgents/helloagents-trip-planner/frontend/src/services/trip-storage.ts) 在读取时做最基本的结构检查；JSON 破损或字段不完整时会删除缓存，并让结果页显示“先创建行程”的空状态。

[ResultView.vue](./code/HelloAgents/helloagents-trip-planner/frontend/src/views/ResultView.vue) 按数据层次展示：

- 顶部是城市、日期、总天数和整体建议；
- 预算区分别展示景点、酒店、餐饮、交通与总额；
- 地图汇总所有有效坐标，为景点创建标记并自适应视野；
- 每日行程用折叠面板展开，内含景点、住宿和餐饮；
- 天气卡片使用同一个 `WeatherInfo` 模型，不在页面内再解析第三方响应。

地图只在存在坐标且配置 `VITE_AMAP_WEB_KEY` 时初始化，离开页面后调用 `destroy()` 释放实例。浏览器端 JS Key 与后端 MCP 使用的 Web 服务 Key 不是同一种用途，不能把 `AMAP_MAPS_API_KEY` 直接填到前端。前端 Key 会出现在浏览器中，应在高德控制台限制可用域名。

### 图片与 PDF 导出

导出功能对结果容器使用 `html2canvas`，图片模式直接下载 PNG；PDF 模式则根据 A4 页面宽度缩放画布，超过一页时逐页添加同一长图的不同偏移区域。文件名会过滤城市中不适合路径的字符。

这种方式保留了原文的“所见即所得”方案，但有两个实际限制：跨域景点图片如果没有允许 CORS，画布可能无法导出；长页面生成的画布占用内存较高。更复杂的排版可以在后续改为服务端 PDF，但不属于 13.5 的实现范围。

### 前端实践结果

安装依赖后执行：

~~~bash
cd code/HelloAgents/helloagents-trip-planner/frontend
npm run build
npm audit
~~~

实际结果为 TypeScript 检查和 Vite 生产构建通过，`3487 modules transformed`，最后一次构建耗时 9.47 秒。结果页、`html2canvas` 和 `jsPDF` 已拆成独立分块；主分块仍为 860.30 kB（gzip 后 276.23 kB），Vite 会给出超过 500 kB 的提示。这不影响本次构建，但说明 Ant Design Vue 还可继续按页面拆分。

原参考项目使用 jsPDF 3.x，当前安装时 `npm audit` 报告了已知问题，因此实践代码使用 4.2.1。升级后审计结果为 `found 0 vulnerabilities`。

浏览器检查中，首页的响应式表单可正常渲染，直接访问没有缓存数据的 `/result` 会显示空状态和“创建旅行计划”入口。本次没有配置真实模型或高德 Key，因此这些结果不代表真实行程生成、地图加载和跨域图片导出已通过联网验证。

### 实践边界

- 配置状态只是凭据存在性检查，不会验证额度、权限和网络；
- LLM、共享高德 MCP 工具与 Unsplash 服务已经装配，但本节没有使用真实密钥联网验证；
- 景点、天气和酒店结果仍以工具 Observation 文本进入规划 Agent，尚未增加独立的高德响应模型适配层；
- 三个信息检索步骤按原文串行执行，尚未加入并发、重试和部分结果降级；
- `/api/trip/plan` 在配置或必要工具不可用时返回 `503`，不会生成占位计划；
- Unsplash 是非关键增强，失败时保留行程并让 `image_url` 为空；
- 前端已实现表单、结果展示、地图和导出，但未配置真实外部服务进行端到端调用；
- 加载进度是模拟的等待反馈，不是 Agent 执行阶段的服务端推送；
- 地图缺少前端 Key 或行程缺少有效坐标时会降级为文本提示；
- 行程编辑、重新排序与路线联动属于 13.6，本节不提前改变数据模型。

按章节顺序保留这些边界，可以让当前代码直接成为后续实现的基线，而不是先写一套新方案，再随着阅读反复推倒。

### 参考资料

- [《Hello-Agents》第十三章：智能旅行助手源文件](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter13/%E7%AC%AC%E5%8D%81%E4%B8%89%E7%AB%A0%20%E6%99%BA%E8%83%BD%E6%97%85%E8%A1%8C%E5%8A%A9%E6%89%8B.md)
- [HelloAgents 智能旅行助手参考项目](https://github.com/datawhalechina/hello-agents/tree/main/code/chapter13/helloagents-trip-planner)
- [官方 `trip_planner_agent.py`](https://github.com/datawhalechina/hello-agents/blob/main/code/chapter13/helloagents-trip-planner/backend/app/agents/trip_planner_agent.py)
- [官方 `unsplash_service.py`](https://github.com/datawhalechina/hello-agents/blob/main/code/chapter13/helloagents-trip-planner/backend/app/services/unsplash_service.py)
- [官方前端 `Home.vue`](https://github.com/datawhalechina/hello-agents/blob/main/code/chapter13/helloagents-trip-planner/frontend/src/views/Home.vue)
- [官方前端 `Result.vue`](https://github.com/datawhalechina/hello-agents/blob/main/code/chapter13/helloagents-trip-planner/frontend/src/views/Result.vue)
- [jsPDF GHSA-wfv2-pwc8-crg5](https://github.com/advisories/GHSA-wfv2-pwc8-crg5)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP](https://gofastmcp.com/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Pydantic Models](https://docs.pydantic.dev/latest/concepts/models/)
- [FastAPI Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- [Vue 3 官方文档](https://vuejs.org/)
- [高德开放平台](https://lbs.amap.com/)
- [Unsplash Developers](https://unsplash.com/developers)

### 小结

智能旅行助手把分散的信息查询、个性化规划和结果展示放进同一应用。13.1 固定四层架构，13.2 建立 Pydantic 与 TypeScript 协议，13.3 由协调器串联四个 Agent，13.4 通过 `MCPTool` 为检索角色接入高德工具，再用普通 HTTP 服务补全景点图片。13.5 用 Vue 表单生成精确的 `TripRequest`，将结果通过会话缓存交给结果页，并完成行程、预算、天气、地图与导出。现在的主链路已贯通到页面层；真实行程生成和地图效果仍需在配置模型与高德 Key 后验证，行程编辑则保留给后续章节。
