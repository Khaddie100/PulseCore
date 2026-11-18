
from pulsecore.ingestion.contracts import (
    ColumnContract,
    ColumnType,
    DatasetContract,
)


def get_wardpulse_dataset_contracts() -> dict[str, DatasetContract]:
    """Return the dataset contracts required by WardPulse."""

    shift_records = DatasetContract(
        name="shift_records",
        description="Healthcare worker shift and workload records.",
        columns=[
            ColumnContract(
                name="shift_id",
                data_type=ColumnType.STRING,
                aliases=["shift number"],
            ),
            ColumnContract(
                name="employee_id",
                data_type=ColumnType.STRING,
                aliases=["staff id", "worker id"],
            ),
            ColumnContract(
                name="department_id",
                data_type=ColumnType.STRING,
                aliases=["unit id"],
            ),
            ColumnContract(
                name="shift_date",
                data_type=ColumnType.DATETIME,
                aliases=["date"],
            ),
            ColumnContract(
                name="scheduled_hours",
                data_type=ColumnType.FLOAT,
            ),
            ColumnContract(
                name="worked_hours",
                data_type=ColumnType.FLOAT,
            ),
            ColumnContract(
                name="overtime_hours",
                data_type=ColumnType.FLOAT,
                required=False,
            ),
            ColumnContract(
                name="shift_type",
                data_type=ColumnType.STRING,
            ),
        ],
        unique_key=["shift_id"],
    )

    employee_history = DatasetContract(
        name="employee_history",
        description="Healthcare workforce employment records.",
        columns=[
            ColumnContract(
                name="employment_record_id",
                data_type=ColumnType.STRING,
            ),
            ColumnContract(
                name="employee_id",
                data_type=ColumnType.STRING,
                aliases=["staff id", "worker id"],
            ),
            ColumnContract(
                name="department_id",
                data_type=ColumnType.STRING,
                aliases=["unit id"],
            ),
            ColumnContract(
                name="role",
                data_type=ColumnType.STRING,
                aliases=["job title", "position"],
            ),
            ColumnContract(
                name="employment_status",
                data_type=ColumnType.STRING,
            ),
            ColumnContract(
                name="employment_type",
                data_type=ColumnType.STRING,
                required=False,
            ),
            ColumnContract(
                name="hire_date",
                data_type=ColumnType.DATETIME,
                required=False,
            ),
            ColumnContract(
                name="exit_date",
                data_type=ColumnType.DATETIME,
                required=False,
            ),
        ],
        unique_key=["employment_record_id"],
    )

    departmental_observations = DatasetContract(
        name="departmental_observations",
        description="Operational measurements recorded for departments.",
        columns=[
            ColumnContract(
                name="department_id",
                data_type=ColumnType.STRING,
            ),
            ColumnContract(
                name="observed_at",
                data_type=ColumnType.DATETIME,
                aliases=["observation_date", "date"],
            ),
            ColumnContract(
                name="metric",
                data_type=ColumnType.STRING,
                aliases=["indicator"],
            ),
            ColumnContract(
                name="value",
                data_type=ColumnType.FLOAT,
            ),
            ColumnContract(
                name="unit",
                data_type=ColumnType.STRING,
                required=False,
            ),
            ColumnContract(
                name="source",
                data_type=ColumnType.STRING,
                required=False,
            ),
        ],
        unique_key=["department_id", "observed_at", "metric"],
    )

    return {
        "shift_records": shift_records,
        "employee_history": employee_history,
        "departmental_observations": departmental_observations,
    }
