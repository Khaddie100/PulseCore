
from typing import Optional
import re

from pulsecore.core.registry import ModuleRegistry
from pulsecore.domain.models import (
    Entity,
    Observation,
    Alert,
    Recommendation,
    Action,
)

class PulseCoreEngine:
    """Central engine for generic operational data management."""

    def __init__(
        self,
        registry: Optional[ModuleRegistry] = None
    ):
        self.registry = registry or ModuleRegistry()

        self._entities: dict[str, Entity] = {}
        self._observations: dict[str, Observation] = {}

        self._alerts: dict[str, Alert] = {}
        self._recommendations: dict[str, Recommendation] = {}
        self._actions: dict[str, Action] = {}

    @staticmethod
    def normalize_name(value: str) -> str:
        """Convert names into consistent lowercase identifiers."""

        normalized = re.sub(
            r"[^a-zA-Z0-9]+",
            "_",
            value.strip()
        ).strip("_").lower()

        if not normalized:
            raise ValueError("Name cannot be empty.")

        return normalized

    def register_entity(self, entity: Entity) -> Entity:
        """Register a new entity."""

        if entity.id in self._entities:
            raise ValueError(
                f"Entity '{entity.id}' already exists."
            )

        normalized_entity = entity.model_copy(
            update={
                "entity_type": self.normalize_name(
                    entity.entity_type
                )
            }
        )

        self._entities[entity.id] = normalized_entity

        return normalized_entity

    def get_entity(self, entity_id: str) -> Entity:
        """Retrieve an entity by ID."""

        if entity_id not in self._entities:
            raise KeyError(
                f"Entity '{entity_id}' not found."
            )

        return self._entities[entity_id]

    def list_entities(
        self,
        entity_type: Optional[str] = None
    ) -> list[Entity]:
        """List all entities or filter by entity type."""

        entities = list(self._entities.values())

        if entity_type:
            normalized_type = self.normalize_name(entity_type)

            entities = [
                entity for entity in entities
                if entity.entity_type == normalized_type
            ]

        return entities

    def record_observation(
        self,
        observation: Observation
    ) -> Observation:
        """Validate and store an observation."""

        if observation.entity_id not in self._entities:
            raise ValueError(
                f"Entity '{observation.entity_id}' "
                "is not registered."
            )

        if observation.id in self._observations:
            raise ValueError(
                f"Observation '{observation.id}' already exists."
            )

        normalized_observation = observation.model_copy(
            update={
                "metric": self.normalize_name(
                    observation.metric
                )
            }
        )

        self._observations[
            normalized_observation.id
        ] = normalized_observation

        return normalized_observation

    def record_alert(self, alert: Alert) -> Alert:
        if alert.id in self._alerts:
            raise ValueError(f"Alert '{alert.id}' already exists.")

        self.get_entity(alert.entity_id)
        self._alerts[alert.id] = alert
        return alert


    def get_alerts(
        self,
        entity_id: Optional[str] = None
    ) -> list[Alert]:
        alerts = list(self._alerts.values())

        if entity_id:
            alerts = [
                alert for alert in alerts
                if alert.entity_id == entity_id
            ]

        return alerts


    def record_recommendation(
        self,
        recommendation: Recommendation
    ) -> Recommendation:
        if recommendation.id in self._recommendations:
            raise ValueError(
                f"Recommendation '{recommendation.id}' already exists."
            )

        self.get_entity(recommendation.entity_id)
        self._recommendations[recommendation.id] = recommendation
        return recommendation


    def get_recommendations(
        self,
        entity_id: Optional[str] = None
    ) -> list[Recommendation]:
        recommendations = list(self._recommendations.values())

        if entity_id:
            recommendations = [
                item for item in recommendations
                if item.entity_id == entity_id
            ]

        return recommendations


    def record_action(self, action: Action) -> Action:
        if action.id in self._actions:
            raise ValueError(f"Action '{action.id}' already exists.")

        self.get_entity(action.entity_id)

        if (
            action.recommendation_id
            and action.recommendation_id not in self._recommendations
        ):
            raise ValueError("Referenced recommendation does not exist.")

        self._actions[action.id] = action
        return action


    def get_actions(self, entity_id: Optional[str] = None) -> list[Action]:
        actions = list(self._actions.values())

        if entity_id:
            actions = [
                action for action in actions
                if action.entity_id == entity_id
            ]

        return actions


    def update_action_status(
        self,
        action_id: str,
        status: str
    ) -> Action:
        allowed_statuses = {
            "pending",
            "in_progress",
            "completed",
            "cancelled",
        }

        if status not in allowed_statuses:
            raise ValueError(
                f"Invalid action status '{status}'."
            )

        if action_id not in self._actions:
            raise KeyError(f"Action '{action_id}' not found.")

        updated_action = self._actions[action_id].model_copy(
            update={"status": status}
        )

        self._actions[action_id] = updated_action
        return updated_action

    def get_observations(
        self,
        entity_id: Optional[str] = None,
        metric: Optional[str] = None
    ) -> list[Observation]:
        """Retrieve observations using optional filters."""

        observations = list(self._observations.values())

        if entity_id:
            observations = [
                item for item in observations
                if item.entity_id == entity_id
            ]

        if metric:
            normalized_metric = self.normalize_name(metric)

            observations = [
                item for item in observations
                if item.metric == normalized_metric
            ]

        return observations

    def register_module(self, module):
        """Register an application module."""

        return self.registry.register(module)
