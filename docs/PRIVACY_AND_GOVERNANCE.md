# Privacy, Responsible Use and Governance

## Purpose

WardPulse is a prototype organisational early-warning and decision-support application. It is designed to help authorised healthcare managers review aggregated workforce, clinical-service, environmental and workplace-safety signals.

It is not a diagnostic tool, a clinical decision-making system, an employee-performance scoring system or an automated employment decision system.

## Data minimisation

The prototype should process only information necessary for its configured departmental indicators.

- Department-level observations are the primary analytical input.
- Employee identifiers should not be included in department-level observation metadata.
- Patient-identifiable information is not required for the demonstration.
- Synthetic or appropriately anonymised datasets should be used in demonstrations and testing.
- Imported source files should be handled only by authorised users.

## Aggregation and interpretation

WardPulse calculates indicators at department level. It does not currently calculate individual employee burnout, mental-health or disease-risk scores.

An alert means that a configured rule condition was met. It does not prove that an occupational illness, outbreak, burnout condition or causal relationship exists.

Managers should review the underlying data, contextual factors and data quality before deciding whether to act.

## Human oversight

Recommendations are decision-support suggestions. An authorised manager must review them before an operational action is created or assigned.

The prototype does not autonomously discipline, rank, dismiss, diagnose or make employment decisions about workers.

## Access and security limitations

The current demonstration uses an in-memory engine and a local Streamlit interface. It does not yet implement production-grade authentication, role-based access control, tenant isolation, encrypted persistent storage or a complete audit trail.

It must not be used to store or process identifiable workforce or patient records in a production environment.

These capabilities are required before a real deployment.

## Data quality

Imported data passes through dataset reading, schema validation, entity linking and observation generation. Validation, linking, generation and storage issues should be reviewed before the resulting surveillance report is interpreted.

Incorrect, incomplete or poorly mapped data can produce misleading indicators and alerts.

## Responsible deployment requirements

Before operational deployment, the system requires:

1. A documented lawful basis and purpose for processing.
2. A privacy impact assessment where required.
3. Appropriate access control and authentication.
4. Tenant and facility-level data isolation.
5. Encryption in transit and at rest.
6. Retention and deletion policies.
7. Audit logging for data imports, report generation and operational actions.
8. Clinical, occupational-health and workforce-governance review of indicators and thresholds.
9. Validation with representative real-world data.
10. A process for correcting inaccurate data and reviewing alerts.

## Current status

The competition version is a synthetic-data prototype demonstrating a reusable ingestion and early-warning workflow. Its results are illustrative and must not be interpreted as validated clinical or workforce-risk predictions.