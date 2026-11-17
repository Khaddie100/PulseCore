
import pytest

from pulsecore.core.engine import PulseCoreEngine
from pulsecore.core.registry import ModuleManifest
from pulsecore.domain.models import Entity, Observation
from pulsecore.applications.wardpulse.module import WardPulseModule
from pulsecore.applications.wardpulse.schemas import (
    HealthcareWorkerSchema
)
from pulsecore.applications.wardpulse.demo_data import (
    create_demo_engine
)


def test_entity_registration():
    engine = PulseCoreEngine()

    entity = Entity(
        id="E001",
        entity_type="Hospital",
        name="Test Hospital"
    )

    result = engine.register_entity(entity)

    assert result.entity_type == "hospital"
    assert engine.get_entity("E001").name == "Test Hospital"


def test_duplicate_entity_rejected():
    engine = PulseCoreEngine()

    entity = Entity(
        id="E001",
        entity_type="hospital",
        name="Test Hospital"
    )

    engine.register_entity(entity)

    with pytest.raises(ValueError):
        engine.register_entity(entity)


def test_entity_filtering():
    engine = PulseCoreEngine()

    engine.register_entity(
        Entity(
            id="E001",
            entity_type="hospital",
            name="Hospital A"
        )
    )

    engine.register_entity(
        Entity(
            id="E002",
            entity_type="department",
            name="Emergency"
        )
    )

    result = engine.list_entities("hospital")

    assert len(result) == 1
    assert result[0].id == "E001"


def test_observation_registration():
    engine = PulseCoreEngine()

    engine.register_entity(
        Entity(
            id="DEP001",
            entity_type="department",
            name="Emergency"
        )
    )

    observation = Observation(
        entity_id="DEP001",
        metric="Overtime Hours",
        value=12,
        unit="hours"
    )

    result = engine.record_observation(observation)

    assert result.metric == "overtime_hours"
    assert result.value == 12


def test_observation_requires_registered_entity():
    engine = PulseCoreEngine()

    observation = Observation(
        entity_id="UNKNOWN",
        metric="Overtime Hours",
        value=12
    )

    with pytest.raises(ValueError):
        engine.record_observation(observation)


def test_observation_filtering():
    engine = PulseCoreEngine()

    engine.register_entity(
        Entity(
            id="DEP001",
            entity_type="department",
            name="Emergency"
        )
    )

    engine.record_observation(
        Observation(
            entity_id="DEP001",
            metric="Overtime Hours",
            value=12
        )
    )

    engine.record_observation(
        Observation(
            entity_id="DEP001",
            metric="Staff Absence Count",
            value=2
        )
    )

    result = engine.get_observations(
        entity_id="DEP001",
        metric="Overtime Hours"
    )

    assert len(result) == 1
    assert result[0].value == 12


def test_wardpulse_registration():
    engine = PulseCoreEngine()

    manifest = engine.register_module(WardPulseModule())

    assert manifest.module_id == "wardpulse"
    assert "department" in manifest.supported_entity_types


def test_invalid_module_rejected():
    engine = PulseCoreEngine()

    class InvalidModule:
        manifest = {"name": "Invalid"}

    with pytest.raises(ValueError):
        engine.register_module(InvalidModule())


def test_worker_schema_conversion():
    worker = HealthcareWorkerSchema(
        id="WRK001",
        department_id="DEP001",
        role="Nurse"
    )

    entity = worker.to_entity()

    assert entity.entity_type == "healthcare_worker"
    assert entity.attributes["department_id"] == "DEP001"


def test_demo_dataset():
    engine = create_demo_engine()

    assert len(engine.list_entities()) == 6
    assert len(engine.get_observations()) == 140
    assert len(engine.registry.list_modules()) == 1

    metrics = {
        observation.metric
        for observation in engine.get_observations()
    }

    assert metrics == {
        "overtime_hours",
        "staff_absence_count",
        "respiratory_case_count",
        "air_quality_index",
        "occupational_incident_count",
    }

def test_module_duplicate_rejected():
    engine = PulseCoreEngine()

    engine.register_module(WardPulseModule())

    with pytest.raises(ValueError):
        engine.register_module(WardPulseModule())
