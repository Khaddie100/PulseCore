
from pulsecore.domain.models import Indicator


def get_wardpulse_indicators() -> list[Indicator]:
    """Return the indicators monitored by WardPulse."""

    return [
        Indicator(
            id="WP-IND-001",
            name="Staff Absence",
            description="Number of staff absences recorded.",
            entity_type="department",
            metric="staff_absence_count",
            unit="staff absences",
            metadata={
                "aggregation": "sum",
                "signal_category": "workforce",
                "risk_direction": "increase",
            },
        ),
        Indicator(
            id="WP-IND-002",
            name="Staff Overtime",
            description="Total staff overtime hours recorded.",
            entity_type="department",
            metric="overtime_hours",
            unit="hours",
            metadata={
                "aggregation": "sum",
                "signal_category": "workforce",
                "risk_direction": "increase",
            },
        ),
        Indicator(
            id="WP-IND-003",
            name="Respiratory Cases",
            description="Number of respiratory cases recorded by a department.",
            entity_type="department",
            metric="respiratory_case_count",
            unit="cases",
            metadata={
                "aggregation": "sum",
                "signal_category": "clinical_service",
                "risk_direction": "increase",
            },
        ),
        Indicator(
            id="WP-IND-004",
            name="Air Quality Index",
            description="Average air quality index recorded during the period.",
            entity_type="department",
            metric="air_quality_index",
            unit="AQI",
            metadata={
                "aggregation": "average",
                "signal_category": "environmental",
                "risk_direction": "increase",
            },
        ),
        Indicator(
            id="WP-IND-005",
            name="Occupational Incidents",
            description="Number of reported occupational safety incidents.",
            entity_type="department",
            metric="occupational_incident_count",
            unit="incidents",
            metadata={
                "aggregation": "sum",
                "signal_category": "workplace_safety",
                "risk_direction": "increase",
            },
        ),
    ]
