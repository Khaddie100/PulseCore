
from datetime import datetime, timedelta, timezone

from pulsecore.core.engine import PulseCoreEngine
from pulsecore.applications.wardpulse.module import WardPulseModule
from pulsecore.applications.wardpulse.schemas import (
    FacilitySchema,
    DepartmentSchema,
    HealthcareWorkerSchema,
)
from pulsecore.domain.models import Observation


def create_demo_engine() -> PulseCoreEngine:
    engine = PulseCoreEngine()
    engine.register_module(WardPulseModule())

    # Facility
    facility = FacilitySchema(
        id="FAC-001",
        name="Demo General Hospital",
        facility_type="General Hospital",
        location="Nigeria",
    )
    engine.register_entity(facility.to_entity())

    # Departments
    departments = [
        DepartmentSchema(
            id="DEP-001",
            facility_id="FAC-001",
            name="Emergency Department",
        ),
        DepartmentSchema(
            id="DEP-002",
            facility_id="FAC-001",
            name="Medical Ward",
        ),
    ]

    for department in departments:
        engine.register_entity(department.to_entity())

    # Synthetic worker entities for the facility structure.
    workers = [
        HealthcareWorkerSchema(
            id="WRK-001",
            department_id="DEP-001",
            role="Nurse",
        ),
        HealthcareWorkerSchema(
            id="WRK-002",
            department_id="DEP-001",
            role="Doctor",
        ),
        HealthcareWorkerSchema(
            id="WRK-003",
            department_id="DEP-002",
            role="Nurse",
        ),
    ]

    for worker in workers:
        engine.register_entity(worker.to_entity())

    # Two historical reporting periods:
    # Baseline: 25-31 October 2026
    # Current: 1-7 November 2026
    baseline_start = datetime(
        2026, 10, 25, tzinfo=timezone.utc
    )

    # Values are daily department-level aggregates.
    # They are synthetic demonstration data, not real hospital records.
    department_data = {
        "DEP-001": {
            "overtime_hours": [
                8, 9, 8, 10, 9, 8, 8,
                14, 15, 16, 15, 17, 16, 17,
            ],
            "staff_absence_count": [
                0, 0, 1, 0, 0, 1, 0,
                1, 1, 1, 2, 1, 1, 2,
            ],
            "respiratory_case_count": [
                2, 2, 3, 2, 3, 2, 2,
                4, 5, 5, 6, 5, 6, 7,
            ],
            "air_quality_index": [
                45, 48, 46, 47, 49, 46, 48,
                75, 78, 80, 82, 79, 84, 81,
            ],
            "occupational_incident_count": [
                0, 0, 0, 0, 1, 0, 0,
                1, 0, 1, 1, 1, 0, 1,
            ],
        },
        "DEP-002": {
            "overtime_hours": [
                7, 8, 7, 8, 7, 8, 7,
                8, 8, 9, 8, 9, 8, 8,
            ],
            "staff_absence_count": [
                0, 0, 0, 1, 0, 0, 0,
                0, 0, 1, 0, 0, 0, 0,
            ],
            "respiratory_case_count": [
                1, 2, 1, 2, 1, 2, 1,
                2, 2, 2, 1, 2, 2, 2,
            ],
            "air_quality_index": [
                44, 45, 46, 44, 45, 46, 45,
                46, 45, 47, 46, 45, 46, 47,
            ],
            "occupational_incident_count": [
                0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0, 0,
            ],
        },
    }

    metric_units = {
        "overtime_hours": "hours",
        "staff_absence_count": "staff",
        "respiratory_case_count": "cases",
        "air_quality_index": "AQI",
        "occupational_incident_count": "incidents",
    }

    for department_id, metrics in department_data.items():
        for metric, daily_values in metrics.items():
            for day_offset, value in enumerate(daily_values):
                observed_at = baseline_start + timedelta(
                    days=day_offset
                )

                observation = Observation(
                    entity_id=department_id,
                    metric=metric,
                    value=value,
                    unit=metric_units[metric],
                    source="synthetic_demo_dataset",
                    observed_at=observed_at,
                    metadata={
                        "signal_category": (
                            "environmental"
                            if metric == "air_quality_index"
                            else "clinical_service"
                            if metric == "respiratory_case_count"
                            else "workplace_safety"
                            if metric == "occupational_incident_count"
                            else "workforce"
                        ),
                        "synthetic": True,
                    },
                )

                engine.record_observation(observation)

    assert len(engine.list_entities()) == 6

    return engine
