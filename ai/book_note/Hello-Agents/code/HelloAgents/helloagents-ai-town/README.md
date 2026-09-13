# HelloAgents 赛博小镇

这是第十五章的持续实践目录。15.1 只实现原文已经确定的工程边界：Godot 场景骨架、FastAPI 基础服务、四层架构契约和一次对话的数据流。NPC Agent、记忆、好感度、自主状态和日志将在后续小节继续接入。

## 目录

```text
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
│   ├── scenes/
│   │   ├── dialogue_ui.tscn
│   │   ├── main.tscn
│   │   ├── npc.tscn
│   │   └── player.tscn
│   ├── scripts/
│   │   ├── api_client.gd
│   │   ├── config.gd
│   │   ├── dialogue_ui.gd
│   │   ├── main.gd
│   │   ├── npc.gd
│   │   └── player.gd
│   └── project.godot
└── project_demo.py
```

## 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
python main.py
```

可用接口：

- `GET /`：当前实现范围；
- `GET /healthz`：配置存在性和对话就绪状态；
- `GET /architecture`：四层架构、组件和八步数据流；
- `GET /npcs`：张三、李四、王五的基础目录；
- `POST /chat`：15.1 中保留接口，固定返回 `501`，不伪造 NPC 回复。

`/healthz` 中的集成状态只表示配置是否存在，不会探测 LLM、Qdrant 或 SQLite。15.1 尚未建立 NPC Agent，所以 `conversation_ready` 明确为 `false`。

离线验证：

```bash
PYTHONDONTWRITEBYTECODE=1 python architecture_demo.py
```

## Godot

使用 Godot 4.2 或更高版本导入 `helloagents-ai-town/project.godot`，运行主场景。WASD 控制玩家，靠近 NPC 后按 E 打开对话面板，Esc 关闭。Godot 会读取 `CYBER_TOWN_API_URL`，未设置时默认连接 `http://127.0.0.1:8000`。

当前场景可以独立启动；后端在线时会显示连接状态，但发送按钮保持禁用，因为真实对话属于 15.2。这样保留完整交互和网络接口，又不会用静态台词冒充 Agent 输出。

本机没有安装 Godot，无法执行引擎级导入检查。可以先运行不依赖 Godot 的静态工程验证：

```bash
PYTHONDONTWRITEBYTECODE=1 python project_demo.py
```

脚本检查主场景、场景与脚本资源引用、WASD/E 键契约和 API 路径。它不能替代 Godot 编辑器的 GDScript 解析和实际运行。

不要提交真实 `.env`、模型密钥、运行日志、数据库或 Godot 缓存目录。
