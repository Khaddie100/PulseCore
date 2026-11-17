
from datetime import datetime, timezone, timedelta

import pytest

from pulsecore.domain.models import Entity, Indicator, Observation
from pulsecore.intelligence import IndicatorCalculator


@pytest.fixture
def calculator():
    return IndicatorCalculator()


@pytest.fixture
def department():
    return Entity(
        id="DEP-001",
        entity_type="department",
        name="Emergency Department",
    )


@pytest.fixture
def observations():
    start = datetime(2026, 11, 1, tzinfo=timezone.utc)

    return [
        Observation(
            id="OBS-001",
            entity_id="DEP-001",
            metric="Overtime Hours",
            value=10,
            unit="hours",
            observed_at=start,
        ),
        Observation(
            id="OBS-002",
            entity_id="DEP-001",
            metric="overtime_hours",
            value=20,
            unit="hours",
            observed_at=start + timedelta(days=1),
        ),
        Observation(
            id="OBS-003",
            entity_id="DEP-001",
            metric="overtime_hours",
            value=30,
            unit="hours",
            observed_at=start + timedelta(days=2),
        ),
        Observation(
            id="OBS-004",
            entity_id="DEP-002",
            metric="overtime_hours",
            value=100,
            unit="hours",
            observed_at=start + timedelta(days=2),
        ),
    ]


def make_indicator(aggregation):
    return Indicator(
        id=f"IND-{aggregation}",
        name="Department Overtime",
        entity_type="department",
        metric="overtime_hours",
        unit="hours",
        metadata={"aggregation": aggregation},
    )


def test_calculates_sum(
    calculator, department, observations
):
    result = calculator.calculate(
        make_indicator("sum"),
        department,
        observations,
    )

    assert result.value == 60
    assert result.observation_count == 3
    assert result.status == "calculated"


def test_calculates_average(
    calculator, department, observations
):
    result = calculator.calculate(
        make_indicator("average"),
        department,
        observations,
    )

    assert result.value == 20


def test_calculates_count(
    calculator, department, observations
):
    result = calculator.calculate(
        make_indicator("count"),
        department,
        observations,
    )

    assert result.value == 3


def test_calculates_minimum_and_maximum(
    calculator, department, observations
):
    minimum = calculator.calculate(
        make_indicator("minimum"),
        department,
        observations,
    )

    maximum = calculator.calculate(
        make_indicator("maximum"),
        department,
        observations,
    )

    assert minimum.value == 10
    assert maximum.value == 30


def test_calculates_latest(
    calculator, department, observations
):
    result = calculator.calculate(
        make_indicator("latest"),
        department,
        observations,
    )

    assert result.value == 30


def test_ignores_observations_from_other_entities(
    calculator, department, observations
):
    result = calculator.calculate(
        make_indicator("sum"),
        department,
        observations,
    )

    assert result.value == 60
    assert "OBS-004" not in result.observation_ids


def test_returns_no_data_when_metric_is_missing(
    calculator, department
):
    result = calculator.calculate(
        make_indicator("sum"),
        department,
        [],
    )

    assert result.value is None
    assert result.status == "no_data"
    assert result.observation_count == 0


def test_rejects_wrong_entity_type(
    calculator, observations
):
    facility = Entity(
        id="FAC-001",
        entity_type="facility",
        name="Demo Hospital",
    )

    with pytest.raises(ValueError):
        calculator.calculate(
            make_indicator("sum"),
            facility,
            observations,
        )


def test_rejects_unsupported_aggregation(
    calculator, department, observations
):
    indicator = make_indicator("median")
    indicator.metadata["aggregation"] = "median"

    with pytest.raises(ValueError):
        calculator.calculate(
            indicator,
            department,
            observations,
        )


def test_result_tracks_contributing_observations(
    calculator, department, observations
):
    result = calculator.calculate(
        make_indicator("sum"),
        department,
        observations,
    )

    assert result.observation_ids == [
        "OBS-001",
        "OBS-002",
        "OBS-003",
    ]
    assert result.period_start is not None
    assert result.period_end is not None
