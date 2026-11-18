# PulseCore Architecture

## 1. Architectural approach

PulseCore uses a modular-monolith architecture. The application is deployed and developed as one Python project, while its responsibilities are separated into modules with defined boundaries.

This approach supports a focused prototype while allowing individual modules to evolve independently.

## 2. Logical layers

### Domain layer

Contains the generic data models used throughout the platform:

- Entity
- Observation
- Indicator
- Rule
- Alert
- Recommendation
- Action

These models are not restricted to healthcare.

### Core layer

The PulseCore engine manages registered entities and stored observations and operational outputs. It provides the central interface used by intelligence and application modules.

### Ingestion layer

The ingestion layer provides reusable dataset processing:

- Dataset contracts.
- CSV and Excel reading.
- Column mapping and validation.
- External identifier linking.
- Observation generation.
- Storage through the core engine.

### Intelligence layer

The intelligence layer calculates indicators, compares periods, evaluates rules and assesses risk.

The core calculations are reusable. Application modules provide the domain-specific indicator definitions and rule configuration.

### Operations layer

The operations layer supports alerts, recommendations and actions. Actions provide a record of the operational response associated with a recommendation.

### Application layer

An application module configures the generic engine for a specific domain.

WardPulse defines healthcare department schemas, indicators, rules, recommendations, dataset contracts and surveillance workflows.

## 3. WardPulse data flow

1. A source file is selected.
2. The reader extracts rows.
3. The validator checks and normalises values.
4. The entity linker maps external department identifiers to registered department entities.
5. The observation generator creates PulseCore observations.
6. The engine stores the observations.
7. WardPulse retrieves observations for each department.
8. The indicator calculator aggregates matching observations.
9. Analytics compares baseline and current periods.
10. The rule engine evaluates configured conditions.
11. Risk evaluation produces a departmental assessment.
12. Recommendation generation creates preventive suggestions.
13. An authorised manager reviews a recommendation and may create an action.

## 4. Domain separation

PulseCore should not contain healthcare-specific assumptions such as department risk thresholds or clinical indicator definitions.

WardPulse owns those definitions. A future application such as AcademyPulse can reuse the generic engine and ingestion capabilities while providing its own entity types, indicators, rules and workflows.

## 5. Current deployment architecture

The competition prototype uses:

- Python modular monolith.
- Streamlit user interface.
- In-memory PulseCore engine.
- CSV and XLSX ingestion.
- Synthetic demonstration data.

The current implementation is not a distributed microservices architecture and does not claim production SaaS readiness.

## 6. Future architecture extensions

Future platform development can introduce:

- FastAPI application interfaces.
- PostgreSQL persistence.
- Authentication and role-based access.
- Tenant and facility isolation.
- Audit events and data lineage.
- Hosted and self-hosted deployment.
- External integration adapters and SDKs.
- Visual administrative configuration.

These are planned extensions rather than completed capabilities of the competition prototype.