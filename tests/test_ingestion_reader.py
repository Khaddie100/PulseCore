
import csv

import pytest
from openpyxl import Workbook

from pulsecore.ingestion.reader import DatasetReader
from pulsecore.ingestion.contracts import (
    ColumnContract,
    DatasetContract,
    DatasetFormat,
)


@pytest.fixture
def contract():
    return DatasetContract(
        name="employee_records",
        columns=[
            ColumnContract(name="employee_id"),
            ColumnContract(name="department_id"),
        ],
        supported_formats=[
            DatasetFormat.CSV,
            DatasetFormat.XLSX,
        ],
    )


def test_reads_csv_file(tmp_path, contract):
    path = tmp_path / "employees.csv"

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["employee_id", "department_id"])
        writer.writerow(["EMP001", "CARDIOLOGY"])

    result = DatasetReader().read(path, contract)

    assert len(result) == 1
    assert result[0]["employee_id"] == "EMP001"


def test_reads_excel_file(tmp_path, contract):
    path = tmp_path / "employees.xlsx"

    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["employee_id", "department_id"])
    sheet.append(["EMP001", "CARDIOLOGY"])
    workbook.save(path)

    result = DatasetReader().read(path, contract)

    assert len(result) == 1
    assert result[0]["department_id"] == "CARDIOLOGY"


def test_missing_file_raises_error(contract):
    with pytest.raises(FileNotFoundError):
        DatasetReader().read(
            "missing.csv",
            contract,
        )


def test_unsupported_extension_raises_error(
    tmp_path,
    contract,
):
    path = tmp_path / "employees.txt"
    path.write_text("some data")

    with pytest.raises(ValueError):
        DatasetReader().read(path, contract)


def test_unsupported_contract_format_raises_error(
    tmp_path,
    contract,
):
    path = tmp_path / "employees.xlsx"

    path.touch()

    csv_only_contract = DatasetContract(
        name="csv_only",
        columns=[
            ColumnContract(name="employee_id"),
        ],
        supported_formats=[DatasetFormat.CSV],
    )

    with pytest.raises(ValueError):
        DatasetReader().read(path, csv_only_contract)


def test_duplicate_csv_headers_are_rejected(
    tmp_path,
    contract,
):
    path = tmp_path / "employees.csv"
    path.write_text(
        "employee_id,employee_id\nEMP001,EMP002\n"
    )

    with pytest.raises(ValueError):
        DatasetReader().read(path, contract)


def test_empty_csv_is_rejected(tmp_path, contract):
    path = tmp_path / "empty.csv"
    path.touch()

    with pytest.raises(ValueError):
        DatasetReader().read(path, contract)
