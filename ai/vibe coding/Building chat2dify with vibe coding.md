## 使用 vibe coding 构建 chat2dify

### 背景

* ```chat2dify``` 是一个围绕 ```Dify``` 的自然语言应用创建与编辑组件。它尝试解决的问题是：当我们已经能用对话描述一个工作流时，是否可以让 AI 帮我们完成 Dify 应用的创建、修改、测试运行和发布，而不是反复在画布上拖节点。

* 这个项目很适合作为一个 ```vibe coding``` 项目来复盘，因为它不是简单地“让大模型写代码”，而是把自然语言、结构化计划、Dify DSL、草稿安全写回和人类确认串成了一个闭环。

### 项目定位

* ```chat2dify``` 的运行形态是一个独立的 ```FastAPI``` sidecar 组件：

  * 通过 ```Dify Console API``` 连接本地或局域网内的 Dify。
  * 用户在 Web UI 或 Dify Console 内嵌面板中输入自然语言。
  * 服务端把意图转换成可审阅的操作卡片。
  * 用户确认后，后台任务再执行创建、修改、运行或发布。

* 从 ```v3.0.0``` 开始，它既可以独立运行，也可以通过 compose overlay 挂载到 Dify nginx 的 ```/chat2dify/``` 子路径，并在 Dify Console 中以内嵌抽屉面板的形式出现。

### 核心链路

* 典型链路如下：

  ```text
  用户自然语言
    -> POST /api/assistant/plan
    -> 缺信息则继续追问
    -> 生成待确认操作卡片
    -> 用户确认
    -> POST /api/assistant/execute
    -> 后台任务执行 create / modify / run / publish
    -> 返回 Dify app_id、草稿 hash、运行结果或错误详情
  ```

* 这个链路里最关键的设计是：大模型不直接拥有写 Dify 的权限。它先生成 ```Plan IR```，再由后续的规范化、校验、编译、预检和保护逻辑来决定是否能真正写入。

### 技术栈

* 后端使用：

  * ```FastAPI``` 提供 Web UI、助手 API、Dify 资源查询 API 和后台任务 API。
  * ```Pydantic``` 定义请求、响应和 Plan IR 模型。
  * ```httpx``` 访问 Dify Console API 和 Planner 模型服务。
  * ```PyYAML``` 处理 Dify DSL。
  * ```SQLite``` 持久化后台任务状态。

* 项目中比较重要的模块：

  * ```app/assistant.py```：对话助手的意图解析和待确认操作生成。
  * ```app/agent/```：Planner、编辑器、差异、规范化和风险保护逻辑。
  * ```app/compiler/```：把 Plan IR 编译成 Dify DSL。
  * ```app/dify/```：Dify Console API client、graph 适配、版本读取和预检。
  * ```app/tasks.py```：创建、修改、运行、发布等操作的后台任务队列。
  * ```deploy/dify/```：Dify docker compose overlay、nginx 子路径和 Console 内嵌入口适配。

### 支持能力

* 应用类型：

  | Dify 类型 | app_mode | 说明 |
  | --- | --- | --- |
  | Workflow | ```workflow``` | 普通工作流 |
  | Chatflow | ```advanced-chat``` | 对话流 |
  | Chatbot | ```chat``` | 基础聊天助手 |
  | Agent | ```agent-chat``` | Agent 应用 |
  | Completion | ```completion``` | 文本生成应用 |

* 主要操作：

  * 创建应用：自然语言生成 Plan IR，再导入为 Dify 草稿。
  * 修改草稿：先生成预览，不直接写回；确认后再应用修改。
  * 测试运行：把自然语言测试输入映射到不同应用类型的 draft run/chat API。
  * 发布应用：必须显式确认，并带当前草稿 hash。
  * 查询资源：读取 Dify 已安装的数据集、模型、工具、Agent Strategy 和 Trigger Provider。

### vibe coding 的关键点

* 第一个关键点是把“感觉”拆成可执行的边界。用户说“创建一个电脑城售后服务工作流”时，AI 可以负责理解意图，但系统必须把它落到应用名称、应用类型、输入输出、节点结构、模型配置和工具选择这些结构化字段上。

* 第二个关键点是用确认卡片承接不确定性。写入 Dify 草稿、发布应用、修改节点连接都属于高风险动作，不能因为模型说得流畅就直接执行。```chat2dify``` 让 AI 先规划，让用户再确认，这让 vibe coding 变得可控。

* 第三个关键点是保留工程化护栏。项目里有 Plan IR 校验、DSL 预检、草稿 hash、破坏性修改保护、任务状态持久化和模型 provider fallback，这些都是把原型推进到可长期使用工具所必需的部分。

### 运行

* 独立运行：

  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  cp .env.example .env
  uvicorn app.main:app --host 127.0.0.1 --port 8000
  ```

* 打开：

  ```text
  http://127.0.0.1:8000/
  ```

* Dify 面板模式下，入口通常是：

  ```text
  http://localhost/chat2dify/
  /chat2dify/?embed=1&intent=create&app_mode=workflow
  /chat2dify/?embed=1&intent=modify&app_id=<app_id>&app_mode=workflow&app_name=<name>
  ```

### 适合继续迭代的方向

* 更细粒度的节点能力覆盖，例如复杂循环、外部工具、数据集检索和 Trigger 工作流的可视化解释。
* 更强的 Dify 版本适配层，降低 Dify DSL 或 Console API 变化带来的维护成本。
* 把创建、修改、运行、发布的历史沉淀成可回放的操作日志，方便复盘和回滚。
* 增加更多真实业务工作流样例，让 Planner 的提示词和校验器可以持续从项目实践中演进。

### 总结

* ```chat2dify``` 的价值不只是“用对话创建 Dify 应用”，而是把 vibe coding 的即时表达能力接入了一个有边界、有校验、有确认、有任务状态的工程系统。它让我感觉比较重要的一点是：AI 可以加速构建，但真正让工具可靠的，仍然是中间表示、校验链路和对高风险动作的克制。

### 参考文献

* [Garden12138/chat2dify](https://github.com/Garden12138/chat2dify)
* [Dify](https://github.com/langgenius/dify)
