
from pulsecore.domain.models import Rule


class RuleEngine:
    """Validates and evaluates configurable rule conditions."""

    OPERATORS = {
        "gt": lambda value, threshold: value > threshold,
        "gte": lambda value, threshold: value >= threshold,
        "lt": lambda value, threshold: value < threshold,
        "lte": lambda value, threshold: value <= threshold,
        "eq": lambda value, threshold: value == threshold,
        "ne": lambda value, threshold: value != threshold,
        ">": lambda value, threshold: value > threshold,
        ">=": lambda value, threshold: value >= threshold,
        "<": lambda value, threshold: value < threshold,
        "<=": lambda value, threshold: value <= threshold,
        "==": lambda value, threshold: value == threshold,
        "!=": lambda value, threshold: value != threshold,
    }

    @classmethod
    def evaluate(cls, value: float, rule: Rule) -> bool:
        if not rule.enabled:
            return False

        operator = rule.operator.lower()

        if operator not in cls.OPERATORS:
            raise ValueError(
                f"Unsupported operator '{rule.operator}'."
            )

        return cls.OPERATORS[operator](
            value,
            rule.threshold,
        )
