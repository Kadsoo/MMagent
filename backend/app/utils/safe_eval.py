from __future__ import annotations

import ast
import operator
import re
from typing import Any


ALLOWED_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
ALLOWED_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def safe_calculate(expression: str) -> int | float:
    clean = expression.strip()
    if not clean:
        raise ValueError("Expression cannot be empty.")
    if len(clean) > 120:
        raise ValueError("Expression is too long.")
    if not re.fullmatch(r"[0-9+\-*/().\s]+", clean):
        raise ValueError("Expression contains unsupported characters.")
    if "**" in clean or "//" in clean:
        raise ValueError("Only +, -, *, /, and parentheses are supported.")

    parsed = ast.parse(clean, mode="eval")
    value = _eval_node(parsed.body)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return round(value, 8) if isinstance(value, float) else value


def _eval_node(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_BIN_OPS:
            raise ValueError("Unsupported arithmetic operator.")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return ALLOWED_BIN_OPS[op_type](left, right)

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in ALLOWED_UNARY_OPS:
            raise ValueError("Unsupported unary operator.")
        return ALLOWED_UNARY_OPS[op_type](_eval_node(node.operand))

    raise ValueError("Unsupported expression.")

