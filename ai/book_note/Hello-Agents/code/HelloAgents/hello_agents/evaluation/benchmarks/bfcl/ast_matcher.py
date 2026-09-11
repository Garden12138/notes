"""Small, dependency-free BFCL-style parser and structural matcher.

This is intentionally a teaching implementation. Official leaderboard scores must
still be produced by the evaluator shipped with the Gorilla/BFCL repository.
"""

from __future__ import annotations

import ast
import json
import math
import re
from collections.abc import Mapping, Sequence
from typing import Any


FunctionCall = dict[str, Any]
ExpectedCalls = list[list[FunctionCall]]
_MISSING = object()
_TOOL_MARKER = re.compile(
    r"\[TOOL_CALL:([^:\]]+):(.*?)\]",
    flags=re.DOTALL,
)
_CODE_BLOCK = re.compile(r"```(?:python|json)?\s*(.*?)```", re.DOTALL | re.I)
_ARITHMETIC = re.compile(r"^[\d\s.+\-*/%()]+$")


def extract_function_calls(
    response: str | Mapping[str, Any] | Sequence[Any],
    function_definitions: Sequence[Mapping[str, Any]] = (),
) -> list[FunctionCall]:
    """Extract JSON, Python-call and HelloAgents text-protocol outputs."""
    if isinstance(response, Mapping) or (
        isinstance(response, Sequence) and not isinstance(response, str)
    ):
        return _deduplicate(_calls_from_json_value(response))
    if not isinstance(response, str):
        raise TypeError("response must be text, a mapping, or a sequence")

    calls: list[FunctionCall] = []
    for match in _TOOL_MARKER.finditer(response):
        name = match.group(1).strip()
        arguments = _parse_marker_arguments(
            name,
            match.group(2).strip(),
            function_definitions,
        )
        calls.append({"name": name, "arguments": arguments})

    calls.extend(_extract_json_values(response))

    code_blocks = _CODE_BLOCK.findall(response)
    for code in code_blocks:
        calls.extend(_parse_python_calls(code, function_definitions))
    if not calls:
        calls.extend(_parse_python_calls(response, function_definitions))
    return _deduplicate(calls)


def normalize_ground_truth(value: Any) -> ExpectedCalls:
    """Normalize official BFCL ground truth into alternative call sequences."""
    if value is None or value == []:
        return [[]]
    if isinstance(value, Mapping):
        call = _ground_truth_call(value)
        return [[call]] if call else [[]]
    if not isinstance(value, list):
        raise ValueError("ground_truth must be an object or list")
    if not value:
        return [[]]

    # A list of lists means alternative valid call sequences. The common BFCL
    # single-turn form is a flat list of one or more calls.
    if all(isinstance(item, list) for item in value):
        alternatives = []
        for sequence in value:
            alternatives.append(
                [
                    call
                    for item in sequence
                    if (call := _ground_truth_call(item)) is not None
                ]
            )
        return alternatives or [[]]

    sequence = [
        call
        for item in value
        if (call := _ground_truth_call(item)) is not None
    ]
    return [sequence]


def match_function_calls(predicted: Any, ground_truth: Any) -> bool:
    """Compare call count, names and parameters; call order is ignored."""
    predicted_calls = _normalize_predicted_calls(predicted)
    alternatives = normalize_ground_truth(ground_truth)
    return any(
        _match_unordered(predicted_calls, expected)
        for expected in alternatives
    )


def best_match_statistics(predicted: Any, ground_truth: Any) -> dict[str, int]:
    """Return the best call/name/parameter overlap for auxiliary metrics."""
    predicted_calls = _normalize_predicted_calls(predicted)
    alternatives = normalize_ground_truth(ground_truth)
    candidates = [
        _sequence_statistics(predicted_calls, expected)
        for expected in alternatives
    ]
    return max(
        candidates,
        key=lambda item: (
            item["exact_call_matches"],
            item["parameter_matches"],
            item["function_name_matches"],
        ),
    )


def _normalize_predicted_calls(value: Any) -> list[FunctionCall]:
    if isinstance(value, str):
        return extract_function_calls(value)
    return _calls_from_json_value(value)


def _calls_from_json_value(value: Any) -> list[FunctionCall]:
    if isinstance(value, list) or isinstance(value, tuple):
        calls: list[FunctionCall] = []
        for item in value:
            calls.extend(_calls_from_json_value(item))
        return calls
    if not isinstance(value, Mapping):
        return []

    if "tool_calls" in value:
        return _calls_from_json_value(value["tool_calls"])
    if "function" in value and isinstance(value["function"], Mapping):
        function = value["function"]
        return _calls_from_json_value(
            {
                "name": function.get("name"),
                "arguments": function.get("arguments", {}),
            }
        )
    if "name" in value:
        name = str(value.get("name", "")).strip()
        arguments = value.get("arguments", value.get("parameters", {}))
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                return []
        if name and isinstance(arguments, Mapping):
            return [{"name": name, "arguments": dict(arguments)}]
        return []

    # Also accept BFCL's ground-truth-like {function_name: {arguments}} shape.
    if len(value) == 1:
        name, arguments = next(iter(value.items()))
        if isinstance(arguments, Mapping):
            return [{"name": str(name), "arguments": dict(arguments)}]
    return []


def _ground_truth_call(value: Any) -> FunctionCall | None:
    calls = _calls_from_json_value(value)
    if len(calls) != 1:
        return None
    return calls[0]


def _extract_json_values(text: str) -> list[FunctionCall]:
    decoder = json.JSONDecoder()
    calls: list[FunctionCall] = []
    index = 0
    while index < len(text):
        starts = [
            position
            for position in (text.find("{", index), text.find("[", index))
            if position >= 0
        ]
        if not starts:
            break
        start = min(starts)
        try:
            value, consumed = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            index = start + 1
            continue
        calls.extend(_calls_from_json_value(value))
        index = start + consumed
    return calls


def _parse_marker_arguments(
    name: str,
    raw: str,
    function_definitions: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if raw.startswith("{"):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = None
        if isinstance(value, dict):
            return value

    if "=" in raw:
        parsed = _parse_python_calls(f"{name}({raw})", function_definitions)
        if parsed:
            return parsed[0]["arguments"]
        pairs: dict[str, Any] = {}
        for fragment in raw.split(","):
            key, separator, value = fragment.partition("=")
            if not separator or not key.strip():
                pairs = {}
                break
            pairs[key.strip()] = _coerce_scalar(value)
        if pairs:
            return pairs

    property_names = _parameter_names(name, function_definitions)
    if len(property_names) == 1:
        return {property_names[0]: _coerce_scalar(raw)}
    return {"input": _coerce_scalar(raw)}


def _parse_python_calls(
    text: str,
    function_definitions: Sequence[Mapping[str, Any]],
) -> list[FunctionCall]:
    try:
        module = ast.parse(text.strip())
    except (SyntaxError, ValueError):
        return []

    calls: list[FunctionCall] = []
    for statement in module.body:
        node = statement.value if isinstance(statement, ast.Expr) else None
        nodes = (
            [node]
            if isinstance(node, ast.Call)
            else [
                item
                for item in getattr(node, "elts", [])
                if isinstance(item, ast.Call)
            ]
        )
        for call_node in nodes:
            name = _call_name(call_node.func)
            if not name:
                continue
            property_names = _parameter_names(name, function_definitions)
            arguments: dict[str, Any] = {}
            try:
                for position, argument in enumerate(call_node.args):
                    key = (
                        property_names[position]
                        if position < len(property_names)
                        else f"__arg{position}"
                    )
                    arguments[key] = _safe_value(argument)
                for keyword in call_node.keywords:
                    if keyword.arg is None:
                        raise ValueError("**kwargs is not supported")
                    arguments[keyword.arg] = _safe_value(keyword.value)
            except ValueError:
                continue
            calls.append({"name": name, "arguments": arguments})
    return calls


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else None
    return None


def _safe_value(node: ast.AST) -> Any:
    """Evaluate literals and constant arithmetic without executing code."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_safe_value(item) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_safe_value(item) for item in node.elts)
    if isinstance(node, ast.Set):
        return {_safe_value(item) for item in node.elts}
    if isinstance(node, ast.Dict):
        return {
            _safe_value(key): _safe_value(value)
            for key, value in zip(node.keys, node.values)
            if key is not None
        }
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        operand = _safe_value(node.operand)
        if not isinstance(operand, (int, float)) or isinstance(operand, bool):
            raise ValueError("unary operation requires a number")
        return operand if isinstance(node.op, ast.UAdd) else -operand
    if isinstance(node, ast.BinOp) and isinstance(
        node.op,
        (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow),
    ):
        left = _safe_value(node.left)
        right = _safe_value(node.right)
        if not all(
            isinstance(item, (int, float)) and not isinstance(item, bool)
            for item in (left, right)
        ):
            raise ValueError("arithmetic operands must be numeric")
        if isinstance(node.op, ast.Pow) and abs(right) > 10:
            raise ValueError("exponent is too large")
        operations = {
            ast.Add: lambda: left + right,
            ast.Sub: lambda: left - right,
            ast.Mult: lambda: left * right,
            ast.Div: lambda: left / right,
            ast.FloorDiv: lambda: left // right,
            ast.Mod: lambda: left % right,
            ast.Pow: lambda: left**right,
        }
        value = operations[type(node.op)]()
        if not math.isfinite(float(value)) or abs(float(value)) > 1e100:
            raise ValueError("arithmetic result is outside the safe range")
        return value
    raise ValueError(f"unsupported expression: {type(node).__name__}")


def _parameter_names(
    function_name: str,
    definitions: Sequence[Mapping[str, Any]],
) -> list[str]:
    for definition in definitions:
        function = definition.get("function", definition)
        if not isinstance(function, Mapping):
            continue
        if function.get("name") != function_name:
            continue
        parameters = function.get("parameters", {})
        properties = (
            parameters.get("properties", {})
            if isinstance(parameters, Mapping)
            else {}
        )
        return list(properties) if isinstance(properties, Mapping) else []
    return []


def _coerce_scalar(value: str) -> Any:
    stripped = value.strip()
    try:
        return ast.literal_eval(stripped)
    except (SyntaxError, ValueError):
        return stripped


def _match_unordered(
    predicted: list[FunctionCall],
    expected: list[FunctionCall],
) -> bool:
    if len(predicted) != len(expected):
        return False

    def search(index: int, unused: tuple[int, ...]) -> bool:
        if index == len(expected):
            return True
        return any(
            _call_equivalent(predicted[candidate], expected[index])
            and search(index + 1, tuple(i for i in unused if i != candidate))
            for candidate in unused
        )

    return search(0, tuple(range(len(predicted))))


def _call_equivalent(predicted: FunctionCall, expected: FunctionCall) -> bool:
    if predicted.get("name") != expected.get("name"):
        return False
    predicted_args = predicted.get("arguments", {})
    expected_args = expected.get("arguments", {})
    if not isinstance(predicted_args, Mapping) or not isinstance(
        expected_args,
        Mapping,
    ):
        return False
    if set(predicted_args) - set(expected_args):
        return False
    for name, options in expected_args.items():
        accepted = options if isinstance(options, list) else [options]
        value = predicted_args.get(name, _MISSING)
        if value is _MISSING:
            if "" in accepted:
                continue
            return False
        non_empty = [option for option in accepted if option != ""]
        if not any(_values_equivalent(value, option) for option in non_empty):
            return False
    return True


def _values_equivalent(left: Any, right: Any) -> bool:
    left = _constant_arithmetic(left, right)
    right = _constant_arithmetic(right, left)
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(float(left), float(right), rel_tol=1e-9, abs_tol=1e-12)
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        return set(left) == set(right) and all(
            _values_equivalent(left[key], right[key]) for key in left
        )
    if (
        isinstance(left, (list, tuple))
        and isinstance(right, (list, tuple))
    ):
        return len(left) == len(right) and all(
            _values_equivalent(a, b) for a, b in zip(left, right)
        )
    return left == right


def _constant_arithmetic(value: Any, other: Any) -> Any:
    if not isinstance(value, str) or not isinstance(other, (int, float)):
        return value
    if not _ARITHMETIC.fullmatch(value) or not any(op in value for op in "+-*/%"):
        return value
    try:
        return _safe_value(ast.parse(value, mode="eval").body)
    except (SyntaxError, ValueError, ZeroDivisionError, OverflowError):
        return value


def _sequence_statistics(
    predicted: list[FunctionCall],
    expected: list[FunctionCall],
) -> dict[str, int]:
    exact_matches = _maximum_pair_matches(predicted, expected, _call_equivalent)
    name_matches = _maximum_pair_matches(
        predicted,
        expected,
        lambda left, right: left.get("name") == right.get("name"),
    )

    parameter_total = sum(
        len(call.get("arguments", {}))
        for call in expected
        if isinstance(call.get("arguments", {}), Mapping)
    )
    parameter_matches = 0
    unused = set(range(len(predicted)))
    for expected_call in expected:
        candidates = [
            index
            for index in unused
            if predicted[index].get("name") == expected_call.get("name")
        ]
        if not candidates:
            continue
        best = max(
            candidates,
            key=lambda index: _parameter_match_count(
                predicted[index], expected_call
            ),
        )
        parameter_matches += _parameter_match_count(
            predicted[best], expected_call
        )
        unused.remove(best)

    return {
        "predicted_calls": len(predicted),
        "expected_calls": len(expected),
        "exact_call_matches": exact_matches,
        "function_name_matches": name_matches,
        "parameter_matches": parameter_matches,
        "expected_parameters": parameter_total,
    }


def _parameter_match_count(
    predicted: FunctionCall,
    expected: FunctionCall,
) -> int:
    predicted_args = predicted.get("arguments", {})
    expected_args = expected.get("arguments", {})
    if not isinstance(predicted_args, Mapping) or not isinstance(
        expected_args,
        Mapping,
    ):
        return 0
    matches = 0
    for name, options in expected_args.items():
        accepted = options if isinstance(options, list) else [options]
        value = predicted_args.get(name, _MISSING)
        if value is _MISSING and "" in accepted:
            matches += 1
        elif value is not _MISSING and any(
            _values_equivalent(value, option)
            for option in accepted
            if option != ""
        ):
            matches += 1
    return matches


def _maximum_pair_matches(
    predicted: list[FunctionCall],
    expected: list[FunctionCall],
    predicate: Any,
) -> int:
    best = 0

    def search(index: int, unused: tuple[int, ...], matched: int) -> None:
        nonlocal best
        if index == len(expected):
            best = max(best, matched)
            return
        search(index + 1, unused, matched)
        for candidate in unused:
            if predicate(predicted[candidate], expected[index]):
                search(
                    index + 1,
                    tuple(item for item in unused if item != candidate),
                    matched + 1,
                )

    search(0, tuple(range(len(predicted))), 0)
    return best


def _deduplicate(calls: list[FunctionCall]) -> list[FunctionCall]:
    unique: list[FunctionCall] = []
    seen: set[str] = set()
    for call in calls:
        marker = json.dumps(call, ensure_ascii=False, sort_keys=True, default=str)
        if marker not in seen:
            seen.add(marker)
            unique.append(call)
    return unique
