
from dataclasses import dataclass, field
from typing import Any

from pulsecore.domain.models import Entity


@dataclass
class EntityLinkIssue:
    """Describes a record that could not be linked to an entity."""

    row_number: int
    external_id: str | None
    code: str
    message: str


@dataclass
class EntityLinkResult:
    """Contains linked records and unresolved linking issues."""

    linked_rows: list[dict[str, Any]] = field(default_factory=list)
    unmatched_rows: list[dict[str, Any]] = field(default_factory=list)
    issues: list[EntityLinkIssue] = field(default_factory=list)

    @property
    def total_rows(self) -> int:
        return len(self.linked_rows) + len(self.unmatched_rows)

    @property
    def linked_count(self) -> int:
        return len(self.linked_rows)

    @property
    def unmatched_count(self) -> int:
        return len(self.unmatched_rows)


class EntityLinker:
    """Links imported records to existing PulseCore entities."""

    @staticmethod
    def _normalize_identifier(value: Any) -> str | None:
        if value is None:
            return None

        normalized = str(value).strip()
        return normalized or None

    def link(
        self,
        rows: list[dict[str, Any]],
        entities: list[Entity],
        external_id_field: str,
        entity_attribute: str | None = None,
        entity_type: str | None = None,
        output_field: str = "entity_id",
    ) -> EntityLinkResult:
        """
        Match imported records to existing entities.

        external_id_field:
            Identifier column in each imported row.

        entity_attribute:
            Attribute on the PulseCore Entity containing the same
            external identifier. Defaults to external_id_field.

        entity_type:
            Optional entity type filter, such as "employee".

        output_field:
            Field added to each successfully linked row.
        """

        if not external_id_field.strip():
            raise ValueError("external_id_field cannot be empty.")

        if not output_field.strip():
            raise ValueError("output_field cannot be empty.")

        attribute_name = entity_attribute or external_id_field

        entity_index: dict[str, Entity] = {}

        for entity in entities:
            if (
                entity_type
                and entity.entity_type.strip().lower()
                != entity_type.strip().lower()
            ):
                continue

            external_id = self._normalize_identifier(
                entity.attributes.get(attribute_name)
            )

            if external_id is None:
                continue

            if external_id in entity_index:
                raise ValueError(
                    "Multiple entities share the external identifier "
                    f"'{external_id}' for attribute '{attribute_name}'."
                )

            entity_index[external_id] = entity

        result = EntityLinkResult()

        for row_number, row in enumerate(rows, start=2):
            external_id = self._normalize_identifier(
                row.get(external_id_field)
            )

            if external_id is None:
                result.unmatched_rows.append(dict(row))
                result.issues.append(
                    EntityLinkIssue(
                        row_number=row_number,
                        external_id=None,
                        code="missing_external_id",
                        message=(
                            f"'{external_id_field}' is missing or empty."
                        ),
                    )
                )
                continue

            entity = entity_index.get(external_id)

            if entity is None:
                result.unmatched_rows.append(dict(row))
                result.issues.append(
                    EntityLinkIssue(
                        row_number=row_number,
                        external_id=external_id,
                        code="entity_not_found",
                        message=(
                            f"No matching entity was found for "
                            f"'{external_id}'."
                        ),
                    )
                )
                continue

            linked_row = dict(row)

            if (
                output_field in linked_row
                and linked_row[output_field] != entity.id
            ):
                result.unmatched_rows.append(dict(row))
                result.issues.append(
                    EntityLinkIssue(
                        row_number=row_number,
                        external_id=external_id,
                        code="entity_id_conflict",
                        message=(
                            f"'{output_field}' already contains a "
                            "different value."
                        ),
                    )
                )
                continue

            linked_row[output_field] = entity.id
            result.linked_rows.append(linked_row)

        return result
