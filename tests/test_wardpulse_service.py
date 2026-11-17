
from datetime import datetime, timezone

import pytest

from pulsecore.applications.wardpulse.demo_data import create_demo_engine
from pulsecore.applications.wardpulse.service import WardPulseSurveillance


@pytest.fixture
def surveillance():
    engine = create_demo_engine()
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
            2026, 11, 7, 23, 59, tzinfo=timezone.utc
        ),
    )

    return engine, service, report


def test_surveillance_pipeline_monitors_all_departments(surveillance):
    _, _, report = surveillance

    assert report.departments_monitored == 2
    assert len(report.departments) == 2


def test_pipeline_generates_risk_findings(surveillance):
    _, _, report = surveillance

    emergency = next(
        item for item in report.departments
        if item.entity_id == "DEP-001"
    )

    medical = next(
        item for item in report.departments
        if item.entity_id == "DEP-002"
    )

    assert emergency.assessment.risk_level.value == "critical"
    assert len(emergency.alerts) == 5
    assert len(emergency.recommendations) == 4

    assert medical.assessment.alert_count == 0
    assert medical.recommendations == []


def test_pipeline_persists_alerts_and_recommendations(surveillance):
    engine, _, report = surveillance

    assert len(engine.get_alerts()) == 5
    assert len(engine.get_recommendations()) == 4

    assert len(engine.get_alerts("DEP-001")) == 5
    assert len(engine.get_recommendations("DEP-001")) == 4


def test_recommendation_can_become_tracked_action(surveillance):
    engine, service, report = surveillance

    recommendation = report.departments[0].recommendations[0]

    action = service.create_action(
        recommendation_id=recommendation.id,
        assigned_to="Environmental Health Officer",
    )

    assert action.entity_id == recommendation.entity_id
    assert action.recommendation_id == recommendation.id
    assert action.status == "pending"
    assert action.assigned_to == "Environmental Health Officer"

    assert len(engine.get_actions()) == 1


def test_action_status_can_be_updated(surveillance):
    engine, service, report = surveillance

    recommendation = report.departments[0].recommendations[0]
    action = service.create_action(recommendation.id)

    updated = engine.update_action_status(
        action.id,
        "in_progress",
    )

    assert updated.status == "in_progress"
    assert engine.get_actions()[0].status == "in_progress"


def test_action_can_be_completed(surveillance):
    engine, service, report = surveillance

    recommendation = report.departments[0].recommendations[0]
    action = service.create_action(recommendation.id)

    updated = engine.update_action_status(
        action.id,
        "completed",
    )

    assert updated.status == "completed"


def test_invalid_action_status_is_rejected(surveillance):
    engine, service, report = surveillance

    recommendation = report.departments[0].recommendations[0]
    action = service.create_action(recommendation.id)

    with pytest.raises(ValueError):
        engine.update_action_status(action.id, "started")


def test_unknown_recommendation_cannot_create_action(surveillance):
    _, service, _ = surveillance

    with pytest.raises(KeyError):
        service.create_action("UNKNOWN-RECOMMENDATION")
