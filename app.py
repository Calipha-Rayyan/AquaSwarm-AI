import streamlit as st

from workflows.aquaswarm_flow import AquaSwarmFlow
from ui.dashboard import render_dashboard


st.set_page_config(
    page_title="AquaSwarm AI",
    page_icon="💧",
    layout="wide",
)


if "workflow_state" not in st.session_state:
    st.session_state.workflow_state = None


st.sidebar.markdown("### AquaSwarm Control")


# =========================================================
# TANK SELECTION
# =========================================================

tank_options = [
    "TANK-001",
    "TANK-002",
    "TANK-003",
]

selected_tank = st.sidebar.selectbox(
    "Select Water Tank",
    tank_options,
    index=0,
)


# =========================================================
# RUN WATER OPERATION
# =========================================================

if st.sidebar.button(
    "▶ Run Water Operation",
    use_container_width=True,
):
    with st.spinner(
        f"AquaSwarm agents are analyzing {selected_tank}..."
    ):

        flow = AquaSwarmFlow()

        # Run the complete AquaSwarm workflow
        # for the selected tank.
        flow.kickoff(
            inputs={
                "selected_tank_id": selected_tank
            }
        )

        # CrewAI Flow stores the completed state
        # on the flow object.
        st.session_state.workflow_state = flow.state

    st.rerun()


# =========================================================
# DASHBOARD
# =========================================================

render_dashboard(
    st.session_state.workflow_state
)