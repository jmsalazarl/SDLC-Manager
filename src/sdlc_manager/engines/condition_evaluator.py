from __future__ import annotations

from pathlib import PurePath
from typing import Any


class ConditionEvaluationError(ValueError):
    """Indica que una condicion declarativa no cumple el contrato cerrado."""


class ConditionEvaluator:
    """Evalua condiciones declarativas sin ejecutar expresiones dinamicas."""

    def evaluate(self, node: dict[str, Any], context: dict[str, Any]) -> bool:
        if not node:
            return True
        if "all" in node:
            return all(self.evaluate(child, context) for child in self._condition_list(node["all"]))
        if "any" in node:
            return any(self.evaluate(child, context) for child in self._condition_list(node["any"]))
        if not {"field", "operator"}.issubset(node):
            raise ConditionEvaluationError("La condicion debe declarar field y operator")
        field = node["field"]
        operator = node["operator"]
        if not isinstance(field, str) or not isinstance(operator, str):
            raise ConditionEvaluationError("field y operator deben ser texto")
        return self.apply(operator, context.get(field), node.get("value"))

    @staticmethod
    def apply(operator: str, actual: Any, expected: Any) -> bool:
        if operator == "equals":
            return type(actual) is type(expected) and actual == expected
        if operator == "not_equals":
            return not (type(actual) is type(expected) and actual == expected)
        if operator == "exists":
            return (actual is not None) is bool(expected)
        if operator == "contains":
            if isinstance(actual, str) and isinstance(expected, str):
                return expected in actual
            if isinstance(actual, list):
                return expected in actual
            raise ConditionEvaluationError("contains requiere texto o lista")
        if operator == "in":
            if not isinstance(expected, list):
                raise ConditionEvaluationError("in requiere una lista como value")
            return actual in expected
        if operator == "file_extension_matches":
            if not isinstance(actual, list) or not isinstance(expected, list):
                raise ConditionEvaluationError("file_extension_matches requiere listas")
            return any(ConditionEvaluator.extension(str(item)) in expected for item in actual)
        raise ConditionEvaluationError(f"Operador no permitido: {operator}")

    @staticmethod
    def extension(path: str) -> str:
        return PurePath(path).suffix.lower()

    @staticmethod
    def _condition_list(value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
            raise ConditionEvaluationError("all y any deben contener listas de condiciones")
        return value
