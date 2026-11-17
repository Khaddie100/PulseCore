
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def generate_id() -> str:
    return str(uuid4())


def current_timestamp() -> datetime:
    return datetime.now(timezone.utc)


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Entity(BaseModel):
    """Any identifiable object PulseCore monitors."""

    id: str = Field(default_factory=generate_id)
    entity_type: str
    name: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=current_timestamp)


class Observation(BaseModel):
    """A recorded event, measurement or data point."""

    id: str = Field(default_factory=generate_id)
    entity_id: str
    metric: str
    value: Any
    unit: str | None = None
    source: str | None = None
    observed_at: datetime = Field(default_factory=current_timestamp)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Indicator(BaseModel):
    """A measurable representation of operational performance."""

    id: str = Field(default_factory=generate_id)
    name: str
    description: str = ""
    entity_type: str
    metric: str
    unit: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Rule(BaseModel):
    """A configurable condition for evaluating observations."""

    id: str = Field(default_factory=generate_id)
    name: str
    description: str = ""
    metric: str
    operator: str
    threshold: float
    severity: Severity = Severity.MEDIUM
    enabled: bool = True


class Alert(BaseModel):
    """A notification generated when a condition is met."""

    id: str = Field(default_factory=generate_id)
    entity_id: str
    rule_id: str
    message: str
    severity: Severity
    triggered_at: datetime = Field(default_factory=current_timestamp)
    acknowledged: bool = False


class Recommendation(BaseModel):
    """An actionable suggestion produced by the engine."""

    id: str = Field(default_factory=generate_id)
    entity_id: str
    title: str
    description: str
    priority: Severity = Severity.MEDIUM
    rationale: str = ""
    created_at: datetime = Field(default_factory=current_timestamp)


class Action(BaseModel):
    """An operational response to a recommendation or alert."""

    id: str = Field(default_factory=generate_id)
    entity_id: str
    description: str
    status: str = "pending"
    assigned_to: str | None = None
    created_at: datetime = Field(default_factory=current_timestamp)
    recommendation_id: str | None = None