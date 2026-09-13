## 构建赛博小镇

> 阅读资料：[15.1 项目概述与架构设计](https://datawhalechina.github.io/hello-agents/#/./chapter15/%E7%AC%AC%E5%8D%81%E4%BA%94%E7%AB%A0%20%E6%9E%84%E5%BB%BA%E8%B5%9B%E5%8D%9A%E5%B0%8F%E9%95%87?id=_151-%e9%a1%b9%e7%9b%ae%e6%a6%82%e8%bf%b0%e4%b8%8e%e6%9e%b6%e6%9e%84%e8%ae%be%e8%ae%a1)
>
> 15.1 先确定产品目标、四层架构和一次交互的数据流。本节代码只落地工程基线，不提前实现后续的 NPC Agent、记忆和好感度算法。

### 为什么要把 Agent 放进游戏

传统 NPC 通常依靠固定台词和对话树：输入范围有限，但剧情节奏、内容和状态变化都可预测。LLM NPC 则允许玩家直接使用自然语言，回复可以结合角色设定、历史互动和关系状态，不必为每种说法预写分支。

| 维度 | 对话树 NPC | LLM NPC |
| --- | --- | --- |
| 输入 | 预设选项或有限关键词 | 开放式自然语言 |
| 输出 | 编剧写好的固定分支 | 根据上下文动态生成 |
| 连贯性 | 依赖脚本变量 | 依赖 Prompt、短期记忆和长期记忆 |
| 可控性 | 高，容易测试 | 存在随机性，需要校验和内容治理 |
| 运行成本 | 主要是本地逻辑 | 增加模型费用、网络和推理延迟 |

这里的“有生命力”是一种交互体验，不等于 NPC 真的具有意识。工程上的关键变化是：以前由编剧穷举台词，现在由系统准备角色、记忆和关系上下文，再让模型生成一段候选回复。

这个方案也不适合把所有游戏规则交给模型。位置、碰撞、物品、任务完成条件等确定性状态仍应由游戏和后端代码维护；模型适合处理开放式语言，不能因为一句自然语言回复就直接修改权威游戏状态。

### 赛博小镇的五项能力

| 能力 | 用户看到什么 | 系统需要什么 |
| --- | --- | --- |
| 智能 NPC 对话 | 可以自由输入，不局限于选项 | 独立角色 Prompt、LLM 调用、响应校验 |
| 记忆系统 | NPC 记得过去的交流 | 工作记忆、长期记忆、相关性检索 |
| 好感度系统 | NPC 态度随互动变化 | 玩家—NPC 关系状态、更新规则、等级映射 |
| 游戏化交互 | 在 2D 办公室移动并与 NPC 交谈 | Godot 场景、碰撞区域、输入和对话 UI |
| 实时日志 | 可以回看对话和状态变化 | 结构化日志、时间戳、错误与调用信息 |

这五项能力不是并列堆在一起。游戏交互产生对话请求，Agent 使用记忆生成回复，好感度根据互动更新，日志再记录整条链路。

### 四层技术架构

原文采用“游戏引擎 + 后端服务”分离方案：

~~~mermaid
flowchart TB
    subgraph G["游戏前端 · Godot 4.5"]
        SCENE["2D 场景与渲染"]
        PLAYER["玩家移动与碰撞"]
        NPC_VIEW["NPC 展示与交互区域"]
        DIALOGUE["对话 UI 与 API Client"]
    end

    subgraph B["后端服务 · FastAPI"]
        API["HTTP API"]
        STATE["NPC 与关系状态"]
        COORDINATOR["对话协调与日志"]
    end

    subgraph A["智能体层 · HelloAgents"]
        NPC_AGENT["每个 NPC 一个 SimpleAgent"]
        MEMORY["短期记忆 + 长期记忆"]
        AFFINITY["好感度计算"]
    end

    subgraph E["外部服务层"]
        LLM["LLM API"]
        QDRANT["Qdrant 向量检索"]
        SQLITE["SQLite 持久化"]
    end

    PLAYER --> NPC_VIEW --> DIALOGUE --> API
    API --> COORDINATOR --> NPC_AGENT
    NPC_AGENT --> MEMORY
    NPC_AGENT --> LLM
    COORDINATOR --> AFFINITY --> STATE
    MEMORY --> QDRANT
    STATE --> SQLITE
    COORDINATOR --> API --> DIALOGUE
~~~

| 层次 | 主要职责 | 不应承担的职责 |
| --- | --- | --- |
| Godot 前端 | 帧循环、画面、移动、碰撞、输入、对话展示 | 保存模型密钥、计算权威好感度 |
| FastAPI 后端 | 请求校验、NPC 定位、流程协调、状态和日志 | 阻塞 Godot 帧循环、决定画面节点如何渲染 |
| HelloAgents | 角色扮演、记忆组织、回复生成、好感度分析 | 直接移动玩家或修改场景树 |
| 外部服务 | 模型推理、向量检索、结构化持久化 | 决定游戏交互顺序 |

分层首先解决的是延迟隔离。Godot 发起异步 HTTP 请求后仍能继续渲染；模型调用慢或失败，只影响当前对话，不应拖住游戏主循环。其次是安全边界：API Key 留在后端，Godot 客户端只知道服务地址。

### 一次 NPC 对话如何流转

~~~mermaid
sequenceDiagram
    actor P as 玩家
    participant G as Godot
    participant F as FastAPI
    participant A as NPC SimpleAgent
    participant M as 记忆系统
    participant L as LLM
    participant S as 状态与日志

    P->>G: 靠近 NPC，按 E 并输入消息
    G->>F: POST /chat
    F->>F: 校验玩家、NPC 和消息
    F->>A: 角色设定 + 玩家消息
    A->>M: 检索相关历史互动
    M-->>A: 短期与长期记忆
    A->>L: 生成角色化回复
    L-->>A: 候选回复
    A-->>F: NPC 回复与互动信息
    F->>S: 更新状态、好感度并记录日志
    F-->>G: 返回结构化响应
    G-->>P: 展示 NPC 回复
~~~

这条链路中至少有三类状态：

- 场景状态：玩家和 NPC 的位置、交互范围、对话框是否打开；
- 对话状态：当前 NPC、消息、回复和请求是否进行中；
- 持久状态：记忆、好感度、NPC 状态和日志。

场景状态适合留在 Godot，持久状态由后端维护，对话请求则是两者之间的边界。如果同一份好感度同时由 Godot 和后端独立修改，很快就会出现状态冲突。

### 工程结构

实践代码放在 `code/HelloAgents/helloagents-ai-town/`，沿用原文的 Godot 与 Python 双工程结构：

~~~text
helloagents-ai-town/
├── backend/
│   ├── architecture.py
│   ├── config.py
│   ├── main.py
│   ├── models.py
│   ├── .env.example
│   ├── architecture_demo.py
│   └── pyproject.toml
├── helloagents-ai-town/
│   ├── assets/
│   │   ├── characters/
│   │   ├── interiors/
│   │   ├── ui/
│   │   └── audio/
│   ├── scenes/
│   │   ├── main.tscn
│   │   ├── player.tscn
│   │   ├── npc.tscn
│   │   └── dialogue_ui.tscn
│   ├── scripts/
│   │   ├── main.gd
│   │   ├── player.gd
│   │   ├── npc.gd
│   │   ├── dialogue_ui.gd
│   │   ├── api_client.gd
│   │   └── config.gd
│   └── project.godot
├── project_demo.py
└── README.md
~~~

目录边界与原文一致，但代码不会为了“看起来完整”提前塞入假的 Agent 回复。15.1 能确定的部分全部实现；依赖后续章节的组件通过状态字段和 `501 Not Implemented` 显式标记。

### 代码实践

#### 用架构契约区分已实现和待实现

[architecture.py](./code/HelloAgents/helloagents-ai-town/backend/architecture.py) 定义四层、六个组件和八个数据流步骤，每个组件与步骤都有 `implemented` 或 `deferred` 状态。这样架构图描述的是最终目标，API 返回的契约则能说明当前代码真正走到了哪里。

~~~python
DataFlowStep(
    order=1,
    actor="Player",
    action="靠近 NPC 并按 E",
    status="implemented",
)
DataFlowStep(
    order=4,
    actor="SimpleAgent",
    action="接收角色设定和玩家消息",
    status="deferred",
)
~~~

三个 NPC 的基础目录也在这一层固定：张三是 Python 工程师，李四是产品经理，王五是 UI 设计师。这里只保存身份、工作区域和是否可交互，不包含后续 Prompt、记忆或关系数据。

#### FastAPI 先提供稳定入口

[main.py](./code/HelloAgents/helloagents-ai-town/backend/main.py) 提供五个入口：

| 接口 | 15.1 行为 |
| --- | --- |
| `GET /` | 返回项目名、范围和文档入口 |
| `GET /healthz` | 返回配置存在性，`conversation_ready=false` |
| `GET /architecture` | 返回四层架构和数据流 |
| `GET /npcs` | 返回三个 NPC 的基础资料 |
| `POST /chat` | 校验请求后返回 `501`，等待 15.2 接入 Agent |

`/chat` 已经使用 [models.py](./code/HelloAgents/helloagents-ai-town/backend/models.py) 校验 `npc_name`、`player_id` 和非空消息，但不会返回静态台词。真实对话加入后可以保留前端调用方式，只替换服务实现。

[config.py](./code/HelloAgents/helloagents-ai-town/backend/config.py) 从后端目录的 `.env` 读取配置，导入模块时不连接外部服务。健康检查中的 `llm`、`qdrant` 和 `sqlite` 只表示配置是否存在，不代表服务可用。

#### Godot 骨架可以独立交互

[main.tscn](./code/HelloAgents/helloagents-ai-town/helloagents-ai-town/scenes/main.tscn) 组合玩家、三个 NPC、HUD 和对话界面。当前使用几何图形代替像素素材，后续替换资源时不需要修改场景职责。

- [player.gd](./code/HelloAgents/helloagents-ai-town/helloagents-ai-town/scripts/player.gd) 处理 WASD 移动和场景边界；
- [npc.gd](./code/HelloAgents/helloagents-ai-town/helloagents-ai-town/scripts/npc.gd) 通过 `Area2D` 判断玩家是否进入范围，按 E 后发出 NPC 身份信号；
- [dialogue_ui.gd](./code/HelloAgents/helloagents-ai-town/helloagents-ai-town/scripts/dialogue_ui.gd) 管理打开、关闭、提交和响应状态；
- [api_client.gd](./code/HelloAgents/helloagents-ai-town/helloagents-ai-town/scripts/api_client.gd) 使用 `HTTPRequest` 异步检查 `/healthz`，并预留 `POST /chat`；
- [main.gd](./code/HelloAgents/helloagents-ai-town/helloagents-ai-town/scripts/main.gd) 连接上述信号，不把网络请求写进玩家或 NPC 脚本。

后端在线但对话未实现时，HUD 会显示“后端已连接，NPC 对话将在 15.2 接入”，发送按钮保持禁用。这个状态比展示一段假的模型回复更准确。

### 运行方式

后端要求 Python 3.10+：

~~~bash
cd code/HelloAgents/helloagents-ai-town/backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
python main.py
~~~

启动后访问 `http://127.0.0.1:8000/docs` 查看接口。15.1 的架构验证不需要填写模型密钥，也不会访问 Qdrant 或 SQLite。

游戏端使用 Godot 4.2 或更高版本导入：

~~~text
code/HelloAgents/helloagents-ai-town/helloagents-ai-town/project.godot
~~~

运行主场景后用 WASD 移动，靠近 NPC 按 E，按 Esc 关闭对话框。API 地址默认是 `http://127.0.0.1:8000`，也可以通过 `CYBER_TOWN_API_URL` 修改。

### 实践结果

后端验证实际请求了架构、健康检查和 NPC 目录，并确认尚未实现的对话接口返回 501：

~~~text
=== 15.1 赛博小镇架构基线验证 ===
architecture_layers: 4
data_flow_steps: 8
npc_catalog: 3
fastapi_contract: ready
chat_endpoint: deferred_501
external_api_calls: 0
~~~

Godot 静态验证检查了主场景、四个场景、六个脚本、资源引用、WASD/E 键和两个 API 路径：

~~~text
=== 15.1 Godot 工程骨架验证 ===
required_files: 11
resource_references: 8
main_scene_contract: ready
movement_and_interaction_contract: ready
api_client_contract: ready
godot_runtime: not_executed
external_api_calls: 0
~~~

本机没有安装 Godot，因此第二组结果不能证明 GDScript 已被引擎成功导入，也不代表游戏已经完成真实 NPC 对话。后续可在 Godot 中执行无窗口导入或直接运行主场景补足这一项验证。

### 实践边界

- 当前完成 15.1 的双工程骨架、四层契约、基础接口、玩家移动、NPC 交互区域和对话面板；
- `POST /chat` 只有数据模型和接口位置，尚未创建 `SimpleAgent`；
- 记忆、好感度、NPC 自主状态、日志和数据库均未提前实现；
- LLM 输出将来只能提供对话与分析结果，位置、碰撞和权威关系状态仍需代码校验；
- `.env.example` 不含真实密钥，验证过程没有调用模型或外部服务；
- Godot 代码已做资源和接口静态检查，仍需安装 Godot 后进行引擎级验证。

### 参考资料

- [《Hello-Agents》第十五章：构建赛博小镇](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter15/%E7%AC%AC%E5%8D%81%E4%BA%94%E7%AB%A0%20%E6%9E%84%E5%BB%BA%E8%B5%9B%E5%8D%9A%E5%B0%8F%E9%95%87.md)
- [官方赛博小镇项目](https://github.com/datawhalechina/hello-agents/tree/main/code/chapter15/Helloagents-AI-Town)
- [Godot 4 官方文档](https://docs.godotengine.org/zh-cn/4.x/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Qdrant 官方文档](https://qdrant.tech/documentation/)
- [SQLite 官方文档](https://www.sqlite.org/docs.html)

### 小结

赛博小镇不是让 LLM 接管整个游戏，而是把开放式对话接入一套确定性的游戏系统。Godot 负责画面、输入和碰撞，FastAPI 负责请求、状态和日志，HelloAgents 负责 NPC 角色、记忆与回复，LLM、Qdrant 和 SQLite 提供外部能力。15.1 的重点是先固定这些边界以及一次对话的八步链路；当前实践已经建立可启动的 Godot 场景骨架和可验证的 FastAPI 契约，真实 NPC 行为留待后续章节逐步接入。
