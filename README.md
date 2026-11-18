# PulseCore and WardPulse

## Project overview

PulseCore is a reusable operational-intelligence foundation designed to collect structured observations, calculate indicators, compare operational conditions, evaluate configurable rules and support explainable operational responses.

WardPulse is its first application: a healthcare population and workforce health early-warning prototype.

The project demonstrates how a domain-independent engine can support a specialised application without embedding all healthcare-specific logic into the core.

## The problem

Healthcare organisations manage multiple connected operational pressures. Workforce absence, overtime, clinical-service activity, environmental conditions and occupational incidents can change over time.

These signals may be held in separate records and reviewed through disconnected processes. This can make it difficult for operational teams to recognise developing patterns and coordinate an early response.

WardPulse demonstrates a structured approach to bringing selected departmental signals into one review workflow.

## Solution

WardPulse receives structured departmental observations and shift-related records. The ingestion process reads, validates and maps the source records to registered departments. Valid observations are stored in PulseCore.

The application then calculates configured indicators, compares baseline and current periods, evaluates rules and produces explainable alerts and preventive recommendations.

An authorised manager can review a recommendation and create a tracked operational action.

## Architecture

The project uses a Python modular-monolith architecture.

### PulseCore foundation

- Domain models: entities, observations, indicators, rules, alerts, recommendations and actions.
- Core engine: entity registration and storage of operational records.
- Ingestion: dataset contracts, file reading, validation, entity linking and observation generation.
- Intelligence: indicator calculation, analytics, rule evaluation and risk assessment.
- Operations: alerts, recommendations and action tracking.
- API and integration boundaries: extension points for future external interfaces.

### WardPulse application

WardPulse contains healthcare-specific schemas, dataset contracts, indicators, rules, recommendations, demonstration data, ingestion workflows and surveillance orchestration.

This separation allows future applications to reuse PulseCore while defining their own entities, indicators, rules and workflows.

## Configured WardPulse indicators

| Indicator | Description | Aggregation |
|---|---|---|
| Staff absence count | Department-level staff absence observations | Sum |
| Overtime hours | Department-level overtime observations | Sum |
| Respiratory case count | Department-level respiratory case observations | Sum |
| Air quality index | Department-level air-quality observations | Average |
| Occupational incident count | Department-level occupational incident observations | Sum |

These indicators and their rules are configurable prototype inputs. They are not validated clinical or workforce-risk prediction models.

## Data ingestion

The ingestion layer supports CSV and XLSX workflows.

The processing sequence is:

1. Read the source dataset.
2. Validate its structure and values against a dataset contract.
3. Link external department identifiers to registered PulseCore entities.
4. Generate observations from accepted and linked records.
5. Store the observations in the engine.
6. Review validation, linking, generation and storage issues.

WardPulse defines contracts for shift records, employee history and departmental observations. The current surveillance indicators use departmental observations. Shift records can provide overtime observations when the source includes an explicit overtime value. Employee history is a defined dataset contract but is not currently a direct source for the five surveillance indicators.

## Surveillance workflow

The surveillance service retrieves registered departments and their observations. It calculates each configured indicator over baseline and current periods, evaluates applicable rules, assesses departmental risk and generates recommendations.

The system provides the rationale and contributing signals behind its findings. Recommendations can be converted into operational actions and assigned for follow-up.

## Demonstration interface

The Streamlit interface provides:

- Surveillance overview.
- Department analysis.
- Alerts and recommendations.
- Action tracking.
- Dataset ingestion.

The current demonstration uses synthetic data and in-memory storage. Imported observations do not persist after the application process is restarted.

## Technology

- Python
- Pydantic
- Streamlit
- Pandas
- OpenPyXL
- Pytest

## Setup

Create and activate a virtual environment, then install the project dependencies.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
```

If the project is not installed as an editable package, use the existing project configuration and source-path setup.

Run the tests:

```powershell
python -m pytest -q
```

Run the application:

```powershell
python -m streamlit run app.py
```

## Demonstration data

The project includes synthetic demonstration data for two departments. Sample CSV files can also be placed in `sample_data/` and imported through the Data Ingestion page.

All sample data should be clearly identified as synthetic.

## Responsible use and limitations

WardPulse is an early-warning and decision-support prototype. An alert indicates that a configured rule condition has been met; it does not establish a diagnosis, causal relationship or confirmed adverse event.

The prototype does not generate individual employee burnout or mental-health scores. Recommendations require human review.

The current version does not implement production authentication, role-based access control, tenant isolation, encrypted persistent storage, a complete audit trail or validated clinical prediction. It should not process identifiable patient or employee information in a production environment.

See `docs/PRIVACY_AND_GOVERNANCE.md`.

## Future development

Potential future work includes:

- Persistent PostgreSQL storage.
- Authentication, role-based access and tenant isolation.
- Audit logging and configurable retention.
- FastAPI-based external interfaces.
- Hospital information system and workforce management integrations.
- Additional application modules, including AcademyPulse.
- Hosted and self-hosted deployment options.
- Validation against representative operational data.

## Project naming

PulseCore and WardPulse are working project names. Names used for demonstration departments, roles, users and other entities are placeholders and may be changed in future versions.

## Project status

The project is a competition prototype demonstrating a reusable operational-intelligence foundation and a healthcare workforce early-warning application. Production deployment and real-world validation remain future work.