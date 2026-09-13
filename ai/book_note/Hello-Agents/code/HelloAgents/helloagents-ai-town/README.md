# HelloAgents 赛博小镇

这是第十五章的持续实践目录。15.1 建立四层边界；15.2 接入独立 NPC、角色 Prompt、两类记忆和批量背景对白；15.3 加入玩家—NPC 好感度；15.4 补齐 FastAPI 服务；15.5 完成 Godot 四场景、玩家控制、NPC 巡逻和交互信号链。

## 目录

```text
helloagents-ai-town/
├── backend/
│   ├── agents.py
│   ├── architecture.py
│   ├── batch_generator.py
│   ├── config.py
│   ├── main.py
│   ├── models.py
│   ├── logger.py
│   ├── relationship_manager.py
│   ├── state_manager.py
│   ├── view_logs.py
│   ├── .env.example
│   ├── architecture_demo.py
│   └── pyproject.toml
├── helloagents-ai-town/
│   ├── assets/
│   ├── scenes/
│   ├── scripts/
│   └── project.godot
└── project_demo.py
```

## NPC 智能体

[backend/agents.py](backend/agents.py) 为张三、李四和王五分别创建 `SimpleAgent` 与 `MemoryManager`。每次对话会按下面的顺序处理：

1. 读取当前 NPC 与玩家的好感度，将等级修饰词加入系统 Prompt；
2. 取得最近 5 条工作记忆，并从情景记忆中检索 3 条相关历史；
3. 将角色、关系、记忆和当前消息交给对应 NPC；
4. 用独立分析 Agent 生成结构化分值变化；
5. 保存好感度，以及带关系元数据的对话记忆。

本地 `SimpleAgent` 没有原文示例中的 `memory_manager` 构造参数，也不能把 `context` 直接传给 `run()`。因此记忆编排放在 `NPCAgentManager`，再序列化为输入文本；角色和记忆逻辑仍与原文一致。

[backend/batch_generator.py](backend/batch_generator.py) 只生成 NPC 背景气泡。它将三名 NPC 合并为一次模型调用，并严格校验返回 JSON 的键和值。玩家按 E 发起的对话仍走专属 Agent，不使用预生成内容。

[backend/relationship_manager.py](backend/relationship_manager.py) 按 `(npc_name, player_id)` 隔离关系，默认从 `0/陌生` 开始。分析结果必须包含 `should_change`、`change_amount`、`reason` 和 `sentiment`；解析或调用失败时保持分数不变。最终分数限制在 0～100，并写入 `SQLITE_PATH`。

## 后端

[backend/state_manager.py](backend/state_manager.py) 同时维护 NPC 的忙碌状态和背景对白缓存。`POST /chat` 会原子占用指定 NPC；已被占用时返回 `409`，处理结束后通过 `finally` 释放。服务启动时立即批量生成一次背景对白，此后按 `NPC_UPDATE_INTERVAL` 定时更新。

[backend/logger.py](backend/logger.py) 将对话、记忆数量、好感度变化、状态刷新和错误同时写到控制台与 `LOG_PATH/dialogue_YYYY-MM-DD.log`。查看当日日志：

```bash
python view_logs.py --lines 80 --follow
```

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
python main.py
```

填写 `LLM_MODEL_ID`、`LLM_API_KEY`、`LLM_BASE_URL` 后，`POST /chat` 才会就绪。未配置时接口返回 `503`，未知 NPC 返回 `404`，模型调用失败返回 `502`，不会用固定台词冒充模型结果。

可用接口：

- `GET /healthz`：返回对话与状态调度器是否就绪；
- `GET /architecture`：返回当前四层架构、组件和十三步数据流；
- `GET /npcs`：返回三名 NPC 的角色资料；
- `GET /npcs/status`、`GET /npcs/{npc_name}/status`：查询整体或单个 NPC 状态；
- `POST /npcs/status/refresh`：立即刷新批量背景对白；
- `GET /npcs/{npc_name}/affinity`、`GET /affinities`：查询单个或全部关系；
- `POST /chat`：即时生成回复，更新关系和记忆，并记录日志。

`/chat` 在原有 `message` 外返回好感度分数、等级、实际变化量、原因、情感、分析有效性和互动次数。一次玩家对话通常需要两次模型调用：一次生成 NPC 回复，一次分析好感度。

离线验证使用 Fake LLM、临时 SQLite 目录，不调用真实模型：

```bash
PYTHONDONTWRITEBYTECODE=1 python architecture_demo.py
```

## Godot

使用 Godot 4.2 或更高版本导入 `helloagents-ai-town/project.godot`。Main 实例化 Player、三个 NPC 和 DialogueUI；玩家与 NPC 都使用 `CharacterBody2D`，NPC 的子节点 `InteractionArea` 负责近距离检测。WASD 或方向键控制玩家，靠近 NPC 后按 E/Enter 打开对话框，Esc 关闭。对话期间玩家和当前 NPC 都会停止移动，成功回复还会显示为 NPC 头顶气泡。

场景中的几何图形是无需额外素材即可运行的占位外观；`AnimatedSprite2D` 和两个音频节点已按原文保留，可在 Godot 编辑器中替换为正式精灵帧和音频资源。

Godot 默认连接 `http://127.0.0.1:8000`，可通过 `CYBER_TOWN_API_URL` 修改。

```bash
PYTHONDONTWRITEBYTECODE=1 python project_demo.py
```

静态脚本检查四个场景的节点组成、资源引用、移动/巡逻/交互脚本、信号链，以及 Godot 与后端的请求字段。它不能替代 Godot 编辑器的 GDScript 解析和实际运行。

当前 Godot 只消费 `/chat` 的回复文本，尚未轮询背景对白或显示好感度。不要提交真实 `.env`、模型密钥、记忆数据库、关系数据库、运行日志或 Godot 缓存目录。
