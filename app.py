from pathlib import Path
import sys
from datetime import datetime, time as datetime_time, timezone
from uuid import uuid4

import pandas as pd
import streamlit as st

# ----------------------------------------------------------
# IMPORT PATH AND PULSECORE IMPORTS
# ----------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pulsecore.applications.wardpulse.demo_data import create_demo_engine
from pulsecore.applications.wardpulse.service import WardPulseSurveillance
from pulsecore.domain.models import Observation

# ----------------------------------------------------------
# PAGE CONFIGURATION
# ----------------------------------------------------------
st.set_page_config(
    page_title="WardPulse | Workforce Early Warning",
    page_icon="🏥",
    layout="wide",
)

st.title("WardPulse")
st.caption("Population and Workforce Health Early Warning System")

# ----------------------------------------------------------
# REPORTING PERIODS
# ----------------------------------------------------------
BASELINE_START = datetime(2026, 10, 25, tzinfo=timezone.utc)
BASELINE_END = datetime(
    2026, 10, 31, 23, 59, 59, tzinfo=timezone.utc
)
CURRENT_START = datetime(2026, 11, 1, tzinfo=timezone.utc)


def get_current_period_end():
    today = datetime.now(timezone.utc).date()
    return datetime.combine(
        today,
        datetime_time(23, 59, 59),
        tzinfo=timezone.utc,
    )


# ----------------------------------------------------------
# APPLICATION INITIALISATION AND SESSION STATE
# ----------------------------------------------------------
def refresh_surveillance():
    """Recalculate WardPulse results using current observations."""
    service = st.session_state.get("service")
    if service is None:
        raise RuntimeError("WardPulse service has not been initialized.")

    report = service.run(
        baseline_start=BASELINE_START,
        baseline_end=BASELINE_END,
        current_start=CURRENT_START,
        current_end=get_current_period_end(),
    )
    st.session_state["report"] = report
    return report


def initialize_application():
    """Create a fresh demonstration engine and surveillance service."""
    engine = create_demo_engine()
    service = WardPulseSurveillance(engine)

    # Set all required keys before calling any function that reads them.
    st.session_state["engine"] = engine
    st.session_state["service"] = service
    st.session_state["report"] = None

    refresh_surveillance()


def ensure_application_initialized():
    """Recover safely if session state is missing or partially initialized."""
    required = ("engine", "service", "report")
    if any(key not in st.session_state for key in required):
        initialize_application()
        return

    if (
        st.session_state["engine"] is None
        or st.session_state["service"] is None
        or st.session_state["report"] is None
    ):
        initialize_application()


ensure_application_initialized()

engine = st.session_state["engine"]
service = st.session_state["service"]
report = st.session_state["report"]

# ----------------------------------------------------------
# COMMON HELPERS
# ----------------------------------------------------------
def get_enum_value(value):
    return str(getattr(value, "value", value))


def get_risk_level(assessment):
    return get_enum_value(assessment.risk_level).upper()


def get_status_value(status):
    return get_enum_value(status).lower()


def get_department_report(department_id):
    return next(
        (
            item for item in report.departments
            if item.entity_id == department_id
        ),
        None,
    )


def get_department_name(department_id):
    department = engine.get_entity(department_id)
    return department.name if department is not None else str(department_id)


def get_action_for_recommendation(recommendation_id):
    return next(
        (
            action for action in engine.get_actions()
            if action.recommendation_id == recommendation_id
        ),
        None,
    )


def display_alert(alert):
    severity = get_enum_value(alert.severity).upper()
    st.warning(f"**{severity}** — {alert.message}")


def display_recommendations(department_result):
    recommendations = department_result.recommendations
    if not recommendations:
        st.info("No recommendations currently available.")
        return

    for recommendation in recommendations:
        priority = get_enum_value(recommendation.priority).upper()
        st.markdown(f"**{priority} priority**")
        st.write(recommendation.description)

        existing_action = get_action_for_recommendation(recommendation.id)
        if existing_action:
            st.caption(
                "Action status: "
                + get_status_value(existing_action.status).replace(
                    "_", " "
                ).title()
            )
        elif st.button(
            "Create tracked action",
            key=f"create_action_{recommendation.id}",
        ):
            service.create_action(recommendation_id=recommendation.id)
            st.success("Action created.")
            st.rerun()

        st.divider()


def get_department_summary():
    rows = []
    for item in report.departments:
        rows.append({
            "Department": get_department_name(item.entity_id),
            "Risk level": get_risk_level(item.assessment),
            "Alerts": item.assessment.alert_count,
            "Signal categories": ", ".join(
                item.assessment.signal_categories
            ) or "None",
        })
    return pd.DataFrame(rows)


def get_indicator_dataframe(department_result):
    rows = []
    for result in department_result.analytics:
        rows.append({
            "Indicator": result.indicator_name,
            "Baseline": result.baseline.value,
            "Current": result.current.value,
            "Change": result.absolute_deviation,
            "Change (%)": result.percentage_deviation,
            "Trend": get_enum_value(result.trend).replace(
                "_", " "
            ).title(),
            "Status": get_enum_value(result.status).replace(
                "_", " "
            ).title(),
        })
    return pd.DataFrame(
        rows,
        columns=[
            "Indicator", "Baseline", "Current", "Change",
            "Change (%)", "Trend", "Status",
        ],
    )


def display_indicator_table_and_chart(department_result, chart_title):
    analytics_df = get_indicator_dataframe(department_result)
    if analytics_df.empty:
        st.info("No indicator comparisons are available.")
        return

    st.dataframe(
        analytics_df,
        use_container_width=True,
        hide_index=True,
    )

    chart_df = analytics_df[
        ["Indicator", "Baseline", "Current"]
    ].copy()
    chart_df["Baseline"] = pd.to_numeric(
        chart_df["Baseline"], errors="coerce"
    )
    chart_df["Current"] = pd.to_numeric(
        chart_df["Current"], errors="coerce"
    )
    chart_df = chart_df.dropna(
        subset=["Baseline", "Current"]
    )

    if not chart_df.empty:
        st.subheader(chart_title)
        st.bar_chart(chart_df.set_index("Indicator"))


# ----------------------------------------------------------
# SIDEBAR AND DEPARTMENT SELECTION
# ----------------------------------------------------------
st.sidebar.title("WardPulse")
st.sidebar.caption("Demonstration workspace")

workspace = st.sidebar.selectbox(
    "Select workspace",
    ["Executive Dashboard", "Department Manager Dashboard"],
    key="workspace_selector",
)

st.sidebar.divider()

departments = engine.list_entities(entity_type="department")
department_names = {
    department.id: department.name for department in departments
}
department_ids = list(department_names.keys())

selected_department_id = None
if workspace == "Department Manager Dashboard":
    if department_ids:
        selected_department_id = st.sidebar.selectbox(
            "Select department",
            department_ids,
            format_func=lambda department_id: department_names[
                department_id
            ],
            key="manager_department",
        )
    else:
        st.sidebar.warning("No departments are available in the demo data.")

st.sidebar.divider()
st.sidebar.caption("Reporting periods")
st.sidebar.write("Baseline: 25–31 October 2026")
st.sidebar.write(
    "Current: 1 November – "
    f"{get_current_period_end().strftime('%d %B %Y')}"
)
st.sidebar.divider()

if st.sidebar.button(
    "Refresh surveillance results",
    use_container_width=True,
):
    try:
        refresh_surveillance()
        st.rerun()
    except Exception as error:
        st.sidebar.error(f"Refresh failed: {error}")

if st.sidebar.button(
    "Reset demonstration data",
    use_container_width=True,
):
    try:
        initialize_application()
        st.rerun()
    except Exception as error:
        st.sidebar.error(f"Reset failed: {error}")

st.sidebar.caption("Demonstration environment · Synthetic data")
st.sidebar.caption(
    "Workspace selection is not authentication or an access-control "
    "mechanism."
)

# ----------------------------------------------------------
# EXECUTIVE DASHBOARD
# ----------------------------------------------------------
def executive_dashboard():
    st.header("Executive Dashboard")
    st.caption(
        "Facility-wide overview of workforce and operational conditions."
    )

    total_alerts = sum(len(item.alerts) for item in report.departments)
    elevated_departments = sum(
        get_risk_level(item.assessment) in ("HIGH", "CRITICAL")
        for item in report.departments
    )
    all_actions = engine.get_actions()
    pending_actions = sum(
        get_status_value(action.status) == "pending"
        for action in all_actions
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Departments monitored", report.departments_monitored)
    col2.metric("Active alerts", total_alerts)
    col3.metric("Elevated-risk departments", elevated_departments)
    col4.metric("Pending actions", pending_actions)

    st.divider()
    st.subheader("Departmental Risk Overview")
    summary = get_department_summary()
    if summary.empty:
        st.info("No departments are currently available.")
    else:
        st.dataframe(
            summary, use_container_width=True, hide_index=True
        )

    st.divider()
    st.subheader("Departments Requiring Attention")
    attention_needed = [
        item for item in report.departments
        if get_risk_level(item.assessment) in ("HIGH", "CRITICAL")
    ]

    if not attention_needed:
        st.success(
            "No departments currently meet the configured "
            "elevated-risk conditions."
        )
    else:
        for item in attention_needed:
            department_name = get_department_name(item.entity_id)
            with st.expander(
                f"{department_name} — {get_risk_level(item.assessment)}"
            ):
                st.write(item.assessment.summary)
                st.write(f"Alerts: {item.assessment.alert_count}")
                for alert in item.alerts:
                    display_alert(alert)
                st.markdown("**Recommendations**")
                display_recommendations(item)

    st.divider()
    st.subheader("Action Progress")
    actions = engine.get_actions()
    if not actions:
        st.info("No operational actions have been created yet.")
    else:
        action_data = [
            {
                "Department": get_department_name(action.entity_id),
                "Action": action.description,
                "Assigned to": action.assigned_to or "Unassigned",
                "Status": get_status_value(action.status).replace(
                    "_", " "
                ).title(),
            }
            for action in actions
        ]
        st.dataframe(
            pd.DataFrame(action_data),
            use_container_width=True,
            hide_index=True,
        )


# ----------------------------------------------------------
# EXECUTIVE DEPARTMENT ANALYSIS
# ----------------------------------------------------------
def executive_department_analysis():
    st.header("Department Analysis")
    if not department_ids:
        st.info("No departments are available for analysis.")
        return

    selected_id = st.selectbox(
        "Select department",
        department_ids,
        format_func=lambda department_id: department_names[
            department_id
        ],
        key="executive_analysis_department",
    )
    selected = get_department_report(selected_id)
    if selected is None:
        st.warning("No surveillance results are available.")
        return

    st.subheader(department_names[selected_id])
    col1, col2, col3 = st.columns(3)
    col1.metric("Risk level", get_risk_level(selected.assessment))
    col2.metric("Triggered alerts", selected.assessment.alert_count)
    col3.metric(
        "Signal categories",
        len(selected.assessment.signal_categories),
    )
    st.write(selected.assessment.summary)

    st.divider()
    st.subheader("Indicator Comparisons")
    display_indicator_table_and_chart(
        selected, "Baseline vs Current Values"
    )

    st.divider()
    st.subheader("Contributing Alerts")
    if selected.alerts:
        for alert in selected.alerts:
            display_alert(alert)
    else:
        st.success("No configured alerts were triggered.")

    st.divider()
    st.subheader("Recommendations")
    display_recommendations(selected)


# ----------------------------------------------------------
# DEPARTMENT MANAGER DASHBOARD
# ----------------------------------------------------------
def manager_dashboard():
    if selected_department_id is None:
        st.header("Department Manager Dashboard")
        st.info("Select a department in the sidebar to continue.")
        return

    department_id = selected_department_id
    department_name = department_names[department_id]
    selected = get_department_report(department_id)

    st.header("Department Manager Dashboard")
    st.caption(f"Operational workspace · {department_name}")

    if selected is None:
        st.warning(
            "No surveillance results are available for this department."
        )
        return

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Department risk level", get_risk_level(selected.assessment)
    )
    col2.metric("Active alerts", selected.assessment.alert_count)
    col3.metric("Recommendations", len(selected.recommendations))

    st.divider()
    st.subheader("Department Status")
    st.write(selected.assessment.summary)

    st.divider()
    st.subheader("Your Departmental Indicators")
    display_indicator_table_and_chart(selected, "Indicator Trends")

    st.divider()
    st.subheader("Alerts Requiring Review")
    if selected.alerts:
        for alert in selected.alerts:
            display_alert(alert)
    else:
        st.success("No configured alerts for this department.")

    st.divider()
    st.subheader("Recommended Follow-up")
    display_recommendations(selected)


# ----------------------------------------------------------
# OBSERVATION ENTRY
# ----------------------------------------------------------
def record_observation_page():
    if selected_department_id is None:
        st.header("Record Department Observation")
        st.info("Select a department in the sidebar to continue.")
        return

    department_id = selected_department_id
    department_name = department_names[department_id]

    st.header("Record Department Observation")
    st.caption(f"Submit an operational observation for {department_name}.")

    metric_options = {
        "Staff Absence": {
            "metric": "staff_absence_count",
            "unit": "staff absences",
            "category": "workforce",
        },
        "Staff Overtime": {
            "metric": "overtime_hours",
            "unit": "hours",
            "category": "workforce",
        },
        "Respiratory Cases": {
            "metric": "respiratory_case_count",
            "unit": "cases",
            "category": "clinical_service",
        },
        "Air Quality Index": {
            "metric": "air_quality_index",
            "unit": "index",
            "category": "environmental",
        },
        "Occupational Incidents": {
            "metric": "occupational_incident_count",
            "unit": "incidents",
            "category": "workplace_safety",
        },
    }

    st.info(
        "Use one reporting interval consistently for each metric. "
        "Avoid mixing shift, daily and weekly totals for the same "
        "metric because this may distort aggregate calculations."
    )

    with st.form("department_observation_form"):
        observation_date = st.date_input(
            "Observation date",
            value=datetime.now(timezone.utc).date(),
            max_value=datetime.now(timezone.utc).date(),
        )
        reporting_interval = st.selectbox(
            "Reporting interval", ["Shift", "Daily", "Weekly summary"]
        )

        shift = "Not applicable"
        if reporting_interval == "Shift":
            shift = st.selectbox(
                "Shift", ["Morning", "Afternoon", "Night"]
            )

        metric_label = st.selectbox(
            "Observation category / metric", list(metric_options.keys())
        )
        metric_details = metric_options[metric_label]
        st.caption(f"Unit: {metric_details['unit']}")

        observation_value = st.number_input(
            "Observed value", min_value=0.0, value=0.0, step=1.0
        )
        observation_note = st.text_area(
            "Contextual note (optional)",
            placeholder="Add relevant operational context...",
        )
        submitted = st.form_submit_button(
            "Submit observation", use_container_width=True
        )

    if submitted:
        observed_at = datetime.combine(
            observation_date,
            datetime_time(12, 0),
            tzinfo=timezone.utc,
        )
        observation = Observation(
            id=f"MANUAL-{uuid4().hex[:12]}",
            entity_id=department_id,
            metric=metric_details["metric"],
            value=observation_value,
            unit=metric_details["unit"],
            source="department_manager_entry",
            observed_at=observed_at,
            metadata={
                "reporting_interval": reporting_interval,
                "shift": shift,
                "category": metric_details["category"],
                "note": observation_note,
                "synthetic": True,
                "entered_via": "manager_dashboard",
            },
        )

        try:
            engine.record_observation(observation)
            refresh_surveillance()
            st.success(
                "Observation recorded and surveillance results recalculated."
            )
            st.rerun()
        except Exception as error:
            st.error(f"Could not record observation: {error}")

    st.divider()
    st.subheader("Recent Department Observations")
    observations = engine.get_observations(entity_id=department_id)
    observations = sorted(
        observations,
        key=lambda item: item.observed_at,
        reverse=True,
    )

    recent_data = [
        {
            "Date": item.observed_at.strftime("%d %b %Y"),
            "Metric": item.metric.replace("_", " ").title(),
            "Value": item.value,
            "Unit": item.unit or "",
            "Source": item.source or "Demo data",
        }
        for item in observations[:15]
    ]

    if recent_data:
        st.dataframe(
            pd.DataFrame(recent_data),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No observations recorded yet.")


# ----------------------------------------------------------
# ALERTS AND RECOMMENDATIONS
# ----------------------------------------------------------
def alerts_and_recommendations_page(department_filter=None):
    st.header("Alerts and Recommendations")
    departments_to_display = report.departments

    if department_filter is not None:
        departments_to_display = [
            item for item in departments_to_display
            if item.entity_id == department_filter
        ]

    if not departments_to_display:
        st.info("No department results are available.")
        return

    for item in departments_to_display:
        st.subheader(get_department_name(item.entity_id))
        if not item.alerts:
            st.success("No configured alerts for this department.")
        else:
            for alert in item.alerts:
                display_alert(alert)

        st.markdown("**Recommendations**")
        display_recommendations(item)
        st.divider()


# ----------------------------------------------------------
# ACTION TRACKING
# ----------------------------------------------------------
def action_tracking_page(department_filter=None):
    st.header("Action Tracking")
    actions = engine.get_actions()

    if department_filter is not None:
        actions = [
            action for action in actions
            if action.entity_id == department_filter
        ]

    if not actions:
        st.info(
            "No tracked actions are currently available. "
            "Create an action from a recommendation."
        )
        return

    valid_statuses = [
        "pending", "in_progress", "completed", "cancelled"
    ]

    for action in actions:
        department_name = get_department_name(action.entity_id)
        current_status = get_status_value(action.status)

        with st.expander(
            f"{department_name} — "
            f"{current_status.replace('_', ' ').title()}"
        ):
            st.write(action.description)
            st.write(
                f"**Assigned to:** {action.assigned_to or 'Unassigned'}"
            )
            st.write(
                f"**Current status:** "
                f"{current_status.replace('_', ' ').title()}"
            )

            status_index = (
                valid_statuses.index(current_status)
                if current_status in valid_statuses
                else 0
            )
            selected_status = st.selectbox(
                "Update action status",
                valid_statuses,
                index=status_index,
                key=f"status_{action.id}",
            )

            if st.button(
                "Save status", key=f"save_status_{action.id}"
            ):
                try:
                    engine.update_action_status(
                        action.id, selected_status
                    )
                    st.success("Action status updated.")
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not update action: {error}")

    st.divider()
    st.subheader("Action Summary")

    all_actions = engine.get_actions()
    if department_filter is not None:
        all_actions = [
            action for action in all_actions
            if action.entity_id == department_filter
        ]

    action_summary = {
        "Pending": sum(
            get_status_value(action.status) == "pending"
            for action in all_actions
        ),
        "In progress": sum(
            get_status_value(action.status) == "in_progress"
            for action in all_actions
        ),
        "Completed": sum(
            get_status_value(action.status) == "completed"
            for action in all_actions
        ),
        "Cancelled": sum(
            get_status_value(action.status) == "cancelled"
            for action in all_actions
        ),
    }

    st.dataframe(
        pd.DataFrame([
            {"Status": status, "Actions": count}
            for status, count in action_summary.items()
        ]),
        use_container_width=True,
        hide_index=True,
    )


# ----------------------------------------------------------
# WORKSPACE NAVIGATION
# ----------------------------------------------------------
if workspace == "Executive Dashboard":
    page = st.sidebar.radio(
        "Executive navigation",
        [
            "Overview",
            "Department Analysis",
            "Alerts & Recommendations",
            "Action Tracking",
        ],
        key="executive_navigation",
    )

    if page == "Overview":
        executive_dashboard()
    elif page == "Department Analysis":
        executive_department_analysis()
    elif page == "Alerts & Recommendations":
        alerts_and_recommendations_page()
    elif page == "Action Tracking":
        action_tracking_page()

else:
    page = st.sidebar.radio(
        "Manager navigation",
        [
            "My Department",
            "Record Observation",
            "Alerts & Recommendations",
            "Action Tracking",
        ],
        key="manager_navigation",
    )

    if page == "My Department":
        manager_dashboard()
    elif page == "Record Observation":
        record_observation_page()
    elif page == "Alerts & Recommendations":
        alerts_and_recommendations_page(
            department_filter=selected_department_id
        )
    elif page == "Action Tracking":
        action_tracking_page(
            department_filter=selected_department_id
        )

# ----------------------------------------------------------
# FOOTER
# ----------------------------------------------------------
st.divider()
st.caption(
    "WardPulse is a prototype early-warning and decision-support system. "
    "The demonstration uses synthetic data and configurable indicators. "
    "Alerts require human review and do not establish a diagnosis, causal "
    "relationship or validated prediction of workforce health outcomes."
)
