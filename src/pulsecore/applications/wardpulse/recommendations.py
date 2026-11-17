
from pulsecore.domain.models import (
    Alert,
    Recommendation,
)
from pulsecore.intelligence.evaluator import RiskAssessment


RECOMMENDATION_POLICIES = {
    "workforce": (
        "Review staffing coverage and workload distribution",
        "Review staffing levels, shift allocation and overtime patterns. "
        "Consider temporary staffing adjustments and staff wellbeing "
        "support where appropriate.",
    ),
    "clinical_service": (
        "Investigate the increase in respiratory cases",
        "Review aggregated respiratory case trends, reinforce "
        "appropriate infection prevention measures and assess whether "
        "additional clinical or surveillance capacity is required.",
    ),
    "environmental": (
        "Investigate environmental exposure conditions",
        "Verify environmental readings, inspect ventilation and "
        "air-quality controls, and coordinate with the relevant "
        "environmental health team.",
    ),
    "workplace_safety": (
        "Review workplace safety incidents",
        "Investigate reported incident patterns, inspect relevant "
        "work areas and implement proportionate corrective measures.",
    ),
}


def generate_wardpulse_recommendations(
    assessment: RiskAssessment,
    alerts: list[Alert],
) -> list[Recommendation]:
    """Generate preventive recommendations from triggered signal categories."""

    if assessment.alert_count == 0:
        return []

    recommendations = []

    for category in assessment.signal_categories:
        policy = RECOMMENDATION_POLICIES.get(category)

        if policy is None:
            continue

        title, description = policy

        recommendations.append(
            Recommendation(
                entity_id=assessment.entity_id,
                title=title,
                description=description,
                priority=assessment.risk_level,
                rationale=(
                    f"{assessment.summary} "
                    "This recommendation supports early preventive "
                    "review and does not establish causation."
                ),
            )
        )

    return recommendations
