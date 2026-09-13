## 构建赛博小镇

> 阅读资料：
>
> - [15.1 项目概述与架构设计](https://datawhalechina.github.io/hello-agents/#/./chapter15/%E7%AC%AC%E5%8D%81%E4%BA%94%E7%AB%A0%20%E6%9E%84%E5%BB%BA%E8%B5%9B%E5%8D%9A%E5%B0%8F%E9%95%87?id=_151-%e9%a1%b9%e7%9b%ae%e6%a6%82%e8%bf%b0%e4%b8%8e%e6%9e%b6%e6%9e%84%e8%ae%be%e8%ae%a1)
> - [15.2 NPC 智能体系统](https://datawhalechina.github.io/hello-agents/#/./chapter15/%E7%AC%AC%E5%8D%81%E4%BA%94%E7%AB%A0%20%E6%9E%84%E5%BB%BA%E8%B5%9B%E5%8D%9A%E5%B0%8F%E9%95%87?id=_152-npc-%e6%99%ba%e8%83%bd%e4%bd%93%e7%b3%bb%e7%bb%9f)
>
> 15.1 确定 Godot、FastAPI、HelloAgents 与外部服务的边界；15.2 开始实现 NPC 的角色 Prompt、短期/长期记忆，并区分玩家即时对话和批量背景对白。

### 为什么要把 Agent 放进游戏

传统 NPC 依靠固定台词和对话树，输入范围有限，但剧情和状态容易控制。LLM NPC 可以接收开放式自然语言，并根据角色、历史互动和当前场景生成回复，不再需要为每种说法预写分支。

| 维度 | 对话树 NPC | LLM NPC |
| --- | --- | --- |
| 输入 | 预设选项或有限关键词 | 开放式自然语言 |
| 输出 | 固定分支 | 根据上下文动态生成 |
| 连贯性 | 依靠脚本变量 | 依靠 Prompt 与记忆 |
| 可控性 | 高，容易测试 | 存在随机性，需要约束和校验 |
| 运行成本 | 主要是本地逻辑 | 增加模型费用、网络和推理延迟 |

这里的“有生命力”指交互体验，不等于 NPC 具有意识。位置、碰撞、物品、任务条件等确定性规则仍由游戏和后端代码维护；模型只生成开放式内容，不能凭一句回复直接修改权威状态。

### 赛博小镇的能力与依赖

| 能力 | 用户看到什么 | 系统依赖 |
| --- | --- | --- |
| 智能 NPC 对话 | 可以自由输入问题 | 独立 Agent、角色 Prompt、LLM |
| 记忆系统 | NPC 记得过去的交流 | 工作记忆、情景记忆、相关性检索 |
| 好感度系统 | NPC 态度随互动变化 | 玩家—NPC 关系状态和更新规则 |
| 游戏化交互 | 在 2D 办公室移动和交谈 | Godot 场景、碰撞、输入和 UI |
| 实时日志 | 回看对话和状态变化 | 结构化时间、错误和调用日志 |

这些能力存在先后关系：游戏产生对话请求，Agent 检索记忆并生成回复，好感度和状态系统再处理互动结果，最后由日志记录整条链路。15.2 只完成前半段，好感度、NPC 自主状态和日志仍属于后续小节。

### 四层技术架构

~~~mermaid
flowchart TB
    subgraph G["游戏前端 · Godot"]
        PLAYER["玩家移动与碰撞"]
        NPC_VIEW["NPC 展示与交互区域"]
        DIALOGUE["对话 UI 与 API Client"]
    end

    subgraph B["后端服务 · FastAPI"]
        API["HTTP API"]
        COORDINATOR["请求校验与对话协调"]
        STATE["关系、状态与日志"]
    end

    subgraph A["智能体层 · HelloAgents"]
        MANAGER["NPC Agent Manager"]
        AGENTS["三个独立 SimpleAgent"]
        MEMORY["Working + Episodic Memory"]
        BATCH["批量背景对白生成器"]
    end

    subgraph E["外部能力"]
        LLM["LLM API"]
        STORE["SQLite / 可替换向量存储"]
    end

    PLAYER --> NPC_VIEW --> DIALOGUE --> API
    API --> COORDINATOR --> MANAGER --> AGENTS --> LLM
    MANAGER <--> MEMORY --> STORE
    COORDINATOR -.后续章节.-> STATE
    BATCH --> LLM
    BATCH -.定时更新留待后续.-> STATE
    API --> DIALOGUE
~~~

| 层次 | 主要职责 | 不应承担的职责 |
| --- | --- | --- |
| Godot 前端 | 画面、移动、碰撞、输入、对话展示 | 保存模型密钥、计算权威关系状态 |
| FastAPI 后端 | 请求校验、NPC 定位、流程协调、错误转换 | 阻塞游戏帧循环、控制场景节点 |
| HelloAgents | 角色扮演、记忆组织、即时回复、批量对白 | 直接移动玩家或修改场景树 |
| 外部能力 | 模型推理、检索和持久化 | 决定交互顺序与游戏规则 |

Godot 使用异步 HTTP 请求，模型变慢只会影响当前对话，不应卡住渲染循环。API Key 留在后端，客户端只保存服务地址。

### 每个 NPC 都是独立 Agent

赛博小镇不是用一个 Agent 临时切换三套名字，而是为每个 NPC 创建独立的 `SimpleAgent`、系统 Prompt 和记忆管理器。这样角色设定不会混在一起，张三的历史也不会成为李四的上下文。

| NPC | 职业 | 性格 | 擅长的话题 |
| --- | --- | --- | --- |
| 张三 | Python 工程师 | 严谨、直接，重视代码质量 | Python、HelloAgents、算法和代码优化 |
| 李四 | 产品经理 | 外向、善于沟通，习惯从用户出发 | 需求分析、产品规划、用户体验 |
| 王五 | UI 设计师 | 温和、有创意，对视觉敏感 | 界面、交互、色彩和布局 |

角色 Prompt 由稳定信息和行为约束组成：

~~~python
def create_system_prompt(role: NPCRole) -> str:
    return f"""你是 Datawhale 办公室的{role.title}{role.name}。

角色设定：
- 性格：{role.personality}
- 专长：{role.expertise}
- 说话风格：{role.style}
- 当前位置：{role.location}
- 当前活动：{role.activity}

行为准则：
1. 以第一人称保持角色一致。
2. 像办公室同事一样自然交流，通常用 30～50 字回答。
3. 不要编造记忆中不存在的互动。
4. 参考当前消息附带的短期与长期记忆。"""
~~~

身份、性格和规则适合放在 system Prompt；玩家消息、检索结果等动态内容则在每次调用时组装。把历史对话写死在 system Prompt 中，会让它不断膨胀，也难以按玩家隔离。

### 记忆如何参与一次对话

Working Memory 和 Episodic Memory 解决的问题不同：

| 记忆 | 当前实践 | 用途 |
| --- | --- | --- |
| 工作记忆 | 每个 NPC 容量 10 条，TTL 120 分钟 | 保留近期上下文，处理“它”“刚才”等指代 |
| 情景记忆 | 每个 NPC 单独 SQLite 文件，最多 100 条 | 保存完整互动，并按当前消息检索相关历史 |

一次即时对话按下面的顺序执行：

~~~mermaid
sequenceDiagram
    actor P as 玩家
    participant F as FastAPI
    participant M as NPC Agent Manager
    participant W as Working Memory
    participant E as Episodic Memory
    participant A as SimpleAgent
    participant L as LLM

    P->>F: npc_name + player_id + message
    F->>M: 定位 NPC
    M->>W: 取该玩家最近 5 条消息
    W-->>M: 近期上下文
    M->>E: 按当前消息检索 top 3
    E-->>M: 相关历史互动
    M->>A: 记忆上下文 + 当前消息
    A->>L: system Prompt + user content
    L-->>A: 角色化回复
    A-->>M: reply
    M->>W: 写入玩家消息与 NPC 回复
    M->>E: 写入完整互动
    M-->>F: reply
    F-->>P: 结构化响应
~~~

原文中的代码是接口示意，不能直接套到当前持续实现的 HelloAgents：本地 `SimpleAgent` 构造函数没有 `memory_manager` 参数，`run(..., context=...)` 还会把 `context` 继续传给模型 SDK。实践中的 [agents.py](./code/HelloAgents/helloagents-ai-town/backend/agents.py) 因此由 `NPCAgentManager` 显式完成检索和保存，再把上下文整理成文本交给 `SimpleAgent.run()`。

每次调用前会清空 `SimpleAgent` 内部的跨轮历史。跨轮连续性统一由外部记忆负责，并使用 `player_id` 过滤；这样既遵守容量和 TTL，也不会让玩家 A 的原始消息直接进入玩家 B 的请求。

当前长期检索沿用本地 HelloAgents 已实现的 SQLite + TF-IDF 适配器，可以离线运行。它保留了“持久化记录 + 相关性检索”的接口，但检索能力弱于嵌入模型与 Qdrant；生产环境可以替换存储适配器，不需要改 NPC 对话流程。

### 即时对话与批量背景对白

15.2 还区分了两类内容：

| 模式 | 触发 | 输入 | 输出 | 适用场景 |
| --- | --- | --- | --- | --- |
| 即时对话 | 玩家按 E 并发送消息 | 指定 NPC、玩家消息、该玩家记忆 | 一名 NPC 的个性化回复 | 直接交互 |
| 批量生成 | 后台定时任务 | 场景时间和全部 NPC 配置 | 三名 NPC 的背景对白 JSON | 气泡、自言自语、环境状态 |

~~~mermaid
flowchart LR
    SCENE["当前场景"] --> BATCH["一次批量 LLM 调用"]
    ROLES["三名 NPC 配置"] --> BATCH
    BATCH --> JSON["严格 JSON 校验"]
    JSON --> Z["张三背景对白"]
    JSON --> L["李四背景对白"]
    JSON --> W["王五背景对白"]

    PLAYER["玩家消息"] --> ONE["指定 NPC Agent"]
    MEMORY["该 NPC / 该玩家记忆"] --> ONE
    ONE --> REPLY["即时个性化回复"]
~~~

[batch_generator.py](./code/HelloAgents/helloagents-ai-town/backend/batch_generator.py) 将三名 NPC 的角色、位置和活动拼成一个 Prompt，只进行一次 `invoke()`，然后检查返回值：必须是 JSON 对象，必须且只能包含张三、李四、王五三个键，每个值都必须是非空字符串。

这里减少的是请求次数：三次独立背景生成合并为一次。费用不一定严格降到三分之一，因为仍要计算完整 Prompt 和三段输出的 Token。批量内容也不能拿来回答玩家，否则回复无法结合具体问题和个人记忆。

当前只实现可调用的批量生成器，没有提前加入无限循环和状态缓存。每五分钟调度、缓存背景对白并推送到前端，需要依赖后续的 NPC 状态管理。

### 工程实现

代码继续放在 `code/HelloAgents/helloagents-ai-town/`：

~~~text
helloagents-ai-town/
├── backend/
│   ├── agents.py                 # NPC 配置、Prompt、Agent 与记忆编排
│   ├── batch_generator.py        # 一次调用生成三段背景对白
│   ├── architecture.py           # 当前实现范围
│   ├── config.py                 # 环境变量
│   ├── main.py                   # FastAPI 接口
│   ├── models.py                 # 请求与响应模型
│   ├── .env.example
│   ├── architecture_demo.py      # Fake LLM 离线验证
│   └── pyproject.toml
├── helloagents-ai-town/
│   ├── assets/
│   ├── scenes/
│   ├── scripts/
│   └── project.godot
├── project_demo.py               # Godot 契约静态验证
└── README.md
~~~

#### Agent 与记忆管理器

`NPCAgentManager` 在初始化时为每个角色创建一组对象：

~~~python
self.agents[role.name] = SimpleAgent(
    name=f"{role.name}-{role.title}",
    llm=self.llm,
    system_prompt=create_system_prompt(role),
    enable_tool_calling=False,
)
self.memories[role.name] = self._create_memory_manager(role)
~~~

同一 NPC 的请求使用独立锁串行处理，避免两个并发请求同时读取旧记忆、生成回复后再交叉写入。不同 NPC 仍可并行处理。

一轮对话写入三条记录：玩家消息和 NPC 回复各占一条工作记忆，完整问答再作为一条情景记忆。前者适合短期上下文，后者适合长期检索。

#### FastAPI 对话入口

[main.py](./code/HelloAgents/helloagents-ai-town/backend/main.py) 保留 15.1 的接口，并把 `/chat` 从占位状态接到真实管理器：

| 接口 | 当前行为 |
| --- | --- |
| `GET /healthz` | 返回 LLM 配置与 `conversation_ready` |
| `GET /architecture` | 返回当前四层架构和八步数据流 |
| `GET /npcs` | 返回三名 NPC 的角色资料 |
| `POST /chat` | 定位 NPC、检索记忆、调用 Agent、保存互动 |

未配置三项 LLM 参数时返回 `503`；NPC 不存在返回 `404`；模型或记忆处理失败返回 `502`。服务不会用静态台词伪装成成功响应。

返回结构保留 Godot 已使用的 `message`，同时补充 NPC 身份和时间：

~~~json
{
  "npc_name": "张三",
  "npc_title": "Python 工程师",
  "message": "……",
  "success": true,
  "timestamp": "2026-09-13T11:00:00Z"
}
~~~

#### Godot 对话链路

Godot 端继续使用 15.1 的场景和异步 `HTTPRequest`：

- [npc.gd](./code/HelloAgents/helloagents-ai-town/helloagents-ai-town/scripts/npc.gd) 检测玩家进入范围并发出交互信号；
- [dialogue_ui.gd](./code/HelloAgents/helloagents-ai-town/helloagents-ai-town/scripts/dialogue_ui.gd) 根据健康检查启用输入，管理请求中的禁用状态；
- [api_client.gd](./code/HelloAgents/helloagents-ai-town/helloagents-ai-town/scripts/api_client.gd) 发送 `npc_name`、`player_id` 和 `message`，读取响应中的 `message`；
- [main.gd](./code/HelloAgents/helloagents-ai-town/helloagents-ai-town/scripts/main.gd) 连接 NPC、玩家、UI 与 API 信号。

### 运行方式

后端要求 Python 3.10+：

~~~bash
cd code/HelloAgents/helloagents-ai-town/backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
~~~

至少填写：

~~~dotenv
LLM_MODEL_ID=""
LLM_API_KEY=""
LLM_BASE_URL=""
MEMORY_PATH="./memory_data"
~~~

然后启动：

~~~bash
python main.py
~~~

访问 `http://127.0.0.1:8000/docs` 可以直接测试 `/chat`。真实调用会产生模型费用，并在 `MEMORY_PATH` 下创建每个 NPC 的记忆数据库。

游戏端使用 Godot 4.2 或更高版本导入：

~~~text
code/HelloAgents/helloagents-ai-town/helloagents-ai-town/project.godot
~~~

运行主场景后用 WASD 移动，靠近 NPC 按 E，按 Esc 关闭对话框。API 地址默认是 `http://127.0.0.1:8000`，也可以通过 `CYBER_TOWN_API_URL` 修改。

### 实践结果

后端使用 Fake LLM 和临时 SQLite 目录完成了离线验证。测试连续与张三对话两轮，中间询问李四：张三能从自己的工作记忆中找回“命令解析器”，李四的输入上下文没有出现这段记录。同时验证了 Agent 实例、记忆管理器、批量 JSON 和 HTTP 错误码。

~~~text
=== 15.2 NPC 智能体系统离线验证 ===
npc_agents: 3_independent
role_prompts: 3_ready
memory_isolation: npc_and_player_ready
working_memory: capacity_10_ttl_120m
episodic_retrieval: ready
batch_background_dialogues: 3_in_1_call
chat_endpoint: ready
unknown_npc: 404
unconfigured_llm: 503
external_api_calls: 0
~~~

Godot 静态验证检查了场景资源、WASD/E 键，以及前后端约定的请求字段和响应处理：

~~~text
=== 15.1～15.2 Godot 对话契约静态验证 ===
required_files: 11
resource_references: 8
main_scene_contract: ready
movement_and_interaction_contract: ready
chat_request_and_response_contract: ready
godot_runtime: not_executed
external_api_calls: 0
~~~

本机没有安装 Godot，所以第二组结果不能证明 GDScript 已通过引擎解析，也不能替代主场景运行。离线 Fake LLM 只验证控制流、记忆隔离和接口契约，没有证明真实模型的角色表现与回复质量。

### 实践边界

- 已实现三个独立 `SimpleAgent`、角色 Prompt、短期/情景记忆和即时 `/chat`；
- 已实现批量背景对白生成器，但尚未加入定时调度、缓存和前端气泡；
- 当前记忆后端是 SQLite + TF-IDF，不是原文生产方案中的 Qdrant；
- 好感度、NPC 自主状态和实时日志属于后续小节，本节不提前实现；
- LLM 只生成文本，位置、碰撞和未来的关系分数仍由确定性代码维护；
- `.env.example` 不含真实密钥，验证没有访问模型或其他外部服务。

### 参考资料

- [《Hello-Agents》第十五章：构建赛博小镇](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter15/%E7%AC%AC%E5%8D%81%E4%BA%94%E7%AB%A0%20%E6%9E%84%E5%BB%BA%E8%B5%9B%E5%8D%9A%E5%B0%8F%E9%95%87.md)
- [官方赛博小镇项目](https://github.com/datawhalechina/hello-agents/tree/main/code/chapter15/Helloagents-AI-Town)
- [Godot 4 官方文档](https://docs.godotengine.org/zh-cn/4.x/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLite 官方文档](https://www.sqlite.org/docs.html)

### 小结

15.2 将“每个 NPC 一个独立 Agent”落实成了可运行的管理结构：角色 Prompt 决定稳定人格，Working Memory 保持近期连续性，Episodic Memory 召回相关历史，FastAPI 再把这条链路接到 Godot。玩家直接交互必须由专属 Agent 即时处理；不依赖具体玩家的问题，才适合合并为一次批量背景生成。这样既保留个性化，也为后续的状态、好感度和定时调度留下清晰接口。
