import streamlit as st



from datetime import datetime, timezone, timedelta







DASHBOARD_CSS = """



<style>



:root{



  --cyan:#43c8ff; --blue:#416cff; --violet:#8b7bff; --green:#4ade80;



  --amber:#ffb84d; --red:#ff6b6b; --text:#e9f2fa; --muted:#8aa0b4; --dim:#5f778d;



  --line:rgba(120,180,225,.13); --panel:linear-gradient(145deg,rgba(17,32,50,.88),rgba(8,19,33,.94));



}







/* ---------- canvas ---------- */



.stApp{



  background:



    radial-gradient(circle at 6% 0%,rgba(0,180,255,.11),transparent 34%),



    radial-gradient(circle at 96% 100%,rgba(98,88,255,.11),transparent 34%),



    linear-gradient(135deg,#030911 0%,#061421 50%,#050a14 100%);



}



.stApp::before{



  content:""; position:fixed; inset:0; pointer-events:none; z-index:0;



  background-image:linear-gradient(rgba(90,170,230,.04) 1px,transparent 1px),



                   linear-gradient(90deg,rgba(90,170,230,.04) 1px,transparent 1px);



  background-size:56px 56px;



  -webkit-mask-image:radial-gradient(ellipse at 50% 30%,#000 15%,transparent 80%);



          mask-image:radial-gradient(ellipse at 50% 30%,#000 15%,transparent 80%);



}



[data-testid="stHeader"]{background:transparent;}



[data-testid="stDecoration"],footer{display:none !important;}



.block-container{max-width:1450px; padding-top:3rem; padding-bottom:3rem; position:relative; z-index:1;}







@keyframes rise{from{opacity:0;transform:translateY(14px);}to{opacity:1;transform:none;}}



@keyframes ping{from{transform:scale(1);opacity:.7;}to{transform:scale(3.2);opacity:0;}}



@keyframes blink{50%{opacity:.35;}}



@keyframes fillIn{from{width:0;}}



@keyframes sheen{from{transform:translateX(-100%);}to{transform:translateX(250%);}}



@keyframes flowline{to{background-position:32px 0;}}



@keyframes nodePulse{0%,100%{box-shadow:0 0 0 0 rgba(67,200,255,.45),0 0 16px rgba(67,200,255,.25);}



                    50%{box-shadow:0 0 0 9px rgba(67,200,255,0),0 0 22px rgba(67,200,255,.4);}}







/* ---------- header ---------- */



.aq-header{display:flex; justify-content:space-between; align-items:center; min-height:70px;



  margin-bottom:22px; animation:rise .5s ease-out both; gap:16px; flex-wrap:wrap;}



.aq-brand{display:flex; align-items:center; gap:12px; font-size:30px; font-weight:800;



  letter-spacing:-1px; color:#fff;}



.aq-drop{width:18px; height:18px; flex-shrink:0; background:linear-gradient(135deg,#7ee7ff,#2d7bff);



  border-radius:0 50% 50% 50%; transform:rotate(45deg); box-shadow:0 0 18px rgba(67,200,255,.75);}



.aq-brand span.t{background:linear-gradient(100deg,#fff,#8fdcff); -webkit-background-clip:text;



  background-clip:text; color:transparent;}



.aq-subtitle{margin-top:8px; color:var(--muted); font-size:13px; letter-spacing:.3px;}



.aq-right{display:flex; gap:10px; align-items:center; flex-wrap:wrap;}



.aq-chip{color:var(--muted); font-size:11px; font-weight:600; letter-spacing:1.2px; text-transform:uppercase;



  padding:7px 12px; border:1px solid var(--line); border-radius:99px; background:rgba(10,22,38,.6);}



.aq-status{display:flex; align-items:center; gap:9px; color:#65e6a3; font-size:11px; font-weight:650;



  letter-spacing:1.3px; padding:7px 13px; border-radius:99px; text-transform:uppercase;



  border:1px solid rgba(101,230,163,.25); background:rgba(101,230,163,.06); white-space:nowrap;}



.aq-dot{width:8px; height:8px; border-radius:50%; background:var(--green); position:relative; flex-shrink:0;}



.aq-dot::after{content:""; position:absolute; inset:0; border-radius:50%; background:var(--green);



  animation:ping 1.8s ease-out infinite;}



.aq-divider{height:1px; background:linear-gradient(90deg,rgba(67,200,255,.35),var(--line) 30%,transparent);



  margin-bottom:26px;}







.aq-await{display:flex; align-items:center; gap:12px; padding:14px 18px; margin-bottom:26px;



  border:1px solid rgba(67,200,255,.22); border-radius:12px; background:rgba(67,200,255,.05);



  color:#9fdcf7; font-size:13px; animation:rise .6s .1s ease-out both;}



.aq-await i{width:7px; height:7px; border-radius:50%; background:var(--cyan);



  box-shadow:0 0 10px var(--cyan); animation:blink 1.6s ease-in-out infinite;}







/* ---------- KPI ---------- */



.kpi-grid{display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:30px;}



.kpi-card{position:relative; overflow:hidden; background:var(--panel); border:1px solid var(--line);



  border-radius:16px; padding:22px; min-height:142px; box-sizing:border-box;



  box-shadow:0 14px 36px rgba(0,0,0,.32); animation:rise .6s ease-out both;



  transition:border-color .2s ease,transform .2s ease,box-shadow .2s ease;}



.kpi-card:nth-child(2){animation-delay:.07s;} .kpi-card:nth-child(3){animation-delay:.14s;} .kpi-card:nth-child(4){animation-delay:.21s;}



.kpi-card::before{content:""; position:absolute; top:0; left:0; right:0; height:2px;



  background:linear-gradient(90deg,var(--cyan),var(--blue),transparent);}



.kpi-card:hover{border-color:rgba(67,200,255,.4); transform:translateY(-3px);



  box-shadow:0 20px 44px rgba(0,0,0,.42),0 0 28px rgba(67,200,255,.09);}



.kpi-top{display:flex; justify-content:space-between; align-items:center; margin-bottom:17px;}



.kpi-label{color:var(--muted); font-size:11px; font-weight:700; letter-spacing:1.4px; text-transform:uppercase;}



.kpi-icon{font-size:17px; opacity:.85;}



.kpi-value{color:#fff; font-size:31px; font-weight:750; line-height:1; letter-spacing:-.8px;}



.kpi-unit{color:var(--dim); font-size:13px; font-weight:500; margin-left:5px; letter-spacing:0;}



.kpi-meta{color:var(--dim); font-size:12px; margin-top:12px;}



.priority-badge{display:inline-flex; align-items:center; gap:9px; font-size:31px; font-weight:750; line-height:1;}



.priority-dot{width:9px; height:9px; border-radius:50%; background:currentColor;



  box-shadow:0 0 12px currentColor; animation:blink 1.8s ease-in-out infinite;}



.p-high{color:var(--red);} .p-med{color:var(--amber);} .p-low{color:var(--green);}







/* ---------- sections ---------- */



.section-heading{display:flex; align-items:center; gap:10px; color:#fff; font-size:17px; font-weight:700;



  letter-spacing:-.3px; margin-bottom:14px;}



.section-heading::before{content:""; width:3px; height:16px; border-radius:2px;



  background:linear-gradient(180deg,var(--cyan),var(--violet));}



.section-caption{color:var(--dim); font-size:12px; margin-top:-7px; margin-bottom:16px; padding-left:13px;}







.intel-grid{display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:34px;}



.intel-card{background:var(--panel); border:1px solid var(--line); border-radius:16px; padding:24px;



  min-height:245px; box-sizing:border-box; box-shadow:0 14px 36px rgba(0,0,0,.3);



  animation:rise .65s .1s ease-out both; transition:border-color .2s ease,box-shadow .2s ease;}



.intel-card:hover{border-color:rgba(67,200,255,.3); box-shadow:0 20px 44px rgba(0,0,0,.4);}



.intel-header{display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:24px;}



.intel-title{color:#fff; font-size:15px; font-weight:700;}



.intel-subtitle{color:var(--dim); font-size:11px; margin-top:5px;}



.tank-id{color:#9fdcf7; font-size:11px; font-weight:700; letter-spacing:1px; padding:6px 10px;



  border:1px solid rgba(67,200,255,.25); border-radius:8px; background:rgba(67,200,255,.06);}







.tank-level-row{display:flex; justify-content:space-between; align-items:baseline; margin-bottom:12px;}



.tank-current{color:#fff; font-size:32px; font-weight:750; letter-spacing:-.8px;}



.tank-capacity{color:var(--dim); font-size:13px; font-weight:500; letter-spacing:0;}



.tank-bar{position:relative; width:100%; height:16px; background:#0c1724; border:1px solid var(--line);



  border-radius:20px; overflow:hidden; margin-bottom:10px;}



.tank-fill{position:relative; height:100%; border-radius:20px; overflow:hidden;



  background:linear-gradient(90deg,#2878ff,#52d3ff); box-shadow:0 0 18px rgba(82,211,255,.35);



  animation:fillIn 1.3s cubic-bezier(.2,.8,.2,1) both;}



.tank-fill::after{content:""; position:absolute; top:0; bottom:0; width:40%;



  background:linear-gradient(90deg,transparent,rgba(255,255,255,.35),transparent);



  animation:sheen 3.2s ease-in-out infinite;}



.tank-fill.low{background:linear-gradient(90deg,#e08a1e,#ffb84d); box-shadow:0 0 18px rgba(255,184,77,.3);}



.tank-percent{display:flex; justify-content:space-between; color:var(--dim); font-size:11px;}



.tank-status{display:flex; align-items:center; gap:8px; margin-top:25px; color:var(--amber); font-size:12px; font-weight:600;}



.tank-status-dot{width:7px; height:7px; border-radius:50%; background:var(--amber); box-shadow:0 0 10px var(--amber);}



.success-status{color:var(--green);}



.success-status-dot{width:7px; height:7px; border-radius:50%; background:var(--green); box-shadow:0 0 10px var(--green);}







.flow-row{display:flex; justify-content:space-between; align-items:center; padding:13px 0;



  border-bottom:1px solid var(--line);}



.flow-row:last-child{border-bottom:none;}



.flow-label{color:var(--muted); font-size:13px;}



.flow-value{color:#fff; font-size:15px; font-weight:650;}



.flow-value.warning{color:var(--amber);}



.flow-unit{color:var(--dim); font-size:11px; font-weight:400; margin-left:4px;}







/* ---------- pipeline ---------- */



.workflow-card{position:relative; overflow:hidden; background:var(--panel); border:1px solid var(--line);



  border-radius:16px; padding:26px 24px 24px; margin-bottom:30px; box-shadow:0 14px 36px rgba(0,0,0,.3);



  animation:rise .7s .15s ease-out both;}



.workflow-card::before{content:""; position:absolute; top:0; left:-50%; width:40%; height:1px;



  background:linear-gradient(90deg,transparent,var(--cyan),transparent); animation:sheen 6s ease-in-out infinite;}



.workflow-header{display:flex; justify-content:space-between; align-items:center; margin-bottom:30px; gap:12px; flex-wrap:wrap;}



.workflow-title{color:#fff; font-size:15px; font-weight:700;}



.workflow-operation{color:#9fdcf7; font-size:11px; font-weight:600; letter-spacing:.6px; padding:6px 10px;



  border:1px solid rgba(67,200,255,.22); border-radius:8px; background:rgba(67,200,255,.05);}



.workflow-track{display:flex; align-items:flex-start; width:100%;}



.workflow-step{flex:1; min-width:0; position:relative; text-align:center;}



.workflow-step:not(:last-child)::after{content:""; position:absolute; top:20px; left:calc(50% + 24px);



  right:calc(-50% + 24px); height:2px; background:#1d2a39;}



.workflow-step.completed:not(:last-child)::after{



  background:repeating-linear-gradient(90deg,#4ade80 0 8px,rgba(74,222,128,.3) 8px 16px);



  background-size:32px 100%; animation:flowline 1s linear infinite;}



.workflow-node{position:relative; z-index:2; width:42px; height:42px; margin:0 auto 12px; border-radius:50%;



  display:flex; align-items:center; justify-content:center; font-size:14px; font-weight:700; box-sizing:border-box;



  background:#08182a; transition:transform .2s ease;}



.workflow-step:hover .workflow-node{transform:scale(1.08);}



.workflow-node.completed{border:1.5px solid rgba(74,222,128,.7); color:var(--green); box-shadow:0 0 16px rgba(74,222,128,.22);}



.workflow-node.active{border:1.5px solid var(--cyan); color:var(--cyan); animation:nodePulse 2s ease-in-out infinite;}



.workflow-node.pending{border:1.5px solid #2a3a4c; color:var(--dim);}



.workflow-node.skipped{border:1.5px dashed #26323f; color:#44505d;}



.workflow-name{color:#d4e4f1; font-size:11px; font-weight:700; letter-spacing:1.2px; text-transform:uppercase; white-space:nowrap;}



.workflow-step.human .workflow-name::after{content:"HUMAN"; display:block; margin:5px auto 0; width:max-content;



  font-size:8px; letter-spacing:1.4px; color:#a89cff; padding:2px 6px; border:1px solid rgba(139,123,255,.35); border-radius:99px;}



.workflow-state{font-size:10px; margin-top:6px; letter-spacing:.3px;}



.workflow-state.completed{color:var(--green);} .workflow-state.active{color:var(--cyan);}



.workflow-state.pending{color:var(--dim);} .workflow-state.skipped{color:#44505d;}







.no-operation-card{background:var(--panel); border:1px solid rgba(74,222,128,.22); border-radius:16px;



  padding:26px 28px; margin-bottom:30px; box-shadow:0 0 40px rgba(74,222,128,.04); animation:rise .6s ease-out both;}



.no-operation-header{display:flex; align-items:center; gap:14px;}



.no-operation-icon{width:38px; height:38px; flex-shrink:0; border-radius:50%; display:flex; align-items:center;



  justify-content:center; background:rgba(74,222,128,.1); border:1px solid rgba(74,222,128,.4);



  color:var(--green); font-size:16px; font-weight:700; box-shadow:0 0 18px rgba(74,222,128,.2);}



.no-operation-title{color:#fff; font-size:15px; font-weight:700;}



.no-operation-description{color:var(--muted); font-size:12px; margin-top:4px;}





/* ---------- manager approval ---------- */



.approval-card{

  position:relative;

  overflow:hidden;

  background:var(--panel);

  border:1px solid rgba(139,123,255,.34);

  border-radius:16px;

  padding:24px;

  margin-bottom:30px;

  box-shadow:0 14px 36px rgba(0,0,0,.3),0 0 30px rgba(139,123,255,.06);

  animation:rise .65s ease-out both;

}



.approval-card::before{

  content:"";

  position:absolute;

  top:0;

  left:0;

  right:0;

  height:2px;

  background:linear-gradient(90deg,var(--violet),var(--cyan),transparent);

}



.approval-header{

  display:flex;

  justify-content:space-between;

  align-items:flex-start;

  gap:16px;

  margin-bottom:20px;

}



.approval-title{

  color:#fff;

  font-size:15px;

  font-weight:700;

}



.approval-subtitle{

  color:var(--dim);

  font-size:11px;

  margin-top:5px;

}



.approval-badge{

  color:#a89cff;

  font-size:10px;

  font-weight:700;

  letter-spacing:1.2px;

  text-transform:uppercase;

  padding:6px 10px;

  border-radius:99px;

  border:1px solid rgba(139,123,255,.35);

  background:rgba(139,123,255,.08);

  white-space:nowrap;

}



.approval-alert{

  display:flex;

  align-items:center;

  gap:9px;

  color:#c8bdff;

  font-size:12px;

  padding:11px 13px;

  margin-bottom:18px;

  border-radius:10px;

  border:1px solid rgba(139,123,255,.18);

  background:rgba(139,123,255,.05);

}



.approval-alert-dot{

  width:7px;

  height:7px;

  flex-shrink:0;

  border-radius:50%;

  background:var(--violet);

  box-shadow:0 0 10px var(--violet);

  animation:blink 1.6s ease-in-out infinite;

}





/* ---------- responsive ---------- */



@media (max-width:1000px){



  .kpi-grid{grid-template-columns:repeat(2,1fr);} .intel-grid{grid-template-columns:1fr;}



  .workflow-track{overflow-x:auto; padding-bottom:10px;} .workflow-step{min-width:120px;}



}



@media (max-width:600px){



  .kpi-grid{grid-template-columns:1fr;} .aq-brand{font-size:24px;}



}



@media (prefers-reduced-motion:reduce){



  *,*::before,*::after{animation:none !important; transition:none !important;}



}



</style>



"""











def render_dashboard(workflow_state=None, approval_handler=None):



    # =========================================================



    # DATA



    # =========================================================







    water_data = getattr(workflow_state, "water_data", None)



    demand_result = getattr(workflow_state, "demand_result", None)



    anomaly_result = getattr(workflow_state, "anomaly_result", None)



    supply_result = getattr(workflow_state, "supply_result", None)



    allocation_result = getattr(workflow_state, "allocation_result", None)



    approval_result = getattr(workflow_state, "manager_approval_result", None)



    delivery_result = getattr(workflow_state, "delivery_result", None)



    verification_result = getattr(workflow_state, "verification_result", None)







    operation_status = getattr(



        workflow_state,



        "operation_status",



        "Pending",



    )







    # =========================================================



    # WATER DATA



    # =========================================================







    tank_id = getattr(water_data, "tank_id", "TANK-001")



    current_level = getattr(water_data, "current_level", 30)



    capacity = getattr(water_data, "capacity", 100)



    daily_demand = getattr(water_data, "daily_demand", 80)



    inflow = getattr(water_data, "inflow", 10)







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



        operation_status == "No Replenishment Required"



    )







    replenishment_required = (



        operation_status == "Replenishment Required"



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







    approved = getattr(approval_result, "approved", None)







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







    delivery_status = getattr(delivery_result, "status", "Not Started")







    delivery_quantity = getattr(



        delivery_result,



        "quantity",



        allocated_quantity,



    )







    estimated_arrival_raw = getattr(



    delivery_result,



    "estimated_arrival",



    "—",



    )







    if estimated_arrival_raw and estimated_arrival_raw != "—":



        try:



            arrival_dt = datetime.fromisoformat(



                str(estimated_arrival_raw).replace("Z", "+00:00")



            )







            # Display in Pakistan Standard Time (PKT, UTC+5)



            arrival_dt = arrival_dt.astimezone(



                timezone(timedelta(hours=5))



            )







            estimated_arrival = arrival_dt.strftime(



                "%d %b %Y • %I:%M %p PKT"



            )







        except (ValueError, TypeError):



            estimated_arrival = str(estimated_arrival_raw)



    else:



        estimated_arrival = "—"







    # =========================================================



    # VERIFICATION



    # =========================================================







    verified = getattr(verification_result, "verified", None)







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



    anomaly_done = anomaly_result is not None



    supply_done = supply_result is not None



    allocation_done = allocation_result is not None



    approval_done = approval_result is not None



    delivery_done = delivery_result is not None



    verification_done = verification_result is not None







    # =========================================================



    # UI-ONLY DERIVED VALUES



    # =========================================================







    priority_class = {



        "HIGH": "p-high",



        "MEDIUM": "p-med",



        "LOW": "p-low",



    }.get(str(priority).upper(), "p-med")







    tank_fill_class = (



        "low"



        if fill_percentage < 40 and not no_replenishment



        else ""



    )







    # =========================================================



    # GLOBAL PAGE + COMPONENT STYLES



    # =========================================================







    st.html(DASHBOARD_CSS)







    # =========================================================



    # HEADER



    # =========================================================







    st.html(



        f"""



        <div class="aq-header">



            <div>



                <div class="aq-brand">



                    <span class="aq-drop"></span>



                    <span class="t">AquaSwarm AI</span>



                </div>



                <div class="aq-subtitle">



                    Intelligent Water Operations Control Center



                </div>



            </div>







            <div class="aq-right">



                <span class="aq-chip">{operation_status}</span>



                <div class="aq-status">



                    <span class="aq-dot"></span>



                    <span>System Operational</span>



                </div>



            </div>



        </div>







        <div class="aq-divider"></div>



        """



    )







    if workflow_state is None:



        st.html(



            """



            <div class="aq-await">



                <i></i>



                Agents on standby — select <b>Run Water Operation</b>



                in the sidebar to start the pipeline.



            </div>



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



                    <span class="kpi-label">Current Level</span>



                    <span class="kpi-icon">💧</span>



                </div>



                <div class="kpi-value">



                    {current_level:g}



                    <span class="kpi-unit">units</span>



                </div>



                <div class="kpi-meta">



                    {fill_percentage:.0f}% of tank capacity



                </div>



            </div>







            <div class="kpi-card">



                <div class="kpi-top">



                    <span class="kpi-label">Daily Demand</span>



                    <span class="kpi-icon">📈</span>



                </div>



                <div class="kpi-value">



                    {daily_demand:g}



                    <span class="kpi-unit">units</span>



                </div>



                <div class="kpi-meta">Required daily volume</div>



            </div>







            <div class="kpi-card">



                <div class="kpi-top">



                    <span class="kpi-label">Inflow</span>



                    <span class="kpi-icon">↗</span>



                </div>



                <div class="kpi-value">



                    {inflow:g}



                    <span class="kpi-unit">units</span>



                </div>



                <div class="kpi-meta">Current incoming supply</div>



            </div>







            <div class="kpi-card">



                <div class="kpi-top">



                    <span class="kpi-label">Priority</span>



                    <span class="kpi-icon">⚠</span>



                </div>



                <div class="priority-badge {priority_class}">



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



        <div class="section-heading">Tank Intelligence</div>



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



                        <div class="intel-title">Tank Status</div>



                        <div class="intel-subtitle">Current storage level</div>



                    </div>



                    <div class="tank-id">{tank_id}</div>



                </div>







                <div class="tank-level-row">



                    <div class="tank-current">



                        {current_level:g}



                        <span class="tank-capacity">/ {capacity:g} units</span>



                    </div>



                    <div class="tank-capacity">



                        {fill_percentage:.0f}% filled



                    </div>



                </div>







                <div class="tank-bar">



                    <div



                        class="tank-fill {tank_fill_class}"



                        style="width: {min(max(fill_percentage, 0), 100):.1f}%"



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



                        <div class="intel-title">Demand &amp; Supply</div>



                        <div class="intel-subtitle">Current water balance</div>



                    </div>



                </div>







                <div class="flow-row">



                    <span class="flow-label">Daily demand</span>



                    <span class="flow-value">



                        {daily_demand:g}



                        <span class="flow-unit">units</span>



                    </span>



                </div>







                <div class="flow-row">



                    <span class="flow-label">Current inflow</span>



                    <span class="flow-value">



                        {inflow:g}



                        <span class="flow-unit">units</span>



                    </span>



                </div>







                <div class="flow-row">



                    <span class="flow-label">Calculated shortage</span>



                    <span class="flow-value {"" if no_replenishment else "warning"}">



                        {shortage:g}



                        <span class="flow-unit">units</span>



                    </span>



                </div>







                <div class="flow-row">



                    <span class="flow-label">Operational priority</span>



                    <span class="flow-value">{priority}</span>



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



                    <div class="no-operation-icon">✓</div>



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



        <div class="section-heading">AI Agent Workflow</div>



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







    def step_html(name, css_class, symbol, state, extra=""):



        return f"""



        <div class="workflow-step {css_class} {extra}">



            <div class="workflow-node {css_class}">{symbol}</div>



            <div class="workflow-name">{name}</div>



            <div class="workflow-state {css_class}">{state}</div>



        </div>



        """







    # =========================================================



    # NORMAL WORKFLOW



    # =========================================================







    if not no_replenishment:







        demand_class = workflow_class(demand_done)



        anomaly_class = workflow_class(anomaly_done)



        supply_class = workflow_class(supply_done)



        allocation_class = workflow_class(allocation_done)



        approval_class = workflow_class(approval_done)







        delivery_active = (



            delivery_result is not None



            and str(delivery_status).lower() == "in transit"



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







        demand_state = "Completed" if demand_done else "Pending"



        anomaly_state = "Completed" if anomaly_done else "Pending"



        supply_state = "Completed" if supply_done else "Pending"



        allocation_state = "Completed" if allocation_done else "Pending"







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







        steps = "".join(



            [



                step_html("Demand", demand_class,



                          workflow_symbol(demand_done, number="1"),



                          demand_state),



                step_html("Anomaly", anomaly_class,



                          workflow_symbol(anomaly_done, number="2"),



                          anomaly_state),



                step_html("Supply", supply_class,



                          workflow_symbol(supply_done, number="3"),



                          supply_state),



                step_html("Allocation", allocation_class,



                          workflow_symbol(allocation_done, number="4"),



                          allocation_state),



                step_html("Approval", approval_class,



                          workflow_symbol(approval_done, number="5"),



                          approval_state, extra="human"),



                step_html("Delivery", delivery_class,



                          workflow_symbol(delivery_done,



                                          active=delivery_active,



                                          number="6"),



                          delivery_state),



                step_html("Verification", verification_class,



                          workflow_symbol(verified is True,



                                          active=verification_active,



                                          number="7"),



                          verification_state),



            ]



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



                <div class="workflow-track">{steps}</div>



            </div>



            """



        )







    # =========================================================



    # NO-REPLENISHMENT WORKFLOW



    # =========================================================







    else:







        skipped_steps = "".join(



            step_html(name, "skipped", "—", "Not Required")



            for name in (



                "Anomaly",



                "Supply",



                "Allocation",



                "Approval",



                "Delivery",



                "Verification",



            )



        )







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



                    {step_html("Demand", "completed", "✓", "Completed")}



                    {skipped_steps}



                </div>



            </div>



            """



        )





        # =========================================================

    # MANAGER APPROVAL

    # =========================================================



    if (

        approval_handler is not None

        and approval_result is None

        and allocation_result is not None

        and operation_status == "Awaiting Manager Approval"

        and not no_replenishment

    ):



        st.html(

            f"""

            <div class="approval-card">



                <div class="approval-header">



                    <div>

                        <div class="approval-title">

                            Manager Approval Required

                        </div>



                        <div class="approval-subtitle">

                            Human authorization is required before delivery can begin

                        </div>

                    </div>



                    <div class="approval-badge">

                        Awaiting Decision

                    </div>



                </div>



                <div class="approval-alert">

                    <span class="approval-alert-dot"></span>



                    <span>

                        Review the AI allocation and authorize the proposed water movement.

                    </span>

                </div>



                <div class="intel-grid">



                    <div class="intel-card">



                        <div class="intel-header">



                            <div>

                                <div class="intel-title">

                                    Proposed Allocation

                                </div>



                                <div class="intel-subtitle">

                                    AI-generated recommendation

                                </div>

                            </div>



                            <div class="tank-id">

                                {tank_id}

                            </div>



                        </div>



                        <div class="flow-row">

                            <span class="flow-label">

                                Requested quantity

                            </span>



                            <span class="flow-value">

                                {getattr(allocation_result, 'allocated_quantity', shortage):g}

                                <span class="flow-unit">

                                    units

                                </span>

                            </span>

                        </div>



                        <div class="flow-row">

                            <span class="flow-label">

                                Recommended supplier

                            </span>



                            <span class="flow-value">

                                {supplier_id}

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





                    <div class="intel-card">



                        <div class="intel-header">



                            <div>

                                <div class="intel-title">

                                    Decision Control

                                </div>



                                <div class="intel-subtitle">

                                    Manager authorization

                                </div>

                            </div>



                        </div>



                        <div class="flow-row">

                            <span class="flow-label">

                                Current status

                            </span>



                            <span class="flow-value warning">

                                Awaiting Approval

                            </span>

                        </div>



                        <div class="flow-row">

                            <span class="flow-label">

                                Next step

                            </span>



                            <span class="flow-value">

                                Delivery after approval

                            </span>

                        </div>



                    </div>



                </div>



            </div>

            """

        )





        reason = st.text_area(

            "Manager decision note",

            key=f"manager_approval_reason_{tank_id}",

            placeholder="Add a short reason for the approval or rejection...",

            height=90,

        )





        approve_col, reject_col = st.columns(2)





        with approve_col:

            if st.button(
                "✓  APPROVE ALLOCATION",
                key=f"approve_allocation_{tank_id}",
                use_container_width=True,
                type="primary",
            ):
                success = approval_handler(
                    True,
                    reason.strip(),
                )

                if success:
                    st.rerun()





        with reject_col:

            if st.button(
                "✕  REJECT ALLOCATION",
                key=f"reject_allocation_{tank_id}",
                use_container_width=True,
                type="secondary",
            ):
                success = approval_handler(
                    False,
                    reason.strip(),
                )

                if success:
                    st.rerun()







    # =========================================================



    # CURRENT OPERATION



    # =========================================================







    if (



        delivery_result is not None



        and not no_replenishment



    ):







        st.html(



            """



            <div class="section-heading">Current Operation</div>



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



                            <div class="intel-title">Delivery</div>



                            <div class="intel-subtitle">



                                Approved water movement



                            </div>



                        </div>



                        <div class="tank-id">{supplier_id}</div>



                    </div>







                    <div class="flow-row">



                        <span class="flow-label">Quantity</span>



                        <span class="flow-value">



                            {delivery_quantity:g}



                            <span class="flow-unit">units</span>



                        </span>



                    </div>







                    <div class="flow-row">



                        <span class="flow-label">Status</span>



                        <span class="flow-value">{delivery_status}</span>



                    </div>







                    <div class="flow-row">



                        <span class="flow-label">Estimated arrival</span>



                        <span class="flow-value">{estimated_arrival}</span>



                    </div>



                </div>







                <div class="intel-card">



                    <div class="intel-header">



                        <div>



                            <div class="intel-title">Verification</div>



                            <div class="intel-subtitle">



                                Delivery confirmation



                            </div>



                        </div>



                    </div>







                    <div class="flow-row">



                        <span class="flow-label">Verification status</span>



                        <span class="flow-value">{verification_status}</span>



                    </div>







                    <div class="flow-row">



                        <span class="flow-label">Approved quantity</span>



                        <span class="flow-value">



                            {allocated_quantity:g}



                            <span class="flow-unit">units</span>



                        </span>



                    </div>







                    <div class="flow-row">



                        <span class="flow-label">Supplier</span>



                        <span class="flow-value">{supplier_id}</span>



                    </div>



                </div>







            </div>



            """



        )
