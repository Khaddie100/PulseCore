
from pulsecore.applications.wardpulse.dataset_contracts import (
    get_wardpulse_dataset_contracts,
)
from pulsecore.ingestion.contracts import (
    ColumnType,
    DatasetFormat,
)


def test_all_wardpulse_contracts_are_registered():
    contracts = get_wardpulse_dataset_contracts()

    assert set(contracts.keys()) == {
        "shift_records",
        "employee_history",
        "departmental_observations",
    }


def test_shift_records_contract():
    contract = get_wardpulse_dataset_contracts()["shift_records"]

    assert contract.unique_key == ["shift_id"]
    assert "employee_id" in [
        column.name for column in contract.columns
    ]


def test_employee_history_contract():
    contract = get_wardpulse_dataset_contracts()["employee_history"]

    assert contract.unique_key == ["employment_record_id"]

    columns = {column.name: column for column in contract.columns}

    assert columns["employee_id"].required is True
    assert columns["exit_date"].required is False


def test_departmental_observations_contract():
    contract = get_wardpulse_dataset_contracts()[
        "departmental_observations"
    ]

    assert contract.unique_key == [
        "department_id",
        "observed_at",
        "metric",
    ]

    columns = {column.name: column for column in contract.columns}

    assert columns["value"].data_type == ColumnType.FLOAT
    assert columns["unit"].required is False


def test_wardpulse_contracts_support_csv_and_xlsx():
    contracts = get_wardpulse_dataset_contracts()

    for contract in contracts.values():
        assert DatasetFormat.CSV in contract.supported_formats
        assert DatasetFormat.XLSX in contract.supported_formats
