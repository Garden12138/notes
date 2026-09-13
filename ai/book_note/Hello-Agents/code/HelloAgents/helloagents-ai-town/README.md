# HelloAgents 赛博小镇

这是第十五章的持续实践目录。15.1 建立 Godot、FastAPI、HelloAgents 与外部服务的四层边界；15.2 接入三个独立 NPC、角色 Prompt、工作记忆、情景记忆，以及一次调用生成三段环境对白的批量生成器。

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

1. 取得当前玩家最近 5 条工作记忆；
2. 从情景记忆中检索 3 条相关历史；
3. 将两类记忆和当前消息一起交给对应 NPC；
4. 保存两条工作记忆和一条完整互动情景记忆。

本地 `SimpleAgent` 没有原文示例中的 `memory_manager` 构造参数，也不能把 `context` 直接传给 `run()`。因此记忆编排放在 `NPCAgentManager`，再序列化为输入文本；角色和记忆逻辑仍与原文一致。

[backend/batch_generator.py](backend/batch_generator.py) 只生成 NPC 背景气泡。它将三名 NPC 合并为一次模型调用，并严格校验返回 JSON 的键和值。玩家按 E 发起的对话仍走专属 Agent，不使用预生成内容。

## 后端

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

- `GET /healthz`：返回对话就绪状态与配置存在性；
- `GET /architecture`：返回当前四层架构、组件和八步数据流；
- `GET /npcs`：返回三名 NPC 的角色资料；
- `POST /chat`：即时生成角色化回复并保存记忆。

离线验证使用 Fake LLM、临时 SQLite 目录，不调用真实模型：

```bash
PYTHONDONTWRITEBYTECODE=1 python architecture_demo.py
```

## Godot

使用 Godot 4.2 或更高版本导入 `helloagents-ai-town/project.godot`。WASD 控制玩家，靠近 NPC 后按 E 打开对话框，Esc 关闭。Godot 默认连接 `http://127.0.0.1:8000`，可通过 `CYBER_TOWN_API_URL` 修改。

```bash
PYTHONDONTWRITEBYTECODE=1 python project_demo.py
```

静态脚本检查场景、资源引用、WASD/E 键，以及 Godot 与后端的请求字段。它不能替代 Godot 编辑器的 GDScript 解析和实际运行。

当前不实现好感度、NPC 自主状态、后台定时调度和日志，这些属于后续小节。不要提交真实 `.env`、模型密钥、记忆数据库、运行日志或 Godot 缓存目录。
