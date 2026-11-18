
import pytest
from pydantic import ValidationError

from pulsecore.ingestion.contracts import (
    ColumnContract,
    ColumnType,
    DatasetContract,
    DatasetFormat,
    DatasetValidationIssue,
    DatasetValidationResult,
)


def make_contract():
    return DatasetContract(
        name="employee_records",
        columns=[
            ColumnContract(
                name="employee_id",
                data_type=ColumnType.STRING,
            ),
            ColumnContract(
                name="department_id",
                data_type=ColumnType.STRING,
            ),
            ColumnContract(
                name="work_hours",
                data_type=ColumnType.FLOAT,
                required=False,
            ),
        ],
        unique_key=["employee_id"],
    )


def test_valid_dataset_contract():
    contract = make_contract()

    assert contract.name == "employee_records"
    assert len(contract.columns) == 3
    assert contract.unique_key == ["employee_id"]


def test_duplicate_column_names_are_rejected():
    with pytest.raises(ValidationError):
        DatasetContract(
            name="invalid",
            columns=[
                ColumnContract(name="employee_id"),
                ColumnContract(name="employee_id"),
            ],
        )


def test_empty_columns_are_rejected():
    with pytest.raises(ValidationError):
        DatasetContract(
            name="empty",
            columns=[],
        )


def test_unknown_unique_key_is_rejected():
    with pytest.raises(ValidationError):
        DatasetContract(
            name="invalid",
            columns=[
                ColumnContract(name="employee_id"),
            ],
            unique_key=["unknown_id"],
        )


def test_duplicate_aliases_are_rejected():
    with pytest.raises(ValidationError):
        DatasetContract(
            name="invalid",
            columns=[
                ColumnContract(
                    name="employee_id",
                    aliases=["staff number"],
                ),
                ColumnContract(
                    name="worker_id",
                    aliases=["staff number"],
                ),
            ],
        )


def test_supported_formats():
    contract = make_contract()

    assert DatasetFormat.CSV in contract.supported_formats
    assert DatasetFormat.XLSX in contract.supported_formats


def test_validation_result():
    result = DatasetValidationResult(
        valid=False,
        total_rows=10,
        accepted_rows=8,
        rejected_rows=2,
        issues=[
            DatasetValidationIssue(
                row_number=4,
                column="employee_id",
                code="missing_value",
                message="Employee ID is missing.",
            )
        ],
    )

    assert result.valid is False
    assert result.rejected_rows == 2
    assert len(result.issues) == 1
