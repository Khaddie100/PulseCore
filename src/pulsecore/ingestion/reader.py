
import csv
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from pulsecore.ingestion.contracts import (
    DatasetContract,
    DatasetFormat,
)


class DatasetReader:
    """Reads supported datasets into a list of dictionaries."""

    FORMAT_MAP = {
        ".csv": DatasetFormat.CSV,
        ".xlsx": DatasetFormat.XLSX,
        ".xls": DatasetFormat.XLS,
    }

    def read(
        self,
        file_path: str | Path,
        contract: DatasetContract,
        sheet_name: str | None = None,
    ) -> list[dict[str, Any]]:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Dataset file not found: {path}"
            )

        file_format = self.FORMAT_MAP.get(
            path.suffix.lower()
        )

        if file_format is None:
            raise ValueError(
                f"Unsupported file extension: {path.suffix}"
            )

        if file_format not in contract.supported_formats:
            raise ValueError(
                f"Format '{file_format.value}' is not "
                f"supported by dataset '{contract.name}'."
            )

        if file_format == DatasetFormat.CSV:
            return self._read_csv(path)

        if file_format == DatasetFormat.XLSX:
            return self._read_excel(path, sheet_name)

        raise ValueError(
            "Legacy XLS files are not currently supported. "
            "Convert the file to XLSX or CSV."
        )

    @staticmethod
    def _validate_headers(
        headers: list[Any],
    ) -> list[str]:
        if not headers:
            raise ValueError("Dataset has no header row.")

        normalized = []

        for header in headers:
            if header is None or not str(header).strip():
                raise ValueError(
                    "Dataset contains an empty column header."
                )

            normalized.append(str(header).strip())

        lowered = [item.lower() for item in normalized]

        if len(lowered) != len(set(lowered)):
            raise ValueError(
                "Dataset contains duplicate column headers."
            )

        return normalized

    def _read_csv(
        self,
        path: Path,
    ) -> list[dict[str, Any]]:
        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.reader(file)

            try:
                headers = self._validate_headers(
                    next(reader)
                )
            except StopIteration:
                raise ValueError("CSV file is empty.")

            rows = []

            for values in reader:
                if not any(
                    str(value).strip() for value in values
                    if value is not None
                ):
                    continue

                if len(values) != len(headers):
                    raise ValueError(
                        "CSV row contains a different "
                        "number of values than its headers."
                    )

                rows.append(dict(zip(headers, values)))

            return rows

    def _read_excel(
        self,
        path: Path,
        sheet_name: str | None = None,
    ) -> list[dict[str, Any]]:
        workbook = load_workbook(
            path,
            read_only=True,
            data_only=True,
        )

        try:
            if sheet_name:
                if sheet_name not in workbook.sheetnames:
                    raise ValueError(
                        f"Worksheet '{sheet_name}' not found."
                    )

                worksheet = workbook[sheet_name]
            else:
                worksheet = workbook.active

            iterator = worksheet.iter_rows(
                values_only=True
            )

            try:
                headers = self._validate_headers(
                    list(next(iterator))
                )
            except StopIteration:
                raise ValueError(
                    "Excel worksheet is empty."
                )

            rows = []

            for values in iterator:
                if not any(
                    value is not None and str(value).strip()
                    for value in values
                ):
                    continue

                if len(values) != len(headers):
                    raise ValueError(
                        "Excel row contains a different "
                        "number of values than its headers."
                    )

                rows.append(dict(zip(headers, values)))

            return rows

        finally:
            workbook.close()
