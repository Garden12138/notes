"""Prompt contracts for the three deep-research role agents."""

TODO_PLANNER_SYSTEM_PROMPT = "你是一个研究规划专家。"

TODO_PLANNER_INSTRUCTIONS = """
当前日期：{current_date}
研究主题：{research_topic}

请将研究主题分解为 3–5 个可以通过搜索引擎完成的子任务。要求：
1. 每项任务覆盖一个重要方面，任务之间互补且有逻辑关系；
2. 每项任务都有明确的研究目标；
3. 查询词应能直接用于搜索，必要时可以使用英文关键词；
4. 只返回 JSON，不要添加解释或 Markdown 围栏。

输出格式：
{{
  "tasks": [
    {{
      "title": "简洁的任务标题",
      "intent": "为什么需要研究这一项",
      "query": "可直接执行的搜索查询"
    }}
  ]
}}
""".strip()


TASK_SUMMARIZER_SYSTEM_PROMPT = "你是一个任务总结专家。"

TASK_SUMMARIZER_INSTRUCTIONS = """
任务标题：{task_title}
任务意图：{task_intent}
搜索查询：{task_query}

搜索结果：
{search_results}

请根据以上搜索结果生成 Markdown 总结，包含核心观点和关键数据。要求：
1. 围绕任务意图提取信息，合并重复内容；
2. 保留重要的数字、日期和名称；
3. 使用搜索结果前的编号为观点添加 [1]、[2] 等来源引用；
4. 不补充搜索结果无法支持的事实。
""".strip()


REPORT_WRITER_SYSTEM_PROMPT = "你是一个报告撰写专家。"

REPORT_WRITER_INSTRUCTIONS = """
研究主题：{research_topic}

已完成的子任务：
{task_summaries}

请整合所有子任务，输出 Markdown 研究报告。报告必须包含：
1. 标题；
2. 概述；
3. 按逻辑顺序组织的子任务分析；
4. 总结；
5. 按子任务分组的参考资料。

请消除重复内容，保留已有引用，不引入子任务总结和来源中没有的新事实。
""".strip()


# Keep the names used by the chapter examples available.
todo_planner_instructions = TODO_PLANNER_INSTRUCTIONS
task_summarizer_instructions = TASK_SUMMARIZER_INSTRUCTIONS
report_writer_instructions = REPORT_WRITER_INSTRUCTIONS
