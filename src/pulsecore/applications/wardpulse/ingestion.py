
from pulsecore.core.engine import PulseCoreEngine
from pulsecore.ingestion.pipeline import DatasetIngestionPipeline

from pulsecore.applications.wardpulse.dataset_contracts import (
    get_wardpulse_dataset_contracts,
)


class WardPulseIngestionService:
    """Application-specific ingestion workflows for WardPulse."""

    def __init__(
        self,
        engine: PulseCoreEngine,
        pipeline: DatasetIngestionPipeline | None = None,
    ):
        self.engine = engine
        self.pipeline = pipeline or DatasetIngestionPipeline(engine)

    def ingest_shift_records(
        self,
        file_path: str,
        sheet_name: str | None = None,
    ):
        """Import shift records as department-level overtime observations."""

        contract = get_wardpulse_dataset_contracts()["shift_records"]

        return self.pipeline.ingest(
            file_path=file_path,
            contract=contract,
            external_id_field="department_id",
            entity_attribute="department_id",
            entity_type="department",
            metric_fields={
                "overtime_hours": "overtime_hours",
            },
            observed_at_field="shift_date",
            source="wardpulse_shift_records",
            unit_by_metric={
                "overtime_hours": "hours",
            },
            metadata_fields=[
                "shift_id",
                "employee_id",
                "scheduled_hours",
                "worked_hours",
                "shift_type",
            ],
            sheet_name=sheet_name,
        )

    def ingest_departmental_observations(
        self,
        file_path: str,
        sheet_name: str | None = None,
    ):
        """Import dynamic departmental measurements into PulseCore."""

        contract = get_wardpulse_dataset_contracts()[
            "departmental_observations"
        ]

        return self.pipeline.ingest(
            file_path=file_path,
            contract=contract,
            external_id_field="department_id",
            entity_attribute="department_id",
            entity_type="department",
            metric_fields={},
            metric_field="metric",
            value_field="value",
            unit_field="unit",
            observed_at_field="observed_at",
            source_field="source",
            sheet_name=sheet_name,
        )