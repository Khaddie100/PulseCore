
from datetime import datetime, timezone

import pytest

from pulsecore.ingestion.observation_generator import (
    ObservationGenerator,
)


@pytest.fixture
def generator():
    return ObservationGenerator()


@pytest.fixture
def linked_rows():
    return [
        {
            "entity_id": "employee-001",
            "work_hours": 40.0,
            "absence_days": 1,
            "recorded_at": "2026-11-15T08:00:00+00:00",
            "department": "emergency",
            "data_source": "HR system",
        },
        {
            "entity_id": "employee-002",
            "work_hours": 36.0,
            "absence_days": 0,
            "recorded_at": "2026-11-15T08:00:00+00:00",
            "department": "surgery",
            "data_source": "HR system",
        },
    ]


def test_generates_observations_from_multiple_metrics(
    generator,
    linked_rows,
):
    result = generator.generate(
        rows=linked_rows,
        metric_fields={
            "work_hours": "work_hours",
            "absence_days": "absence_days",
        },
    )

    assert result.generated_count == 4
    assert result.total_rows == 2
    assert result.issue_count == 0


def test_observations_use_linked_entity_ids(
    generator,
    linked_rows,
):
    result = generator.generate(
        rows=linked_rows,
        metric_fields={"work_hours": "work_hours"},
    )

    assert result.observations[0].entity_id == "employee-001"
    assert result.observations[1].entity_id == "employee-002"


def test_observation_metric_and_value_are_correct(
    generator,
    linked_rows,
):
    result = generator.generate(
        rows=linked_rows,
        metric_fields={"work_hours": "work_hours"},
    )

    observation = result.observations[0]

    assert observation.metric == "work_hours"
    assert observation.value == 40.0


def test_observation_timestamp_is_parsed(
    generator,
    linked_rows,
):
    result = generator.generate(
        rows=linked_rows,
        metric_fields={"work_hours": "work_hours"},
        observed_at_field="recorded_at",
    )

    assert result.observations[0].observed_at == datetime(
        2026, 11, 15, 8, 0, tzinfo=timezone.utc
    )


def test_fixed_source_and_units_are_applied(
    generator,
    linked_rows,
):
    result = generator.generate(
        rows=linked_rows,
        metric_fields={"work_hours": "work_hours"},
        source="CSV import",
        unit_by_metric={"work_hours": "hours"},
    )

    observation = result.observations[0]

    assert observation.source == "CSV import"
    assert observation.unit == "hours"


def test_source_field_overrides_fixed_source(
    generator,
    linked_rows,
):
    result = generator.generate(
        rows=linked_rows,
        metric_fields={"work_hours": "work_hours"},
        source="Manual import",
        source_field="data_source",
    )

    assert result.observations[0].source == "HR system"


def test_metadata_fields_are_preserved(
    generator,
    linked_rows,
):
    result = generator.generate(
        rows=linked_rows,
        metric_fields={"work_hours": "work_hours"},
        metadata_fields=["department"],
    )

    assert result.observations[0].metadata == {
        "department": "emergency"
    }


def test_missing_entity_id_generates_issue(generator):
    rows = [{"work_hours": 40}]

    result = generator.generate(
        rows=rows,
        metric_fields={"work_hours": "work_hours"},
    )

    assert result.generated_count == 0
    assert result.issues[0].code == "missing_entity_id"


def test_missing_metric_value_generates_issue(generator):
    rows = [
        {
            "entity_id": "employee-001",
            "work_hours": None,
        }
    ]

    result = generator.generate(
        rows=rows,
        metric_fields={"work_hours": "work_hours"},
    )

    assert result.generated_count == 0
    assert result.issues[0].code == "missing_metric_value"


def test_invalid_timestamp_generates_issue(generator):
    rows = [
        {
            "entity_id": "employee-001",
            "work_hours": 40,
            "recorded_at": "not-a-date",
        }
    ]

    result = generator.generate(
        rows=rows,
        metric_fields={"work_hours": "work_hours"},
        observed_at_field="recorded_at",
    )

    assert result.generated_count == 0
    assert (
        result.issues[0].code
        == "invalid_observation_timestamp"
    )


def test_missing_timestamp_uses_model_default(generator):
    rows = [
        {
            "entity_id": "employee-001",
            "work_hours": 40,
        }
    ]

    result = generator.generate(
        rows=rows,
        metric_fields={"work_hours": "work_hours"},
        observed_at_field="recorded_at",
    )

    assert result.generated_count == 1
    assert isinstance(
        result.observations[0].observed_at,
        datetime,
    )


def test_empty_metric_mapping_is_rejected(generator):
    with pytest.raises(ValueError, match="at least one metric"):
        generator.generate(
            rows=[],
            metric_fields={},
        )


def test_empty_rows_return_empty_result(generator):
    result = generator.generate(
        rows=[],
        metric_fields={"work_hours": "work_hours"},
    )

    assert result.total_rows == 0
    assert result.generated_count == 0
    assert result.issues == []


def test_dynamic_metric_mapping_generates_observation():
    generator = ObservationGenerator()

    result = generator.generate(
        rows=[
            {
                "entity_id": "DEP-001",
                "metric": "overtime_hours",
                "value": 12.5,
                "unit": "hours",
                "observed_at": datetime(
                    2026, 11, 10, tzinfo=timezone.utc
                ),
            }
        ],
        metric_field="metric",
        value_field="value",
        unit_field="unit",
        observed_at_field="observed_at",
    )

    assert result.generated_count == 1
    observation = result.observations[0]
    assert observation.entity_id == "DEP-001"
    assert observation.metric == "overtime_hours"
    assert observation.value == 12.5
    assert observation.unit == "hours"


def test_dynamic_mapping_reports_missing_metric():
    generator = ObservationGenerator()

    result = generator.generate(
        rows=[
            {
                "entity_id": "DEP-001",
                "metric": "",
                "value": 12,
            }
        ],
        metric_field="metric",
        value_field="value",
    )

    assert result.generated_count == 0
    assert result.issues[0].code == "missing_metric_name"


def test_dynamic_mapping_reports_missing_value():
    generator = ObservationGenerator()

    result = generator.generate(
        rows=[
            {
                "entity_id": "DEP-001",
                "metric": "overtime_hours",
                "value": None,
            }
        ],
        metric_field="metric",
        value_field="value",
    )

    assert result.generated_count == 0
    assert result.issues[0].code == "missing_metric_value"
