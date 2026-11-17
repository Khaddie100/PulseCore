
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from pulsecore.domain.models import Entity, Indicator, Observation
from pulsecore.intelligence.indicators import (
    IndicatorCalculator,
    IndicatorResult,
)


class AnalyticsResult(BaseModel):
    """Comparison of an indicator across two reporting periods."""

    indicator_id: str
    indicator_name: str
    entity_id: str

    baseline: IndicatorResult
    current: IndicatorResult

    absolute_deviation: float | None = None
    percentage_deviation: float | None = None

    trend: Literal[
        "increasing",
        "decreasing",
        "stable",
        "insufficient_data",
    ] = "insufficient_data"

    status: str = "calculated"


class AnalyticsEngine:
    """Generic historical comparison and trend analysis."""

    def __init__(
        self,
        calculator: IndicatorCalculator | None = None,
        stability_tolerance: float = 5.0,
    ):
        if stability_tolerance < 0:
            raise ValueError(
                "Stability tolerance cannot be negative."
            )

        self.calculator = calculator or IndicatorCalculator()
        self.stability_tolerance = stability_tolerance

    @staticmethod
    def _filter_period(
        observations: list[Observation],
        entity_id: str,
        start: datetime,
        end: datetime,
    ) -> list[Observation]:
        return [
            observation
            for observation in observations
            if observation.entity_id == entity_id
            and start <= observation.observed_at <= end
        ]

    def compare(
        self,
        indicator: Indicator,
        entity: Entity,
        observations: list[Observation],
        baseline_start: datetime,
        baseline_end: datetime,
        current_start: datetime,
        current_end: datetime,
    ) -> AnalyticsResult:
        """Compare current indicator value with a historical baseline."""

        if baseline_start > baseline_end:
            raise ValueError("Invalid baseline reporting period.")

        if current_start > current_end:
            raise ValueError("Invalid current reporting period.")

        if baseline_end >= current_start:
            raise ValueError(
                "Baseline period must end before current period begins."
            )

        baseline_observations = self._filter_period(
            observations,
            entity.id,
            baseline_start,
            baseline_end,
        )

        current_observations = self._filter_period(
            observations,
            entity.id,
            current_start,
            current_end,
        )

        baseline = self.calculator.calculate(
            indicator,
            entity,
            baseline_observations,
        )

        current = self.calculator.calculate(
            indicator,
            entity,
            current_observations,
        )

        result = AnalyticsResult(
            indicator_id=indicator.id,
            indicator_name=indicator.name,
            entity_id=entity.id,
            baseline=baseline,
            current=current,
        )

        if baseline.value is None or current.value is None:
            result.status = "insufficient_data"
            return result

        if (
            isinstance(baseline.value, bool)
            or isinstance(current.value, bool)
            or not isinstance(baseline.value, (int, float))
            or not isinstance(current.value, (int, float))
        ):
            result.status = "non_numeric_comparison"
            return result

        deviation = current.value - baseline.value
        result.absolute_deviation = deviation

        if baseline.value != 0:
            percentage = (
                deviation / abs(baseline.value)
            ) * 100

            result.percentage_deviation = percentage

            if abs(percentage) <= self.stability_tolerance:
                result.trend = "stable"
            elif deviation > 0:
                result.trend = "increasing"
            else:
                result.trend = "decreasing"

        else:
            # Percentage change from zero is undefined.
            if deviation == 0:
                result.trend = "stable"
                result.percentage_deviation = 0.0
            elif deviation > 0:
                result.trend = "increasing"
            else:
                result.trend = "decreasing"

            result.status = "zero_baseline"

        return result
