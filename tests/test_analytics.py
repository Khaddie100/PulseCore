
from datetime import datetime, timezone, timedelta

import pytest

from pulsecore.domain.models import Entity, Indicator, Observation
from pulsecore.intelligence import AnalyticsEngine


@pytest.fixture
def entity():
    return Entity(
        id="DEP-001",
        entity_type="department",
        name="Emergency Department",
    )


@pytest.fixture
def indicator():
    return Indicator(
        id="IND-001",
        name="Department Overtime",
        entity_type="department",
        metric="overtime_hours",
        unit="hours",
        metadata={"aggregation": "average"},
    )


@pytest.fixture
def periods():
    baseline_start = datetime(2026, 11, 1, tzinfo=timezone.utc)
    baseline_end = datetime(2026, 11, 7, tzinfo=timezone.utc)
    current_start = datetime(2026, 11, 8, tzinfo=timezone.utc)
    current_end = datetime(2026, 11, 14, tzinfo=timezone.utc)

    return (
        baseline_start,
        baseline_end,
        current_start,
        current_end,
    )


@pytest.fixture
def observations():
    start = datetime(2026, 11, 1, tzinfo=timezone.utc)

    values = [
        (1, 10),
        (3, 10),
        (8, 20),
        (10, 20),
    ]

    return [
        Observation(
            id=f"OBS-{day}",
            entity_id="DEP-001",
            metric="overtime_hours",
            value=value,
            observed_at=start + timedelta(days=day - 1),
        )
        for day, value in values
    ]


def compare(engine, indicator, entity, observations, periods):
    return engine.compare(
        indicator=indicator,
        entity=entity,
        observations=observations,
        baseline_start=periods[0],
        baseline_end=periods[1],
        current_start=periods[2],
        current_end=periods[3],
    )


def test_detects_increasing_trend(
    entity, indicator, observations, periods
):
    result = compare(
        AnalyticsEngine(), indicator, entity, observations, periods
    )

    assert result.baseline.value == 10
    assert result.current.value == 20
    assert result.absolute_deviation == 10
    assert result.percentage_deviation == 100
    assert result.trend == "increasing"


def test_detects_decreasing_trend(
    entity, indicator, observations, periods
):
    observations = [
        Observation(
            entity_id="DEP-001",
            metric="overtime_hours",
            value=value,
            observed_at=datetime(2026, 11, day, tzinfo=timezone.utc),
        )
        for day, value in [(2, 20), (9, 10)]
    ]

    result = compare(
        AnalyticsEngine(), indicator, entity, observations, periods
    )

    assert result.trend == "decreasing"
    assert result.percentage_deviation == -50


def test_detects_stable_trend(
    entity, indicator, observations, periods
):
    observations = [
        Observation(
            entity_id="DEP-001",
            metric="overtime_hours",
            value=value,
            observed_at=datetime(2026, 11, day, tzinfo=timezone.utc),
        )
        for day, value in [(2, 100), (9, 103)]
    ]

    result = compare(
        AnalyticsEngine(stability_tolerance=5),
        indicator,
        entity,
        observations,
        periods,
    )

    assert result.trend == "stable"


def test_handles_missing_current_data(
    entity, indicator, periods
):
    observations = [
        Observation(
            entity_id="DEP-001",
            metric="overtime_hours",
            value=10,
            observed_at=datetime(2026, 11, 2, tzinfo=timezone.utc),
        )
    ]

    result = compare(
        AnalyticsEngine(), indicator, entity, observations, periods
    )

    assert result.status == "insufficient_data"
    assert result.trend == "insufficient_data"


def test_handles_zero_baseline(
    entity, indicator, periods
):
    observations = [
        Observation(
            entity_id="DEP-001",
            metric="overtime_hours",
            value=value,
            observed_at=datetime(2026, 11, day, tzinfo=timezone.utc),
        )
        for day, value in [(2, 0), (9, 10)]
    ]

    result = compare(
        AnalyticsEngine(), indicator, entity, observations, periods
    )

    assert result.status == "zero_baseline"
    assert result.trend == "increasing"
    assert result.percentage_deviation is None


def test_rejects_overlapping_periods(
    entity, indicator, observations
):
    with pytest.raises(ValueError):
        AnalyticsEngine().compare(
            indicator,
            entity,
            observations,
            datetime(2026, 11, 1, tzinfo=timezone.utc),
            datetime(2026, 11, 9, tzinfo=timezone.utc),
            datetime(2026, 11, 8, tzinfo=timezone.utc),
            datetime(2026, 11, 14, tzinfo=timezone.utc),
        )


def test_rejects_invalid_period_order(
    entity, indicator, observations, periods
):
    with pytest.raises(ValueError):
        AnalyticsEngine().compare(
            indicator,
            entity,
            observations,
            periods[1],
            periods[0],
            periods[2],
            periods[3],
        )


def test_rejects_negative_stability_tolerance():
    with pytest.raises(ValueError):
        AnalyticsEngine(stability_tolerance=-1)
