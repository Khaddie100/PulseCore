
from pydantic import BaseModel, Field

from pulsecore.domain.models import Entity


class FacilitySchema(BaseModel):
    id: str
    name: str
    facility_type: str | None = None
    location: str | None = None

    def to_entity(self) -> Entity:
        return Entity(
            id=self.id,
            entity_type="facility",
            name=self.name,
            attributes={
                "facility_type": self.facility_type,
                "location": self.location
            }
        )


class DepartmentSchema(BaseModel):
    id: str
    facility_id: str
    name: str

    def to_entity(self) -> Entity:
        return Entity(
            id=self.id,
            entity_type="department",
            name=self.name,
            attributes={
                "facility_id": self.facility_id,
                "department_id": self.id,
            }

        )


class HealthcareWorkerSchema(BaseModel):
    id: str
    department_id: str
    role: str
    employment_status: str = "active"
    employment_type: str | None = None

    def to_entity(self) -> Entity:
        return Entity(
            id=self.id,
            entity_type="healthcare_worker",
            name=f"Worker {self.id}",
            attributes={
                "department_id": self.department_id,
                "role": self.role,
                "employment_status": self.employment_status,
                "employment_type": self.employment_type
            }
        )
