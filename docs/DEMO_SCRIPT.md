# WardPulse Demonstration Script

## Demonstration objective

Show how PulseCore can transform structured operational data into explainable departmental early-warning findings and trackable preventive actions through WardPulse.

## 1. Introduction

"PulseCore is a reusable operational-intelligence foundation. WardPulse is its first application, focused on healthcare population and workforce health early warning.

The goal is to demonstrate how multiple operational signals can be brought together, reviewed and translated into earlier organisational action."

## 2. Open the dashboard

Show the Overview page.

Explain the number of departments monitored, active alerts, elevated-risk departments and pending actions.

Clarify that the displayed data is synthetic.

## 3. Review departmental indicators

Open Department Analysis.

Show the five configured indicators:

- Staff absence count.
- Overtime hours.
- Respiratory case count.
- Air quality index.
- Occupational incident count.

Explain that each indicator is calculated using its configured aggregation and compared across baseline and current periods.

## 4. Explain a finding

Open Alerts and Recommendations.

Choose one synthetic department finding.

Explain which indicator or rule condition contributed to the alert, what the alert means and why the recommendation was generated.

Emphasise that an alert is a signal for review, not a diagnosis or proof of causation.

## 5. Demonstrate ingestion

Open Data Ingestion.

Import the sample departmental observations CSV.

Show the validation summary, entity-linking outcome, generated observations and storage result.

Explain that the workflow can also accept Excel files.

## 6. Demonstrate action tracking

Open Action Tracking.

Choose a recommendation, assign it to a demonstration role and create an action.

Update its status to in progress or completed.

Explain that this connects an early-warning finding to a visible operational follow-up.

## 7. Explain the reusable foundation

Close by explaining that the healthcare-specific definitions belong to WardPulse, while the entity, observation, ingestion, analytics, rules and action capabilities belong to PulseCore.

The same foundation can support other domains through separate application modules.

## 8. Limitations

State clearly:

- The demonstration uses synthetic data.
- The prototype uses in-memory storage.
- Thresholds and indicators require validation with real operational data.
- The prototype does not provide individual employee health-risk scoring.
- Production authentication, tenant isolation and persistent storage are future work.

## Closing

"WardPulse demonstrates a path from disconnected operational signals to explainable early warnings and human-reviewed preventive action, built on a reusable PulseCore foundation."