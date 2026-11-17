
from datetime import datetime, timezone

from pulsecore.domain.models import Rule, Severity
from pulsecore.applications.wardpulse.demo_data import create_demo_engine
from pulsecore.applications.wardpulse.indicators import (
    get_wardpulse_indicators,
)
from pulsecore.applications.wardpulse.risk_rules import (
    get_wardpulse_rules,
)
from pulsecore.applications.wardpulse.recommendations import (
    generate_wardpulse_recommendations,
)
from pulsecore.intelligence import (
    AnalyticsEngine,
    RiskEvaluator,
    RuleEngine,
)


def get_analytics_results(engine, department_id):
    department = engine.get_entity(department_id)
    observations = engine.get_observations()
    analytics = AnalyticsEngine()

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

    return [
        analytics.compare(
            indicator=indicator,
            entity=department,
            observations=observations,
            baseline_start=baseline_start,
            baseline_end=baseline_end,
            current_start=current_start,
            current_end=current_end,
        )
        for indicator in get_wardpulse_indicators()
    ]


def test_rule_engine_supports_operators():
    rule = Rule(
        id="RULE-001",
        name="Test threshold",
        metric="test_metric",
        operator="gt",
        threshold=10,
    )

    assert RuleEngine.evaluate(11, rule)
    assert not RuleEngine.evaluate(10, rule)


def test_disabled_rule_does_not_trigger():
    rule = Rule(
        id="RULE-002",
        name="Disabled rule",
        metric="test_metric",
        operator="gt",
        threshold=10,
        enabled=False,
    )

    assert not RuleEngine.evaluate(20, rule)


def test_rule_engine_rejects_unknown_operator():
    rule = Rule(
        id="RULE-003",
        name="Invalid rule",
        metric="test_metric",
        operator="contains",
        threshold=10,
    )

    try:
        RuleEngine.evaluate(20, rule)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_emergency_department_generates_multiple_alerts():
    engine = create_demo_engine()
    indicators = get_wardpulse_indicators()
    rules = get_wardpulse_rules()

    results = get_analytics_results(engine, "DEP-001")

    evaluator = RiskEvaluator()
    alerts = evaluator.evaluate(results, indicators, rules)

    assert len(alerts) == 5
    assert all(alert.entity_id == "DEP-001" for alert in alerts)


def test_emergency_department_receives_combined_risk_assessment():
    engine = create_demo_engine()
    indicators = get_wardpulse_indicators()
    rules = get_wardpulse_rules()

    results = get_analytics_results(engine, "DEP-001")

    evaluator = RiskEvaluator()
    alerts = evaluator.evaluate(results, indicators, rules)

    assessment = evaluator.assess(
        entity_id="DEP-001",
        alerts=alerts,
        rules=rules,
        indicators=indicators,
    )

    assert assessment.risk_level == Severity.CRITICAL
    assert assessment.alert_count == 5
    assert len(assessment.signal_categories) == 4


def test_medical_ward_does_not_trigger_thresholds():
    engine = create_demo_engine()
    indicators = get_wardpulse_indicators()
    rules = get_wardpulse_rules()

    results = get_analytics_results(engine, "DEP-002")

    evaluator = RiskEvaluator()
    alerts = evaluator.evaluate(results, indicators, rules)

    assert alerts == []


def test_recommendations_are_generated_from_risk_assessment():
    engine = create_demo_engine()
    indicators = get_wardpulse_indicators()
    rules = get_wardpulse_rules()

    results = get_analytics_results(engine, "DEP-001")

    evaluator = RiskEvaluator()
    alerts = evaluator.evaluate(results, indicators, rules)

    assessment = evaluator.assess(
        "DEP-001",
        alerts,
        rules,
        indicators,
    )

    recommendations = generate_wardpulse_recommendations(
        assessment,
        alerts,
    )

    assert len(recommendations) == 4
    assert all(
        item.priority == Severity.CRITICAL
        for item in recommendations
    )


def test_no_alerts_generate_no_recommendations():
    engine = create_demo_engine()
    indicators = get_wardpulse_indicators()
    rules = get_wardpulse_rules()

    evaluator = RiskEvaluator()
    assessment = evaluator.assess(
        "DEP-002",
        [],
        rules,
        indicators,
    )

    recommendations = generate_wardpulse_recommendations(
        assessment,
        [],
    )

    assert recommendations == []
