
from datetime import datetime

from pydantic import BaseModel, Field

from pulsecore.core.engine import PulseCoreEngine
from pulsecore.domain.models import (
    Action,
    Alert,
    Recommendation,
)
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
    AnalyticsResult,
    RiskAssessment,
)


class DepartmentSurveillanceResult(BaseModel):
    entity_id: str
    analytics: list[AnalyticsResult] = Field(default_factory=list)
    alerts: list[Alert] = Field(default_factory=list)
    assessment: RiskAssessment
    recommendations: list[Recommendation] = Field(default_factory=list)


class SurveillanceReport(BaseModel):
    generated_at: datetime
    baseline_start: datetime
    baseline_end: datetime
    current_start: datetime
    current_end: datetime
    departments_monitored: int
    departments: list[DepartmentSurveillanceResult] = Field(
        default_factory=list
    )


class WardPulseSurveillance:
    """Coordinates the complete WardPulse surveillance workflow."""

    def __init__(self, engine: PulseCoreEngine):
        self.engine = engine
        self.analytics = AnalyticsEngine()
        self.evaluator = RiskEvaluator()

    def run(
        self,
        baseline_start: datetime,
        baseline_end: datetime,
        current_start: datetime,
        current_end: datetime,
    ) -> SurveillanceReport:

        indicators = get_wardpulse_indicators()
        rules = get_wardpulse_rules()

        departments = self.engine.list_entities(
            entity_type="department"
        )

        report_results = []

        for department in departments:
            observations = self.engine.get_observations(
                entity_id=department.id
            )

            analytics_results = [
                self.analytics.compare(
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

            alerts = self.evaluator.evaluate(
                analytics_results,
                indicators,
                rules,
            )

            assessment = self.evaluator.assess(
                department.id,
                alerts,
                rules,
                indicators,
            )

            recommendations = generate_wardpulse_recommendations(
                assessment,
                alerts,
            )

            for alert in alerts:
                self.engine.record_alert(alert)

            for recommendation in recommendations:
                self.engine.record_recommendation(recommendation)

            report_results.append(
                DepartmentSurveillanceResult(
                    entity_id=department.id,
                    analytics=analytics_results,
                    alerts=alerts,
                    assessment=assessment,
                    recommendations=recommendations,
                )
            )

        return SurveillanceReport(
            generated_at=datetime.now().astimezone(),
            baseline_start=baseline_start,
            baseline_end=baseline_end,
            current_start=current_start,
            current_end=current_end,
            departments_monitored=len(departments),
            departments=report_results,
        )

    def create_action(
        self,
        recommendation_id: str,
        assigned_to: str | None = None,
    ) -> Action:
        """Convert an existing recommendation into a tracked action."""

        recommendation = next(
            (
                item for item in self.engine.get_recommendations()
                if item.id == recommendation_id
            ),
            None,
        )

        if recommendation is None:
            raise KeyError(
                f"Recommendation '{recommendation_id}' not found."
            )

        action = Action(
            entity_id=recommendation.entity_id,
            recommendation_id=recommendation.id,
            description=recommendation.description,
            assigned_to=assigned_to,
            status="pending",
        )

        return self.engine.record_action(action)
