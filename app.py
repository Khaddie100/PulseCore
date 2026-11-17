
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from pulsecore.applications.wardpulse.demo_data import create_demo_engine
from pulsecore.applications.wardpulse.service import WardPulseSurveillance


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="WardPulse | Early Warning",
    page_icon="🏥",
    layout="wide",
)

st.title("WardPulse")
st.caption(
    "Population and Workforce Health Early Warning System"
)


# --------------------------------------------------
# INITIALIZE THE APPLICATION
# --------------------------------------------------

def initialize_application():
    engine = create_demo_engine()
    service = WardPulseSurveillance(engine)

    report = service.run(
        baseline_start=datetime(
            2026, 10, 25, tzinfo=timezone.utc
        ),
        baseline_end=datetime(
            2026, 10, 31, 23, 59, tzinfo=timezone.utc
        ),
        current_start=datetime(
            2026, 11, 1, tzinfo=timezone.utc
        ),
        current_end=datetime(
            2026, 11, 7, 23, 59, tzinfo=timezone.utc
        ),
    )

    st.session_state.engine = engine
    st.session_state.service = service
    st.session_state.report = report


if "report" not in st.session_state:
    initialize_application()

engine = st.session_state.engine
service = st.session_state.service
report = st.session_state.report


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("WardPulse Navigation")

page = st.sidebar.radio(
    "Select a view",
    [
        "Overview",
        "Department Analysis",
        "Alerts and Recommendations",
        "Action Tracking",
    ],
)

st.sidebar.divider()

st.sidebar.caption("Reporting periods")
st.sidebar.write("Baseline: 25–31 October 2026")
st.sidebar.write("Current: 1–7 November 2026")

st.sidebar.divider()

if st.sidebar.button("Refresh demonstration data"):
    initialize_application()
    st.rerun()

st.sidebar.caption(
    "Demonstration environment · Synthetic data"
)


# --------------------------------------------------
# COMMON DATA
# --------------------------------------------------

departments = report.departments

total_alerts = sum(
    len(department.alerts)
    for department in departments
)

high_risk_departments = sum(
    department.assessment.risk_level.value
    in ["high", "critical"]
    for department in departments
)

all_actions = engine.get_actions()

pending_actions = sum(
    action.status == "pending"
    for action in all_actions
)


def risk_label(level):
    return level.value.upper()


def get_action_for_recommendation(recommendation_id):
    return next(
        (
            action for action in engine.get_actions()
            if action.recommendation_id == recommendation_id
        ),
        None,
    )


# --------------------------------------------------
# OVERVIEW
# --------------------------------------------------

if page == "Overview":

    st.header("Surveillance Overview")

    st.caption(
        "Aggregated monitoring of workforce, clinical, "
        "environmental and workplace safety signals."
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Departments monitored",
        report.departments_monitored,
    )

    col2.metric(
        "Active alerts",
        total_alerts,
    )

    col3.metric(
        "Elevated-risk departments",
        high_risk_departments,
    )

    col4.metric(
        "Pending actions",
        pending_actions,
    )

    st.divider()

    st.subheader("Departmental Risk Summary")

    risk_data = []

    for department in departments:
        risk_data.append({
            "Department": department.entity_id,
            "Risk level": risk_label(
                department.assessment.risk_level
            ),
            "Alerts": department.assessment.alert_count,
            "Signal categories": ", ".join(
                department.assessment.signal_categories
            ) or "None",
        })

    st.dataframe(
        pd.DataFrame(risk_data),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Risk Findings")

    for department in departments:
        assessment = department.assessment

        with st.expander(
            f"{department.entity_id} — "
            f"{risk_label(assessment.risk_level)} risk"
        ):
            st.write(assessment.summary)

            if department.alerts:
                for alert in department.alerts:
                    st.warning(
                        f"**{alert.severity.value.upper()}** — "
                        f"{alert.message}"
                    )
            else:
                st.success(
                    "No configured risk thresholds were exceeded."
                )

    st.divider()

    st.subheader("Surveillance Interpretation")

    st.info(
        "An alert indicates that a configured threshold was exceeded. "
        "It is an early-warning signal requiring review, not proof "
        "of an outbreak, occupational illness or causal relationship."
    )


# --------------------------------------------------
# DEPARTMENT ANALYSIS
# --------------------------------------------------

elif page == "Department Analysis":

    st.header("Department Analysis")

    department_ids = [
        department.entity_id
        for department in departments
    ]

    selected_id = st.selectbox(
        "Select department",
        department_ids,
    )

    selected = next(
        department for department in departments
        if department.entity_id == selected_id
    )

    st.subheader(selected_id)

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Risk level",
        risk_label(selected.assessment.risk_level),
    )

    col2.metric(
        "Triggered alerts",
        selected.assessment.alert_count,
    )

    col3.metric(
        "Signal categories",
        len(selected.assessment.signal_categories),
    )

    st.write(selected.assessment.summary)

    st.divider()

    st.subheader("Indicator Comparisons")

    analytics_data = []

    for result in selected.analytics:
        analytics_data.append({
            "Indicator": result.indicator_name,
            "Baseline": result.baseline.value,
            "Current": result.current.value,
            "Change": result.absolute_deviation,
            "Change (%)": result.percentage_deviation,
            "Trend": result.trend,
            "Status": result.status,
        })

    analytics_df = pd.DataFrame(analytics_data)

    st.dataframe(
        analytics_df,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Baseline vs Current Values")

    chart_data = analytics_df.set_index("Indicator")[
        ["Baseline", "Current"]
    ]

    st.bar_chart(chart_data)

    st.caption(
        "Values are aggregated according to each indicator's "
        "configured calculation method."
    )

    st.divider()

    st.subheader("Contributing Alerts")

    if selected.alerts:
        for alert in selected.alerts:
            st.warning(
                f"**{alert.severity.value.upper()}** — {alert.message}"
            )
    else:
        st.success("No alerts were triggered for this department.")


# --------------------------------------------------
# ALERTS AND RECOMMENDATIONS
# --------------------------------------------------

elif page == "Alerts and Recommendations":

    st.header("Alerts and Preventive Recommendations")

    for department in departments:

        st.subheader(department.entity_id)

        if not department.alerts:
            st.success("No configured alerts.")
        else:
            for alert in department.alerts:
                st.warning(
                    f"**{alert.severity.value.upper()}** — "
                    f"{alert.message}"
                )

        st.markdown("**Recommended preventive actions**")

        if not department.recommendations:
            st.write("No recommendations generated.")
        else:
            for recommendation in department.recommendations:
                with st.container(border=True):
                    st.markdown(f"**{recommendation.title}**")
                    st.write(recommendation.description)
                    st.caption(
                        f"Priority: {recommendation.priority.value.upper()}"
                    )
                    st.caption(
                        f"Rationale: {recommendation.rationale}"
                    )


# --------------------------------------------------
# ACTION TRACKING
# --------------------------------------------------

elif page == "Action Tracking":

    st.header("Operational Action Tracking")

    st.caption(
        "Convert preventive recommendations into assigned "
        "and trackable operational tasks."
    )

    recommendations = engine.get_recommendations()

    if not recommendations:
        st.info("There are currently no recommendations.")
    else:
        for recommendation in recommendations:

            action = get_action_for_recommendation(
                recommendation.id
            )

            with st.container(border=True):

                st.markdown(f"**{recommendation.title}**")
                st.write(recommendation.description)

                st.caption(
                    f"Department: {recommendation.entity_id}"
                )

                if action is None:

                    assignee = st.text_input(
                        "Assign to",
                        key=f"assignee_{recommendation.id}",
                        placeholder="e.g. Department Manager",
                    )

                    if st.button(
                        "Create operational action",
                        key=f"create_{recommendation.id}",
                    ):
                        service.create_action(
                            recommendation_id=recommendation.id,
                            assigned_to=assignee.strip() or None,
                        )
                        st.success("Action created.")
                        st.rerun()

                else:

                    st.write(
                        f"**Assigned to:** "
                        f"{action.assigned_to or 'Unassigned'}"
                    )

                    st.write(
                        f"**Current status:** "
                        f"{action.status.replace('_', ' ').title()}"
                    )

                    statuses = [
                        "pending",
                        "in_progress",
                        "completed",
                        "cancelled",
                    ]

                    selected_status = st.selectbox(
                        "Update action status",
                        statuses,
                        index=statuses.index(action.status),
                        key=f"status_{action.id}",
                    )

                    if st.button(
                        "Save status",
                        key=f"save_{action.id}",
                    ):
                        engine.update_action_status(
                            action.id,
                            selected_status,
                        )
                        st.success("Action status updated.")
                        st.rerun()

    st.divider()

    st.subheader("Action Summary")

    actions = engine.get_actions()

    action_summary = {
        "Pending": sum(
            action.status == "pending" for action in actions
        ),
        "In progress": sum(
            action.status == "in_progress" for action in actions
        ),
        "Completed": sum(
            action.status == "completed" for action in actions
        ),
        "Cancelled": sum(
            action.status == "cancelled" for action in actions
        ),
    }

    st.dataframe(
        pd.DataFrame(
            [
                {"Status": status, "Actions": count}
                for status, count in action_summary.items()
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "WardPulse is a prototype early-warning and decision-support "
    "system. All displayed data and risk thresholds are synthetic "
    "demonstration inputs and require operational validation "
    "before real-world deployment."
)
