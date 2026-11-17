
import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from pulsecore.domain.models import Entity, Indicator, Observation


class IndicatorResult(BaseModel):
    """Result of calculating an indicator for an entity."""

    indicator_id: str
    indicator_name: str
    entity_id: str
    entity_type: str

    value: Any | None = None
    unit: str | None = None
    aggregation: str

    observation_count: int = 0
    observation_ids: list[str] = Field(default_factory=list)

    period_start: datetime | None = None
    period_end: datetime | None = None

    status: str = "calculated"


class IndicatorCalculator:
    """Generic indicator calculation engine."""

    SUPPORTED_AGGREGATIONS = {
        "sum",
        "average",
        "count",
        "minimum",
        "maximum",
        "latest",
    }

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(
            r"[^a-zA-Z0-9]+",
            "_",
            value.strip()
        ).strip("_").lower()

    def calculate(
        self,
        indicator: Indicator,
        entity: Entity,
        observations: list[Observation],
    ) -> IndicatorResult:
        """
        Calculate an indicator for one entity using matching observations.

        Aggregation is configured through indicator.metadata:
            {"aggregation": "average"}
        """

        expected_type = self._normalize(indicator.entity_type)
        actual_type = self._normalize(entity.entity_type)

        if expected_type != actual_type:
            raise ValueError(
                f"Indicator '{indicator.name}' expects entity type "
                f"'{expected_type}', but received '{actual_type}'."
            )

        metric = self._normalize(indicator.metric)

        matching = [
            observation
            for observation in observations
            if observation.entity_id == entity.id
            and self._normalize(observation.metric) == metric
        ]

        matching.sort(key=lambda item: item.observed_at)

        aggregation = indicator.metadata.get(
            "aggregation",
            "sum"
        )

        if aggregation not in self.SUPPORTED_AGGREGATIONS:
            raise ValueError(
                f"Unsupported aggregation '{aggregation}'. "
                f"Supported aggregations: "
                f"{', '.join(sorted(self.SUPPORTED_AGGREGATIONS))}."
            )

        result = IndicatorResult(
            indicator_id=indicator.id,
            indicator_name=indicator.name,
            entity_id=entity.id,
            entity_type=entity.entity_type,
            unit=indicator.unit,
            aggregation=aggregation,
            observation_count=len(matching),
            observation_ids=[
                item.id for item in matching
            ],
            period_start=(
                matching[0].observed_at if matching else None
            ),
            period_end=(
                matching[-1].observed_at if matching else None
            ),
        )

        if not matching:
            result.status = "no_data"
            return result

        values = [item.value for item in matching]

        if aggregation == "count":
            result.value = len(values)

        elif aggregation == "latest":
            result.value = matching[-1].value

        else:
            numeric_values = [
                value for value in values
                if isinstance(value, (int, float))
                and not isinstance(value, bool)
            ]

            if not numeric_values:
                result.status = "no_numeric_data"
                return result

            if aggregation == "sum":
                result.value = sum(numeric_values)

            elif aggregation == "average":
                result.value = (
                    sum(numeric_values) / len(numeric_values)
                )

            elif aggregation == "minimum":
                result.value = min(numeric_values)

            elif aggregation == "maximum":
                result.value = max(numeric_values)

        return result
