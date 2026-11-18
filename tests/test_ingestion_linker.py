
import pytest

from pulsecore.domain.models import Entity
from pulsecore.ingestion.linker import EntityLinker


@pytest.fixture
def linker():
    return EntityLinker()


@pytest.fixture
def entities():
    return [
        Entity(
            id="pulse-001",
            entity_type="employee",
            name="Employee One",
            attributes={"employee_id": "EMP001"},
        ),
        Entity(
            id="pulse-002",
            entity_type="employee",
            name="Employee Two",
            attributes={"employee_id": "EMP002"},
        ),
        Entity(
            id="pulse-003",
            entity_type="department",
            name="Emergency",
            attributes={"department_id": "DEPT001"},
        ),
    ]


def test_links_imported_records_to_existing_entities(linker, entities):
    rows = [
        {"employee_id": "EMP001", "worked_hours": 40},
        {"employee_id": "EMP002", "worked_hours": 36},
    ]

    result = linker.link(
        rows=rows,
        entities=entities,
        external_id_field="employee_id",
        entity_type="employee",
    )

    assert result.linked_count == 2
    assert result.unmatched_count == 0
    assert result.linked_rows[0]["entity_id"] == "pulse-001"
    assert result.linked_rows[1]["entity_id"] == "pulse-002"


def test_unmatched_identifier_is_reported(linker, entities):
    rows = [{"employee_id": "EMP999"}]

    result = linker.link(
        rows=rows,
        entities=entities,
        external_id_field="employee_id",
        entity_type="employee",
    )

    assert result.linked_count == 0
    assert result.unmatched_count == 1
    assert result.issues[0].code == "entity_not_found"


def test_missing_identifier_is_reported(linker, entities):
    rows = [{"worked_hours": 40}]

    result = linker.link(
        rows=rows,
        entities=entities,
        external_id_field="employee_id",
        entity_type="employee",
    )

    assert result.unmatched_count == 1
    assert result.issues[0].code == "missing_external_id"


def test_entity_attribute_can_differ_from_source_column(
    linker,
    entities,
):
    rows = [{"staff_code": "EMP001"}]

    result = linker.link(
        rows=rows,
        entities=entities,
        external_id_field="staff_code",
        entity_attribute="employee_id",
        entity_type="employee",
    )

    assert result.linked_count == 1
    assert result.linked_rows[0]["entity_id"] == "pulse-001"


def test_entity_type_filter_prevents_wrong_entity_linking(
    linker,
    entities,
):
    rows = [{"employee_id": "EMP001"}]

    result = linker.link(
        rows=rows,
        entities=entities,
        external_id_field="employee_id",
        entity_type="department",
    )

    assert result.linked_count == 0
    assert result.issues[0].code == "entity_not_found"


def test_duplicate_entity_identifiers_raise_error(linker):
    duplicate_entities = [
        Entity(
            id="pulse-001",
            entity_type="employee",
            name="Employee One",
            attributes={"employee_id": "EMP001"},
        ),
        Entity(
            id="pulse-002",
            entity_type="employee",
            name="Employee Duplicate",
            attributes={"employee_id": "EMP001"},
        ),
    ]

    with pytest.raises(ValueError, match="Multiple entities"):
        linker.link(
            rows=[{"employee_id": "EMP001"}],
            entities=duplicate_entities,
            external_id_field="employee_id",
            entity_type="employee",
        )


def test_linking_does_not_modify_original_rows(linker, entities):
    rows = [{"employee_id": "EMP001"}]

    result = linker.link(
        rows=rows,
        entities=entities,
        external_id_field="employee_id",
        entity_type="employee",
    )

    assert "entity_id" not in rows[0]
    assert result.linked_rows[0]["entity_id"] == "pulse-001"


def test_existing_conflicting_entity_id_is_not_overwritten(
    linker,
    entities,
):
    rows = [
        {
            "employee_id": "EMP001",
            "entity_id": "some-other-id",
        }
    ]

    result = linker.link(
        rows=rows,
        entities=entities,
        external_id_field="employee_id",
        entity_type="employee",
    )

    assert result.linked_count == 0
    assert result.issues[0].code == "entity_id_conflict"


def test_whitespace_in_external_identifiers_is_normalized(
    linker,
    entities,
):
    rows = [{"employee_id": " EMP001 "}]

    result = linker.link(
        rows=rows,
        entities=entities,
        external_id_field="employee_id",
        entity_type="employee",
    )

    assert result.linked_count == 1
    assert result.linked_rows[0]["entity_id"] == "pulse-001"


def test_entity_without_external_identifier_is_ignored(linker):
    entities_without_identifier = [
        Entity(
            id="pulse-001",
            entity_type="employee",
            name="Employee One",
        )
    ]

    result = linker.link(
        rows=[{"employee_id": "EMP001"}],
        entities=entities_without_identifier,
        external_id_field="employee_id",
        entity_type="employee",
    )

    assert result.linked_count == 0
    assert result.issues[0].code == "entity_not_found"
