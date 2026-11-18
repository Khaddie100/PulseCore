
from dataclasses import dataclass, field
from pathlib import Path

from pulsecore.core.engine import PulseCoreEngine
from pulsecore.domain.models import Observation
from pulsecore.ingestion.contracts import DatasetContract
from pulsecore.ingestion.linker import (
    EntityLinkResult,
    EntityLinker,
)
from pulsecore.ingestion.observation_generator import (
    ObservationGenerationResult,
    ObservationGenerator,
)
from pulsecore.ingestion.reader import DatasetReader
from pulsecore.ingestion.validator import (
    DatasetValidationOutput,
    DatasetValidator,
)


@dataclass
class IngestionStorageIssue:
    observation_id: str
    entity_id: str
    metric: str
    message: str


@dataclass
class IngestionPipelineResult:
    validation: DatasetValidationOutput | None = None
    linking: EntityLinkResult | None = None
    generation: ObservationGenerationResult | None = None
    stored_observations: list[Observation] = field(
        default_factory=list
    )
    storage_issues: list[IngestionStorageIssue] = field(
        default_factory=list
    )

    @property
    def stored_count(self) -> int:
        return len(self.stored_observations)

    @property
    def storage_failure_count(self) -> int:
        return len(self.storage_issues)

    @property
    def completed(self) -> bool:
        return (
            self.validation is not None
            and self.linking is not None
            and self.generation is not None
            and self.storage_failure_count == 0
        )


class DatasetIngestionPipeline:
    """Coordinates the generic PulseCore dataset ingestion workflow."""

    def __init__(
        self,
        engine: PulseCoreEngine,
        reader: DatasetReader | None = None,
        validator: DatasetValidator | None = None,
        linker: EntityLinker | None = None,
        observation_generator: ObservationGenerator | None = None,
    ):
        self.engine = engine
        self.reader = reader or DatasetReader()
        self.validator = validator or DatasetValidator()
        self.linker = linker or EntityLinker()
        self.observation_generator = (
            observation_generator or ObservationGenerator()
        )

    def ingest(
        self,
        file_path: str | Path,
        contract: DatasetContract,
        external_id_field: str,
        metric_fields: dict[str, str],
        entity_attribute: str | None = None,
        entity_type: str | None = None,
        sheet_name: str | None = None,
        observed_at_field: str | None = None,
        source: str | None = None,
        source_field: str | None = None,
        unit_by_metric: dict[str, str] | None = None,
        metadata_fields: list[str] | None = None,
        metric_field: str | None = None,
        value_field: str | None = None,
        unit_field: str | None = None,
    ) -> IngestionPipelineResult:
        """Run the complete file-to-observation ingestion workflow."""

        pipeline_result = IngestionPipelineResult()

        # Stage 1: Read source file.
        raw_rows = self.reader.read(
            file_path=file_path,
            contract=contract,
            sheet_name=sheet_name,
        )

        # Stage 2: Validate and normalize records.
        validation = self.validator.validate(
            rows=raw_rows,
            contract=contract,
        )
        pipeline_result.validation = validation

        # No valid rows are available for subsequent processing.
        if not validation.rows:
            return pipeline_result

        # Stage 3: Link records to existing registered entities.
        entities = self.engine.list_entities(
            entity_type=entity_type
        )

        linking = self.linker.link(
            rows=validation.rows,
            entities=entities,
            external_id_field=external_id_field,
            entity_attribute=entity_attribute,
            entity_type=entity_type,
        )
        pipeline_result.linking = linking

        # Stage 4: Generate observations from linked records.
        generation = self.observation_generator.generate(
            rows=linking.linked_rows,
            metric_fields=metric_fields,
            observed_at_field=observed_at_field,
            source=source,
            source_field=source_field,
            unit_by_metric=unit_by_metric,
            metadata_fields=metadata_fields,
            metric_field=metric_field,
            value_field=value_field,
            unit_field=unit_field,
        )
        pipeline_result.generation = generation

        # Stage 5: Store generated observations in PulseCore.
        for observation in generation.observations:
            try:
                self.engine.record_observation(observation)
                pipeline_result.stored_observations.append(
                    observation
                )
            except (ValueError, KeyError) as exc:
                pipeline_result.storage_issues.append(
                    IngestionStorageIssue(
                        observation_id=observation.id,
                        entity_id=observation.entity_id,
                        metric=observation.metric,
                        message=str(exc),
                    )
                )

        return pipeline_result
