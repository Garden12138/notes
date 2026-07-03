## 使用 vibe coding 构建 Worklog Desktop

### 背景

* ```Worklog Desktop``` 是一个本地桌面工作记录与报告应用，用来记录每日工作、生成周报/月报/绩效考核表草稿，并支持 AI 优化、DOCX 导出、邮件投递和定时生成。

* 这个项目也很适合作为 ```vibe coding``` 项目复盘：它从一个非常个人化、非常具体的需求出发，把“我想少花时间写工作总结”变成了一个能在本机长期运行的桌面应用。

### 项目定位

* ```Worklog 2.0``` 使用 ```Tauri 2```、```Rust```、```React``` 和 ```SQLite``` 构建。安装后不依赖 Python、Node.js 或后台 HTTP 服务，数据保存在本机应用数据目录。

* 它的目标不是做一个云端协同系统，而是做一个本地优先的个人工作台：

  * 每日记录工作事项、进展、结果、阻塞、工时和优先级。
  * 基于记录生成周报、月报和绩效考核表。
  * 使用 LLM 优化报告内容或从示例生成模板。
  * 导出 DOCX，并通过 SMTP 发送给固定收件人。
  * 关闭主窗口后驻留系统托盘，继续执行定时报告任务。

### 功能链路

* 一个完整的使用链路可以理解为：

  ```text
  记录每日工作
    -> 选择报告类型和时间周期
    -> 选择 Markdown + Jinja 风格模板
    -> 生成报告草稿
    -> 手动编辑或 AI 优化
    -> 导出 DOCX / 邮件发送
    -> 配置定时报告后自动生成和可选自动发送
  ```

* 这个链路把“写日报/周报”拆成了几个更小的动作：结构化记录、模板渲染、AI 改写、文档导出、邮件投递。vibe coding 在这里的作用，是让这些原本分散的小工具快速整合到一个桌面产品里。

### 技术栈

* 桌面壳：

  * ```Tauri 2``` 负责窗口、系统托盘、单实例、自动启动和原生能力。
  * ```Rust``` 承担本地业务逻辑、SQLite 访问、定时任务、邮件发送、DOCX 生成和密钥管理。

* 前端：

  * ```React``` + ```Vite``` 构建用户界面。
  * ```lucide-react``` 提供侧边栏、按钮和状态图标。
  * 通过 ```@tauri-apps/api/core``` 的 ```invoke``` 调用 Rust command。

* 本地能力：

  * ```sqlx``` 操作 SQLite。
  * ```minijinja``` 渲染报告模板。
  * ```reqwest``` 调用 OpenAI-compatible LLM Provider。
  * ```lettre``` 发送 SMTP 邮件。
  * ```docx-rs``` 导出 Word 文档。
  * ```keyring``` 把 LLM API Key 和 SMTP 密码保存到 macOS Keychain 或 Windows Credential Manager。

### 模块拆解

* Rust 侧主要模块：

  * ```commands.rs```：Tauri command 层，暴露工作记录、模板、报告、邮件、LLM 设置和定时配置等操作。
  * ```db.rs```：SQLite 初始化、迁移和旧版数据库导入。
  * ```reports.rs```：报告周期计算、草稿生成和 AI 优化。
  * ```templates.rs```：模板校验、示例导入和模板优化。
  * ```documents.rs```：DOCX 导出。
  * ```mail.rs```：SMTP 测试和报告邮件发送。
  * ```scheduler.rs```：周报、月报、绩效考核表的定时生成与补生成。
  * ```secrets.rs```：系统密钥存储和旧明文配置迁移。

* React 侧主要页面：

  * 每日记录：分页浏览、创建、更新和删除工作记录。
  * 报告草稿：生成、编辑、优化、导出和发送。
  * 模板管理：维护周报、月报、绩效考核表模板。
  * 系统设置：配置 LLM、SMTP、收件人、定时报告、开机启动和旧数据库导入。

### vibe coding 的关键点

* 第一个关键点是需求非常贴近自己的日常流程。vibe coding 适合从真实痛点开始，而不是先设计一个宏大的平台。```Worklog``` 的核心价值很清晰：让每天的小记录变成可复用的数据，让周期性报告自动生成。

* 第二个关键点是把 AI 放在“优化表达”和“生成模板”的位置，而不是让 AI 接管整个系统。工作记录、报告周期、定时任务、邮件投递、密钥保存这些部分都由确定性的本地代码处理，AI 只负责它更擅长的文本生成和改写。

* 第三个关键点是本地优先。工作日志、绩效材料、邮箱配置和 API Key 都比较敏感，所以桌面应用比云端服务更合适。Rust + SQLite + Keychain/Credential Manager 让这个项目在快速迭代之外，也保留了安全和可维护性。

### 运行与测试

* 开发环境：

  ```text
  Node.js 22
  Rust stable 1.85+
  macOS: Xcode Command Line Tools
  Windows: Microsoft C++ Build Tools 与 WebView2
  ```

* 安装前端依赖：

  ```bash
  npm --prefix frontend install
  ```

* 启动桌面开发模式：

  ```bash
  npm run desktop:dev
  ```

* 测试：

  ```bash
  cargo fmt --manifest-path src-tauri/Cargo.toml -- --check
  cargo clippy --manifest-path src-tauri/Cargo.toml --all-targets -- -D warnings
  cargo test --manifest-path src-tauri/Cargo.toml
  npm --prefix frontend run build
  ```

* 打包：

  ```bash
  npm run desktop:build
  ```

### 适合继续迭代的方向

* 增加更多报告模板预设，例如 OKR、项目复盘、客户周报、研发周报等。
* 对工作记录增加更强的筛选和统计，例如按项目、优先级、阻塞类型和投入时间聚合。
* 让 AI 生成报告前先做缺失信息检查，提醒哪些工作记录不够完整。
* 增加本地备份和导入导出能力，方便跨设备迁移。
* 支持更多投递渠道，例如企业微信、飞书、钉钉或自定义 webhook。

### 总结

* ```Worklog Desktop``` 展示了 vibe coding 的另一种形态：不是只做一个 demo，而是把个人工作流沉淀成真正可安装、可驻留、可定时执行的桌面软件。它的启发是，AI 帮我们把想法快速变成界面和能力，但产品能不能稳定陪伴日常使用，仍然取决于数据模型、原生集成、安全边界和那些看起来不酷但很实用的细节。

### 参考文献

* [Garden12138/worklog](https://github.com/Garden12138/worklog)
* [Tauri](https://tauri.app/)
