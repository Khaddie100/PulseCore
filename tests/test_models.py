
from pulsecore.domain.models import (
    Entity,
    Observation,
    Indicator,
    Rule,
    Alert,
    Recommendation,
    Action,
    Severity,
)


def test_entity_creation():
    entity = Entity(
        entity_type="hospital",
        name="General Hospital"
    )

    assert entity.name == "General Hospital"
    assert entity.id is not None


def test_observation_creation():
    observation = Observation(
        entity_id="hospital-001",
        metric="patient_wait_time",
        value=45,
        unit="minutes"
    )

    assert observation.value == 45
    assert observation.metric == "patient_wait_time"


def test_rule_creation():
    rule = Rule(
        name="Long waiting time",
        metric="patient_wait_time",
        operator="greater_than",
        threshold=30,
        severity=Severity.HIGH
    )

    assert rule.threshold == 30
    assert rule.enabled is True


def test_alert_creation():
    alert = Alert(
        entity_id="hospital-001",
        rule_id="rule-001",
        message="Waiting time exceeded threshold",
        severity=Severity.HIGH
    )

    assert alert.acknowledged is False


def test_recommendation_creation():
    recommendation = Recommendation(
        entity_id="hospital-001",
        title="Review patient flow",
        description="Investigate prolonged waiting times"
    )

    assert recommendation.priority == Severity.MEDIUM


def test_action_creation():
    action = Action(
        entity_id="hospital-001",
        description="Review staffing allocation"
    )

    assert action.status == "pending"
