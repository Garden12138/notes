import re

from llm import HelloAgentsLLM
from tool_executor import ToolExecutor


REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下:
{tools}

请严格按照以下格式进行回应:

Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动。
Action: 你决定采取的行动，必须是以下格式之一:
- `{{tool_name}}[{{tool_input}}]`: 调用一个可用工具。
- `Finish[最终答案]`: 当你认为已经获得最终答案时。

重要规则:
1. 每一轮只能输出一组 Thought 和 Action。
2. Action 必须是本轮回复的最后一段。
3. 如果 Action 是工具调用，调用后必须等待 Observation，不要在同一轮继续输出第二个 Thought 或 Finish。
4. 不要自己编造 Observation。
5. 当 History 中已经有足够 Observation 可以回答问题时，才使用 Finish[最终答案]。

现在，请开始解决以下问题:
Question: {question}
History: {history}
""".strip()


class ReActAgent:
    def __init__(self, llm_client: HelloAgentsLLM, tool_executor: ToolExecutor, max_steps: int = 5):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.history = []

    def _parse_output(self, text: str):
        """解析 LLM 输出，提取第一个 Thought 和第一个 Action。

        这里故意只取“第一个 Action”，因为 ReAct 的标准流程是：
        LLM 每轮只能决定一个动作；工具执行后，再进入下一轮。
        即使模型一次性输出多个 Action，也只执行第一个，避免工具输入被污染。
        """
        thought_match = re.search(r"Thought:\s*(.*?)(?=\s*Action:|$)", text, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else None

        # 提取第一个完整 Action：tool[input] 或 Finish[answer]
        # (?=\s*(Thought:|Action:|$)) 用来防止模型一次输出多个 Thought/Action 时被贪婪吃掉。
        action_match = re.search(
            r"Action:\s*((?:Finish|[A-Za-z_]\w*)\[[\s\S]*?\])(?=\s*(?:Thought:|Action:|$))",
            text,
        )
        action = action_match.group(1).strip() if action_match else None
        return thought, action

    def _parse_action(self, action_text: str):
        """解析 Action 字符串，提取工具名称和输入。"""
        match = re.fullmatch(r"([A-Za-z_]\w*)\[([\s\S]*)\]", action_text.strip())
        if match:
            return match.group(1), match.group(2).strip()
        return None, None

    def _parse_finish(self, action_text: str):
        """解析 Finish[最终答案]，支持多行最终答案。"""
        match = re.fullmatch(r"Finish\[([\s\S]*)\]", action_text.strip())
        if match:
            return match.group(1).strip()
        return None

    def run(self, question: str):
        """运行 ReAct 智能体来回答一个问题。"""
        self.history = []

        for current_step in range(1, self.max_steps + 1):
            print(f"--- 第 {current_step} 步 ---")

            tools_desc = self.tool_executor.getAvailableTools()
            history_str = "\n".join(self.history)
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools=tools_desc,
                question=question,
                history=history_str,
            )

            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm_client.think(messages=messages)

            if not response_text:
                print("错误: LLM 未能返回有效响应。")
                break

            thought, action = self._parse_output(response_text)

            if thought:
                print(f"思考: {thought}")
                self.history.append(f"Thought: {thought}")

            if not action:
                print("警告: 未能解析出有效的 Action，流程终止。")
                self.history.append(f"InvalidResponse: {response_text}")
                break

            if action.startswith("Finish"):
                final_answer = self._parse_finish(action)
                if final_answer is None:
                    print(f"警告: Finish 格式无效: {action}")
                    self.history.append(f"InvalidFinish: {action}")
                    break
                print(f"🎉 最终答案: {final_answer}")
                return final_answer

            tool_name, tool_input = self._parse_action(action)
            if not tool_name:
                observation = f"错误: 无效的 Action 格式: {action}"
                print(f"👀 观察: {observation}")
                self.history.append(f"Action: {action}")
                self.history.append(f"Observation: {observation}")
                continue

            print(f"🎬 行动: {tool_name}[{tool_input}]")

            tool_function = self.tool_executor.getTool(tool_name)
            if not tool_function:
                observation = f"错误: 未找到名为 '{tool_name}' 的工具。"
            else:
                try:
                    observation = tool_function(tool_input)
                except Exception as exc:
                    observation = f"工具 '{tool_name}' 执行异常: {exc}"

            print(f"👀 观察: {observation}")

            self.history.append(f"Action: {action}")
            self.history.append(f"Observation: {observation}")

        print("已达到最大步数，流程终止。")
        return None
