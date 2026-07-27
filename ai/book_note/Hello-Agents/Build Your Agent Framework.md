## 构建你的智能体框架

> 阅读资料：[《Hello-Agents》第七章 7.1：框架整体架构设计](https://datawhalechina.github.io/hello-agents/#/./chapter7/%E7%AC%AC%E4%B8%83%E7%AB%A0%20%E6%9E%84%E5%BB%BA%E4%BD%A0%E7%9A%84Agent%E6%A1%86%E6%9E%B6?id=_71-%e6%a1%86%e6%9e%b6%e6%95%b4%e4%bd%93%e6%9e%b6%e6%9e%84%e8%ae%be%e8%ae%a1)
>
> 阅读资料：[《Hello-Agents》第七章 7.2：HelloAgentsLLM 扩展](https://datawhalechina.github.io/hello-agents/#/./chapter7/%E7%AC%AC%E4%B8%83%E7%AB%A0%20%E6%9E%84%E5%BB%BA%E4%BD%A0%E7%9A%84Agent%E6%A1%86%E6%9E%B6?id=_72-helloagentsllm%e6%89%a9%e5%b1%95)
>
> 实践：沿着章节的演进路线升级同一个 `HelloAgentsLLM`，统一接入云端服务、vLLM 和 Ollama。

### 框架整体架构设计

#### 从使用框架转向设计框架

第四章通过手写代码理解 ReAct、Plan-and-Solve 和 Reflection，第六章则直接使用 AutoGen、AgentScope、CAMEL 和 LangGraph。进入第七章后，关注点从“如何调用框架”转向“一个框架为什么要这样组织”。

单个 Agent 只需要模型、提示词和执行循环；一个可复用框架还需要解决：

- 输入、输出和历史消息如何统一表示。
- 不同模型服务如何通过同一入口调用。
- Agent 范式如何共享公共能力。
- 工具如何注册、查找、执行和组合。
- 配置、异常和扩展点放在哪一层。

因此，自建框架的目标不是再写一套更长的 Agent 代码，而是把反复出现的机制整理成稳定边界。

#### 为什么还要自建框架

成熟框架功能丰富，但它们的目标是覆盖尽可能多的业务场景，不一定适合学习内部机制。

| 问题 | 对开发的影响 | 自建框架带来的价值 |
| --- | --- | --- |
| 抽象层过多 | 完成简单任务前，要先理解大量框架概念 | 只保留 Agent、Model、Message、Tool 等必要抽象 |
| API 迭代频繁 | 升级后接口变化，旧代码需要迁移 | 固定章节版本，让代码与学习内容对应 |
| 核心流程黑盒化 | 出错时难以判断问题位于提示词、模型还是框架 | 可以跟踪消息、模型调用和工具执行的完整路径 |
| 依赖复杂 | 安装体积大，容易与现有项目发生版本冲突 | 控制依赖数量，问题更容易定位 |

自建过程也完成了能力上的转变：

- 从会调用 Agent，进一步理解推理、工具调用和状态传递。
- 可以为金融、医疗、教育等领域加入自己的安全规则和工具。
- 可以控制模型请求、上下文长度、并发方式与资源消耗。
- 会实际处理接口抽象、模块解耦、配置和异常等工程问题。

这里的“自建”并不意味着取代成熟框架。HelloAgents 更像一个可拆解的教学框架：它优先保证代码透明和知识连贯，生产级框架则还要处理权限、租户隔离、持久化、分布式调度和完整的可观测性。

#### HelloAgents 的四个设计理念

**轻量且可读**

框架尽量减少重型依赖，并按章节逐步增加能力。遇到错误时，可以直接沿着自己的代码定位，而不是在多层封装中反复跳转。

轻量不等于把所有逻辑写在一个文件中，而是只保留必要抽象，同时保证模块职责清楚。

**基于标准 API**

HelloAgents 选择兼容 OpenAI 的消息和模型接口，不再额外发明一套模型协议。模型供应商只要提供兼容接口，通常就能通过 `api_key`、`base_url` 和 `model` 完成接入。

这一选择降低了迁移成本，但“接口兼容”不代表“能力完全一致”。不同模型对工具调用、结构化输出、流式响应和思考模式的支持仍可能不同，框架需要保留供应商差异的处理位置。

**渐进式演进**

每个阶段都保留可安装的历史版本，本节对应的体验版本为：

```bash
pip install "hello-agents==0.1.1"
```

要求 Python 3.10+。固定版本的意义是保证书中接口与本地代码一致，避免在学习过程中被最新版本的 API 变化打断。

学习时可以采用两条路径：

1. 先安装章节版本，快速理解框架对外提供什么能力。
2. 再跟随章节实现内部组件，通过测试检查自己的实现。

前者建立整体认识，后者回答“这个接口内部究竟做了什么”。

**“万物皆为工具”**

除 Agent 核心外，HelloAgents 计划把 Memory、RAG、MCP 等能力统一放进 Tool 体系。Agent 面对的仍然是同一种操作：根据任务选择能力，传入参数并读取结果。

这种设计的优点是：

- 减少需要学习的顶层概念。
- 复用工具注册、参数描述、执行和错误处理流程。
- 新能力可以通过新增工具接入，不必修改 Agent 主循环。

它也存在边界。计算器是一次调用即可完成的无状态工具，而 Memory 具有生命周期，RAG 涉及索引和检索策略，MCP 是通信协议，RL 更接近训练方法。教学框架可以先统一它们的调用入口；当系统变复杂后，仍可能需要为状态管理、资源释放、权限和可观测性设计专门接口。

我的理解是：“万物皆工具”适合统一 Agent 的使用视角，但不应抹掉各类能力在实现和生命周期上的差异。

#### 整体分层

HelloAgents 遵循“分层解耦、职责单一、接口统一”。应用层只依赖 Agent 的公共入口，具体 Agent 复用核心组件，并通过工具层扩展能力。

```mermaid
flowchart TB
    APP["应用层<br/>任务、交互与业务规则"] --> IMPL["Agent 实现层<br/>Simple、ReAct、Reflection、Plan-and-Solve"]
    IMPL --> CORE["核心框架层<br/>Agent、LLM、Message、Config、Exceptions"]
    IMPL --> TOOLS["工具系统层<br/>BaseTool、Registry、ToolChain、AsyncExecutor"]
    TOOLS --> BUILTIN["内置与扩展工具<br/>Calculator、Search、Memory、RAG、MCP"]
    CORE --> MODEL["模型服务<br/>OpenAI 兼容 API"]
```

目录蓝图如下：

```text
hello_agents/
├── core/
│   ├── agent.py              # Agent 基类
│   ├── llm.py                # 统一模型接口
│   ├── message.py            # 消息格式
│   ├── config.py             # 配置管理
│   └── exceptions.py         # 异常体系
├── agents/
│   ├── simple_agent.py
│   ├── react_agent.py
│   ├── reflection_agent.py
│   └── plan_solve_agent.py
└── tools/
    ├── base.py               # 工具公共接口
    ├── registry.py           # 工具注册与查找
    ├── chain.py              # 工具链
    ├── async_executor.py     # 异步执行
    └── builtin/
        ├── calculator.py
        └── search.py
```

| 层 | 主要职责 | 变化频率 |
| --- | --- | --- |
| `core` | 定义稳定数据结构、公共接口、配置和异常 | 应尽量稳定 |
| `agents` | 实现不同推理与执行范式 | 随新范式扩展 |
| `tools` | 为 Agent 提供外部能力 | 随业务快速扩展 |
| 应用层 | 组合 Agent、工具和业务规则 | 随具体项目变化 |

依赖方向比目录名称更重要：`core` 不应该反过来依赖某个具体 Agent；新增工具也不应要求修改 Agent 基类。只有保持依赖从上层实现指向下层接口，框架才真正具备可扩展性。

#### 一次任务如何穿过框架

7.1 只给出了架构蓝图，后续章节才会实现具体接口。按照这套分层，一次任务的预期流转过程是：

```mermaid
sequenceDiagram
    participant U as "应用"
    participant A as "具体 Agent"
    participant C as "核心组件"
    participant T as "工具系统"
    participant M as "模型服务"

    U->>A: "提交任务"
    A->>C: "构造消息并读取配置"
    A->>M: "通过统一 LLM 接口请求模型"
    M-->>A: "返回回复或工具调用意图"
    opt "需要外部能力"
        A->>T: "按名称查找并执行工具"
        T-->>A: "返回工具结果"
        A->>M: "携带工具结果继续生成"
        M-->>A: "返回最终回复"
    end
    A->>C: "更新消息历史"
    A-->>U: "返回统一结果"
```

核心层统一“数据长什么样”，Agent 层决定“任务怎么做”，工具层提供“还能做什么”，应用层规定“为什么做以及何时结束”。这四个问题分开后，替换模型、增加工具或新增 Agent 范式时，影响范围才可控。

#### 与前后章节的关系

```mermaid
flowchart LR
    C4["第四章<br/>手写经典 Agent 范式"] --> C7["第七章<br/>抽取公共接口并形成框架"]
    C6["第六章<br/>体验成熟框架"] --> C7
    C7 --> C8["第八章<br/>Memory 与 RAG"]
    C7 --> C9["第九章<br/>上下文工程"]
    C7 --> C10["第十章<br/>协议与工具扩展"]
```

第四章的独立实现提供算法原型，第六章展示成熟框架的组织方式，第七章再把两部分经验收敛为自己的公共底座。后续高级能力不必各自建立一套 Agent 循环，而是围绕已有的消息、模型和工具接口继续扩展。

### HelloAgentsLLM 扩展

7.2 将前面只支持一组 `model`、`api_key` 和 `base_url` 的模型客户端扩展为统一入口，目标包含三部分：

1. 处理不同云端模型服务的默认地址和环境变量。
2. 通过 OpenAI 兼容接口调用 vLLM 与 Ollama 本地服务。
3. 根据配置推断 provider，减少重复参数。

这三部分解决的是同一个问题：Agent 不应该关心模型部署在哪里。Agent 只提交 messages，`HelloAgentsLLM` 负责解析配置、创建客户端并统一返回结果。

这里不能再增加一套平行的模型客户端。后续实现 `Agent` 基类时，会直接从 `hello_agents.core.llm` 导入 `HelloAgentsLLM`；因此 7.2 应继续修改这个核心类，而不是新建一个只在本节使用的 Provider 子类。

```mermaid
flowchart LR
    APP["Agent / CLI"] --> LLM["HelloAgentsLLM"]
    LLM --> SELECT["确定 provider"]
    SELECT --> RESOLVE["解析 model、Key 和 base URL"]
    RESOLVE --> SDK["创建统一的 OpenAI SDK 客户端"]
    SDK --> CLOUD["云端兼容服务"]
    SDK --> VLLM["本地 vLLM<br/>127.0.0.1:8000/v1"]
    SDK --> OLLAMA["本地 Ollama<br/>127.0.0.1:11434/v1"]
```

#### 多提供商扩展

**先修正接口不一致**

附件中的父类构造函数是：

```python
def __init__(
    self,
    model=None,
    apiKey=None,
    baseUrl=None,
    timeout=None,
):
    ...
```

原文在非 ModelScope 分支中调用：

```python
super().__init__(
    model=model,
    api_key=api_key,
    base_url=base_url,
    provider=provider,
    **kwargs,
)
```

这段调用与实际父类接口不一致：

- 父类参数名是 `apiKey` 和 `baseUrl`，不是 `api_key` 和 `base_url`。
- 父类没有 `provider` 参数。
- 父类没有接收任意 `**kwargs`，传入 `temperature`、`max_tokens` 等字段同样会报错。
- 父类把 SDK 客户端保存在 `self.client`，原文 ModelScope 分支却写入 `self._client`，继承的 `think()` 无法读取。

因此，照抄这段代码会在模型请求前抛出 `TypeError`；ModelScope 分支即使完成初始化，调用 `think()` 时也会找不到客户端。

不过，本章的目标是持续完善框架，而不是长期保留旧父类、再叠加一个子类。实践代码直接把原来的 `HelloAgentsLLM` 升级为章节所需接口：

```python
class HelloAgentsLLM:
    def __init__(
        self,
        model=None,
        api_key=None,
        base_url=None,
        provider=None,
        temperature=0.7,
        max_tokens=None,
        timeout=None,
        **kwargs,
    ):
        ...
```

`provider`、配置解析、客户端创建和调用方法都收进同一个类，避免后续出现“Agent 使用基础类，示例却使用扩展类”的分叉。旧代码中的 `apiKey`、`baseUrl` 暂时作为兼容别名接收，新代码统一使用 `api_key`、`base_url`。

配置解析顺序为：

```text
构造参数
  → provider 专属环境变量
    → 通用 LLM_* 环境变量
      → 章节示例默认值
```

所有 provider 最终都通过 `_create_client()` 创建 `self._client`，同时保留旧代码使用的 `self.client` 兼容别名。流式接口 `think()` 返回生成器，非流式接口 `invoke()` 返回完整字符串，`stream_invoke()` 则作为后续框架组件使用的流式别名。完整实现见 [`hello_agents/core/llm.py`](./code/HelloAgents/hello_agents/core/llm.py)。

#### 本地模型调用

vLLM 和 Ollama 都能提供 OpenAI 兼容的 `/v1/chat/completions`，所以 Python 侧不需要编写两套请求代码。真正不同的是模型部署、资源调度和服务管理。

| 对比项 | vLLM 实践 | Ollama 实践 |
| --- | --- | --- |
| 模型 | `Qwen/Qwen1.5-0.5B-Chat` | `qwen3:0.6b` |
| 地址 | `http://127.0.0.1:8000/v1` | `http://127.0.0.1:11434/v1` |
| 模型来源 | 本地下载后上传到服务器 | `ollama pull` |
| 主要目标 | 精细控制 GPU 推理参数 | 快速下载、启动和管理模型 |
| Python 调用 | OpenAI SDK | 同一个 OpenAI SDK |
| API Key | 服务未鉴权时使用非空占位值 `EMPTY` | SDK 要求非空，Ollama 会忽略 `ollama` |

**vLLM 实际部署**

测试环境是 NVIDIA GeForce RTX 2080 Ti，驱动最高兼容 CUDA 12.4。直接安装最新版组合先后遇到了驱动、Tokenizer、BF16、CPU KV Cache 和 CUDA Graph 兼容问题，最后验证成功的版本和参数为：

```text
vLLM 0.7.3
Transformers 4.48.2
Tokenizers 0.21.0
Qwen/Qwen1.5-0.5B-Chat
FP16
最大上下文 4096
```

模型无法从服务器直接访问 Hugging Face，因此先在本地下载，再上传到：

```text
/mnt/data/models/Qwen1.5-0.5B-Chat
```

最终稳定启动命令：

```bash
HF_HUB_OFFLINE=1 \
TRANSFORMERS_OFFLINE=1 \
CUDA_VISIBLE_DEVICES=0 \
python -m vllm.entrypoints.openai.api_server \
  --model /mnt/data/models/Qwen1.5-0.5B-Chat \
  --served-model-name Qwen/Qwen1.5-0.5B-Chat \
  --dtype float16 \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.70 \
  --swap-space 0 \
  --enforce-eager \
  --max-num-seqs 16 \
  --host 0.0.0.0 \
  --port 8000
```

这些固定版本和参数是针对当前 2080 Ti 环境的兼容方案，不是所有 GPU 的通用最佳配置：

- 2080 Ti 不支持 BF16，所以使用 FP16。
- `--swap-space 0` 避开 CPU KV Cache 初始化错误。
- `--enforce-eager` 避开当前 Turing、XFormers 与 CUDA Graph 组合的问题。
- 上下文限制为 4096，以减少 KV Cache 显存占用。
- 离线变量阻止服务重新访问 Hugging Face。

启动完成后先检查服务端实际暴露的模型名：

```bash
curl http://127.0.0.1:8000/v1/models
```

客户端的 `model` 必须与 `--served-model-name` 一致。仅仅“模型文件已经加载”不能证明 Chat API 可用，还应实际请求 `/v1/chat/completions`。

**Ollama 实际部署**

Ollama 由 systemd 管理，本地服务默认监听 `127.0.0.1:11434`。模型通过以下命令拉取并验证：

```bash
ollama pull qwen3:0.6b
ollama run qwen3:0.6b
```

Ollama 原生聊天接口是 `/api/chat`；为了复用 `HelloAgentsLLM` 中的 OpenAI SDK，本次使用它提供的兼容地址：

```text
http://127.0.0.1:11434/v1
```

可以分别检查服务和模型：

```bash
curl http://127.0.0.1:11434/api/tags
ollama list
```

允许其他机器访问时可以设置 `OLLAMA_HOST=0.0.0.0:11434`，但未配置认证的端口不应直接暴露到公网；即使在局域网中，也应通过防火墙限制来源。

**使用同一份实践代码切换**

章节代码集中在 `code/HelloAgents/`：

```text
HelloAgents/
├── .env.example
├── hello_agents/
│   ├── __init__.py
│   └── core/
│       ├── __init__.py
│       ├── exceptions.py
│       └── llm.py
└── examples/
    ├── __init__.py
    └── llm_provider_demo.py
```

这个目录与 7.1 的框架蓝图一致。后续学习 Message、Agent 和工具系统时，可以继续在 `hello_agents/` 包内增加模块，不需要迁移本章代码。

安装客户端依赖：

```bash
python -m pip install openai python-dotenv
```

复制并填写本章环境变量：

```bash
cd code/HelloAgents
cp .env.example .env
```

调用已部署的 vLLM：

```bash
python -m examples.llm_provider_demo \
  --provider vllm \
  --prompt "请解释什么是 ReAct Agent。"
```

切换到 Ollama 时只改 provider：

```bash
python -m examples.llm_provider_demo \
  --provider ollama \
  --prompt "请解释什么是 ReAct Agent。"
```

CLI 没有提供 `--api-key` 参数，避免密钥进入终端历史。云端 Key 只从 `.env` 读取。完整入口见 [`examples/llm_provider_demo.py`](./code/HelloAgents/examples/llm_provider_demo.py)，配置模板见 [`.env.example`](./code/HelloAgents/.env.example)。

#### Provider 规则推断

原文的 `_auto_detect_provider()` 会检查环境变量、匹配域名和端口，最后再猜测 API Key 前缀。这里没有模型参与，也没有动态探索服务能力，本质上是按优先级执行 `if/elif` 规则。

称为“自动检测”容易掩盖它的局限：

- 同时存在多个云服务 Key 时，固定检查顺序会替用户做决定。
- `8000` 端口不一定是 vLLM，vLLM 也不一定运行在 `8000`。
- 代理地址可能不包含服务商域名。
- Key 前缀可能变化或被不同兼容服务复用。
- 推断成功只能说明规则命中，不能证明地址可访问、模型存在或接口兼容。

实践代码保留章节中的 `_auto_detect_provider()` 名称，以便和后续代码衔接；它内部调用 `_infer_provider_by_rules()`，明确说明这只是确定性规则。选择顺序为：

```text
构造参数 provider
  → .env 中的 LLM_PROVIDER
    → auto 规则推断
```

日常使用仍建议显式填写 `provider` 或 `LLM_PROVIDER`，根据成本、隐私、模型能力和服务状态主动切换，而不是让环境中恰好存在的变量决定调用目标。

只有选择 `provider="auto"` 时才会执行规则推断：

- 先根据实际 `base_url` 的主机和端口匹配。
- 环境中出现多个候选 provider 时直接报错，要求显式选择。
- 不通过 API Key 格式猜测服务商。
- 无法识别的 OpenAI 兼容地址按 `custom` 处理。

规则推断可以减少本地演示的配置量，但显式配置更适合生产环境，因为配置文件和启动命令能够直接说明请求将被发往哪里。

### 参考资料

- [《Hello-Agents》第七章：构建你的智能体框架](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter7/%E7%AC%AC%E4%B8%83%E7%AB%A0%20%E6%9E%84%E5%BB%BA%E4%BD%A0%E7%9A%84Agent%E6%A1%86%E6%9E%B6.md)
- [HelloAgents `learn_version`：`core/llm.py`](https://github.com/jjyaoao/HelloAgents/blob/learn_version/hello_agents/core/llm.py)
- [vLLM OpenAI-Compatible Server](https://docs.vllm.ai/en/latest/serving/online_serving/openai_compatible_server/)
- [Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility)
- [Ollama `qwen3:0.6b`](https://ollama.com/library/qwen3:0.6b)

### 小结

- 自建框架的价值在于透明、可控和可扩展，设计时应先确定模块职责与依赖方向。
- 核心接口保持稳定，具体 Agent 和工具才能独立扩展。
- “万物皆工具”统一了调用方式，但不能忽略 Memory、RAG 和协议组件的状态与生命周期。
- HelloAgentsLLM 隔离了 Agent 与模型部署细节，云端服务、vLLM 和 Ollama 可以复用同一调用入口。
- 实践代码应持续升级 `hello_agents.core.llm.HelloAgentsLLM`，避免为单节内容建立平行实现。
- 示例代码必须核对真实的构造函数签名；框架演进时，再有计划地扩展接口并兼容旧参数。
- Provider 自动检测只是确定性规则匹配；显式选择比隐式推断更容易排查和复现。
