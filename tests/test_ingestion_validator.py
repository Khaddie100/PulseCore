
import pytest

from pulsecore.ingestion.contracts import (
    ColumnContract,
    ColumnType,
    DatasetContract,
)
from pulsecore.ingestion.validator import DatasetValidator


@pytest.fixture
def validator():
    return DatasetValidator()


@pytest.fixture
def contract():
    return DatasetContract(
        name="employee_records",
        columns=[
            ColumnContract(
                name="employee_id",
                data_type=ColumnType.STRING,
                aliases=["staff id"],
            ),
            ColumnContract(
                name="work_hours",
                data_type=ColumnType.FLOAT,
            ),
            ColumnContract(
                name="is_active",
                data_type=ColumnType.BOOLEAN,
            ),
        ],
        unique_key=["employee_id"],
    )


def test_valid_rows_are_normalized(validator, contract):
    rows = [
        {
            "staff id": " E001 ",
            "work_hours": "40.5",
            "is_active": "yes",
        }
    ]

    output = validator.validate(rows, contract)

    assert output.result.valid is True
    assert output.result.accepted_rows == 1
    assert output.rows[0] == {
        "employee_id": "E001",
        "work_hours": 40.5,
        "is_active": True,
    }


def test_canonical_column_names_are_supported(validator, contract):
    rows = [
        {
            "employee_id": "E001",
            "work_hours": "40",
            "is_active": "true",
        }
    ]

    output = validator.validate(rows, contract)

    assert output.result.accepted_rows == 1


def test_missing_required_column_is_rejected(validator, contract):
    rows = [
        {
            "work_hours": "40",
            "is_active": "true",
        }
    ]

    output = validator.validate(rows, contract)

    assert output.result.valid is False
    assert output.result.accepted_rows == 0
    assert any(
        issue.code == "missing_required_column"
        for issue in output.result.issues
    )


def test_invalid_numeric_value_rejects_row(validator, contract):
    rows = [
        {
            "staff id": "E001",
            "work_hours": "invalid",
            "is_active": "true",
        }
    ]

    output = validator.validate(rows, contract)

    assert output.result.accepted_rows == 0
    assert output.result.rejected_rows == 1
    assert any(
        issue.code == "invalid_value"
        and issue.column == "work_hours"
        for issue in output.result.issues
    )


def test_invalid_boolean_is_rejected(validator, contract):
    rows = [
        {
            "staff id": "E001",
            "work_hours": "40",
            "is_active": "unknown",
        }
    ]

    output = validator.validate(rows, contract)

    assert output.result.rejected_rows == 1


def test_duplicate_unique_keys_are_rejected(validator, contract):
    rows = [
        {
            "staff id": "E001",
            "work_hours": "40",
            "is_active": "true",
        },
        {
            "staff id": "E001",
            "work_hours": "35",
            "is_active": "false",
        },
    ]

    output = validator.validate(rows, contract)

    assert output.result.accepted_rows == 1
    assert output.result.rejected_rows == 1
    assert any(
        issue.code == "duplicate_record"
        for issue in output.result.issues
    )


def test_extra_columns_generate_warning(validator, contract):
    rows = [
        {
            "staff id": "E001",
            "work_hours": "40",
            "is_active": "true",
            "extra_field": "anything",
        }
    ]

    output = validator.validate(rows, contract)

    assert output.result.accepted_rows == 1
    assert any(
        issue.code == "unexpected_columns"
        and issue.severity == "warning"
        for issue in output.result.issues
    )


def test_extra_columns_can_be_disallowed(validator):
    strict_contract = DatasetContract(
        name="strict_dataset",
        columns=[
            ColumnContract(name="employee_id"),
        ],
        allow_extra_columns=False,
    )

    rows = [
        {
            "employee_id": "E001",
            "unexpected": "value",
        }
    ]

    output = validator.validate(rows, strict_contract)

    assert output.result.valid is False
    assert output.result.accepted_rows == 0


def test_empty_dataset_is_valid(validator, contract):
    output = validator.validate([], contract)

    assert output.result.valid is True
    assert output.result.total_rows == 0
    assert output.rows == []


def test_ambiguous_alias_and_canonical_column_are_rejected(
    validator,
    contract,
):
    rows = [
        {
            "employee_id": "E001",
            "staff id": "E002",
            "work_hours": "40",
            "is_active": "true",
        }
    ]

    output = validator.validate(rows, contract)

    assert output.result.valid is False
    assert output.result.accepted_rows == 0
    assert any(
        issue.code == "ambiguous_column_mapping"
        for issue in output.result.issues
    )
