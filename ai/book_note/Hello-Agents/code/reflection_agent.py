from llm import HelloAgentsLLM
from memory import Memory


class ReflectionAgent:
    def __init__(
        self,
        llm_client: HelloAgentsLLM,
        initial_prompt_template: str,
        reflect_prompt_template: str,
        refine_prompt_template: str,
        max_iterations=3,
    ):
        self.llm_client = llm_client
        self.memory = Memory()
        self.max_iterations = max_iterations
        self.INITIAL_PROMPT_TEMPLATE = initial_prompt_template
        self.REFLECT_PROMPT_TEMPLATE = reflect_prompt_template
        self.REFINE_PROMPT_TEMPLATE = refine_prompt_template

    def run(self, task: str):
        print(f"\n--- 开始处理任务 ---\n任务: {task}")

        # --- 1. 初始执行 ---
        print("\n--- 正在进行初始尝试 ---")
        initial_prompt = self.INITIAL_PROMPT_TEMPLATE.format(task=task)
        initial_execution = self._get_llm_response(initial_prompt)
        self.memory.add_record("execution", initial_execution)

        # --- 2. 迭代循环:反思与优化 ---
        for i in range(self.max_iterations):
            print(f"\n--- 第 {i+1}/{self.max_iterations} 轮迭代 ---")

            # a. 反思
            print("\n-> 正在进行反思...")
            last_execution = self.memory.get_last_execution()
            reflect_prompt = self.REFLECT_PROMPT_TEMPLATE.format(task=task, last_execution=last_execution)
            feedback = self._get_llm_response(reflect_prompt)
            self.memory.add_record("reflection", feedback)

            # b. 检查是否需要停止
            normalized_feedback = feedback.strip().rstrip(
                "。！？!?；;，,.…"
            ).strip()
            if normalized_feedback == "无需改进":
                print("\n✅ 反思认为已无需改进，任务完成。")
                break

            # c. 优化
            print("\n-> 正在进行优化...")
            refine_prompt = self.REFINE_PROMPT_TEMPLATE.format(
                task=task,
                last_execution=last_execution,
                feedback=feedback
            )
            refined_execution = self._get_llm_response(refine_prompt)
            self.memory.add_record("execution", refined_execution)

        final_execution = self.memory.get_last_execution()
        print(f"\n--- 任务完成 ---\n最终生成的结果:\n```python\n{final_execution}\n```")
        return final_execution

    def _get_llm_response(self, prompt: str) -> str:
        """一个辅助方法，用于调用LLM并获取完整的流式响应。"""
        messages = [{"role": "user", "content": prompt}]
        response_text = self.llm_client.think(messages=messages) or ""
        return response_text
