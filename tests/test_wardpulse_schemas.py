
from pulsecore.applications.wardpulse.schemas import (
    DepartmentSchema,
)


def test_department_entity_exposes_external_identifier():
    department = DepartmentSchema(
        id="DEPT001",
        facility_id="FAC001",
        name="Emergency Department",
    )

    entity = department.to_entity()

    assert entity.id == "DEPT001"
    assert entity.entity_type == "department"
    assert entity.attributes["department_id"] == "DEPT001"
    assert entity.attributes["facility_id"] == "FAC001"
