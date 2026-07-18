import asyncio
import os

from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient


# 加载当前目录下的 .env 文件
load_dotenv()


def create_openai_model_client() -> OpenAIChatCompletionClient:
    """
    创建并配置 OpenAI 兼容模型客户端。

    环境变量：
    - LLM_MODEL_ID：模型名称
    - LLM_API_KEY：API Key
    - LLM_BASE_URL：OpenAI 兼容接口地址
    """

    # 注意：下面三行末尾不能加逗号。
    # 加逗号后变量会变成 tuple，例如 ('gpt-5.6-luna',)
    model = os.getenv("LLM_MODEL_ID", "gpt-4o").strip()
    api_key = os.getenv("LLM_API_KEY", "").strip()
    base_url = "https://api.gptsapi.net/v1"

    # 检查必要配置
    if not model:
        raise ValueError(
            "没有配置模型名称，请在 .env 中设置 LLM_MODEL_ID。"
        )

    if not api_key:
        raise ValueError(
            "没有读取到 API Key，请在 .env 中设置 LLM_API_KEY。"
        )

    if not base_url:
        raise ValueError(
            "没有配置接口地址，请在 .env 中设置 LLM_BASE_URL。"
        )

    # 输出配置信息，但不打印完整 API Key
    masked_api_key = (
        f"{api_key[:6]}...{api_key[-4:]}"
        if len(api_key) >= 10
        else "已配置"
    )

    print("模型客户端配置：")
    print(f"  model    = {model}")
    print(f"  base_url = {base_url}")
    print(f"  api_key  = {masked_api_key}")

    # gpt-5.6-luna 属于自定义模型名称，AutoGen 无法自动判断模型能力，
    # 因此需要通过 model_info 手动声明。
    return OpenAIChatCompletionClient(
        model=model,
        api_key=api_key,
        base_url=base_url,
        model_info={
            # 当前任务只处理文本，不处理图片
            "vision": False,

            # 当前没有给智能体配置工具，可以先关闭函数调用
            "function_calling": False,

            # 当前不要求模型返回 JSON
            "json_output": False,

            # 自定义模型使用 unknown
            "family": "unknown",

            # 当前不使用 Pydantic 等结构化输出
            "structured_output": False,
        },
    )


def create_product_manager(
    model_client: OpenAIChatCompletionClient,
) -> AssistantAgent:
    """创建产品经理智能体。"""

    system_message = """
你是一位经验丰富的产品经理，负责软件产品的需求分析和项目规划。

你的核心职责包括：

1. 需求分析
   - 理解用户的真实需求
   - 明确核心功能
   - 识别边界条件和非功能性要求

2. 功能规划
   - 将需求拆分为清晰的功能模块
   - 确定各模块之间的关系
   - 划定本次开发范围

3. 技术规划
   - 根据需求提出合理的技术实现建议
   - 说明关键技术选择的原因
   - 提醒工程师注意接口和数据处理问题

4. 风险评估
   - 识别技术风险
   - 识别第三方接口风险
   - 识别用户体验问题

5. 验收标准
   - 给出清晰、可验证的验收条件

当第一次收到开发任务时，请按以下结构输出：

一、需求理解
二、功能模块
三、技术方案
四、实现优先级
五、风险与异常情况
六、验收标准

完成需求分析后，请在最后明确说：

请工程师开始实现

当团队后续提出修改意见时，请根据当前讨论协调后续工作，
不要重复输出完全相同的初始需求分析。
""".strip()

    return AssistantAgent(
        name="ProductManager",
        description="负责需求分析、功能规划、技术协调和验收标准定义。",
        model_client=model_client,
        system_message=system_message,
    )


def create_engineer(
    model_client: OpenAIChatCompletionClient,
) -> AssistantAgent:
    """创建软件工程师智能体。"""

    system_message = """
你是一位资深软件工程师，擅长 Python 开发和 Web 应用构建。

你的技术专长包括：

1. Python 编程
   - 熟练掌握 Python 语法
   - 遵循 Python 最佳实践
   - 注重类型、命名和代码结构

2. Web 开发
   - 熟悉 Streamlit、Flask 和 Django
   - 能够设计简洁、易用的页面
   - 能够管理页面状态和刷新逻辑

3. API 集成
   - 熟悉 HTTP API 调用
   - 能够处理超时、限流和错误响应
   - 能够校验接口返回的数据

4. 健壮性
   - 重视异常处理
   - 重视输入和响应数据校验
   - 避免程序因为第三方接口异常而直接崩溃

收到开发任务后，请：

1. 阅读产品经理的需求分析
2. 选择适合的实现方案
3. 提供完整、可运行的代码
4. 给出项目依赖安装命令
5. 给出代码文件名称
6. 给出启动和运行命令
7. 添加必要的中文代码注释
8. 处理网络超时、接口失败和异常数据
9. 不要只给伪代码或代码片段

所有代码必须放在 Markdown 代码块中。

完成后，请在最后明确说：

请代码审查员检查
""".strip()

    return AssistantAgent(
        name="Engineer",
        description="负责完成软件设计、代码实现、依赖说明和运行说明。",
        model_client=model_client,
        system_message=system_message,
    )


def create_code_reviewer(
    model_client: OpenAIChatCompletionClient,
) -> AssistantAgent:
    """创建代码审查员智能体。"""

    system_message = """
你是一位经验丰富的代码审查专家，负责检查工程师提交的代码。

你的审查重点包括：

1. 完整性
   - 是否满足产品经理提出的全部需求
   - 是否提供完整可运行代码
   - 是否提供安装和运行命令

2. 正确性
   - 检查导入、变量、函数和调用逻辑
   - 检查 API 请求和数据解析逻辑
   - 检查 Streamlit 的刷新和状态管理逻辑

3. 代码质量
   - 检查代码可读性
   - 检查函数划分
   - 检查命名和注释
   - 检查是否存在重复代码

4. 健壮性
   - 检查网络超时
   - 检查 HTTP 状态码
   - 检查 JSON 字段缺失
   - 检查第三方接口不可用时的处理

5. 安全性
   - 检查是否硬编码密钥
   - 检查是否暴露敏感信息
   - 检查用户输入是否会造成风险

请按照以下结构输出：

一、审查结论
二、发现的问题
三、必须修改项
四、建议优化项
五、修改后的关键方案

即使代码没有严重问题，也必须明确说明检查了哪些内容。

最后明确说：

代码审查完成，请测试工程师验证
""".strip()

    return AssistantAgent(
        name="CodeReviewer",
        description="负责检查代码正确性、完整性、安全性和可维护性。",
        model_client=model_client,
        system_message=system_message,
    )


def create_test_engineer(
    model_client: OpenAIChatCompletionClient,
) -> AssistantAgent:
    """
    创建测试工程师智能体。

    这里没有使用 UserProxyAgent，因为 UserProxyAgent 默认需要真实用户
    在终端输入内容，并不会自动调用模型分析代码。
    """

    system_message = """
你是一位软件测试工程师，负责从用户视角验证当前开发结果。

请根据产品经理的验收标准、工程师提供的代码和代码审查员的意见，
完成静态测试与逻辑验证。

重点检查：

1. 需求覆盖
   - 是否显示比特币当前美元价格
   - 是否显示24小时涨跌额
   - 是否显示24小时涨跌幅
   - 是否支持手动刷新

2. 可运行性
   - 依赖是否完整
   - 导入是否正确
   - 启动命令是否正确
   - 代码是否存在明显语法错误

3. 异常处理
   - 网络请求失败时是否有友好提示
   - 请求超时时是否有处理
   - API 返回字段缺失时是否有处理
   - 页面是否会因为异常直接崩溃

4. 用户体验
   - 页面结构是否清晰
   - 加载状态是否明确
   - 价格和涨跌信息是否容易理解

请按照以下结构输出：

一、测试范围
二、测试结果
三、发现的问题
四、验收结论

终止规则：

- 如果实现满足核心需求，并且没有阻塞运行的严重问题，
  请在最后单独输出：

TERMINATE

- 如果存在严重问题，不要输出 TERMINATE。
  请明确列出问题，并在最后输出：

测试未通过，请工程师修复
""".strip()

    return AssistantAgent(
        name="TestEngineer",
        description="负责验证代码是否满足需求，并决定是否结束团队协作。",
        model_client=model_client,
        system_message=system_message,
    )


async def run_software_development_team():
    """创建并运行软件开发智能体团队。"""

    task = """
我们需要开发一个比特币价格显示应用。

核心功能：

1. 实时显示比特币当前价格，计价货币为 USD。
2. 显示比特币24小时价格变化：
   - 24小时涨跌额
   - 24小时涨跌幅
3. 提供手动刷新价格的功能。

技术要求：

1. 使用 Streamlit 创建 Web 应用。
2. 界面简洁、清晰、用户友好。
3. 显示数据加载状态。
4. 添加合理的网络请求超时。
5. 添加第三方 API 请求失败时的错误处理。
6. 不得在代码中硬编码 API Key。
7. 优先选择无需 API Key 的公开比特币价格接口。
8. 提供完整、可以复制运行的代码。
9. 提供 requirements.txt 内容。
10. 提供安装依赖和启动应用的命令。

请团队按照以下流程协作完成任务：

产品经理分析需求
→ 工程师实现
→ 代码审查员审查
→ 测试工程师验证

代码存在问题时，应根据审查和测试意见继续修改；
测试通过后输出 TERMINATE。
""".strip()

    model_client = create_openai_model_client()

    try:
        # 创建智能体
        product_manager = create_product_manager(model_client)
        engineer = create_engineer(model_client)
        code_reviewer = create_code_reviewer(model_client)
        test_engineer = create_test_engineer(model_client)

        # 只检查 TestEngineer 的回复。
        # 即使用户任务或其他智能体提到 TERMINATE，也不会提前终止。
        termination_condition = TextMentionTermination(
            text="TERMINATE",
            sources=["TestEngineer"],
        )

        # 创建轮询式多智能体团队
        team_chat = RoundRobinGroupChat(
            participants=[
                product_manager,
                engineer,
                code_reviewer,
                test_engineer,
            ],
            termination_condition=termination_condition,
            max_turns=20,
        )

        print("\n" + "=" * 70)
        print("开始运行软件开发多智能体团队")
        print("=" * 70 + "\n")

        # 流式输出智能体之间的对话
        result = await Console(
            team_chat.run_stream(task=task),
            output_stats=True,
        )

        return result

    finally:
        # 无论程序正常结束还是发生异常，都关闭 HTTP 客户端连接
        await model_client.close()
        print("\n模型客户端已关闭。")


def main():
    """程序入口函数。"""

    try:
        result = asyncio.run(run_software_development_team())

        print("\n" + "=" * 70)
        print("团队任务执行结束")
        print("=" * 70)

        # Console 已经输出完整过程，这里只输出最终停止原因
        stop_reason = getattr(result, "stop_reason", None)

        if stop_reason:
            print(f"停止原因：{stop_reason}")

    except KeyboardInterrupt:
        print("\n用户手动终止程序。")

    except Exception as error:
        print("\n程序运行失败：")
        print(f"{type(error).__name__}: {error}")

        # 在开发调试阶段重新抛出异常，方便看到完整调用栈
        raise


if __name__ == "__main__":
    main()
