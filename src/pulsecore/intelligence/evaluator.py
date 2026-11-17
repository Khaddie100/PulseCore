
import re
from collections import defaultdict

from pydantic import BaseModel, Field

from pulsecore.domain.models import (
    Alert,
    Indicator,
    Rule,
    Severity,
)
from pulsecore.intelligence.analytics import AnalyticsResult
from pulsecore.intelligence.rules import RuleEngine


class RiskAssessment(BaseModel):
    """Aggregated risk findings for one monitored entity."""

    entity_id: str
    risk_level: Severity
    alert_count: int = 0
    signal_categories: list[str] = Field(default_factory=list)
    alert_ids: list[str] = Field(default_factory=list)
    summary: str = ""


class RiskEvaluator:
    """Evaluates analytical results and combines related risk signals."""

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(
            r"[^a-zA-Z0-9]+",
            "_",
            value.strip(),
        ).strip("_").lower()

    def evaluate(
        self,
        results: list[AnalyticsResult],
        indicators: list[Indicator],
        rules: list[Rule],
    ) -> list[Alert]:
        """Generate explainable alerts from analytical results."""

        indicator_lookup = {
            indicator.id: indicator
            for indicator in indicators
        }

        alerts = []

        for result in results:
            indicator = indicator_lookup.get(result.indicator_id)

            if indicator is None:
                continue

            if result.status != "calculated":
                continue

            if not isinstance(result.current.value, (int, float)):
                continue

            if isinstance(result.current.value, bool):
                continue

            for rule in rules:
                if self._normalize(rule.metric) != self._normalize(
                    indicator.metric
                ):
                    continue

                if not RuleEngine.evaluate(
                    result.current.value,
                    rule,
                ):
                    continue

                category = indicator.metadata.get(
                    "signal_category",
                    "unspecified",
                )

                deviation = result.absolute_deviation
                percentage = result.percentage_deviation

                evidence = (
                    f"Current value: {result.current.value} "
                    f"{indicator.unit or ''}; "
                    f"baseline: {result.baseline.value}; "
                    f"change: {deviation}; "
                    f"percentage change: "
                    f"{percentage if percentage is not None else 'undefined'}%."
                )

                alerts.append(
                    Alert(
                        entity_id=result.entity_id,
                        rule_id=rule.id,
                        message=(
                            f"{indicator.name} exceeded its configured "
                            f"risk condition ({rule.operator} "
                            f"{rule.threshold}). {evidence} "
                            f"Signal category: {category}."
                        ),
                        severity=rule.severity,
                    )
                )

        return alerts

    def assess(
        self,
        entity_id: str,
        alerts: list[Alert],
        rules: list[Rule],
        indicators: list[Indicator],
    ) -> RiskAssessment:
        """Combine triggered alerts into an entity-level risk assessment."""

        entity_alerts = [
            alert for alert in alerts
            if alert.entity_id == entity_id
        ]

        rule_lookup = {
            rule.id: self._normalize(rule.metric)
            for rule in rules
        }

        indicator_lookup = {
            self._normalize(indicator.metric):
                indicator.metadata.get(
                    "signal_category",
                    "unspecified",
                )
            for indicator in indicators
        }

        categories = set()

        for alert in entity_alerts:
            metric = rule_lookup.get(alert.rule_id)

            if metric:
                categories.add(
                    indicator_lookup.get(metric, "unspecified")
                )

        ordered_categories = sorted(categories)
        category_count = len(ordered_categories)

        if category_count >= 4:
            level = Severity.CRITICAL
        elif category_count == 3:
            level = Severity.HIGH
        elif category_count == 2:
            level = Severity.MEDIUM
        elif category_count == 1:
            level = Severity.LOW
        else:
            level = Severity.LOW

        if category_count:
            summary = (
                f"{category_count} distinct signal categories have "
                f"triggered {len(entity_alerts)} alert(s): "
                f"{', '.join(ordered_categories)}."
            )
        else:
            summary = "No configured risk signals were triggered."

        return RiskAssessment(
            entity_id=entity_id,
            risk_level=level,
            alert_count=len(entity_alerts),
            signal_categories=ordered_categories,
            alert_ids=[
                alert.id for alert in entity_alerts
            ],
            summary=summary,
        )
