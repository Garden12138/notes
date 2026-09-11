"""Answer extraction and quasi-exact matching for GAIA-style tasks."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal, InvalidOperation
import re
import unicodedata


GAIA_SYSTEM_PROMPT = """You are a general AI assistant.
Solve the task with the available tools and inspect any supplied attachment.
End with exactly: FINAL ANSWER: [answer]
Keep the final answer to a number, a few words, or a comma-separated list.
Do not add units, currency signs, percent signs, or number separators unless the
question explicitly asks for them."""


_NUMBER_PATTERN = re.compile(
    r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$"
)
_TOKEN_PATTERN = re.compile(r"[a-z0-9]+|[\u3400-\u9fff]", re.IGNORECASE)
_FINAL_ANSWER_PATTERN = re.compile(
    r"FINAL\s+ANSWER\s*:\s*(?:\[([^\]\n]*)\]|([^\n]*))",
    re.IGNORECASE,
)


def extract_final_answer(response: str) -> str:
    """Extract the last GAIA answer marker, with conservative fallbacks."""
    text = str(response or "").strip()
    matches = list(_FINAL_ANSWER_PATTERN.finditer(text))
    if matches:
        bracketed, plain = matches[-1].groups()
        return (bracketed if bracketed is not None else plain).strip()

    fallback_patterns = (
        r"(?:最终答案|答案)\s*[：:]\s*(.+)",
        r"(?:final answer|answer)\s*[：:]\s*(.+)",
    )
    for pattern in fallback_patterns:
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        if matches:
            return _strip_outer_brackets(matches[-1].group(1).strip())

    for line in reversed(text.splitlines()):
        candidate = line.strip()
        if candidate and not candidate.startswith("#"):
            return _strip_outer_brackets(candidate)
    return text


def normalize_answer(answer: object, reference: object | None = None) -> str:
    """Normalize a number, short string, or comma-separated list.

    The reference controls answer type when supplied. Numeric parsing is tried
    before list parsing so ``$1,234.56`` is not mistaken for a two-item list.
    """
    text = _clean_text(answer)
    reference_text = _clean_text(reference) if reference is not None else text

    reference_number = _parse_number(reference_text)
    if reference_number is not None:
        predicted_number = _parse_number(text)
        if predicted_number is not None:
            return _format_decimal(predicted_number)
        return _normalize_string(text)

    if _is_list(reference_text):
        return ",".join(
            sorted(_normalize_single(part) for part in text.split(","))
        )

    number = _parse_number(text)
    if number is not None:
        return _format_decimal(number)
    if reference is None and _is_list(text):
        return ",".join(
            sorted(_normalize_single(part) for part in text.split(","))
        )
    return _normalize_string(text)


def quasi_exact_match(prediction: object, reference: object) -> bool:
    """Return whether prediction and reference match after normalization."""
    return normalize_answer(prediction, reference) == normalize_answer(
        reference,
        reference,
    )


def partial_match_score(prediction: object, reference: object) -> float:
    """Return a transparent local overlap diagnostic in ``[0, 1]``.

    This score is not an official GAIA leaderboard metric. Numbers only receive
    credit for an exact normalized match; lists and text use multiset token F1.
    """
    if quasi_exact_match(prediction, reference):
        return 1.0

    normalized_prediction = normalize_answer(prediction, reference)
    normalized_reference = normalize_answer(reference, reference)
    if _parse_number(_clean_text(reference)) is not None:
        return 0.0

    if _is_list(_clean_text(reference)):
        predicted_tokens = [
            item for item in normalized_prediction.split(",") if item
        ]
        reference_tokens = [
            item for item in normalized_reference.split(",") if item
        ]
    else:
        predicted_tokens = _TOKEN_PATTERN.findall(normalized_prediction)
        reference_tokens = _TOKEN_PATTERN.findall(normalized_reference)
    return _multiset_f1(predicted_tokens, reference_tokens)


def _clean_text(value: object) -> str:
    if value is None:
        return ""
    return _strip_outer_brackets(
        unicodedata.normalize("NFKC", str(value)).strip()
    )


def _strip_outer_brackets(text: str) -> str:
    if len(text) >= 2 and text[0] == "[" and text[-1] == "]":
        return text[1:-1].strip()
    return text


def _parse_number(text: str) -> Decimal | None:
    candidate = text.strip().replace(",", "")
    candidate = re.sub(r"^[\$€£¥]\s*", "", candidate)
    candidate = re.sub(r"\s*(?:%|\$|€|£|¥)$", "", candidate)
    candidate = candidate.strip()
    if not _NUMBER_PATTERN.fullmatch(candidate):
        return None
    try:
        number = Decimal(candidate)
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def _format_decimal(number: Decimal) -> str:
    if number == 0:
        return "0"
    value = format(number, "f")
    if "." in value:
        value = value.rstrip("0").rstrip(".")
    return value


def _is_list(text: str) -> bool:
    return "," in text and _parse_number(text) is None


def _normalize_single(text: str) -> str:
    number = _parse_number(text)
    if number is not None:
        return _format_decimal(number)
    return _normalize_string(text)


def _normalize_string(text: str) -> str:
    value = unicodedata.normalize("NFKC", text).casefold().strip()
    value = re.sub(r"^(?:the|a|an)\s+", "", value)
    value = " ".join(value.split())
    return value.rstrip(".,;:!?，。；：！？")


def _multiset_f1(prediction: list[str], reference: list[str]) -> float:
    if not prediction or not reference:
        return 1.0 if prediction == reference else 0.0
    overlap = sum((Counter(prediction) & Counter(reference)).values())
    if overlap == 0:
        return 0.0
    precision = overlap / len(prediction)
    recall = overlap / len(reference)
    return 2 * precision * recall / (precision + recall)
