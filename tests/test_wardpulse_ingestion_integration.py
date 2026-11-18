
from datetime import datetime, timezone

from pulsecore.applications.wardpulse.demo_data import (
    create_demo_engine,
)
from pulsecore.applications.wardpulse.ingestion import (
    WardPulseIngestionService,
)
from pulsecore.applications.wardpulse.service import (
    WardPulseSurveillance,
)


def test_csv_observations_reach_engine_and_surveillance(tmp_path):
    engine = create_demo_engine()
    ingestion = WardPulseIngestionService(engine)

    csv_file = tmp_path / "departmental_observations.csv"
    csv_file.write_text(
        "department_id,observed_at,metric,value,unit,source\n"
        "DEP-001,2026-11-10T10:00:00+00:00,"
        "overtime_hours,12,hours,test_source\n"
        "DEP-001,2026-11-11T10:00:00+00:00,"
        "staff_absence_count,3,staff absences,test_source\n",
        encoding="utf-8",
    )

    result = ingestion.ingest_departmental_observations(
        csv_file
    )

    assert result.stored_count == 2
    assert result.storage_failure_count == 0

    overtime = engine.get_observations(
        entity_id="DEP-001",
        metric="overtime_hours",
    )
    absence = engine.get_observations(
        entity_id="DEP-001",
        metric="staff_absence_count",
    )

    assert any(item.value == 12 for item in overtime)
    assert any(item.value == 3 for item in absence)

    service = WardPulseSurveillance(engine)

    report = service.run(
        baseline_start=datetime(
            2026, 10, 25, tzinfo=timezone.utc
        ),
        baseline_end=datetime(
            2026, 10, 31, 23, 59, tzinfo=timezone.utc
        ),
        current_start=datetime(
            2026, 11, 1, tzinfo=timezone.utc
        ),
        current_end=datetime(
            2026, 11, 15, 23, 59, tzinfo=timezone.utc
        ),
    )

    assert report.departments_monitored == 2
    assert len(report.departments) == 2
