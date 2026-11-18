
from datetime import datetime
from typing import Any

from pulsecore.ingestion.contracts import (
    ColumnType,
    DatasetContract,
    DatasetValidationIssue,
    DatasetValidationResult,
)


class DatasetValidationOutput:
    """Contains normalized rows and their validation summary."""

    def __init__(
        self,
        rows: list[dict[str, Any]],
        result: DatasetValidationResult,
    ):
        self.rows = rows
        self.result = result


class DatasetValidator:
    """Validates and normalizes rows against a dataset contract."""

    NULL_VALUES = {"", "null", "none", "n/a", "na"}

    def validate(
        self,
        rows: list[dict[str, Any]],
        contract: DatasetContract,
    ) -> DatasetValidationOutput:
        issues: list[DatasetValidationIssue] = []

        if not rows:
            result = DatasetValidationResult(
                valid=True,
                total_rows=0,
                accepted_rows=0,
                rejected_rows=0,
                issues=[],
            )
            return DatasetValidationOutput([], result)

        source_headers = list(rows[0].keys())

        normalized_headers = {
            str(header).strip().lower(): header
            for header in source_headers
        }

        mapping: dict[str, str] = {}
        used_source_headers: set[str] = set()

        # Map source headers to canonical contract column names.
        for column in contract.columns:
            possible_names = [
                column.name,
                *column.aliases,
            ]

            matches = [
                normalized_headers[name.strip().lower()]
                for name in possible_names
                if name.strip().lower() in normalized_headers
            ]

            if len(matches) > 1:
                issues.append(
                    DatasetValidationIssue(
                        code="ambiguous_column_mapping",
                        column=column.name,
                        message=(
                            f"Multiple source columns match "
                            f"'{column.name}': {matches}"
                        ),
                    )
                )
                continue

            if matches:
                source_name = matches[0]
                mapping[column.name] = source_name
                used_source_headers.add(source_name)

            elif column.required:
                issues.append(
                    DatasetValidationIssue(
                        code="missing_required_column",
                        column=column.name,
                        message=(
                            f"Required column '{column.name}' "
                            "was not found."
                        ),
                    )
                )

        extra_headers = [
            header
            for header in source_headers
            if header not in used_source_headers
        ]

        if extra_headers:
            severity = (
                "warning"
                if contract.allow_extra_columns
                else "error"
            )
            issues.append(
                DatasetValidationIssue(
                    code="unexpected_columns",
                    message=f"Unexpected columns found: {extra_headers}",
                    severity=severity,
                )
            )

        # Dataset-level errors prevent reliable row validation.
        blocking_codes = {
            "ambiguous_column_mapping",
            "missing_required_column",
        }

        if any(issue.code in blocking_codes for issue in issues):
            result = DatasetValidationResult(
                valid=False,
                total_rows=len(rows),
                accepted_rows=0,
                rejected_rows=len(rows),
                issues=issues,
            )
            return DatasetValidationOutput([], result)

        if extra_headers and not contract.allow_extra_columns:
            result = DatasetValidationResult(
                valid=False,
                total_rows=len(rows),
                accepted_rows=0,
                rejected_rows=len(rows),
                issues=issues,
            )
            return DatasetValidationOutput([], result)

        accepted_rows: list[dict[str, Any]] = []
        seen_keys: set[tuple[Any, ...]] = set()

        for row_number, source_row in enumerate(rows, start=2):
            normalized_row: dict[str, Any] = {}
            row_has_error = False

            for column in contract.columns:
                source_name = mapping.get(column.name)
                raw_value = (
                    source_row.get(source_name)
                    if source_name is not None
                    else None
                )

                try:
                    value = self._normalize_value(
                        raw_value,
                        column.data_type,
                    )

                    if column.required and value is None:
                        raise ValueError("Required value is missing.")

                    normalized_row[column.name] = value

                except (ValueError, TypeError) as exc:
                    row_has_error = True
                    issues.append(
                        DatasetValidationIssue(
                            row_number=row_number,
                            column=column.name,
                            code="invalid_value",
                            message=str(exc),
                        )
                    )

            if row_has_error:
                continue

            # Check uniqueness using the contract's composite key.
            if contract.unique_key:
                key = tuple(
                    normalized_row.get(name)
                    for name in contract.unique_key
                )

                if key in seen_keys:
                    issues.append(
                        DatasetValidationIssue(
                            row_number=row_number,
                            column=", ".join(contract.unique_key),
                            code="duplicate_record",
                            message=f"Duplicate unique key: {key}",
                        )
                    )
                    continue

                seen_keys.add(key)

            accepted_rows.append(normalized_row)

        rejected_rows = len(rows) - len(accepted_rows)

        result = DatasetValidationResult(
            valid=not any(
                issue.severity == "error"
                for issue in issues
            ),
            total_rows=len(rows),
            accepted_rows=len(accepted_rows),
            rejected_rows=rejected_rows,
            issues=issues,
        )

        return DatasetValidationOutput(
            rows=accepted_rows,
            result=result,
        )


    def _normalize_value(
        self,
        value: Any,
        data_type: ColumnType,
    ) -> Any:
        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()

            if value.lower() in self.NULL_VALUES:
                return None

        if data_type == ColumnType.STRING:
            return str(value).strip()

        if data_type == ColumnType.INTEGER:
            if isinstance(value, bool):
                raise ValueError("Boolean values are not valid integers.")
            return int(value)

        if data_type == ColumnType.FLOAT:
            if isinstance(value, bool):
                raise ValueError("Boolean values are not valid numbers.")
            return float(value)

        if data_type == ColumnType.BOOLEAN:
            if isinstance(value, bool):
                return value

            normalized = str(value).strip().lower()

            if normalized in {"true", "yes", "1"}:
                return True

            if normalized in {"false", "no", "0"}:
                return False

            raise ValueError(
                f"Cannot interpret '{value}' as a boolean."
            )

        if data_type == ColumnType.DATETIME:
            if isinstance(value, datetime):
                return value

            return datetime.fromisoformat(str(value))

        return value
