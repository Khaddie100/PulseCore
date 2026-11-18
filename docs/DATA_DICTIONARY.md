# WardPulse Data Dictionary

## 1. Dataset: departmental_observations

Purpose: import observations used by WardPulse's configured departmental indicators.

| Field | Type | Purpose |
|---|---|---|
| department_id | String | External identifier of a registered department |
| observed_at | Datetime | Time the observation was recorded |
| metric | String | PulseCore metric identifier |
| value | Float | Numeric observation value |
| unit | String | Measurement unit |
| source | String | Origin of the observation |

Supported metric identifiers:

- `staff_absence_count`
- `overtime_hours`
- `respiratory_case_count`
- `air_quality_index`
- `occupational_incident_count`

The department identifier must match a registered department's external `department_id` attribute.

## 2. Dataset: shift_records

Purpose: import shift-related records and generate departmental overtime observations.

| Field | Type | Purpose |
|---|---|---|
| shift_id | String | Unique source shift record identifier |
| employee_id | String | Source employee identifier; not required in department-level observation metadata |
| department_id | String | Department identifier |
| shift_date | Datetime | Date/time associated with the shift |
| scheduled_hours | Float | Scheduled shift duration |
| worked_hours | Float | Actual worked duration |
| overtime_hours | Float | Explicit overtime value supplied by the source |
| shift_type | String | Shift classification |

The current ingestion workflow uses the explicit `overtime_hours` field. It does not infer overtime from scheduled and worked hours.

## 3. Dataset: employee_history

Purpose: define a validated structure for employment-history records.

| Field | Type | Purpose |
|---|---|---|
| employment_record_id | String | Unique employment record |
| employee_id | String | External employee identifier |
| department_id | String | Department identifier |
| role | String | Job role |
| employment_status | String | Employment status |
| employment_type | String | Employment classification |
| hire_date | Datetime | Employment start date |
| exit_date | Datetime | Employment end date |

This contract is not currently connected to the five configured WardPulse surveillance indicators.

## 4. Observation model

A PulseCore observation contains:

- Unique observation identifier.
- Linked entity identifier.
- Normalised metric name.
- Value and optional unit.
- Optional source.
- Observation timestamp.
- Optional metadata.

## 5. Data quality

The ingestion process reports issues including missing required fields, invalid values, duplicate unique keys, unmatched entities, missing metric values, invalid timestamps and storage failures.

A successful file read does not imply that every row is valid or that every row was stored.

## 6. Data interpretation

Indicators are calculated according to their configured aggregation. The resulting values depend on source completeness, time period, metric definition and data quality.

The prototype's configured thresholds and synthetic observations are demonstration inputs, not validated clinical or workforce standards.