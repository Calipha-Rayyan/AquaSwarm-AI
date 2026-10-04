import streamlit as st


def render_dashboard(workflow_state=None):
    # =========================================================
    # DATA
    # =========================================================

    water_data = getattr(
        workflow_state,
        "water_data",
        None,
    )

    demand_result = getattr(
        workflow_state,
        "demand_result",
        None,
    )

    anomaly_result = getattr(
        workflow_state,
        "anomaly_result",
        None,
    )

    supply_result = getattr(
        workflow_state,
        "supply_result",
        None,
    )

    allocation_result = getattr(
        workflow_state,
        "allocation_result",
        None,
    )

    approval_result = getattr(
        workflow_state,
        "manager_approval_result",
        None,
    )

    delivery_result = getattr(
        workflow_state,
        "delivery_result",
        None,
    )

    verification_result = getattr(
        workflow_state,
        "verification_result",
        None,
    )

    operation_status = getattr(
        workflow_state,
        "operation_status",
        "Pending",
    )

    # =========================================================
    # WATER DATA
    # =========================================================

    tank_id = getattr(
        water_data,
        "tank_id",
        "TANK-001",
    )

    current_level = getattr(
        water_data,
        "current_level",
        30,
    )

    capacity = getattr(
        water_data,
        "capacity",
        100,
    )

    daily_demand = getattr(
        water_data,
        "daily_demand",
        80,
    )

    inflow = getattr(
        water_data,
        "inflow",
        10,
    )

    fill_percentage = (
        (current_level / capacity) * 100
        if capacity > 0
        else 0
    )

    # =========================================================
    # DEMAND DATA
    # =========================================================

    shortage = getattr(
        demand_result,
        "shortage",
        max(daily_demand - current_level, 0),
    )

    priority = getattr(
        demand_result,
        "priority",
        (
            "HIGH"
            if shortage > 50 or fill_percentage < 20
            else "MEDIUM"
            if shortage > 20 or fill_percentage < 40
            else "LOW"
        ),
    )

    # =========================================================
    # OPERATION STATE
    # =========================================================

    no_replenishment = (
        operation_status
        == "No Replenishment Required"
    )

    replenishment_required = (
        operation_status
        == "Replenishment Required"
    )

    # =========================================================
    # SUPPLY / ALLOCATION
    # =========================================================

    supplier_id = getattr(
        allocation_result,
        "supplier_id",
        getattr(
            supply_result,
            "recommended_supplier",
            "—",
        ),
    )

    allocated_quantity = getattr(
        allocation_result,
        "allocated_quantity",
        shortage,
    )

    # =========================================================
    # APPROVAL
    # =========================================================

    approved = getattr(
        approval_result,
        "approved",
        None,
    )

    approval_status = (
        "Approved"
        if approved is True
        else "Rejected"
        if approved is False
        else "Pending"
    )

    # =========================================================
    # DELIVERY
    # =========================================================

    delivery_status = getattr(
        delivery_result,
        "status",
        "Not Started",
    )

    delivery_quantity = getattr(
        delivery_result,
        "quantity",
        allocated_quantity,
    )

    estimated_arrival = getattr(
        delivery_result,
        "estimated_arrival",
        "—",
    )

    # =========================================================
    # VERIFICATION
    # =========================================================

    verified = getattr(
        verification_result,
        "verified",
        None,
    )

    verification_status = (
        "Verified"
        if verified is True
        else "Pending"
        if verified is False
        else "Not Started"
    )

    # =========================================================
    # WORKFLOW STATUS
    # =========================================================

    demand_done = demand_result is not None

    anomaly_done = (
        anomaly_result is not None
    )

    supply_done = (
        supply_result is not None
    )

    allocation_done = (
        allocation_result is not None
    )

    approval_done = (
        approval_result is not None
    )

    delivery_done = (
        delivery_result is not None
    )

    verification_done = (
        verification_result is not None
    )

    # =========================================================
    # GLOBAL PAGE + COMPONENT STYLES
    # =========================================================

    st.html(
        """
        <style>
        .main {
            background: #0b0f14;
        }

        .block-container {
            max-width: 1450px;
            padding-top: 3.5rem;
            padding-bottom: 3rem;
        }

        .aq-header {
            width: 100%;
            display: flex;
            justify-content: space-between;
            align-items: center;
            min-height: 76px;
            margin-bottom: 28px;
        }

        .aq-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 30px;
            font-weight: 700;
            letter-spacing: -0.5px;
            line-height: 1.3;
            color: #f5f7fa;
        }

        .aq-logo {
            font-size: 34px;
            line-height: 1;
        }

        .aq-subtitle {
            margin-top: 8px;
            color: #8b949e;
            font-size: 14px;
            line-height: 1.4;
        }

        .aq-status {
            display: flex;
            align-items: center;
            gap: 9px;
            color: #8b949e;
            font-size: 13px;
            font-weight: 500;
            white-space: nowrap;
        }

        .aq-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #2ecc71;
            box-shadow: 0 0 12px rgba(46, 204, 113, 0.55);
            flex-shrink: 0;
        }

        .aq-divider {
            width: 100%;
            height: 1px;
            background: rgba(255, 255, 255, 0.08);
            margin-bottom: 30px;
        }

        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            width: 100%;
            margin-bottom: 30px;
        }

        .kpi-card {
            background: #11161d;
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 14px;
            padding: 22px;
            min-height: 142px;
            box-sizing: border-box;
            transition: border-color 0.2s ease,
                        transform 0.2s ease;
        }

        .kpi-card:hover {
            border-color: rgba(255, 255, 255, 0.14);
            transform: translateY(-2px);
        }

        .kpi-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 17px;
        }

        .kpi-label {
            color: #8b949e;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.8px;
            text-transform: uppercase;
        }

        .kpi-icon {
            font-size: 18px;
            opacity: 0.9;
        }

        .kpi-value {
            color: #f5f7fa;
            font-size: 29px;
            font-weight: 700;
            line-height: 1;
            letter-spacing: -0.5px;
        }

        .kpi-unit {
            color: #8b949e;
            font-size: 13px;
            font-weight: 500;
            margin-left: 5px;
        }

        .kpi-meta {
            color: #6e7781;
            font-size: 12px;
            margin-top: 12px;
        }

        .priority-badge {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            color: #ffb84d;
            font-size: 29px;
            font-weight: 700;
            line-height: 1;
        }

        .priority-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #ffb84d;
            box-shadow: 0 0 10px rgba(255, 184, 77, 0.45);
        }

        .section-heading {
            color: #f5f7fa;
            font-size: 17px;
            font-weight: 650;
            letter-spacing: -0.2px;
            margin-bottom: 14px;
        }

        .section-caption {
            color: #6e7781;
            font-size: 12px;
            margin-top: -7px;
            margin-bottom: 16px;
        }

        .intel-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            width: 100%;
            margin-bottom: 34px;
        }

        .intel-card {
            background: #11161d;
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 14px;
            padding: 24px;
            min-height: 245px;
            box-sizing: border-box;
        }

        .intel-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 24px;
        }

        .intel-title {
            color: #f5f7fa;
            font-size: 15px;
            font-weight: 650;
        }

        .intel-subtitle {
            color: #6e7781;
            font-size: 11px;
            margin-top: 5px;
        }

        .tank-id {
            color: #8b949e;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.7px;
            padding: 6px 9px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 7px;
        }

        .tank-level-row {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 10px;
        }

        .tank-current {
            color: #f5f7fa;
            font-size: 30px;
            font-weight: 700;
        }

        .tank-capacity {
            color: #6e7781;
            font-size: 13px;
        }

        .tank-bar {
            width: 100%;
            height: 14px;
            background: #1b222b;
            border-radius: 20px;
            overflow: hidden;
            margin-bottom: 10px;
        }

        .tank-fill {
            height: 100%;
            border-radius: 20px;
            background: linear-gradient(
                90deg,
                #2878ff,
                #52b7ff
            );
            box-shadow: 0 0 14px rgba(82, 183, 255, 0.22);
        }

        .tank-percent {
            display: flex;
            justify-content: space-between;
            color: #6e7781;
            font-size: 11px;
        }

        .tank-status {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 25px;
            color: #ffb84d;
            font-size: 12px;
            font-weight: 600;
        }

        .tank-status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #ffb84d;
        }

        .success-status {
            color: #2ecc71;
        }

        .success-status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #2ecc71;
        }

        .flow-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 13px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }

        .flow-row:last-child {
            border-bottom: none;
        }

        .flow-label {
            color: #8b949e;
            font-size: 13px;
        }

        .flow-value {
            color: #f5f7fa;
            font-size: 15px;
            font-weight: 650;
        }

        .flow-value.warning {
            color: #ffb84d;
        }

        .flow-unit {
            color: #6e7781;
            font-size: 11px;
            font-weight: 400;
            margin-left: 4px;
        }

        .workflow-card {
            background: #11161d;
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 14px;
            padding: 26px 24px 24px 24px;
            margin-bottom: 30px;
        }

        .workflow-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 28px;
        }

        .workflow-title {
            color: #f5f7fa;
            font-size: 15px;
            font-weight: 650;
        }

        .workflow-operation {
            color: #8b949e;
            font-size: 11px;
            padding: 6px 10px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 7px;
        }

        .workflow-track {
            display: flex;
            align-items: flex-start;
            width: 100%;
        }

        .workflow-step {
            flex: 1;
            min-width: 0;
            position: relative;
            text-align: center;
        }

        .workflow-step:not(:last-child)::after {
            content: "";
            position: absolute;
            top: 15px;
            left: calc(50% + 17px);
            right: calc(-50% + 17px);
            height: 2px;
            background: #29313b;
        }

        .workflow-step.completed:not(:last-child)::after {
            background: #2ecc71;
        }

        .workflow-node {
            position: relative;
            z-index: 2;
            width: 30px;
            height: 30px;
            margin: 0 auto 12px auto;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 700;
            box-sizing: border-box;
        }

        .workflow-node.completed {
            background: rgba(46, 204, 113, 0.14);
            border: 1px solid rgba(46, 204, 113, 0.55);
            color: #2ecc71;
        }

        .workflow-node.active {
            background: rgba(82, 183, 255, 0.14);
            border: 1px solid rgba(82, 183, 255, 0.7);
            color: #52b7ff;
            box-shadow: 0 0 14px rgba(82, 183, 255, 0.18);
        }

        .workflow-node.pending {
            background: #171d25;
            border: 1px solid #303944;
            color: #6e7781;
        }

        .workflow-node.skipped {
            background: #171d25;
            border: 1px solid #303944;
            color: #4f5863;
        }

        .workflow-name {
            color: #c9d1d9;
            font-size: 11px;
            font-weight: 600;
            white-space: nowrap;
        }

        .workflow-state {
            font-size: 10px;
            margin-top: 5px;
        }

        .workflow-state.completed {
            color: #2ecc71;
        }

        .workflow-state.active {
            color: #52b7ff;
        }

        .workflow-state.pending {
            color: #6e7781;
        }

        .workflow-state.skipped {
            color: #4f5863;
        }

        .no-operation-card {
            background: #11161d;
            border: 1px solid rgba(46, 204, 113, 0.18);
            border-radius: 14px;
            padding: 26px 28px;
            margin-bottom: 30px;
        }

        .no-operation-header {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .no-operation-icon {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(46, 204, 113, 0.12);
            border: 1px solid rgba(46, 204, 113, 0.35);
            color: #2ecc71;
            font-size: 16px;
            font-weight: 700;
        }

        .no-operation-title {
            color: #f5f7fa;
            font-size: 15px;
            font-weight: 650;
        }

        .no-operation-description {
            color: #8b949e;
            font-size: 12px;
            margin-top: 4px;
        }

        @media (max-width: 1000px) {
            .kpi-grid {
                grid-template-columns: repeat(2, 1fr);
            }

            .intel-grid {
                grid-template-columns: 1fr;
            }

            .workflow-track {
                overflow-x: auto;
                padding-bottom: 10px;
            }

            .workflow-step {
                min-width: 120px;
            }
        }

        @media (max-width: 600px) {
            .aq-header {
                align-items: flex-start;
                gap: 20px;
            }

            .kpi-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """
    )

    # =========================================================
    # HEADER
    # =========================================================

    st.html(
        """
        <div class="aq-header">
            <div>
                <div class="aq-brand">
                    <span class="aq-logo">💧</span>
                    <span>AquaSwarm AI</span>
                </div>

                <div class="aq-subtitle">
                    Intelligent Water Operations Control Center
                </div>
            </div>

            <div class="aq-status">
                <span class="aq-dot"></span>
                <span>System Operational</span>
            </div>
        </div>

        <div class="aq-divider"></div>
        """
    )

    # =========================================================
    # KPI CARDS
    # =========================================================

    st.html(
        f"""
        <div class="kpi-grid">

            <div class="kpi-card">
                <div class="kpi-top">
                    <span class="kpi-label">
                        Current Level
                    </span>

                    <span class="kpi-icon">
                        💧
                    </span>
                </div>

                <div class="kpi-value">
                    {current_level:g}
                    <span class="kpi-unit">
                        units
                    </span>
                </div>

                <div class="kpi-meta">
                    {fill_percentage:.0f}% of tank capacity
                </div>
            </div>


            <div class="kpi-card">
                <div class="kpi-top">
                    <span class="kpi-label">
                        Daily Demand
                    </span>

                    <span class="kpi-icon">
                        📈
                    </span>
                </div>

                <div class="kpi-value">
                    {daily_demand:g}
                    <span class="kpi-unit">
                        units
                    </span>
                </div>

                <div class="kpi-meta">
                    Required daily volume
                </div>
            </div>


            <div class="kpi-card">
                <div class="kpi-top">
                    <span class="kpi-label">
                        Inflow
                    </span>

                    <span class="kpi-icon">
                        ↗
                    </span>
                </div>

                <div class="kpi-value">
                    {inflow:g}
                    <span class="kpi-unit">
                        units
                    </span>
                </div>

                <div class="kpi-meta">
                    Current incoming supply
                </div>
            </div>


            <div class="kpi-card">
                <div class="kpi-top">
                    <span class="kpi-label">
                        Priority
                    </span>

                    <span class="kpi-icon">
                        ⚠
                    </span>
                </div>

                <div class="priority-badge">
                    <span class="priority-dot"></span>
                    {priority}
                </div>

                <div class="kpi-meta">
                    {
                        "No replenishment required"
                        if no_replenishment
                        else "Operational attention level"
                    }
                </div>
            </div>

        </div>
        """
    )

    # =========================================================
    # TANK INTELLIGENCE
    # =========================================================

    st.html(
        """
        <div class="section-heading">
            Tank Intelligence
        </div>

        <div class="section-caption">
            Live operational condition and water balance
        </div>
        """
    )

    if fill_percentage < 40:
        tank_status_text = (
            "Low storage level — replenishment required"
        )
    else:
        tank_status_text = (
            "Storage level within operating range"
        )

    tank_status_class = (
        "success-status"
        if no_replenishment
        else ""
    )

    tank_status_dot_class = (
        "success-status-dot"
        if no_replenishment
        else "tank-status-dot"
    )

    st.html(
        f"""
        <div class="intel-grid">

            <div class="intel-card">

                <div class="intel-header">

                    <div>
                        <div class="intel-title">
                            Tank Status
                        </div>

                        <div class="intel-subtitle">
                            Current storage level
                        </div>
                    </div>

                    <div class="tank-id">
                        {tank_id}
                    </div>

                </div>


                <div class="tank-level-row">

                    <div class="tank-current">
                        {current_level:g}

                        <span class="tank-capacity">
                            / {capacity:g} units
                        </span>
                    </div>

                    <div class="tank-capacity">
                        {fill_percentage:.0f}% filled
                    </div>

                </div>


                <div class="tank-bar">

                    <div
                        class="tank-fill"
                        style="
                            width:
                            {min(max(fill_percentage, 0), 100):.1f}%
                        "
                    ></div>

                </div>


                <div class="tank-percent">
                    <span>0 units</span>
                    <span>{capacity:g} units</span>
                </div>


                <div class="tank-status {tank_status_class}">

                    <span class="{tank_status_dot_class}"></span>

                    {
                        "Sufficient water available — no replenishment needed"
                        if no_replenishment
                        else tank_status_text
                    }

                </div>

            </div>


            <div class="intel-card">

                <div class="intel-header">

                    <div>
                        <div class="intel-title">
                            Demand &amp; Supply
                        </div>

                        <div class="intel-subtitle">
                            Current water balance
                        </div>
                    </div>

                </div>


                <div class="flow-row">

                    <span class="flow-label">
                        Daily demand
                    </span>

                    <span class="flow-value">
                        {daily_demand:g}

                        <span class="flow-unit">
                            units
                        </span>
                    </span>

                </div>


                <div class="flow-row">

                    <span class="flow-label">
                        Current inflow
                    </span>

                    <span class="flow-value">
                        {inflow:g}

                        <span class="flow-unit">
                            units
                        </span>
                    </span>

                </div>


                <div class="flow-row">

                    <span class="flow-label">
                        Calculated shortage
                    </span>

                    <span
                        class="flow-value
                        {
                            ""
                            if no_replenishment
                            else "warning"
                        }"
                    >
                        {shortage:g}

                        <span class="flow-unit">
                            units
                        </span>
                    </span>

                </div>


                <div class="flow-row">

                    <span class="flow-label">
                        Operational priority
                    </span>

                    <span class="flow-value">
                        {priority}
                    </span>

                </div>

            </div>

        </div>
        """
    )

    # =========================================================
    # NO REPLENISHMENT RESULT
    # =========================================================

    if no_replenishment:

        st.html(
            f"""
            <div class="no-operation-card">

                <div class="no-operation-header">

                    <div class="no-operation-icon">
                        ✓
                    </div>

                    <div>
                        <div class="no-operation-title">
                            No Replenishment Required
                        </div>

                        <div class="no-operation-description">
                            {tank_id} has sufficient water available.
                            AquaSwarm has stopped procurement and delivery
                            because the calculated shortage is 0 units.
                        </div>
                    </div>

                </div>

            </div>
            """
        )

    # =========================================================
    # AI AGENT WORKFLOW
    # =========================================================

    st.html(
        """
        <div class="section-heading">
            AI Agent Workflow
        </div>

        <div class="section-caption">
            Autonomous decision pipeline for the current water operation
        </div>
        """
    )

    # =========================================================
    # WORKFLOW HELPERS
    # =========================================================

    def workflow_class(
        done,
        active=False,
        skipped=False,
    ):

        if skipped:
            return "skipped"

        if active:
            return "active"

        if done:
            return "completed"

        return "pending"


    def workflow_symbol(
        done,
        active=False,
        skipped=False,
        number="",
    ):

        if skipped:
            return "—"

        if active:
            return "→"

        if done:
            return "✓"

        return number

    # =========================================================
    # NORMAL WORKFLOW
    # =========================================================

    if not no_replenishment:

        demand_class = workflow_class(
            demand_done
        )

        anomaly_class = workflow_class(
            anomaly_done
        )

        supply_class = workflow_class(
            supply_done
        )

        allocation_class = workflow_class(
            allocation_done
        )

        approval_class = workflow_class(
            approval_done
        )

        delivery_active = (
            delivery_result is not None
            and str(delivery_status).lower()
            == "in transit"
        )

        delivery_class = workflow_class(
            delivery_done,
            active=delivery_active,
        )

        verification_active = (
            verification_result is not None
            and verified is not True
            and str(delivery_status).lower() == "delivered"
        )

        verification_class = workflow_class(
            verified is True,
            active=verification_active,
        )

        demand_state = (
            "Completed"
            if demand_done
            else "Pending"
        )

        anomaly_state = (
            "Completed"
            if anomaly_done
            else "Pending"
        )

        supply_state = (
            "Completed"
            if supply_done
            else "Pending"
        )

        allocation_state = (
            "Completed"
            if allocation_done
            else "Pending"
        )

        approval_state = approval_status

        delivery_state = (
            str(delivery_status)
            if delivery_done
            else "Pending"
        )

        verification_state = (
            "Verified"
            if verified is True
            else "Waiting for Delivery"
            if str(delivery_status).lower() == "in transit"
            else verification_status
        )

        st.html(
            f"""
            <div class="workflow-card">

                <div class="workflow-header">

                    <div class="workflow-title">
                        AquaSwarm Decision Pipeline
                    </div>

                    <div class="workflow-operation">
                        {tank_id} · {allocated_quantity:g} units
                    </div>

                </div>


                <div class="workflow-track">


                    <div class="workflow-step {demand_class}">

                        <div
                            class="workflow-node
                            {demand_class}"
                        >
                            {workflow_symbol(demand_done)}
                        </div>

                        <div class="workflow-name">
                            Demand
                        </div>

                        <div
                            class="workflow-state
                            {demand_class}"
                        >
                            {demand_state}
                        </div>

                    </div>


                    <div class="workflow-step {anomaly_class}">

                        <div
                            class="workflow-node
                            {anomaly_class}"
                        >
                            {workflow_symbol(anomaly_done)}
                        </div>

                        <div class="workflow-name">
                            Anomaly
                        </div>

                        <div
                            class="workflow-state
                            {anomaly_class}"
                        >
                            {anomaly_state}
                        </div>

                    </div>


                    <div class="workflow-step {supply_class}">

                        <div
                            class="workflow-node
                            {supply_class}"
                        >
                            {workflow_symbol(supply_done)}
                        </div>

                        <div class="workflow-name">
                            Supply
                        </div>

                        <div
                            class="workflow-state
                            {supply_class}"
                        >
                            {supply_state}
                        </div>

                    </div>


                    <div class="workflow-step {allocation_class}">

                        <div
                            class="workflow-node
                            {allocation_class}"
                        >
                            {workflow_symbol(allocation_done)}
                        </div>

                        <div class="workflow-name">
                            Allocation
                        </div>

                        <div
                            class="workflow-state
                            {allocation_class}"
                        >
                            {allocation_state}
                        </div>

                    </div>


                    <div class="workflow-step {approval_class}">

                        <div
                            class="workflow-node
                            {approval_class}"
                        >
                            {workflow_symbol(approval_done)}
                        </div>

                        <div class="workflow-name">
                            Approval
                        </div>

                        <div
                            class="workflow-state
                            {approval_class}"
                        >
                            {approval_state}
                        </div>

                    </div>


                    <div class="workflow-step {delivery_class}">

                        <div
                            class="workflow-node
                            {delivery_class}"
                        >
                            {
                                workflow_symbol(
                                    delivery_done,
                                    active=delivery_active
                                )
                            }
                        </div>

                        <div class="workflow-name">
                            Delivery
                        </div>

                        <div
                            class="workflow-state
                            {delivery_class}"
                        >
                            {delivery_state}
                        </div>

                    </div>


                    <div class="workflow-step {verification_class}">

                        <div
                            class="workflow-node
                            {verification_class}"
                        >
                            {
                                workflow_symbol(
                                    verified is True,
                                    active=verification_active,
                                    number="7"
                                )
                            }
                        </div>

                        <div class="workflow-name">
                            Verification
                        </div>

                        <div
                            class="workflow-state
                            {verification_class}"
                        >
                            {verification_state}
                        </div>

                    </div>


                </div>

            </div>
            """
        )

    # =========================================================
    # NO-REPLENISHMENT WORKFLOW
    # =========================================================

    else:

        st.html(
            f"""
            <div class="workflow-card">

                <div class="workflow-header">

                    <div class="workflow-title">
                        AquaSwarm Decision Pipeline
                    </div>

                    <div class="workflow-operation">
                        {tank_id} · No Procurement
                    </div>

                </div>


                <div class="workflow-track">


                    <div class="workflow-step completed">

                        <div class="workflow-node completed">
                            ✓
                        </div>

                        <div class="workflow-name">
                            Demand
                        </div>

                        <div class="workflow-state completed">
                            Completed
                        </div>

                    </div>


                    <div class="workflow-step skipped">

                        <div class="workflow-node skipped">
                            —
                        </div>

                        <div class="workflow-name">
                            Anomaly
                        </div>

                        <div class="workflow-state skipped">
                            Not Required
                        </div>

                    </div>


                    <div class="workflow-step skipped">

                        <div class="workflow-node skipped">
                            —
                        </div>

                        <div class="workflow-name">
                            Supply
                        </div>

                        <div class="workflow-state skipped">
                            Not Required
                        </div>

                    </div>


                    <div class="workflow-step skipped">

                        <div class="workflow-node skipped">
                            —
                        </div>

                        <div class="workflow-name">
                            Allocation
                        </div>

                        <div class="workflow-state skipped">
                            Not Required
                        </div>

                    </div>


                    <div class="workflow-step skipped">

                        <div class="workflow-node skipped">
                            —
                        </div>

                        <div class="workflow-name">
                            Approval
                        </div>

                        <div class="workflow-state skipped">
                            Not Required
                        </div>

                    </div>


                    <div class="workflow-step skipped">

                        <div class="workflow-node skipped">
                            —
                        </div>

                        <div class="workflow-name">
                            Delivery
                        </div>

                        <div class="workflow-state skipped">
                            Not Required
                        </div>

                    </div>


                    <div class="workflow-step skipped">

                        <div class="workflow-node skipped">
                            —
                        </div>

                        <div class="workflow-name">
                            Verification
                        </div>

                        <div class="workflow-state skipped">
                            Not Required
                        </div>

                    </div>


                </div>

            </div>
            """
        )

    # =========================================================
    # CURRENT OPERATION
    # =========================================================

    if (
        delivery_result is not None
        and not no_replenishment
    ):

        st.html(
            """
            <div class="section-heading">
                Current Operation
            </div>

            <div class="section-caption">
                Active water movement and fulfillment status
            </div>
            """
        )

        st.html(
            f"""
            <div class="intel-grid">


                <div class="intel-card">

                    <div class="intel-header">

                        <div>
                            <div class="intel-title">
                                Delivery
                            </div>

                            <div class="intel-subtitle">
                                Approved water movement
                            </div>
                        </div>

                        <div class="tank-id">
                            {supplier_id}
                        </div>

                    </div>


                    <div class="flow-row">

                        <span class="flow-label">
                            Quantity
                        </span>

                        <span class="flow-value">
                            {delivery_quantity:g}

                            <span class="flow-unit">
                                units
                            </span>
                        </span>

                    </div>


                    <div class="flow-row">

                        <span class="flow-label">
                            Status
                        </span>

                        <span class="flow-value">
                            {delivery_status}
                        </span>

                    </div>


                    <div class="flow-row">

                        <span class="flow-label">
                            Estimated arrival
                        </span>

                        <span class="flow-value">
                            {estimated_arrival}
                        </span>

                    </div>

                </div>


                <div class="intel-card">

                    <div class="intel-header">

                        <div>
                            <div class="intel-title">
                                Verification
                            </div>

                            <div class="intel-subtitle">
                                Delivery confirmation
                            </div>
                        </div>

                    </div>


                    <div class="flow-row">

                        <span class="flow-label">
                            Verification status
                        </span>

                        <span class="flow-value">
                            {verification_status}
                        </span>

                    </div>


                    <div class="flow-row">

                        <span class="flow-label">
                            Approved quantity
                        </span>

                        <span class="flow-value">
                            {allocated_quantity:g}

                            <span class="flow-unit">
                                units
                            </span>
                        </span>

                    </div>


                    <div class="flow-row">

                        <span class="flow-label">
                            Supplier
                        </span>

                        <span class="flow-value">
                            {supplier_id}
                        </span>

                    </div>

                </div>

            </div>
            """
        )