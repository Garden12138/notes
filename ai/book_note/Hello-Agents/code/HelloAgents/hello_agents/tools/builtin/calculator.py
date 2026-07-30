"""Safe arithmetic evaluator used by the calculator examples."""

from __future__ import annotations

import ast
import math
import operator
from typing import Any, Callable

from ..base import Tool, ToolParameter
from ..registry import ToolRegistry


BinaryOperator = Callable[[float, float], float]

_OPERATORS: dict[type[ast.operator], BinaryOperator] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_FUNCTIONS: dict[str, Callable[..., float]] = {
    "sqrt": math.sqrt,
}
_CONSTANTS = {
    "pi": math.pi,
}
_MAX_EXPRESSION_LENGTH = 200


def _eval_node(node: ast.AST) -> float | int:
    """Evaluate only the AST nodes supported by chapter 7.5."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(
            node.value,
            (int, float),
        ):
            raise ValueError("只允许数字常量")
        return node.value

    if isinstance(node, ast.BinOp):
        operation = _OPERATORS.get(type(node.op))
        if operation is None:
            raise ValueError("只支持 +、-、*、/ 四种运算")
        return operation(_eval_node(node.left), _eval_node(node.right))

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("不允许属性或链式函数调用")
        function = _FUNCTIONS.get(node.func.id)
        if function is None:
            raise ValueError(f"不支持函数：{node.func.id}")
        if node.keywords:
            raise ValueError("不支持关键字参数")
        arguments = [_eval_node(argument) for argument in node.args]
        return function(*arguments)

    if isinstance(node, ast.Name):
        if node.id in _CONSTANTS:
            return _CONSTANTS[node.id]
        raise ValueError(f"不支持变量：{node.id}")

    raise ValueError(f"不支持的表达式节点：{type(node).__name__}")


def my_calculate(expression: str) -> str:
    """Evaluate a basic arithmetic expression without calling ``eval``."""
    expression = expression.strip()
    if not expression:
        return "计算表达式不能为空"
    if len(expression) > _MAX_EXPRESSION_LENGTH:
        return "计算失败：表达式过长"

    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree.body)
        if isinstance(result, float) and not math.isfinite(result):
            raise ValueError("结果不是有限数")
        return str(result)
    except (
        SyntaxError,
        TypeError,
        ValueError,
        ZeroDivisionError,
        OverflowError,
    ):
        return "计算失败，请检查表达式格式"


def calculate(expression: str) -> str:
    """Compatibility name for direct calculator use."""
    return my_calculate(expression)


class CalculatorTool(Tool):
    """Object-style wrapper around the chapter's calculator function."""

    def __init__(self) -> None:
        super().__init__(
            name="python_calculator",
            description=(
                "执行安全的数学计算，支持 +、-、*、/、sqrt 和 pi。"
            ),
        )

    def run(self, parameters: dict[str, Any]) -> str:
        expression = str(
            parameters.get("input")
            or parameters.get("expression")
            or "",
        )
        return my_calculate(expression)

    def get_parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="input",
                type="string",
                description="要计算的数学表达式",
                required=True,
            ),
        ]


def create_calculator_registry() -> ToolRegistry:
    """Create the lightweight function registry shown in the chapter."""
    registry = ToolRegistry()
    registry.register_function(
        name="my_calculator",
        description=(
            "简单数学计算工具，支持 +、-、*、/、sqrt 和 pi。"
        ),
        func=my_calculate,
    )
    return registry
