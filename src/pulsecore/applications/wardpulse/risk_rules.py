
from pulsecore.domain.models import Rule, Severity


def get_wardpulse_rules() -> list[Rule]:
    """Initial demonstration thresholds for WardPulse."""

    return [
        Rule(
            id="WP-RULE-001",
            name="Elevated Staff Overtime",
            metric="overtime_hours",
            operator="gt",
            threshold=90,
            severity=Severity.HIGH,
        ),
        Rule(
            id="WP-RULE-002",
            name="Elevated Staff Absence",
            metric="staff_absence_count",
            operator="gt",
            threshold=7,
            severity=Severity.HIGH,
        ),
        Rule(
            id="WP-RULE-003",
            name="Increase in Respiratory Cases",
            metric="respiratory_case_count",
            operator="gt",
            threshold=30,
            severity=Severity.HIGH,
        ),
        Rule(
            id="WP-RULE-004",
            name="Poor Air Quality",
            metric="air_quality_index",
            operator="gt",
            threshold=75,
            severity=Severity.HIGH,
        ),
        Rule(
            id="WP-RULE-005",
            name="Occupational Safety Incidents",
            metric="occupational_incident_count",
            operator="gt",
            threshold=3,
            severity=Severity.MEDIUM,
        ),
    ]
