## 构建赛博小镇

> 阅读资料：
>
> - [15.1 项目概述与架构设计](https://datawhalechina.github.io/hello-agents/#/./chapter15/%E7%AC%AC%E5%8D%81%E4%BA%94%E7%AB%A0%20%E6%9E%84%E5%BB%BA%E8%B5%9B%E5%8D%9A%E5%B0%8F%E9%95%87?id=_151-%e9%a1%b9%e7%9b%ae%e6%a6%82%e8%bf%b0%e4%b8%8e%e6%9e%b6%e6%9e%84%e8%ae%be%e8%ae%a1)
> - [15.2 NPC 智能体系统](https://datawhalechina.github.io/hello-agents/#/./chapter15/%E7%AC%AC%E5%8D%81%E4%BA%94%E7%AB%A0%20%E6%9E%84%E5%BB%BA%E8%B5%9B%E5%8D%9A%E5%B0%8F%E9%95%87?id=_152-npc-%e6%99%ba%e8%83%bd%e4%bd%93%e7%b3%bb%e7%bb%9f)
> - [15.3 好感度系统设计](https://datawhalechina.github.io/hello-agents/#/./chapter15/%E7%AC%AC%E5%8D%81%E4%BA%94%E7%AB%A0%20%E6%9E%84%E5%BB%BA%E8%B5%9B%E5%8D%9A%E5%B0%8F%E9%95%87?id=_153-%e5%a5%bd%e6%84%9f%e5%ba%a6%e7%b3%bb%e7%bb%9f%e8%ae%be%e8%ae%a1)
>
> - [15.4 后端服务实现](https://datawhalechina.github.io/hello-agents/#/./chapter15/%E7%AC%AC%E5%8D%81%E4%BA%94%E7%AB%A0%20%E6%9E%84%E5%BB%BA%E8%B5%9B%E5%8D%9A%E5%B0%8F%E9%95%87?id=_154-%e5%90%8e%e7%ab%af%e6%9c%8d%e5%8a%a1%e5%ae%9e%e7%8e%b0)
>
> 15.1 确定四层边界；15.2 实现 NPC 的角色、记忆和两种对话模式；15.3 加入玩家—NPC 好感度；15.4 用 FastAPI 把对话、状态、定时更新和日志串成后端服务。

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

这些能力存在先后关系：游戏产生请求，后端先占用 NPC，Agent 再结合记忆和当前关系生成回复，好感度系统处理互动结果，最后释放状态并记录日志。15.4 已把这条后端链路接通；好感度面板和背景气泡的前端展示仍留给后续章节。

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
        RELATION["玩家—NPC 关系"]
        STATE["忙碌状态与背景对白缓存"]
        LOGGER["每日对话日志"]
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
        LOG_FILE["dialogue_YYYY-MM-DD.log"]
    end

    PLAYER --> NPC_VIEW --> DIALOGUE --> API
    API --> COORDINATOR
    COORDINATOR <--> STATE
    COORDINATOR --> MANAGER --> AGENTS --> LLM
    MANAGER <--> MEMORY --> STORE
    MANAGER <--> RELATION --> STORE
    RELATION --> LLM
    STATE --> BATCH --> LLM
    COORDINATOR --> LOGGER --> LOG_FILE
    STATE --> LOGGER
    API --> DIALOGUE
~~~

| 层次 | 主要职责 | 不应承担的职责 |
| --- | --- | --- |
| Godot 前端 | 画面、移动、碰撞、输入、对话展示 | 保存模型密钥、计算权威关系状态 |
| FastAPI 后端 | 请求校验、状态占用、对话协调、定时更新、日志 | 阻塞游戏帧循环、控制场景节点 |
| HelloAgents | 角色扮演、记忆组织、关系分析、批量对白 | 直接移动玩家或修改场景树 |
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

15.4 将批量生成器接入状态管理器：服务启动时先生成一次，之后按配置间隔刷新缓存。这里更新的是 NPC 背景对白，玩家发起的即时对话仍走独立 Agent。

### 好感度表示一对关系

好感度不是 NPC 自身的全局属性，而是 `(npc_name, player_id)` 对应的关系状态。同一个张三可以与 Garden 是“熟悉”，与新玩家仍是“陌生”；三个 NPC 对同一玩家的分数也互不影响。

原文将分数限制在 0～100，并分为五档：

| 分数 | 等级 | 对话倾向 |
| --- | --- | --- |
| 0～20 | 陌生 | 礼貌但保持距离，回复简短 |
| 21～40 | 熟悉 | 可以正常交流，语气自然友好 |
| 41～60 | 友好 | 愿意分享更多信息，回复更热情 |
| 61～80 | 亲密 | 主动关心，可以谈较私人的内容 |
| 81～100 | 挚友 | 像老朋友一样亲切、坦率 |

正文的代码从 0 分开始，符合“第一次见面是陌生”的描述；官方项目代码则从 50 分开始，并把 20、40、60、80 直接作为下一档起点。两者在初始状态和边界上并不一致。当前实践按正文表格实现：初始值为 0，20 仍是陌生，21 才进入熟悉，其他边界以此类推。

互动次数和好感度也要分开。每次对话都会增加 `interaction_count`，但普通闲聊、解析失败或者分数已经到达边界时，好感度可以不变。

### 从一轮对话到分值更新

原文用 LLM 判断玩家态度，而不是给每轮对话固定加分。当前实践沿用官方项目中较完整的四字段协议：

~~~json
{
  "should_change": true,
  "change_amount": 5,
  "reason": "友好感谢",
  "sentiment": "positive"
}
~~~

评分提示词参考下面的范围：

| 互动 | 建议变化 |
| --- | --- |
| 赞美、感谢、请教 | +3～+8 |
| 友好问候、正常交流 | +1～+3 |
| 普通闲聊、中性话题 | 0 |
| 批评、质疑、不耐烦 | -3～-8 |
| 侮辱、攻击、恶意 | -8～-15 |

模型给出的 `change_amount` 仍只是建议，最终更新必须由确定性代码执行：

`new_score = min(100, max(0, old_score + change_amount))`

例如当前是 2 分，模型建议 -8，最终只能降到 0；API 返回的实际变化量应是 -2，而不是 -8。这样日志、前端和数据库看到的是同一个结果。

~~~mermaid
sequenceDiagram
    actor P as 玩家
    participant M as NPC Agent Manager
    participant R as RelationshipManager
    participant A as NPC SimpleAgent
    participant J as AffinityAnalyzer
    participant D as SQLite

    P->>M: 发送消息
    M->>R: 读取当前关系
    R-->>M: old_score + level + modifier
    M->>A: 角色 + 当前关系 + 记忆 + 消息
    A-->>M: NPC 回复
    M->>J: 玩家消息 + NPC 回复
    J-->>R: JSON 分析结果
    R->>R: 校验字段并限制到 0～100
    R->>D: 保存 score 与 interaction_count
    R-->>M: old/new score、等级与实际变化
    M-->>P: 回复 + 好感度结果
~~~

[relationship_manager.py](./code/HelloAgents/helloagents-ai-town/backend/relationship_manager.py) 对模型输出做了完整校验：布尔值、整数范围、原因、情感枚举以及“不改变时变化量必须为 0”都要成立。JSON 无法解析、字段缺失或模型调用失败时，当前对话仍然返回，但分数保持不变，并设置 `affinity_analysis_valid=false`。这比解析失败后默认加分更安全。

关系记录写入 `SQLITE_PATH` 指向的 SQLite 数据库，主键是 `(npc_name, player_id)`。分数、互动次数和带时区更新时间可以跨进程重启恢复；模型密钥、原始 Prompt 和完整模型响应不会写进关系表。

### 当前关系影响下一轮回复

好感度只有进入 Prompt 才会影响 NPC 行为。每次生成回复前，管理器先读取旧关系，再动态扩展该 NPC 的 system Prompt：

~~~text
当前与玩家的关系：熟悉（好感度 24/100）。
本轮对话方式：已经认识这位玩家，可以正常交流，回复自然友好。
~~~

顺序不能反过来。本轮回复使用更新前的关系；玩家的这句话经过分析后得到新分数，新等级从下一轮开始生效。这样因果关系清楚，也避免先根据尚未发生的评分改变本轮态度。

一次玩家对话现在通常产生两次模型调用：第一次由 NPC Agent 生成回复，第二次由分析 Agent 评估好感度。角色回复和关系判断职责分开了，但延迟与 Token 成本也随之增加；后续可以换成更小的分类模型或规则与模型结合，接口无需变化。

### 后端是编排层，不是第四个 Agent

15.4 的重点不是再增加一种推理能力，而是把前三节的对象组织成稳定服务。各模块只处理一类状态：

| 模块 | 负责什么 | 状态存放位置 |
| --- | --- | --- |
| `NPCAgentManager` | 角色回复、记忆检索与保存 | 每个 NPC 的 MemoryManager |
| `RelationshipManager` | 玩家—NPC 分数、等级与更新 | SQLite |
| `NPCStateManager` | 忙碌状态、当前动作、背景对白缓存 | 进程内存 |
| `DialogueLogger` | 对话、关系变化、状态刷新和错误 | 控制台与日志文件 |
| FastAPI `main.py` | 校验请求、调用以上模块、转换 HTTP 错误 | 不长期保存业务数据 |

原文片段使用 `@app.on_event("startup")`，官方完整工程已经改用 `lifespan`。当前实践也使用 `lifespan`：启动时开启状态调度器，关闭时取消后台任务、关闭记忆数据库和日志句柄。资源的创建和销毁由同一处管理，测试时也能注入 Fake LLM、临时状态管理器和临时日志目录。

### NPC 状态包含交互与环境两部分

[state_manager.py](./code/HelloAgents/helloagents-ai-town/backend/state_manager.py) 中的状态分为两组：

- 交互状态：位置、`is_busy`、`current_action`、正在交谈的 `player_id` 和最后互动时间；
- 环境状态：三名 NPC 当前的背景对白、上次批量更新时间和下次更新倒计时。

它们都不是好感度。好感度描述长期关系，需要持久化；忙碌状态只在请求执行期间有效；背景对白是可重新生成的缓存。把三者混成一个字典，会让一次对话失败时很难判断应该恢复哪部分数据。

正文先调用 `is_npc_busy()`，再调用 `set_npc_busy(True)`。并发请求可能同时通过第一次检查，因此实践将两步合并为加锁的 `try_begin_dialogue()`：只有一个请求能把 NPC 从空闲切换为忙碌，其余请求得到 `409 Conflict`。

~~~mermaid
sequenceDiagram
    actor P as 玩家
    participant F as FastAPI
    participant S as NPCStateManager
    participant A as NPCAgentManager
    participant L as DialogueLogger

    P->>F: POST /chat
    F->>S: try_begin_dialogue(npc, player)
    alt NPC 已忙碌
        S-->>F: false
        F-->>P: 409 Conflict
    else 成功占用
        S-->>F: true
        F->>A: 生成回复并更新关系、记忆
        alt 处理成功
            A-->>F: reply + affinity
            F->>L: 记录完整对话
            F-->>P: 200 OK
        else 模型或存储失败
            A-->>F: exception
            F->>L: 记录错误
            F-->>P: 502 Bad Gateway
        end
        F->>S: finally 释放 NPC
    end
~~~

`finally` 很重要：释放动作不依赖 Agent 是否成功。如果只在正常返回前设置空闲，一次模型超时就会让 NPC 永久停在忙碌状态。

### 定时批量更新与生命周期

状态管理器启动后立即调用一次 `NPCBatchGenerator` 填充缓存，再按 `NPC_UPDATE_INTERVAL` 周期刷新。默认 30 秒意味着每小时约 120 次批量请求；这是成本配置，不是越短越好。启动服务本身也会产生一次真实模型调用。

~~~mermaid
flowchart LR
    START["FastAPI lifespan 启动"] --> FIRST["立即批量生成一次"]
    FIRST --> CACHE["原子替换背景对白缓存"]
    CACHE --> WAIT["等待配置间隔"]
    WAIT --> GENERATE["在线程中执行同步 LLM 调用"]
    GENERATE -->|成功| CACHE
    GENERATE -->|失败| KEEP["记录错误并保留旧缓存"]
    KEEP --> WAIT
    STOP["FastAPI lifespan 关闭"] --> CANCEL["取消并等待后台任务"]
~~~

批量生成器是同步接口，直接放进异步循环会阻塞 FastAPI 事件循环。实践通过 `asyncio.to_thread()` 执行模型调用；状态写入仍由锁保护。手动刷新与定时刷新共用同一把异步锁，不会同时覆盖缓存。

### 每日对话日志

[logger.py](./code/HelloAgents/helloagents-ai-town/backend/logger.py) 中的 `DialogueLogger` 同时输出到控制台和 `LOG_PATH/dialogue_YYYY-MM-DD.log`。一条成功日志包含 NPC、玩家、双方消息、近期/相关记忆数量、好感度实际变化、原因、情感和评分是否有效；状态刷新与异常也进入同一日志。日志按本地日期切换文件，但不会记录模型密钥。

~~~bash
python view_logs.py --lines 80
python view_logs.py --follow
python view_logs.py --date 2026-09-13
~~~

[view_logs.py](./code/HelloAgents/helloagents-ai-town/backend/view_logs.py) 默认读取当天文件，可以指定日期、末尾行数或持续跟踪。这里的日志主要用于开发追踪，不等于完整的生产可观测性。高并发服务还需要请求 ID、结构化 JSON、敏感文本脱敏和集中式日志采集。

### 场景与节点是下一步前端实现的基础

15.4.4 用节点和场景解释 Godot 的组织方式。节点承担单一功能，并按父子关系组成场景树；场景则是可保存、可复用和可实例化的节点树。当前工程已经把 Player、NPC 和 DialogueUI 拆成独立场景，再由 Main 场景组合。这个小节是 15.5 前端开发的概念铺垫，本次没有重复创建另一套 Godot 文件。

### 工程实现

代码继续放在 `code/HelloAgents/helloagents-ai-town/`：

~~~text
helloagents-ai-town/
├── backend/
│   ├── agents.py                 # NPC 配置、Prompt、Agent 与记忆编排
│   ├── batch_generator.py        # 一次调用生成三段背景对白
│   ├── architecture.py           # 当前实现范围
│   ├── config.py                 # 环境变量
│   ├── logger.py                 # 控制台与每日文件日志
│   ├── main.py                   # FastAPI 接口
│   ├── models.py                 # 请求与响应模型
│   ├── relationship_manager.py   # 好感度分析、分级与 SQLite 持久化
│   ├── state_manager.py          # 忙碌状态、背景对白缓存与定时器
│   ├── view_logs.py              # 日志查看命令
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

15.3 在记忆元数据中同步保存更新后的分数、实际变化量、等级、情感、原因和分析是否有效。以后检索出某次旧对话时，可以知道当时的关系背景，而不只是看到两段孤立文本。

#### 好感度管理器

`RelationshipManager` 自己维护一个分析用 `SimpleAgent`，不与三个 NPC 的角色历史混用。分析前会清空它的内部历史，避免上一位玩家的评分内容影响下一次判断；数据库访问与分析调用分别使用锁，查询分数不必一直等待模型返回。

~~~python
current = relationship_manager.get_affinity(name, player_id)
agent.system_prompt = create_affinity_system_prompt(role, current)
response = agent.run(enhanced_message)
affinity = relationship_manager.analyze_and_update_affinity(
    npc_name=name,
    player_message=message,
    npc_response=response,
    player_id=player_id,
)
~~~

关系先按旧状态影响回复，随后才更新。更新与情景记忆保存都在同一个 NPC 的对话锁内，避免该 NPC 的并发请求交叉覆盖；不同 NPC 仍能分别处理。

#### FastAPI 接口与生命周期

[main.py](./code/HelloAgents/helloagents-ai-town/backend/main.py) 通过依赖注入组装 Agent、状态和日志组件。`lifespan` 启停后台调度器，路由只处理协议和流程：

正文示意接口名是 `/dialogue`，官方完整工程和当前 Godot 客户端使用 `/chat`。实践保留 `/chat`，避免为同一流程维护两套路由。

| 接口 | 当前行为 |
| --- | --- |
| `GET /healthz` | 返回对话与状态调度器是否就绪 |
| `GET /architecture` | 返回当前四层架构和十三步数据流 |
| `GET /npcs` | 返回三名 NPC，并按忙碌状态计算 `available` |
| `GET /npcs/status` | 返回全部状态、背景对白和下次更新倒计时 |
| `GET /npcs/{npc_name}/status` | 返回单个 NPC 的位置、动作与忙碌状态 |
| `POST /npcs/status/refresh` | 立即执行一次批量背景对白更新 |
| `GET /npcs/{npc_name}/affinity` | 查询一组玩家—NPC 关系 |
| `GET /affinities` | 查询指定玩家与全部 NPC 的关系 |
| `POST /chat` | 占用 NPC，生成回复，更新关系与记忆，写日志后释放 |

未配置三项 LLM 参数或没有批量生成器时返回 `503`；NPC 不存在返回 `404`；NPC 已被占用返回 `409`；模型、记忆或刷新处理失败返回 `502`。服务不会用静态台词伪装成成功响应。

返回结构保留 Godot 已使用的 `message`，并加入完整的关系更新结果：

~~~json
{
  "npc_name": "张三",
  "npc_title": "Python 工程师",
  "message": "……",
  "affinity_score": 24,
  "affinity_level": "熟悉",
  "affinity_change": 5,
  "affinity_reason": "友好感谢",
  "affinity_sentiment": "positive",
  "affinity_analysis_valid": true,
  "interaction_count": 3,
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

当前 Godot UI 只调用 `/healthz` 和 `/chat`，新增的好感度字段会被安全忽略；状态与背景对白接口已经就绪，但前端尚未轮询和显示这些数据。

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
SQLITE_PATH="./data/cyber_town.db"
NPC_UPDATE_INTERVAL="30"
LOG_PATH="./logs"
~~~

然后启动：

~~~bash
python main.py
~~~

访问 `http://127.0.0.1:8000/docs` 可以测试全部接口。真实运行会在启动时和每次状态刷新时调用模型，在 `MEMORY_PATH` 下创建 NPC 记忆数据库，在 `SQLITE_PATH` 保存关系分数，并把日志写入 `LOG_PATH`。

游戏端使用 Godot 4.2 或更高版本导入：

~~~text
code/HelloAgents/helloagents-ai-town/helloagents-ai-town/project.godot
~~~

运行主场景后用 WASD 移动，靠近 NPC 按 E，按 Esc 关闭对话框。API 地址默认是 `http://127.0.0.1:8000`，也可以通过 `CYBER_TOWN_API_URL` 修改。

### 实践结果

后端使用 Fake LLM、临时 SQLite 和临时日志目录完成离线验证。除了保留 Agent、记忆和好感度回归测试，还检查了原子忙碌状态、`409` 冲突、`finally` 释放、生命周期启停、启动/手动状态刷新、状态与好感度接口以及每日文件日志。

~~~text
=== 15.4 后端服务离线验证 ===
npc_agents_memory_affinity: regression_ready
busy_state: atomic_409_and_finally_release_ready
background_scheduler: startup_and_manual_refresh_ready
state_api: list_single_and_cache_ready
affinity_api: single_compatibility_and_all_ready
daily_dialogue_log: console_file_contract_ready
lifespan: scheduler_start_stop_ready
sqlite_persistence: restart_ready
external_api_calls: 0
~~~

Godot 静态验证检查了场景资源、WASD/E 键，以及前后端约定的请求字段和响应处理：

~~~text
=== 15.1～15.4 Godot 对话契约静态验证 ===
required_files: 11
resource_references: 8
main_scene_contract: ready
movement_and_interaction_contract: ready
chat_request_and_response_contract: ready
godot_runtime: not_executed
external_api_calls: 0
~~~

本机没有安装 Godot，所以第二组结果不能证明 GDScript 已通过引擎解析，也不能替代主场景运行。离线 Fake LLM 只验证控制流、状态、日志和接口契约，没有证明真实模型的角色表现、好感度判断质量或线上调度稳定性。

### 实践边界

- 已实现三个独立 `SimpleAgent`、角色 Prompt、短期/情景记忆和即时 `/chat`；
- 已实现五档好感度、结构化分析、动态对话修饰、NPC—玩家隔离和 SQLite 持久化；
- 已实现 NPC 忙碌状态、原子占用、`409` 冲突和异常后的释放；
- 已实现批量背景对白的启动刷新、定时调度、缓存查询与手动刷新；
- 已实现控制台与每日文件日志，并提供 `view_logs.py`；
- 当前记忆后端是 SQLite + TF-IDF，不是原文生产方案中的 Qdrant；
- Godot 尚未轮询背景对白，也没有好感度 UI，这些属于后续前端小节；
- LLM 负责提出关系变化，确定性代码负责校验、限幅和持久化，位置与碰撞仍由游戏维护；
- `.env.example` 不含真实密钥，验证没有访问模型或其他外部服务。

### 参考资料

- [《Hello-Agents》第十五章：构建赛博小镇](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter15/%E7%AC%AC%E5%8D%81%E4%BA%94%E7%AB%A0%20%E6%9E%84%E5%BB%BA%E8%B5%9B%E5%8D%9A%E5%B0%8F%E9%95%87.md)
- [官方赛博小镇项目](https://github.com/datawhalechina/hello-agents/tree/main/code/chapter15/Helloagents-AI-Town)
- [官方 `state_manager.py`](https://github.com/datawhalechina/hello-agents/blob/main/code/chapter15/Helloagents-AI-Town/backend/state_manager.py)
- [官方 `logger.py`](https://github.com/datawhalechina/hello-agents/blob/main/code/chapter15/Helloagents-AI-Town/backend/logger.py)
- [Godot 4 官方文档](https://docs.godotengine.org/zh-cn/4.x/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLite 官方文档](https://www.sqlite.org/docs.html)

### 小结

15.4 把前三节的对象变成了可运行的服务：FastAPI 负责协议和编排，状态管理器原子占用 NPC 并缓存定时生成的背景对白，Agent 负责回复、记忆和关系更新，日志器记录完整结果，生命周期统一启动和回收资源。LLM 仍只生成开放式内容；并发冲突、状态释放、分值边界和持久化都由确定性代码控制。
