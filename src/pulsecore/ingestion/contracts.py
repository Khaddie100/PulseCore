
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class DatasetFormat(str, Enum):
    CSV = "csv"
    XLSX = "xlsx"
    XLS = "xls"


class ColumnType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"


class ColumnContract(BaseModel):
    """Defines the expected structure of one dataset column."""

    name: str
    data_type: ColumnType = ColumnType.STRING
    required: bool = True
    aliases: list[str] = Field(default_factory=list)


class DatasetContract(BaseModel):
    """Defines the structure and validation expectations of a dataset."""

    name: str
    description: str = ""

    columns: list[ColumnContract]

    unique_key: list[str] = Field(default_factory=list)

    supported_formats: list[DatasetFormat] = Field(
        default_factory=lambda: [
            DatasetFormat.CSV,
            DatasetFormat.XLSX,
        ]
    )

    allow_extra_columns: bool = True

    @model_validator(mode="after")
    def validate_contract(self):
        column_names = [column.name for column in self.columns]

        if len(column_names) != len(set(column_names)):
            raise ValueError("Dataset column names must be unique.")

        if not column_names:
            raise ValueError("A dataset must define at least one column.")

        unknown_keys = set(self.unique_key) - set(column_names)

        if unknown_keys:
            raise ValueError(
                f"Unique key references undefined columns: "
                f"{sorted(unknown_keys)}"
            )

        if len(self.unique_key) != len(set(self.unique_key)):
            raise ValueError("Unique key columns must not be repeated.")

        aliases = [
            alias.strip().lower()
            for column in self.columns
            for alias in column.aliases
        ]

        if len(aliases) != len(set(aliases)):
            raise ValueError("Column aliases must be unique.")

        return self


class DatasetMetadata(BaseModel):
    """Records information about an imported dataset."""

    dataset_name: str
    source_filename: str
    source_format: DatasetFormat
    imported_by: str | None = None
    source_system: str | None = None


class DatasetValidationIssue(BaseModel):
    """Describes a problem detected during dataset validation."""

    row_number: int | None = None
    column: str | None = None
    code: str
    message: str
    severity: Literal["error", "warning"] = "error"


class DatasetValidationResult(BaseModel):
    """Summarizes the outcome of dataset validation."""

    valid: bool
    total_rows: int = 0
    accepted_rows: int = 0
    rejected_rows: int = 0
    issues: list[DatasetValidationIssue] = Field(
        default_factory=list
    )
