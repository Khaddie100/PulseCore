
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pulsecore.domain.models import Observation


@dataclass
class ObservationGenerationIssue:
    row_number: int
    metric: str | None
    code: str
    message: str


@dataclass
class ObservationGenerationResult:
    observations: list[Observation] = field(default_factory=list)
    issues: list[ObservationGenerationIssue] = field(
        default_factory=list
    )
    total_rows: int = 0

    @property
    def generated_count(self) -> int:
        return len(self.observations)

    @property
    def issue_count(self) -> int:
        return len(self.issues)


class ObservationGenerator:
    """Converts entity-linked dataset rows into PulseCore observations."""

    @staticmethod
    def _parse_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            return datetime.fromisoformat(value.strip())

        raise ValueError(
            "Observation timestamp must be a datetime or ISO-format string."
        )

    def generate(
        self,
        rows: list[dict[str, Any]],
        metric_fields: dict[str, str] | None = None,
        observed_at_field: str | None = None,
        source: str | None = None,
        source_field: str | None = None,
        unit_by_metric: dict[str, str] | None = None,
        metadata_fields: list[str] | None = None,
        metric_field: str | None = None,
        value_field: str | None = None,
        unit_field: str | None = None,
    ) -> ObservationGenerationResult:
        """Generate observations using fixed or dynamic metric mapping."""

        fixed_mapping = metric_fields or {}

        dynamic_mapping = bool(metric_field or value_field or unit_field)

        if dynamic_mapping and not (metric_field and value_field):
            raise ValueError(
                "Dynamic mapping requires both metric_field and value_field."
            )

        if not fixed_mapping and not dynamic_mapping:
            raise ValueError(
                "at least one metric mapping is required."
            )

        if any(
            not metric.strip() or not field_name.strip()
            for metric, field_name in fixed_mapping.items()
        ):
            raise ValueError(
                    "at least one metric mapping is required."
                )

        result = ObservationGenerationResult(total_rows=len(rows))
        units = unit_by_metric or {}
        metadata_names = metadata_fields or []

        for row_number, row in enumerate(rows, start=2):
            entity_id = row.get("entity_id")

            if entity_id is None or not str(entity_id).strip():
                result.issues.append(
                    ObservationGenerationIssue(
                        row_number=row_number,
                        metric=None,
                        code="missing_entity_id",
                        message="The row has no linked PulseCore entity_id.",
                    )
                )
                continue

            entity_id = str(entity_id).strip()

            observed_at = None

            if observed_at_field:
                raw_timestamp = row.get(observed_at_field)

                if raw_timestamp is not None:
                    try:
                        observed_at = self._parse_datetime(raw_timestamp)
                    except (ValueError, TypeError) as exc:
                        result.issues.append(
                            ObservationGenerationIssue(
                                row_number=row_number,
                                metric=None,
                                code="invalid_observation_timestamp",
                                message=str(exc),
                            )
                        )
                        continue

            row_source = source

            if source_field and row.get(source_field) is not None:
                row_source = str(row[source_field]).strip() or source

            metadata = {
                name: row[name]
                for name in metadata_names
                if name in row
            }

            # Build the observations to generate for this row.
            row_metrics = []

            for metric, field_name in fixed_mapping.items():
                row_metrics.append(
                    (metric, row.get(field_name), units.get(metric))
                )

            if dynamic_mapping:
                raw_metric = row.get(metric_field)
                raw_value = row.get(value_field)

                if raw_metric is None or not str(raw_metric).strip():
                    result.issues.append(
                        ObservationGenerationIssue(
                            row_number=row_number,
                            metric=None,
                            code="missing_metric_name",
                            message=f"Field '{metric_field}' has no metric name.",
                        )
                    )
                elif raw_value is None or (
                    isinstance(raw_value, str) and not raw_value.strip()
                ):
                    result.issues.append(
                        ObservationGenerationIssue(
                            row_number=row_number,
                            metric=str(raw_metric).strip(),
                            code="missing_metric_value",
                            message=f"Field '{value_field}' has no value.",
                        )
                    )
                else:
                    metric_name = str(raw_metric).strip()
                    dynamic_unit = (
                        row.get(unit_field)
                        if unit_field and row.get(unit_field) is not None
                        else units.get(metric_name)
                    )

                    row_metrics.append(
                        (metric_name, raw_value, dynamic_unit)
                    )

            for metric, value, unit in row_metrics:
                if value is None or (
                    isinstance(value, str) and not value.strip()
                ):
                    result.issues.append(
                        ObservationGenerationIssue(
                            row_number=row_number,
                            metric=metric,
                            code="missing_metric_value",
                            message=f"No value was supplied for metric '{metric}'.",
                        )
                    )
                    continue

                observation_data = {
                    "entity_id": entity_id,
                    "metric": metric,
                    "value": value,
                    "unit": unit,
                    "source": row_source,
                    "metadata": metadata.copy(),
                }

                if observed_at is not None:
                    observation_data["observed_at"] = observed_at

                try:
                    observation = Observation(**observation_data)
                except (ValueError, TypeError) as exc:
                    result.issues.append(
                        ObservationGenerationIssue(
                            row_number=row_number,
                            metric=metric,
                            code="observation_creation_failed",
                            message=str(exc),
                        )
                    )
                    continue

                result.observations.append(observation)

        return result