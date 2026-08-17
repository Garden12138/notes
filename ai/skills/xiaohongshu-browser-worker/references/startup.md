# OpenClaw 加载与 Gateway 客户端启动

本说明包含三部分：加载并检查 Skill、连接本机固定 Chrome Profile，以及使用
`workers/openclaw` 客户端向 Automation Gateway 注册 Worker、领取任务或运行
`xiaohongshu.check_login@1.0`、`xiaohongshu.search_notes@1.0` 或
`xiaohongshu.collect_note_detail@0.1`、`xiaohongshu.collect_comments@0.1`，以及稳定采集版本
`xiaohongshu.search_notes@1.1`、`xiaohongshu.collect_note_detail@0.2`、
`xiaohongshu.collect_comments@0.2`，以及创作端
`xiaohongshu.publisher_login_check@1.0`、`xiaohongshu.publisher_image_upload@1.0`、
`xiaohongshu.publisher_form_fill@1.0`、`xiaohongshu.publisher_draft_save@1.0`、
`xiaohongshu.publisher_final_publish@1.0`、`xiaohongshu.publisher_final_status_sync@1.0`。
`browser-check` 仍只做独立连接
验收；完整任务生命周期由 `run` 命令按 capability/version 分派执行。

## 1. 合并配置

正式目标 Mac 应安装平台发布的独立 Connector wheel，不需要检出或运行平台仓库。先用以下命令取得
wheel 内的资源目录：

```sh
ai-content-ops-openclaw resource-path plugin
ai-content-ops-openclaw resource-path skills
```

检查返回的插件目录后，使用 OpenClaw 的本地目录安装命令安装，不要使用仓库路径或开发用 `--link`：

```sh
PLUGIN_DIR=/上一步返回的绝对插件目录
openclaw plugins install "$PLUGIN_DIR"
```

将 `openclaw-config.example.json` 的字段合并到 `~/.openclaw/openclaw.json`，不要直接覆盖已有的
模型、Agent 或插件配置。至少完成以下设置：

- 确认 `skills.load.extraDirs` 指向上面 `resource-path skills` 返回的已安装目录；仅在仓库开发模式下才
  指向仓库的 `workers/openclaw/skills`。
- 安装 `resource-path plugin` 返回的受限插件；仅在仓库开发模式下才使用
  `workers/openclaw/plugin`。把
  `AI_CONTENT_OPS_ATTEMPT_BRIDGE_TOKEN` 作为固定环境变量提供给 Gateway；OpenClaw 2026.6.6
  不可靠地物化外部插件的配置 SecretRef，因此插件直接读取该固定变量。不要把明文令牌写入
  `openclaw.json`。
- 确认专用 Agent 的 Skill allowlist 只包含 `xiaohongshu-browser-worker`，工具 allowlist 只包含
  `ai_content_ops_attempt_context`、`ai_content_ops_attempt_step` 和
  `ai_content_ops_attempt_finish`。不要启用 OpenClaw browser、Shell、文件、消息或发布工具。

合并完成后执行 `openclaw config validate --json`、`openclaw gateway restart --safe`、
`openclaw gateway status --require-rpc`、
`openclaw plugins inspect ai-content-ops-attempt --runtime --json` 和 `openclaw skills list`。插件运行时
必须只注册三个 Attempt 工具，Skill 必须可见；任一检查失败时不得启动 Connector。

`worker-config.example.json` 是 Gateway 客户端和本机 Profile 绑定的无秘密配置契约。Skill 本身不读取
该文件，也不要在其中添加租约令牌、Cookie、密码、API 凭据或数据库连接。仓库示例必须保持
`browser_profiles: []`；真实 Profile UUID、小红书用户 ID 和本机绑定只写入不受 Git 管理的副本。

## 2. 检查 Skill

在已安装 OpenClaw 的主机上运行：

```sh
openclaw skills check
openclaw skills list
```

确认 `xiaohongshu-browser-worker` 可见且没有加载错误。能力清单中的
`xiaohongshu.check_login@1.0`、`xiaohongshu.search_notes@1.0` 与
`xiaohongshu.collect_note_detail@0.1`、`xiaohongshu.collect_comments@0.1`，以及三个稳定采集新版本应为 `active`、enabled
且允许向 Gateway 声明；只读创作账号核验 `xiaohongshu.publisher_login_check@1.0` 也应为
`active`、enabled；受限图片上传 `xiaohongshu.publisher_image_upload@1.0` 仅在已通过账号/Profile
核验且运行时部署共享确定性 Handler 后声明。
受限草稿保存 `xiaohongshu.publisher_draft_save@1.0` 还必须有当前 PASS validation 和逐任务人工门禁；
不得仅因能力为 active 就创建或领取真实写入 Job。
最终发布 `xiaohongshu.publisher_final_publish@1.0` 还必须有当前 APPROVED 任务、逐任务用户不可逆确认、
`max_attempts=1` 和 `OPERATOR_REQUIRED`；准备审批、聊天许可或历史授权都不能代替该门禁。

## 3. 启动或刷新 OpenClaw 本机 Gateway

前台开发模式使用：

```sh
openclaw gateway run
```

若 Gateway 已作为本机服务运行，安装受限插件并配置环境 SecretRef 后执行：

```sh
openclaw gateway restart --safe
openclaw gateway status --require-rpc
```

## 4. 执行无副作用烟雾检查

只验证配置、插件和 Skill；三个 Attempt 工具必须由绑定了当前 Attempt 的 Python loopback bridge
驱动，禁止用自由文本伪造烟雾调用：

```sh
openclaw config validate --json
openclaw plugins validate
openclaw skills list
```

预期结果是配置有效、`ai-content-ops-attempt` 插件有效且 Skill 可见。专用 Agent 的最终工具清单必须
恰好为三个桥接工具。该 smoke 不执行任何浏览器动作，也不要使用真实 Job、Profile、Cookie、租约令牌
或生产账号进行本次检查。

## 5. 准备 Automation Gateway 客户端配置

正式接入时直接使用平台 ADMIN 在“Automation Center → 外部 OpenClaw”下载的无密钥 Connector JSON。
它已经固定 RuntimeMachine ID、Worker ID、`profile_root` 和审核过的能力集合，Machine Token 只从
`AI_CONTENT_OPS_GATEWAY_MACHINE_TOKEN` 环境变量读取。不要手工扩大能力。

仅在仓库开发或离线调试时，才从仓库复制示例配置并替换环境相关值：

```sh
cp \
  workers/openclaw/skills/xiaohongshu-browser-worker/references/worker-config.example.json \
  /tmp/openclaw-worker.json
```

- `gateway_url` 必须是 Automation Gateway 的 HTTP(S) Origin，不带路径、查询参数、凭据或片段；非本机
  环境应使用可信的 HTTPS 地址。
- `machine_id` 必须对应平台中已准备并允许承载 `OPENCLAW` Runtime 的机器。
- `worker_id` 与 `machine_id` 必须是两个不同的非零 UUID。一个 Worker 实例应长期复用同一
  `worker_id`，重新注册会刷新该 Worker，而不是创建临时身份。
- `runtime_version` 填当前客户端版本；`max_concurrency` 当前只能为 `1`。
- `profile_root` 是相对 `$HOME` 的规范 POSIX 路径，不相对仓库或当前工作目录，也不能写 `~` 或绝对
  路径。每个绑定的专用 Chrome user-data-dir 为 `$HOME/<profile_root>/<profile_path>`。
- `openclaw_bridge_token_env` 只允许固定为 `AI_CONTENT_OPS_ATTEMPT_BRIDGE_TOKEN`。真实令牌由 Worker 与
  OpenClaw Gateway 的进程环境提供，不写入本机 Worker JSON。
- `browser_connect_timeout_seconds`、`browser_navigation_timeout_seconds` 和
  `browser_probe_timeout_seconds` 分别保持 `10`、`30`、`10` 秒。
- `browser_profiles` 在仓库示例中必须为空；本机副本中的每个绑定包含 `machine_id`、`profile_id`、
  `profile_path` 和 `expected_user_id`。绑定的机器必须是本 Worker 的 `machine_id`，Profile UUID、相对
  路径和最终 user-data-dir 均不能重复。
- `enabled_capabilities` 是本次注册的完整能力快照，Gateway 按 `name` 与 `version` 精确匹配任务。

仓库示例没有真实 Profile 绑定，因此即使 `xiaohongshu.check_login@1.0` 已发布，示例仍必须保持：

```json
"enabled_capabilities": []
```

空能力快照可以用于注册和上线识别，但不能运行 `claim`、`poll` 或 `run`。只有完成固定 Profile
绑定、人工登录并通过 `browser-check` 后，才在不受 Git 管理的本机副本中显式声明已发布能力：

```json
"enabled_capabilities": [
  {"name": "xiaohongshu.check_login", "version": "1.0"},
  {"name": "xiaohongshu.search_notes", "version": "1.0"},
  {"name": "xiaohongshu.collect_note_detail", "version": "0.1"},
  {"name": "xiaohongshu.collect_comments", "version": "0.1"},
  {"name": "xiaohongshu.search_notes", "version": "1.1"},
  {"name": "xiaohongshu.collect_note_detail", "version": "0.2"},
  {"name": "xiaohongshu.collect_comments", "version": "0.2"},
  {"name": "xiaohongshu.publisher_login_check", "version": "1.0"},
  {"name": "xiaohongshu.publisher_image_upload", "version": "1.0"},
  {"name": "xiaohongshu.publisher_form_fill", "version": "1.0"},
  {"name": "xiaohongshu.publisher_draft_save", "version": "1.0"},
  {"name": "xiaohongshu.publisher_final_publish", "version": "1.0"},
  {"name": "xiaohongshu.publisher_final_status_sync", "version": "1.0"}
]
```

本机只声明其运行时实际部署并已通过浏览器检查的 active 能力；不得声明清单中仍为 `planned` 或
disabled 的其他小红书能力。能力身份、输入和输出 Schema 必须与 `capabilities.json` 精确一致。

## 6. 准备固定 Chrome Profile

先在 `/tmp/openclaw-worker.json` 的 `browser_profiles` 中加入唯一的本机绑定。以下仅为结构示意；所有
占位值都应在本机副本中替换，真实值不得复制回仓库：

```json
"browser_profiles": [
  {
    "machine_id": "<与 Worker 配置一致的机器 UUID>",
    "profile_id": "<Automation Gateway 中的 Profile UUID>",
    "profile_path": "xiaohongshu/account-main",
    "expected_user_id": "<登录后页面可回读的小红书稳定用户 ID>"
  }
]
```

为自动化账号使用专用 user-data-dir，不要指向日常 Chrome 的默认资料目录，也不要用同一目录同时启动
两个 Chrome 进程。以下命令在独立终端以前台方式启动 macOS Chrome；`--remote-debugging-port=0` 让
Chrome 选择空闲 loopback 端口并在专用目录写入 `DevToolsActivePort`，无需也不得把动态端口写入配置：
Chrome 136 及以上版本也要求远程调试使用这种非默认 user-data-dir。

```sh
PROFILE_ROOT_RELATIVE=.browser-profiles/xiaohongshu-browser-worker
PROFILE_PATH=xiaohongshu/account-main
USER_DATA_DIR="$HOME/$PROFILE_ROOT_RELATIVE/$PROFILE_PATH"
mkdir -p "$USER_DATA_DIR"

"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --user-data-dir="$USER_DATA_DIR" \
  --remote-debugging-address=127.0.0.1 \
  --remote-debugging-port=0 \
  --no-first-run \
  --no-default-browser-check
```

Linux 可将可执行文件替换为本机受信任的 `google-chrome` 路径，其余参数保持一致。首次启动后由运营
人员在该窗口手动登录并核对小红书账号；不要导出 Cookie 或 storage state，也不要在命令行、配置或
日志中放入密码。后续检查只复用这个已运行的 Profile，不负责启动 Chrome、登录或切换账号。

连接器只接受专用目录中严格两行的 `DevToolsActivePort`，并交叉验证 loopback `/json/version` 返回的
精确 WebSocket 地址。文件缺失、端口或路径不合法、端点不一致、存在零个或多个浏览器上下文、登录
失效或 `expected_user_id` 不匹配都会失败关闭；不会扫描其他端口、回退默认 Profile 或新建会话。

## 7. 执行固定 Profile 的 20 次 smoke

`browser-check` 不访问 Automation Gateway，不注册 Worker、不 Claim，也不会创建 Attempt 或
ProfileLease。它按显式 `--profile-id` 选择一个本机绑定，连接既有 Chrome，在既有上下文中打开并探测
小红书页面，然后输出不含端口、WebSocket 地址、绝对路径、Cookie 或 storage state 的摘要。

从仓库根目录连续执行 20 次连接与探测：

```sh
uv run python -m workers.openclaw browser-check \
  --config /tmp/openclaw-worker.json \
  --profile-id '<本机绑定的 Profile UUID>' \
  --repeat 20
```

等价的 Make 入口为：

```sh
make openclaw-browser-check \
  OPENCLAW_WORKER_CONFIG=/tmp/openclaw-worker.json \
  OPENCLAW_BROWSER_PROFILE_ID='<本机绑定的 Profile UUID>'
```

20 次都应报告页面可控、已登录且账号匹配；任意一次失败时命令立即以非零状态退出。重复检查前后应仍
是同一个 Chrome 进程、同一个浏览器上下文和同一个账号，原有标签页数量恢复且没有标签页泄漏，并且
外部 Chrome/CDP 仍可连接；连接器会在每轮断开 Playwright 后重新核验同一 CDP 身份。不得产生新的
user-data-dir 或错误账号会话。

## 8. 注册、领取或运行

以下命令均从仓库根目录运行。`register` 创建或刷新 Worker 注册，并以配置中的完整能力列表覆盖该
Worker 的注册快照：

```sh
python -m workers.openclaw register --config /tmp/openclaw-worker.json
```

成功时输出 `status=REGISTERED` 的 JSON。示例的空能力配置已经足以让平台识别 Worker。
根目录的等价入口是
`make openclaw-worker OPENCLAW_WORKER_CONFIG=/tmp/openclaw-worker.json`，默认只执行安全的
`register`；可用 `OPENCLAW_WORKER_COMMAND=claim` 或 `poll` 显式选择领取模式。

`claim` 会先确保注册成功，再只发送一次 Claim 请求：

```sh
python -m workers.openclaw claim --config /tmp/openclaw-worker.json
```

领取成功时输出 `status=CLAIMED`；没有匹配任务的 `204` 响应输出 `status=IDLE` 并正常退出。

`poll` 会先确保注册成功，仅在 Gateway 明确返回 `204` 时按
`claim_poll_interval_seconds` 等待并重试，直到领取一项任务或耗尽轮询等待预算：

```sh
python -m workers.openclaw poll \
  --config /tmp/openclaw-worker.json \
  --timeout 180
```

等待预算在已完成的请求之间检查；在途请求仍由 `request_timeout_seconds` 单独约束，因为取消一个已经
发出的 Claim 可能丢失唯一一次返回的租约令牌。超时、配置错误、Gateway 错误或不确定的网络失败都会
输出 `status=FAILED` 的 JSON 到标准错误并以非零状态退出；客户端不会在不确定的 Claim 失败后盲目
重试。

`run` 会先注册，再串行领取并按精确 capability/version 分派
`xiaohongshu.check_login@1.0`、`xiaohongshu.search_notes@1.0` 或
`xiaohongshu.collect_note_detail@0.1`、`xiaohongshu.collect_comments@0.1`、三个稳定采集新版本，以及
只读 `xiaohongshu.publisher_login_check@1.0` 和受限
`xiaohongshu.publisher_image_upload@1.0`、`xiaohongshu.publisher_form_fill@1.0`、
`xiaohongshu.publisher_draft_save@1.0`，以及显式只读
`metrics.collect@1.0`。
旧版本和显式 Agent 任务使用 `AGENT_REQUIRED`；新版本的 `DETERMINISTIC_FIRST` Job 只有在 Gateway
提供同 Job、当前 Attempt 的有效 `runner_fallback@1.0` 上下文后才会被 OpenClaw 领取。认证失效、
验证码、风控和基础设施错误不会触发 fallback，切换后也不会回到 Playwright。常驻运行使用：

```sh
python -m workers.openclaw run --config /tmp/openclaw-worker.json
```

验收时最多处理一个任务并设置 180 秒领取等待预算：

```sh
python -m workers.openclaw run \
  --config /tmp/openclaw-worker.json \
  --once \
  --timeout 180
```

Worker 会校验 Claim 与本机 machine/Profile/path 绑定，并连接唯一既有浏览器 Context。登录检查在
owned page 中检查 `/explore`，依次上报事件、敏感截图 Artifact、Profile 快照和 Result；退出登录、
验证码、风控、错账号、冲突或未知但可控页面进入 `WAITING_HUMAN`，`RESUME` 后复用同一 Attempt 和
页面重新检查。

创作账号核验优先复用精确匹配
`https://creator.xiaohongshu.com/publish/publish?source=official` 的唯一既有标签；缺少时，只有平台内
当前 PublishTask 的准备授权才能让共享确定性 Page Object 在同一固定 Profile 新建一个标签，精确打开该
完整官方 URL，回读路由后保留给后续准备 Job。OpenClaw 不访问不完整的 `/publish` 空页面，不拼接或推断
URL，也不在重复创作标签之间选择。共享确定性 Page Object 读取稳定账号标识并与 PublishTask 冻结
`account_ref` 精确比较；昵称、“我”菜单、头像或 URL 不能单独作为通过依据。该能力不登录、不切换账号、
不上传、不填写、不保存、不预览，也不发布。

图片上传要求 `AGENT_REQUIRED`、`max_attempts=1` 和当前 PREPARING PublishTask。共享确定性 Handler
必须先校验全部冻结源字节，再执行一次完整有序文件输入并回读缩略图数量、顺序和完成状态；同批次精确回放
只能零写入。该能力不删除、不重排、不填写、不预览、不保存、不发布，遇到任何账号、验证码、风控、页面、
超时或租约异常立即安全停止且不自动重试。

草稿保存还要求当前 PASS validation、逐任务用户审计和字面 `SAVE_DRAFT_ONLY` 授权。真实 Job 必须使用
`AGENT_REQUIRED/max_attempts=1`；共享 Handler 先核对账号、三图、标题/正文/标签和保存/最终发布控件
完全分离，才允许一次保存草稿点击。成功必须有可信保存状态/时间、保存后完整回读、全页遮罩截图和安全
DOM 摘要；同值回放只能零写入。最终发布控件始终不可操作，任何歧义、风控或回读变化立即停止且不重试。

指标采集只能领取显式 `AGENT_REQUIRED` 的 `metrics.collect@1.0`、`metrics.collect@1.1` 或
`metrics.collect@1.2` REAL Job。
v1.1 只增加冻结 ContentVersion 标题作为无 Token 的精确帖子搜索恢复上下文；只有规范 URL 落到 `/404`
时才允许搜索，并且必须按同一 `platform_post_id` 唯一匹配。OpenClaw Agent 仍只调用三项
Attempt bridge 工具，实际页面工作由共享确定性 Handler 完成；只允许导航、等待、有界滚动和 DOM 读取，
公开评论固定 `passive_only`。登录、账号/帖子错配、验证码、风控、页面歧义或租约丢失立即安全停止，且禁止
点赞、收藏、评论、关注、编辑、删除、保存或发布。

v1.2 只读访问创作服务平台的官方数据列表页，优先以冻结帖子 ID 唯一定位表格行；列表 DOM 不暴露 ID 时，
只允许用冻结的完整笔记标题做精确且唯一的行匹配。读取曝光、观看、点赞、评论、收藏、分享及数据更新时间；
列存在但数值不可见时保留 `null + NOT_VISIBLE`，不得填 0 或挪用其他列。不点击表格行、不进入详情、不点击
图表、导出、导航或任何发布控件。
`NATURAL` 保持正式业务时间；验收专用
`ACCELERATED_REAL_READ` 仅允许把逻辑 24H 门禁压缩为发布后至少 1,440 秒，并必须在 Result 中保留自然
计划时间、实际经过秒数和加速警告。该结果不得冒充自然 24H 指标或进入自然表现排名。

搜索执行严格拒绝绝对发布时间字段，按 `search → scroll → extract → finish` 上报事件与四张敏感截图，
输出真实可见公开卡片且固定 `query_window=null`。搜索中的登录失效、验证码和风控直接提交结构化、
不可重试的失败 Result，不进入原 Attempt 的人工恢复，也不承诺阻断页截图。上游完成独立登录恢复后
才能创建新的搜索 Job。`CANCEL` 会安全停止并提交取消 Result；首次终止信号会停止领取新任务，并让
当前 Attempt 安全收敛。

详情执行严格校验规范笔记 ID 和 URL 身份，按 `open_note → extract_detail → finish` 上报三张截图，
并在提取步骤上传安全有界的 `DOM_SNAPSHOT`。正文、时间原文和公开作者身份缺失或歧义时按页面变化
失败；成功输出的 `raw_snapshot_artifact_id` 同时属于 Result `evidence_refs`。

截图只通过 `evidence_refs` 关联，按敏感数据处理，不写入能力输出或日志。CDP、导航、超时和无可用
DOM 等基础设施故障按可重试失败上报，不进入人工接管。

## 9. 领取安全警告

`claim`、`poll` 和 `run` 都会真实创建 Attempt 与 Profile 租约，不是只读探测。`claim` 与 `poll` 保留
低层验收语义，领取后即退出，不会执行或主动释放租约；生产队列应使用 `run`。一次性 `lease_token`
只保存在进程内存且不会出现在日志或最终 JSON 中。不要记录、转储或复制租约令牌、账号 ID、带查询
参数的页面 URL、页面标题或 `resolved_resources` 中的临时凭据；不要为了让命令通过而声明尚未发布
的能力。

## 官方参考

- [OpenClaw Skills](https://github.com/openclaw/openclaw/blob/main/docs/tools/skills.md)
- [`openclaw agent` CLI](https://github.com/openclaw/openclaw/blob/main/docs/cli/agent.md)
