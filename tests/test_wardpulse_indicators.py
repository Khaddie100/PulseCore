
from datetime import datetime, timezone

from pulsecore.applications.wardpulse.demo_data import (
    create_demo_engine,
)
from pulsecore.applications.wardpulse.indicators import (
    get_wardpulse_indicators,
)
from pulsecore.intelligence import AnalyticsEngine


def test_wardpulse_defines_multiple_signal_categories():
    indicators = get_wardpulse_indicators()

    categories = {
        indicator.metadata["signal_category"]
        for indicator in indicators
    }

    assert len(indicators) == 5
    assert categories == {
        "workforce",
        "clinical_service",
        "environmental",
        "workplace_safety",
    }


def test_demo_dataset_contains_historical_observations():
    engine = create_demo_engine()

    observations = engine.get_observations()

    assert len(observations) == 140
    assert len(engine.list_entities()) == 6

    metrics = {item.metric for item in observations}

    assert metrics == {
        "overtime_hours",
        "staff_absence_count",
        "respiratory_case_count",
        "air_quality_index",
        "occupational_incident_count",
    }


def test_emergency_department_shows_multiple_rising_signals():
    engine = create_demo_engine()
    department = engine.get_entity("DEP-001")
    observations = engine.get_observations()

    analytics = AnalyticsEngine()
    indicators = get_wardpulse_indicators()

    baseline_start = datetime(
        2026, 10, 25, tzinfo=timezone.utc
    )
    baseline_end = datetime(
        2026, 10, 31, 23, 59, tzinfo=timezone.utc
    )
    current_start = datetime(
        2026, 11, 1, tzinfo=timezone.utc
    )
    current_end = datetime(
        2026, 11, 7, 23, 59, tzinfo=timezone.utc
    )

    results = [
        analytics.compare(
            indicator=indicator,
            entity=department,
            observations=observations,
            baseline_start=baseline_start,
            baseline_end=baseline_end,
            current_start=current_start,
            current_end=current_end,
        )
        for indicator in indicators
    ]

    rising_results = [
        result for result in results
        if result.trend == "increasing"
    ]

    assert len(rising_results) == 5
    assert all(
        result.status == "calculated"
        for result in results
    )


def test_medical_ward_has_a_different_signal_pattern():
    engine = create_demo_engine()
    department = engine.get_entity("DEP-002")
    observations = engine.get_observations()

    analytics = AnalyticsEngine()

    results = [
        analytics.compare(
            indicator=indicator,
            entity=department,
            observations=observations,
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
                2026, 11, 7, 23, 59, tzinfo=timezone.utc
            ),
        )
        for indicator in get_wardpulse_indicators()
    ]

    assert any(
        result.trend == "stable"
        for result in results
    )
    assert any(
        result.trend == "increasing"
        for result in results
    )
