import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from workflows.aquaswarm_flow import AquaSwarmFlow, AquaSwarmState
from ui.dashboard import render_dashboard

def resume_flow_from_state(workflow_state):
    """Restore the saved workflow state into a new AquaSwarmFlow instance."""

    restored_state = AquaSwarmState.model_validate(
        workflow_state.model_dump()
    )

    return AquaSwarmFlow(
        initial_state=restored_state
    )

def handle_manager_decision(approved: bool, reason: str = ""):
    workflow_state = st.session_state.get("workflow_state")

    if workflow_state is None:
        st.error("No active water operation found.")
        return False

    decided_by = st.session_state.get(
        "current_user",
        "Manager"
    )

    try:
        flow = resume_flow_from_state(workflow_state)

        flow.manager_decision(
            approved=approved,
            decided_by=decided_by,
            reason=reason.strip(),
        )

        st.session_state.workflow_state = flow.state

        return True

    except Exception as exc:
        st.error(f"Unable to process manager decision: {exc}")
        st.exception(exc)
        return False

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AquaSwarm AI",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# HELPERS
# ============================================================

def html(markup: str):
    """Render HTML safely through st.markdown.

    Markdown treats lines indented by 4+ spaces as code blocks, which is what
    makes HTML show up as raw text. Stripping every line avoids that.
    """
    flat = "".join(line.strip() for line in markup.splitlines())
    st.markdown(flat, unsafe_allow_html=True)


# ============================================================
# LOGIN PAGE STYLE
# ============================================================

LOGIN_CSS = """
<style>
:root{
  --bg0:#030911; --bg1:#061421; --cyan:#43c8ff; --blue:#416cff;
  --violet:#8b7bff; --green:#4ade80; --text:#e6f1fa; --muted:#7f95a9;
  --line:rgba(120,180,225,.14);
}

/* ---------- canvas ---------- */
.stApp{
  background:
    radial-gradient(circle at 8% 40%, rgba(0,180,255,.12), transparent 32%),
    radial-gradient(circle at 94% 60%, rgba(98,88,255,.12), transparent 32%),
    linear-gradient(135deg,#030911 0%,#061421 50%,#050a14 100%);
}
/* subtle infrastructure grid */
.stApp::before{
  content:""; position:fixed; inset:0; pointer-events:none; z-index:0;
  background-image:
    linear-gradient(rgba(90,170,230,.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(90,170,230,.045) 1px, transparent 1px);
  background-size:56px 56px;
  -webkit-mask-image:radial-gradient(ellipse at 50% 45%, #000 20%, transparent 75%);
          mask-image:radial-gradient(ellipse at 50% 45%, #000 20%, transparent 75%);
}
/* drifting water glow */
.stApp::after{
  content:""; position:fixed; width:520px; height:520px; left:-140px; bottom:-180px;
  pointer-events:none; z-index:0; border-radius:50%;
  background:radial-gradient(circle, rgba(0,170,255,.16), transparent 65%);
  animation:drift 16s ease-in-out infinite alternate;
}
@keyframes drift{ to{ transform:translate(180px,-90px) scale(1.15);} }

[data-testid="stHeader"]{background:transparent;}
[data-testid="stToolbar"], [data-testid="stDecoration"], footer{display:none !important;}
.block-container{max-width:1240px; padding-top:1.4rem; padding-bottom:1rem; position:relative; z-index:1;}

/* ---------- top bar ---------- */
.topbar{display:flex; justify-content:space-between; align-items:center;
  padding-bottom:14px; border-bottom:1px solid var(--line); margin-bottom:6px;}
.brand{display:flex; align-items:center; gap:10px; color:#fff; font-size:13px;
  font-weight:750; letter-spacing:2.4px;}
.drop{width:14px; height:14px; background:linear-gradient(135deg,#7ee7ff,#2d7bff);
  border-radius:0 50% 50% 50%; transform:rotate(45deg); box-shadow:0 0 14px rgba(67,200,255,.7);}
.status{display:flex; align-items:center; gap:8px; color:#65e6a3; font-size:11px;
  font-weight:650; letter-spacing:1.4px; padding:6px 12px; border-radius:99px;
  border:1px solid rgba(101,230,163,.25); background:rgba(101,230,163,.06);}
.pulse{width:7px; height:7px; border-radius:50%; background:#65e6a3; position:relative;}
.pulse::after{content:""; position:absolute; inset:0; border-radius:50%; background:#65e6a3;
  animation:ping 1.8s ease-out infinite;}
@keyframes ping{ from{transform:scale(1); opacity:.7;} to{transform:scale(3.2); opacity:0;} }

/* ---------- hero ---------- */
.kicker{color:#52caff; font-size:11px; font-weight:700; letter-spacing:2.4px;
  margin:34px 0 12px; animation:rise .6s ease-out both;}
.title{color:#fff; font-size:50px; line-height:1.03; font-weight:800; letter-spacing:-2px;
  margin:0; animation:rise .7s .08s ease-out both;}
.title span{background:linear-gradient(100deg,#43c8ff,#6f7bff);
  -webkit-background-clip:text; background-clip:text; color:transparent;}
.sub{color:var(--muted); font-size:14px; margin:14px 0 4px; animation:rise .7s .16s ease-out both;}
.label{color:#5f778d; font-size:10px; font-weight:700; letter-spacing:2px; margin:18px 0 0;}
@keyframes rise{ from{opacity:0; transform:translateY(14px);} to{opacity:1; transform:none;} }

/* ---------- stats ---------- */
.stats{display:grid; grid-template-columns:repeat(3,1fr); gap:0; margin-top:6px;
  border-top:1px solid var(--line); border-bottom:1px solid var(--line);}
.stat{padding:16px 4px 14px; border-right:1px solid var(--line);}
.stat:last-child{border-right:none;}
.stat+.stat{padding-left:22px;}
.sv{color:#fff; font-size:27px; font-weight:750; line-height:1; letter-spacing:-.5px;}
.sl{color:#71879b; font-size:9px; font-weight:700; letter-spacing:1.4px; margin-top:8px;}
.ticker{display:flex; align-items:center; gap:10px; margin-top:16px; color:#52caff;
  font-size:11px; letter-spacing:1.2px; font-weight:600;}
.ticker i{width:6px; height:6px; border-radius:50%; background:#43c8ff;
  box-shadow:0 0 10px #43c8ff; animation:blink 1.6s ease-in-out infinite;}
@keyframes blink{ 50%{opacity:.25;} }

/* ---------- login form ---------- */
div[data-testid="stForm"]{
  margin-top:48px; padding:34px 36px 30px;
  background:linear-gradient(145deg, rgba(17,32,50,.92), rgba(8,19,33,.96));
  border:1px solid var(--line); border-radius:20px; backdrop-filter:blur(10px);
  box-shadow:0 30px 80px rgba(0,0,0,.45), 0 0 60px rgba(40,130,255,.06), inset 0 1px 0 rgba(255,255,255,.04);
  animation:rise .75s .1s ease-out both; position:relative; overflow:hidden;
}
div[data-testid="stForm"]::before{ /* slow scanning highlight */
  content:""; position:absolute; top:0; left:-60%; width:40%; height:1px;
  background:linear-gradient(90deg, transparent, #43c8ff, transparent);
  animation:scan 5s ease-in-out infinite;
}
@keyframes scan{ to{ left:120%; } }
div[data-testid="stForm"] h2{color:#fff !important; font-size:26px !important; font-weight:700 !important;
  letter-spacing:-.7px !important; margin-bottom:2px !important;}
div[data-testid="stForm"] p{color:#8197ab !important; font-size:12px !important;}
div[data-testid="stForm"] label p{color:#d6e4ef !important; font-weight:600 !important;}
div[data-testid="stForm"] input{min-height:44px !important; background:rgba(2,9,17,.8) !important;
  color:#fff !important; border-radius:10px !important;
  transition:border-color .2s ease, box-shadow .25s ease;}
div[data-testid="InputInstructions"] > span {
    visibility: hidden !important;
}
div[data-testid="stForm"] [data-baseweb="input"],
div[data-testid="stForm"] [data-baseweb="base-input"]{
  background:rgba(2,9,17,.8) !important; border-radius:10px !important;
  border:1px solid rgba(132,172,202,.16) !important; transition:all .25s ease;}
div[data-testid="stForm"] [data-baseweb="input"]:focus-within{
  border-color:rgba(67,199,255,.7) !important; box-shadow:0 0 0 3px rgba(67,199,255,.12), 0 0 18px rgba(67,199,255,.12) !important;}
div[data-testid="stFormSubmitButton"] button{
  height:48px; border:none; border-radius:10px; position:relative; overflow:hidden;
  background:linear-gradient(100deg,#079bff,#416cff 52%,#6258ff);
  box-shadow:0 10px 28px rgba(38,119,255,.25);
  transition:transform .18s ease, box-shadow .18s ease;}
div[data-testid="stFormSubmitButton"] button p{color:#fff !important; font-size:13px; font-weight:700; letter-spacing:.4px;}
div[data-testid="stFormSubmitButton"] button:hover{transform:translateY(-2px);
  box-shadow:0 16px 38px rgba(38,119,255,.42), 0 0 22px rgba(67,200,255,.25);}
div[data-testid="stFormSubmitButton"] button:active{transform:translateY(0) scale(.99);}
.secure{color:#5d7489; font-size:11px; text-align:center; margin-top:14px; letter-spacing:.3px;}
.formchip{display:inline-flex; align-items:center; gap:8px; color:#65e6a3; font-size:10px;
  font-weight:700; letter-spacing:1.5px; margin-bottom:10px;}

/* ---------- responsive ---------- */
@media (max-width:850px){
  .title{font-size:36px;}
  div[data-testid="stForm"]{margin-top:18px; padding:26px 22px;}
  .stat+.stat{padding-left:12px;} .sv{font-size:21px;}
}
@media (prefers-reduced-motion:reduce){
  *, *::before, *::after{animation:none !important; transition:none !important;}
}
</style>
"""


def apply_login_style():
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)


# ============================================================
# AGENT NETWORK VISUAL (rendered in an isolated iframe so the
# SVG animation always works and never shows up as raw code)
# ============================================================

AGENTS = [
    # name, x, y, accent
    ("Demand", 90, 80, "#43c8ff"),
    ("Anomaly", 270, 80, "#43c8ff"),
    ("Supply", 450, 80, "#43c8ff"),
    ("Allocation", 630, 80, "#43c8ff"),
    ("Approval", 630, 220, "#8b7bff"),
    ("Delivery", 450, 220, "#43c8ff"),
    ("Verification", 270, 220, "#4ade80"),
    ("Replanning", 90, 220, "#43c8ff"),
]


def build_network_svg() -> str:
    nodes = ""
    for i, (name, x, y, color) in enumerate(AGENTS):
        delay = i * 0.35
        tag = ""
        if name == "Approval":
            tag = (
                f'<text x="{x}" y="{y - 38}" class="tag">HUMAN IN THE LOOP</text>'
            )
        nodes += f"""
        <g transform="translate({x},{y})">
          <circle r="26" class="ring" style="stroke:{color};animation-delay:{delay}s"/>
          <circle r="26" class="node" style="stroke:{color}"/>
          <circle r="3" fill="{color}" class="core" style="animation-delay:{delay}s"/>
          <text y="-34" class="num">{i + 1:02d}</text>
          <text y="48" class="name">{name.upper()}</text>
        </g>{tag}"""

    return f"""
<!DOCTYPE html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;background:transparent;font-family:Inter,'Segoe UI',system-ui,sans-serif;overflow:hidden}}
svg{{width:100%;height:100%;display:block}}
.edge{{stroke:rgba(90,170,230,.16);stroke-width:2;fill:none}}
.flow{{stroke:#43c8ff;stroke-width:2;fill:none;stroke-dasharray:6 10;animation:dash 1.6s linear infinite;opacity:.75}}
.back{{stroke:#8b7bff;stroke-width:1.6;fill:none;stroke-dasharray:3 9;animation:dash 2.2s linear infinite reverse;opacity:.7}}
@keyframes dash{{to{{stroke-dashoffset:-32}}}}
.node{{fill:#08182a;stroke-width:1.6;filter:url(#glow)}}
.ring{{fill:none;stroke-width:1;transform-box:fill-box;transform-origin:center;animation:ring 3.2s ease-out infinite}}
@keyframes ring{{from{{transform:scale(1);opacity:.55}}to{{transform:scale(1.9);opacity:0}}}}
.core{{animation:core 2.8s ease-in-out infinite}}
@keyframes core{{50%{{opacity:.3}}}}
.name{{fill:#cfe2f1;font-size:10.5px;font-weight:700;letter-spacing:1.6px;text-anchor:middle}}
.num{{fill:#4f6a82;font-size:9px;font-weight:700;letter-spacing:1px;text-anchor:middle}}
.tag{{fill:#a89cff;font-size:8.5px;font-weight:700;letter-spacing:1.6px;text-anchor:middle}}
.loop{{fill:#6f86a0;font-size:8.5px;font-weight:700;letter-spacing:1.6px}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.packet{{display:none}}}}
</style></head><body>
<svg viewBox="0 0 720 300" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <path d="M90,80 H630 V220 H90" class="edge"/>
  <path d="M90,80 H630 V220 H90" class="flow"/>
  <path d="M90,220 V80" class="edge"/>
  <path d="M90,220 V80" class="back"/>
  <text x="102" y="154" class="loop">REPLAN LOOP</text>
  {nodes}
  <circle r="4" fill="#bff3ff" filter="url(#glow)" class="packet">
    <animateMotion dur="11s" repeatCount="indefinite" path="M90,80 H630 V220 H90 V80"/>
  </circle>
  <circle r="3.5" fill="#c9c2ff" filter="url(#glow)" class="packet">
    <animateMotion dur="11s" begin="-5.5s" repeatCount="indefinite" path="M90,80 H630 V220 H90 V80"/>
  </circle>
</svg></body></html>"""


# ============================================================
# LOGIN PAGE
# ============================================================

def render_login():

    apply_login_style()

    # --------------------------------------------------------
    # TOP BAR
    # --------------------------------------------------------

    html(
        """
        <div class="topbar">
          <div class="brand"><span class="drop"></span>AQUASWARM AI</div>
          <div class="status"><span class="pulse"></span>SYSTEM ONLINE</div>
        </div>
        """
    )

    # --------------------------------------------------------
    # MAIN LAYOUT
    # --------------------------------------------------------

    left, right = st.columns([1.3, 0.7], gap="large")

    # ========================================================
    # LEFT SIDE — IDENTITY + AGENT NETWORK
    # ========================================================

    with left:

        html(
            """
            <div class="kicker">AI WATER OPERATIONS</div>
            <h1 class="title">Autonomous intelligence<br>for <span>water.</span></h1>
            <div class="sub">Eight coordinated agents. One human in command.</div>
            <div class="label">LIVE AGENT NETWORK</div>
            """
        )

        components.html(build_network_svg(), height=290)

        html(
            """
            <div class="stats">
              <div class="stat"><div class="sv">09</div><div class="sl">AI AGENTS</div></div>
              <div class="stat"><div class="sv">24/7</div><div class="sl">UPTIME</div></div>
              <div class="stat"><div class="sv">HUMAN</div><div class="sl">FINAL CONTROL</div></div>
            </div>
            <div class="ticker"><i></i>AGENT SWARM ACTIVE · REPLANNING LOOP READY</div>
            """
        )

    # ========================================================
    # RIGHT SIDE — LOGIN
    # ========================================================

    with right:

        with st.form("login_form"):

            html(
                '<div class="formchip"><span class="pulse"></span>SECURE SESSION</div>'
            )

            st.markdown("## Welcome back")

            st.caption("Secure access to your operations center.")

            st.write("")

            email = st.text_input(
                "Email",
                placeholder="you@organization.com",
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
            )

            st.write("")

            login = st.form_submit_button(
                "Sign In  →",
                use_container_width=True,
                type="primary",
            )

            # ------------------------------------------------
            # TEMPORARY AUTHENTICATION (unchanged)
            # ------------------------------------------------

            if login:

                if not email or not password:

                    st.error("Please enter your email and password.")

                elif email.strip().lower() == "demo@aquaswarm.ai" and password == "AquaSwarm@123":

                    st.session_state.authenticated = True
                    st.session_state.current_user = email.strip().lower()
                    st.rerun()

                else:

                    st.error("Invalid email or password.")

        html(
            '<p class="secure">🔒 Authorized personnel only · Secure operations access</p>'
        )


# ============================================================
# SIDEBAR STYLE (authenticated view)
# ============================================================

def apply_sidebar_style():

    st.markdown(
        """
        <style>
        [data-testid="stSidebar"]{
            background:linear-gradient(180deg,#061421,#040b15);
            border-right:1px solid rgba(120,180,225,.12);
        }
        [data-testid="stSidebar"] button{
            border-radius:10px;
            border:1px solid rgba(120,180,225,.18);
            transition:transform .18s ease, box-shadow .18s ease, border-color .18s ease;
        }
        [data-testid="stSidebar"] button:hover{
            transform:translateY(-1px);
            border-color:rgba(67,200,255,.6);
            box-shadow:0 8px 22px rgba(38,119,255,.25);
        }
        @media (prefers-reduced-motion:reduce){
            *{animation:none !important; transition:none !important;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# MAIN APPLICATION
# ============================================================

def render_app():

    if "workflow_state" not in st.session_state:

        st.session_state.workflow_state = None

    if "authenticated" not in st.session_state:

        st.session_state.authenticated = False

    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    if not st.session_state.authenticated:

        render_login()

        return

    # ========================================================
    # AUTHENTICATED APPLICATION
    # ========================================================

    apply_sidebar_style()

    st.sidebar.markdown("### AquaSwarm Control")

    # --------------------------------------------------------
    # TANK SELECTION
    # --------------------------------------------------------

    tank_data = pd.read_csv("data/sample_water_data.csv")

    tank_options = (
        tank_data["tank_id"]
        .astype(str)
        .drop_duplicates()
        .tolist()
    )

    if "selected_tank_id" not in st.session_state:
        st.session_state.selected_tank_id = (
            tank_options[0] if tank_options else "TANK-001"
        )

    selected_tank = st.sidebar.selectbox(
        "Select Tank",
        tank_options,
        index=(
            tank_options.index(st.session_state.selected_tank_id)
            if st.session_state.selected_tank_id in tank_options
            else 0
        ),
        key="selected_tank_id",
    )

    st.sidebar.caption(
        "Choose the water tank for the next AI operation."
    )

    st.sidebar.markdown("---")

    # --------------------------------------------------------
    # RUN OPERATION
    # --------------------------------------------------------

    if st.sidebar.button("▶ Run Water Operation", use_container_width=True):
        with st.spinner("AquaSwarm agents are analyzing the operation..."):
            flow = AquaSwarmFlow()

            flow.kickoff(
                inputs={"selected_tank_id": selected_tank}
            )

            st.session_state.workflow_state = flow.state

        st.rerun()



    # --------------------------------------------------------
    # LOGOUT
    # --------------------------------------------------------

    if st.sidebar.button(
        "Logout",
        use_container_width=True,
    ):

        st.session_state.authenticated = False

        st.session_state.workflow_state = None

        st.rerun()

    # --------------------------------------------------------
    # DASHBOARD
    # --------------------------------------------------------

    render_dashboard(
        st.session_state.workflow_state,
        approval_handler=handle_manager_decision,
    )


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

render_app()