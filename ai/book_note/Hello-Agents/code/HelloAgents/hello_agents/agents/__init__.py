"""Concrete Agent paradigms built on the shared Agent interface."""

from .function_call_agent import FunctionCallAgent
from .plan_solve_agent import Executor, PlanAndSolveAgent, Planner
from .react_agent import ReActAgent
from .reflection_agent import Memory, ReflectionAgent
from .simple_agent import SimpleAgent
from .tool_aware_simple_agent import ToolAwareSimpleAgent, ToolCallInfo

__all__ = [
    "Executor",
    "FunctionCallAgent",
    "Memory",
    "PlanAndSolveAgent",
    "Planner",
    "ReActAgent",
    "ReflectionAgent",
    "SimpleAgent",
    "ToolAwareSimpleAgent",
    "ToolCallInfo",
]
