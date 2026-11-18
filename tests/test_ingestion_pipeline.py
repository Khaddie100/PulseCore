
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from pulsecore.domain.models import Entity
from pulsecore.ingestion.contracts import (
    ColumnContract,
    ColumnType,
    DatasetContract,
)
from pulsecore.ingestion.pipeline import DatasetIngestionPipeline


@pytest.fixture
def contract():
    return DatasetContract(
        name="employee_work_records",
        columns=[
            ColumnContract(
                name="employee_id",
                data_type=ColumnType.STRING,
            ),
            ColumnContract(
                name="work_hours",
                data_type=ColumnType.FLOAT,
            ),
            ColumnContract(
                name="recorded_at",
                data_type=ColumnType.DATETIME,
            ),
        ],
        unique_key=["employee_id"],
    )


@pytest.fixture
def rows():
    return [
        {
            "employee_id": "EMP001",
            "work_hours": "40",
            "recorded_at": "2026-11-15T08:00:00+00:00",
        },
        {
            "employee_id": "EMP002",
            "work_hours": "36",
            "recorded_at": "2026-11-15T08:00:00+00:00",
        },
    ]


@pytest.fixture
def engine():
    mock_engine = MagicMock()

    mock_engine.list_entities.return_value = [
        Entity(
            id="entity-001",
            entity_type="employee",
            name="Employee One",
            attributes={"employee_id": "EMP001"},
        ),
        Entity(
            id="entity-002",
            entity_type="employee",
            name="Employee Two",
            attributes={"employee_id": "EMP002"},
        ),
    ]

    return mock_engine


@pytest.fixture
def pipeline(engine, rows):
    reader = MagicMock()
    reader.read.return_value = rows

    return DatasetIngestionPipeline(
        engine=engine,
        reader=reader,
    )


def test_pipeline_processes_complete_dataset(
    pipeline,
    contract,
    engine,
):
    result = pipeline.ingest(
        file_path="employees.csv",
        contract=contract,
        external_id_field="employee_id",
        entity_type="employee",
        metric_fields={"work_hours": "work_hours"},
        observed_at_field="recorded_at",
        source="HR system",
        unit_by_metric={"work_hours": "hours"},
    )

    assert result.validation is not None
    assert result.linking is not None
    assert result.generation is not None

    assert result.validation.result.accepted_rows == 2
    assert result.linking.linked_count == 2
    assert result.generation.generated_count == 2
    assert result.stored_count == 2
    assert result.completed is True

    assert engine.record_observation.call_count == 2


def test_pipeline_uses_linked_entity_ids(
    pipeline,
    contract,
):
    result = pipeline.ingest(
        file_path="employees.csv",
        contract=contract,
        external_id_field="employee_id",
        entity_type="employee",
        metric_fields={"work_hours": "work_hours"},
    )

    assert {
        item.entity_id for item in result.stored_observations
    } == {"entity-001", "entity-002"}


def test_pipeline_reports_unmatched_entities(
    pipeline,
    contract,
    engine,
    rows,
):
    engine.list_entities.return_value = [
        Entity(
            id="entity-001",
            entity_type="employee",
            name="Employee One",
            attributes={"employee_id": "EMP001"},
        )
    ]

    result = pipeline.ingest(
        file_path="employees.csv",
        contract=contract,
        external_id_field="employee_id",
        entity_type="employee",
        metric_fields={"work_hours": "work_hours"},
    )

    assert result.linking.linked_count == 1
    assert result.linking.unmatched_count == 1
    assert result.stored_count == 1


def test_pipeline_does_not_store_when_validation_has_no_valid_rows(
    pipeline,
    contract,
    engine,
    rows,
):
    pipeline.reader.read.return_value = [
        {
            "employee_id": "EMP001",
            "work_hours": "invalid",
            "recorded_at": datetime(
                2026, 11, 15, tzinfo=timezone.utc
            ),
        }
    ]

    result = pipeline.ingest(
        file_path="employees.csv",
        contract=contract,
        external_id_field="employee_id",
        entity_type="employee",
        metric_fields={"work_hours": "work_hours"},
    )

    assert result.validation.result.accepted_rows == 0
    assert result.linking is None
    assert result.generation is None
    assert result.stored_count == 0
    engine.record_observation.assert_not_called()


def test_pipeline_reports_storage_failures(
    pipeline,
    contract,
    engine,
):
    engine.record_observation.side_effect = ValueError(
        "Observation already exists."
    )

    result = pipeline.ingest(
        file_path="employees.csv",
        contract=contract,
        external_id_field="employee_id",
        entity_type="employee",
        metric_fields={"work_hours": "work_hours"},
    )

    assert result.generation.generated_count == 2
    assert result.stored_count == 0
    assert result.storage_failure_count == 2
    assert result.completed is False


def test_pipeline_passes_sheet_name_to_reader(
    pipeline,
    contract,
):
    pipeline.ingest(
        file_path="employees.xlsx",
        contract=contract,
        external_id_field="employee_id",
        entity_type="employee",
        metric_fields={"work_hours": "work_hours"},
        sheet_name="November",
    )

    pipeline.reader.read.assert_called_once_with(
        file_path="employees.xlsx",
        contract=contract,
        sheet_name="November",
    )


def test_pipeline_preserves_observation_metadata(
    pipeline,
):
    contract_with_metadata = DatasetContract(
        name="employee_work_records",
        columns=[
            ColumnContract(
                name="employee_id",
                data_type=ColumnType.STRING,
            ),
            ColumnContract(
                name="work_hours",
                data_type=ColumnType.FLOAT,
            ),
            ColumnContract(
                name="recorded_at",
                data_type=ColumnType.DATETIME,
            ),
            ColumnContract(
                name="department",
                data_type=ColumnType.STRING,
                required=False,
            ),
        ],
        unique_key=["employee_id"],
    )

    pipeline.reader.read.return_value = [
        {
            "employee_id": "EMP001",
            "work_hours": "40",
            "recorded_at": "2026-11-15T08:00:00+00:00",
            "department": "emergency",
        }
    ]

    result = pipeline.ingest(
        file_path="employees.csv",
        contract=contract_with_metadata,
        external_id_field="employee_id",
        entity_type="employee",
        metric_fields={"work_hours": "work_hours"},
        metadata_fields=["department"],
    )

    assert result.stored_observations[0].metadata == {
        "department": "emergency"
    }
