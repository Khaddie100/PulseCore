
from unittest.mock import MagicMock

from pulsecore.applications.wardpulse.ingestion import (
    WardPulseIngestionService,
)
from pulsecore.applications.wardpulse.dataset_contracts import (
    get_wardpulse_dataset_contracts,
)


def test_shift_ingestion_uses_wardpulse_contract():
    engine = MagicMock()
    pipeline = MagicMock()
    pipeline.ingest.return_value = "ingestion-result"

    service = WardPulseIngestionService(
        engine=engine,
        pipeline=pipeline,
    )

    result = service.ingest_shift_records(
        file_path="shifts.csv",
    )

    assert result == "ingestion-result"

    kwargs = pipeline.ingest.call_args.kwargs

    assert kwargs["contract"] == (
        get_wardpulse_dataset_contracts()["shift_records"]
    )
    assert kwargs["external_id_field"] == "department_id"
    assert kwargs["entity_attribute"] == "department_id"
    assert kwargs["entity_type"] == "department"
    assert kwargs["metric_fields"] == {
        "overtime_hours": "overtime_hours",
    }
    assert kwargs["observed_at_field"] == "shift_date"


def test_shift_ingestion_preserves_metadata_and_sheet_name():
    engine = MagicMock()
    pipeline = MagicMock()

    service = WardPulseIngestionService(
        engine=engine,
        pipeline=pipeline,
    )

    service.ingest_shift_records(
        file_path="shifts.xlsx",
        sheet_name="November",
    )

    kwargs = pipeline.ingest.call_args.kwargs

    assert kwargs["sheet_name"] == "November"
    assert "employee_id" in kwargs["metadata_fields"]
    assert "shift_id" in kwargs["metadata_fields"]
    assert kwargs["unit_by_metric"]["overtime_hours"] == "hours"
