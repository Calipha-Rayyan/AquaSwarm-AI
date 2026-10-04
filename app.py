import streamlit as st
import pandas as pd

from backend.services import (
    load_tanks,
    load_suppliers,
    load_consumption,
    detect_alerts,
)

from backend.api import (
    get_deliveries,
    get_verifications,
    create_delivery,
    approve_delivery,
    update_delivery,
    verify_delivery,
    log_agent_run,
)

from agents.orchestrator import run_operational_analysis


st.set_page_config(
    page_title="AquaSwarm AI",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    .main {
        background-color: #f7f9fb;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .top-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #16324f;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        color: #617386;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }

    .section-title {
        font-size: 1.35rem;
        font-weight: 650;
        color: #16324f;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
    }

    .info-box {
        background: white;
        border-left: 4px solid #2b6f8a;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ---------------------------------------------------------
# DATA
# ---------------------------------------------------------

tanks = load_tanks()
suppliers = load_suppliers()
consumption = load_consumption()

alerts = detect_alerts()

deliveries = get_deliveries()
verifications = get_verifications()


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.markdown(
    '<div class="top-title">AquaSwarm AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Water operations monitoring and shortage coordination control room'
    '</div>',
    unsafe_allow_html=True
)

st.info(
    "MVP environment using synthetic operational data. "
    "Critical physical actions require manager approval."
)


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

st.sidebar.title("Control Room")

page = st.sidebar.radio(
    "Navigate",
    [
        "Overview",
        "AI Operations",
        "Tank Monitoring",
        "Alerts",
        "Suppliers",
        "Delivery Operations",
        "Verification",
        "Agent Activity",
    ]
)

if st.sidebar.button("Refresh data"):
    st.rerun()


# ---------------------------------------------------------
# OVERVIEW
# ---------------------------------------------------------

if page == "Overview":

    st.markdown(
        '<div class="section-title">Operational Overview</div>',
        unsafe_allow_html=True
    )

    available_supplier_count = int(
        suppliers["available"].sum()
    )

    critical_alerts = sum(
        1
        for alert in alerts
        if alert["severity"] == "CRITICAL"
    )

    active_deliveries = sum(
        1
        for delivery in deliveries
        if delivery["status"] in [
            "requested",
            "approved",
            "dispatched"
        ]
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Monitored Sites",
            len(tanks)
        )

    with col2:
        st.metric(
            "Available Suppliers",
            available_supplier_count
        )

    with col3:
        st.metric(
            "Active Alerts",
            len(alerts)
        )

    with col4:
        st.metric(
            "Active Deliveries",
            active_deliveries
        )

    st.markdown(
        '<div class="section-title">System Workflow</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Observe → Predict → Diagnose → Allocate → "
        "Approve → Deliver → Verify → Re-plan"
    )

    st.markdown(
        '<div class="section-title">Tank Status</div>',
        unsafe_allow_html=True
    )

    tank_view = tanks.copy()

    tank_view["level_percent"] = (
        tank_view["current_level"]
        / tank_view["capacity"]
        * 100
    )

    tank_view["status"] = tank_view[
        "level_percent"
    ].apply(
        lambda value:
        "Critical"
        if value <= 20
        else "High"
        if value <= 35
        else "Normal"
    )

    st.dataframe(
        tank_view,
        width="stretch",
        hide_index=True
    )


# ---------------------------------------------------------
# AI OPERATIONS
# ---------------------------------------------------------

elif page == "AI Operations":

    st.markdown(
        '<div class="section-title">AI Operations Center</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Run the deterministic operational analysis used by "
        "AquaSwarm AI to identify shortage risk, abnormal consumption, "
        "supplier options and water allocation."
    )

    st.warning(
        "Demo scenario: simulate a major consumption spike at Site 1 "
        "(Hostel A). No real-world supplier or physical dispatch occurs."
    )

    demo_mode = st.checkbox(
        "Simulate Hostel A consumption spike"
    )

    spike_site = 1 if demo_mode else None

    if st.button(
        "Run AquaSwarm Analysis"
    ):

        results = run_operational_analysis(
            tanks,
            consumption,
            suppliers,
            spike_site
        )

        log_agent_run(
            "AquaSwarm Orchestrator",
            "completed"
        )

        st.success(
            "Operational analysis completed."
        )

        for result in results:

            prediction = result["prediction"]
            anomaly = result["anomaly"]
            allocation = result["allocation"]

            st.markdown(
                f"### Site {result['site_id']}"
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("Shortage Risk")
                st.write(
                    f"**{prediction['risk']}**"
                )
                st.write(
                    f"Level: "
                    f"{prediction['level_percent']}%"
                )
                st.write(
                    f"Estimated hours to empty: "
                    f"{prediction['hours_to_empty']}"
                )

            with col2:
                st.write("Anomaly Detection")

                if anomaly["is_anomaly"]:
                    st.error(
                        f"{anomaly['severity']} anomaly"
                    )
                else:
                    st.success(
                        "No abnormal consumption detected"
                    )

                st.write(
                    anomaly["reason"]
                )

            with col3:
                st.write("Allocation")

                st.write(
                    f"Required: "
                    f"{allocation['requested']:,.0f}"
                )

                st.write(
                    f"Allocated: "
                    f"{allocation['allocated']:,.0f}"
                )

                if allocation["fully_allocated"]:
                    st.success(
                        "Requirement fully allocated"
                    )
                else:
                    st.warning(
                        f"Remaining: "
                        f"{allocation['remaining']:,.0f}"
                    )

            if result["suppliers"]:

                st.write(
                    "Supplier Evaluation"
                )

                supplier_df = pd.DataFrame(
                    result["suppliers"]
                )

                st.dataframe(
                    supplier_df,
                    width="stretch",
                    hide_index=True
                )

            st.divider()


# ---------------------------------------------------------
# TANK MONITORING
# ---------------------------------------------------------

elif page == "Tank Monitoring":

    st.markdown(
        '<div class="section-title">Tank Monitoring</div>',
        unsafe_allow_html=True
    )

    tank_view = tanks.copy()

    tank_view["level_percent"] = (
        tank_view["current_level"]
        / tank_view["capacity"]
        * 100
    )

    for _, tank in tank_view.iterrows():

        st.write(
            f"Site {int(tank['site_id'])}"
        )

        percentage = int(
            tank["level_percent"]
        )

        st.progress(
            min(
                max(
                    percentage,
                    0
                ),
                100
            )
        )

        st.write(
            f"{tank['current_level']:,.0f} / "
            f"{tank['capacity']:,.0f} units "
            f"({tank['level_percent']:.1f}%)"
        )

        st.divider()


# ---------------------------------------------------------
# ALERTS
# ---------------------------------------------------------

elif page == "Alerts":

    st.markdown(
        '<div class="section-title">'
        'Alerts and Exceptions'
        '</div>',
        unsafe_allow_html=True
    )

    if not alerts:

        st.success(
            "No current high or critical tank-level alerts."
        )

    else:

        for alert in alerts:

            if alert["severity"] == "CRITICAL":

                st.error(
                    f"Site {alert['site_id']}: "
                    f"{alert['message']}"
                )

            else:

                st.warning(
                    f"Site {alert['site_id']}: "
                    f"{alert['message']}"
                )


# ---------------------------------------------------------
# SUPPLIERS
# ---------------------------------------------------------

elif page == "Suppliers":

    st.markdown(
        '<div class="section-title">'
        'Supplier Capacity'
        '</div>',
        unsafe_allow_html=True
    )

    supplier_view = suppliers.copy()

    supplier_view["status"] = supplier_view[
        "available"
    ].apply(
        lambda value:
        "Available"
        if value == 1
        else "Unavailable"
    )

    st.dataframe(
        supplier_view,
        width="stretch",
        hide_index=True
    )


# ---------------------------------------------------------
# DELIVERY OPERATIONS
# ---------------------------------------------------------

elif page == "Delivery Operations":

    st.markdown(
        '<div class="section-title">'
        'Delivery Operations'
        '</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Critical delivery actions require manager approval."
    )

    available_suppliers = suppliers[
        suppliers["available"] == 1
    ]

    supplier_options = (
        available_suppliers["id"].tolist()
    )

    with st.form("delivery_form"):

        site_id = st.number_input(
            "Site ID",
            min_value=1,
            max_value=len(tanks),
            value=1,
            step=1
        )

        if supplier_options:

            supplier_id = st.selectbox(
                "Supplier",
                supplier_options
            )

            quantity = st.number_input(
                "Requested Quantity",
                min_value=1.0,
                value=5000.0,
                step=500.0
            )

            submitted = st.form_submit_button(
                "Create Delivery Request"
            )

            if submitted:

                result = create_delivery(
                    int(site_id),
                    int(supplier_id),
                    float(quantity)
                )

                log_agent_run(
                    "Delivery Coordination",
                    "requested"
                )

                st.success(
                    f"Delivery request #{result['id']} created."
                )

                st.rerun()

        else:

            st.warning(
                "No available suppliers."
            )

    deliveries = get_deliveries()

    st.markdown(
        '<div class="section-title">'
        'Delivery Requests'
        '</div>',
        unsafe_allow_html=True
    )

    if deliveries:

        st.dataframe(
            pd.DataFrame(deliveries),
            width="stretch",
            hide_index=True
        )

        selected_id = st.selectbox(
            "Select Delivery ID",
            [
                item["id"]
                for item in deliveries
            ]
        )

        selected_delivery = next(
            item
            for item in deliveries
            if item["id"] == selected_id
        )

        st.write(
            f"Current status: "
            f"**{selected_delivery['status']}**"
        )

        if selected_delivery["status"] == "requested":

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "Approve Delivery"
                ):

                    approve_delivery(
                        selected_id,
                        True,
                        "Manager"
                    )

                    log_agent_run(
                        "Manager Approval",
                        "approved"
                    )

                    st.success(
                        "Delivery approved."
                    )

                    st.rerun()

            with col2:

                if st.button(
                    "Reject Delivery"
                ):

                    approve_delivery(
                        selected_id,
                        False,
                        "Manager"
                    )

                    log_agent_run(
                        "Manager Approval",
                        "rejected"
                    )

                    st.warning(
                        "Delivery rejected."
                    )

                    st.rerun()

        elif selected_delivery["status"] == "approved":

            if st.button(
                "Mark as Dispatched"
            ):

                update_delivery(
                    selected_id,
                    "dispatched"
                )

                log_agent_run(
                    "Delivery Coordination",
                    "dispatched"
                )

                st.success(
                    "Delivery marked as dispatched."
                )

                st.rerun()

        elif selected_delivery["status"] == "dispatched":

            if st.button(
                "Mark as Delivered"
            ):

                update_delivery(
                    selected_id,
                    "delivered"
                )

                log_agent_run(
                    "Delivery Coordination",
                    "delivered"
                )

                st.success(
                    "Delivery marked as delivered."
                )

                st.rerun()

    else:

        st.info(
            "No delivery requests have been created yet."
        )


# ---------------------------------------------------------
# VERIFICATION
# ---------------------------------------------------------

elif page == "Verification":

    st.markdown(
        '<div class="section-title">'
        'Delivery Verification'
        '</div>',
        unsafe_allow_html=True
    )

    deliveries = get_deliveries()

    delivered = [
        delivery
        for delivery in deliveries
        if delivery["status"] == "delivered"
    ]

    if delivered:

        selected_id = st.selectbox(
            "Delivered Request",
            [
                item["id"]
                for item in delivered
            ]
        )

        selected_delivery = next(
            item
            for item in delivered
            if item["id"] == selected_id
        )

        expected = float(
            selected_delivery["quantity"]
        )

        st.write(
            f"Expected quantity: "
            f"{expected:,.0f}"
        )

        actual = st.number_input(
            "Actual Delivered Quantity",
            min_value=0.0,
            value=expected,
            step=100.0
        )

        if st.button(
            "Verify Delivery"
        ):

            result = verify_delivery(
                selected_id,
                expected,
                float(actual)
            )

            log_agent_run(
                "Verification Agent",
                result["status"]
            )

            if result["status"] == "passed":

                st.success(
                    "Verification passed within the 10% tolerance."
                )

            else:

                st.error(
                    "Verification exception detected. "
                    "Re-planning is required."
                )

        verifications = get_verifications()

        if verifications:

            st.markdown(
                '<div class="section-title">'
                'Verification History'
                '</div>',
                unsafe_allow_html=True
            )

            st.dataframe(
                pd.DataFrame(verifications),
                width="stretch",
                hide_index=True
            )

    else:

        st.info(
            "No delivered requests are available for verification."
        )


# ---------------------------------------------------------
# AGENT ACTIVITY
# ---------------------------------------------------------

elif page == "Agent Activity":

    st.markdown(
        '<div class="section-title">'
        'Agent Activity and Audit Trail'
        '</div>',
        unsafe_allow_html=True
    )

    from backend.database import get_connection

    connection = get_connection()

    agent_runs = pd.read_sql_query(
        """
        SELECT *
        FROM agent_runs
        ORDER BY id DESC
        """,
        connection
    )

    connection.close()

    if agent_runs.empty:

        st.info(
            "No agent activity has been recorded yet."
        )

    else:

        st.dataframe(
            agent_runs,
            width="stretch",
            hide_index=True
        )