from __future__ import annotations

import streamlit as st
from ui.components import authenticate, build_network_svg, get_tank_options
from ui.dashboard import render_dashboard
from workflows.aquaswarm_flow import AquaSwarmFlow, AquaSwarmState


st.set_page_config(
    page_title="AquaSwarm AI",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)


def resume_flow_from_state(workflow_state: AquaSwarmState) -> AquaSwarmFlow:
    """Restore an interrupted operation into a new flow instance."""
    restored_state = AquaSwarmState.model_validate(
        workflow_state.model_dump()
    )
    return AquaSwarmFlow(initial_state=restored_state)


def handle_manager_decision(approved: bool, reason: str = "") -> bool:
    """Record the human decision and continue the approved/rejected branch."""
    workflow_state = st.session_state.get("workflow_state")

    if workflow_state is None:
        st.error("No active water operation found.")
        return False

    decided_by = st.session_state.get("current_user", "Manager")

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
        return False


def handle_delivery_completion(actual_quantity: float) -> bool:
    """Record the physical received quantity and trigger verification."""
    workflow_state = st.session_state.get("workflow_state")

    if workflow_state is None:
        st.error("No active water operation found.")
        return False

    try:
        flow = resume_flow_from_state(workflow_state)
        flow.complete_delivery(float(actual_quantity))
        st.session_state.workflow_state = flow.state
        return True
    except Exception as exc:
        st.error(f"Unable to complete delivery: {exc}")
        return False


LOGIN_CSS = r"""
<style>
:root{
  --bg0:#030911; --bg1:#061421; --cyan:#43c8ff; --blue:#416cff;
  --violet:#8b7bff; --green:#4ade80; --muted:#a5b8ca;
  --line:rgba(120,180,225,.18); --panel:#0b1a2b;
}

/* ---------- application canvas ---------- */
.stApp{
  background:
    radial-gradient(circle at 8% 40%, rgba(0,180,255,.12), transparent 32%),
    radial-gradient(circle at 94% 60%, rgba(98,88,255,.13), transparent 32%),
    linear-gradient(135deg,#030911 0%,#061421 50%,#050a14 100%);
  color:#eef6ff !important;
}
.stApp::before{
  content:""; position:fixed; inset:0; pointer-events:none; z-index:0;
  background-image:
    linear-gradient(rgba(90,170,230,.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(90,170,230,.045) 1px, transparent 1px);
  background-size:56px 56px;
}
[data-testid="stHeader"],[data-testid="stDecoration"],footer{background:transparent;}
[data-testid="stToolbar"],footer{display:none !important;}
.block-container{
  max-width:1240px; padding-top:1.4rem; padding-bottom:1rem;
  position:relative; z-index:1;
}

/* ---------- top bar ---------- */
.topbar{
  display:flex; justify-content:space-between; align-items:center;
  padding-bottom:14px; border-bottom:1px solid var(--line); gap:14px;
}
.brand{
  display:flex; align-items:center; gap:10px; color:#f7fbff !important; font-size:13px;
  font-weight:750; letter-spacing:2.4px;
}
.drop{
  width:14px; height:14px; background:linear-gradient(135deg,#7ee7ff,#2d7bff);
  border-radius:0 50% 50% 50%; transform:rotate(45deg);
  box-shadow:0 0 14px rgba(67,200,255,.7);
}
.status{
  display:flex; align-items:center; gap:8px; color:#86efac !important; font-size:11px;
  font-weight:650; letter-spacing:1.4px; padding:6px 12px; border-radius:99px;
  border:1px solid rgba(101,230,163,.25); background:rgba(101,230,163,.06);
}
.pulse{width:7px;height:7px;border-radius:50%;background:#65e6a3;box-shadow:0 0 10px #65e6a3;}
.hero-kicker{color:#67d4ff !important;font-size:11px;font-weight:700;letter-spacing:2.4px;margin:34px 0 12px;}
.hero-title{color:#f8fbff !important;font-size:50px;line-height:1.03;font-weight:800;letter-spacing:-2px;margin:0;}
.hero-title span{background:linear-gradient(100deg,#43c8ff,#6f7bff);-webkit-background-clip:text;background-clip:text;color:transparent !important;}
.hero-sub{color:#a5b8ca !important;font-size:14px;margin:14px 0 4px;line-height:1.6;}
.login-label{color:#7fa0b8 !important;font-size:10px;font-weight:700;letter-spacing:2px;margin:18px 0 0;}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:0;margin-top:6px;border-top:1px solid var(--line);border-bottom:1px solid var(--line);}
.stat{padding:16px 4px 14px;border-right:1px solid var(--line);}
.stat:last-child{border-right:none;}
.stat+.stat{padding-left:22px;}
.sv{color:#f7fbff !important;font-size:27px;font-weight:750;line-height:1;}
.sl{color:#8ca4b8 !important;font-size:9px;font-weight:700;letter-spacing:1.2px;margin-top:8px;}
.ticker{display:flex;align-items:center;gap:10px;margin-top:16px;color:#67d4ff !important;font-size:11px;letter-spacing:1.2px;font-weight:600;}
.ticker i{width:6px;height:6px;border-radius:50%;background:#43c8ff;box-shadow:0 0 10px #43c8ff;}

/* ---------- login form ---------- */
div[data-testid="stForm"]{
  margin-top:48px;padding:34px 36px 30px;
  background:linear-gradient(145deg,rgba(16,33,52,.98),rgba(7,18,31,.99)) !important;
  border:1px solid rgba(120,180,225,.22);border-radius:20px;
  box-shadow:0 30px 80px rgba(0,0,0,.45);
  color:#edf6ff !important;
}
div[data-testid="stForm"] h1,
div[data-testid="stForm"] h2,
div[data-testid="stForm"] h3,
div[data-testid="stForm"] strong,
div[data-testid="stForm"] [data-testid="stMarkdownContainer"] p{
  color:#eef6ff !important;
}
div[data-testid="stForm"] [data-testid="stCaptionContainer"],
div[data-testid="stForm"] [data-testid="stCaptionContainer"] p{
  color:#9eb3c5 !important;
}
div[data-testid="stTextInput"] label,
div[data-testid="stTextInput"] label p{
  color:#9db2c5 !important;
  font-size:12px !important;
  font-weight:600 !important;
}
div[data-testid="stTextInput"] input{
  min-height:44px !important;
  background:#0a1625 !important;
  color:#f7fbff !important;
  -webkit-text-fill-color:#f7fbff !important;
  caret-color:#7ee7ff !important;
  border:1px solid #395166 !important;
  border-radius:10px !important;
  box-shadow:none !important;
}
div[data-testid="stTextInput"] input:focus{
  border-color:#43c8ff !important;
  box-shadow:0 0 0 1px rgba(67,200,255,.45),0 0 18px rgba(67,200,255,.08) !important;
}
div[data-testid="stTextInput"] input::placeholder{
  color:#71879b !important;
  -webkit-text-fill-color:#71879b !important;
  opacity:1 !important;
}
div[data-testid="stTextInput"] input:-webkit-autofill,
div[data-testid="stTextInput"] input:-webkit-autofill:hover,
div[data-testid="stTextInput"] input:-webkit-autofill:focus{
  -webkit-text-fill-color:#f7fbff !important;
  box-shadow:0 0 0 1000px #0a1625 inset !important;
  transition:background-color 9999s ease-in-out 0s;
}
div[data-testid="stTextInput"] button{
  color:#dbe9f4 !important;
  background:transparent !important;
}
div[data-testid="stFormSubmitButton"] button{
  height:48px;border:none;border-radius:10px;
  background:linear-gradient(100deg,#079bff,#416cff 52%,#6258ff) !important;
  color:#ffffff !important;
  font-weight:750 !important;
  box-shadow:0 10px 24px rgba(46,112,255,.22);
}
div[data-testid="stFormSubmitButton"] button p,
div[data-testid="stFormSubmitButton"] button span{color:#ffffff !important;}
.secure{color:#8ca6ba !important;font-size:11px;text-align:center;margin-top:14px;}

/* ---------- sidebar / manager controls ---------- */
[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#071624 0%,#040b15 100%) !important;
  border-right:1px solid rgba(120,180,225,.16);
  color:#eaf4fc !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p{
  color:#b7c8d7 !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3{
  color:#f5faff !important;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] label p{
  color:#c8d7e4 !important;
  font-weight:600 !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div{
  background:#0a1726 !important;
  border-color:#32485c !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] *{
  color:#f2f8fd !important;
}
[data-testid="stSidebar"] [data-baseweb="popover"] *{
  color:#102030 !important;
}
[data-testid="stSidebar"] button{
  min-height:42px !important;
  border-radius:10px !important;
  border:1px solid rgba(120,180,225,.22) !important;
  color:#edf6ff !important;
  background:#0a1726 !important;
}
[data-testid="stSidebar"] button p,
[data-testid="stSidebar"] button span{color:#edf6ff !important;}
[data-testid="stSidebar"] button[kind="primary"]{
  background:linear-gradient(100deg,#087eff,#5a55ff) !important;
  color:#ffffff !important;
  border-color:rgba(111,213,255,.4) !important;
  box-shadow:0 8px 22px rgba(38,118,255,.22);
}
[data-testid="stSidebar"] button[kind="primary"] p,
[data-testid="stSidebar"] button[kind="primary"] span{color:#ffffff !important;}
[data-testid="stSidebar"] button:hover{border-color:rgba(67,200,255,.5) !important;}



/* ---------- login card ---------- */
.st-key-login_card{
  margin-top:34px;
  padding:32px 36px 28px;
  background:linear-gradient(145deg,rgba(17,32,50,.97),rgba(8,19,33,.99));
  border:1px solid rgba(90,160,210,.24);
  border-radius:20px;
  box-shadow:0 30px 80px rgba(0,0,0,.46);
}
.login-title{
  color:#ffffff !important;
  font-size:28px;
  line-height:1.15;
  font-weight:800;
  letter-spacing:-.7px;
  margin-bottom:9px;
}
.login-copy{
  color:#b7c7d4 !important;
  font-size:13px;
  line-height:1.6;
  margin-bottom:24px;
}
.login-field-label{
  color:#c3d2de !important;
  font-size:11px;
  font-weight:750;
  letter-spacing:1.5px;
  margin:0 0 7px;
}
.login-password-label{margin-top:16px;}
.st-key-login_card div[data-testid="stTextInput"]{margin-bottom:0 !important;}
.st-key-login_card div[data-testid="stTextInput"] input{
  min-height:46px !important;
  height:46px !important;
  box-sizing:border-box !important;
  background:#0c1724 !important;
  color:#f5f9fc !important;
  -webkit-text-fill-color:#f5f9fc !important;
  border:1px solid rgba(125,164,195,.34) !important;
  border-radius:10px !important;
  font-size:14px !important;
  font-weight:550 !important;
  padding-left:13px !important;
}
.st-key-login_card div[data-testid="stTextInput"] input::placeholder{
  color:#6f879b !important;
  opacity:1 !important;
}
.st-key-login_card div[data-testid="stTextInput"] input:focus{
  border-color:#43c8ff !important;
  box-shadow:0 0 0 1px rgba(67,200,255,.25),0 0 20px rgba(67,200,255,.08) !important;
  outline:none !important;
}
.st-key-login_card div[data-testid="stTextInput"] button{
  color:#b7c7d4 !important;
  background:transparent !important;
}
.st-key-login_submit button{
  margin-top:22px !important;
  height:48px !important;
  border:0 !important;
  border-radius:10px !important;
  color:#ffffff !important;
  -webkit-text-fill-color:#ffffff !important;
  background:linear-gradient(100deg,#079bff,#416cff 52%,#6258ff) !important;
  box-shadow:0 10px 28px rgba(38,118,255,.22) !important;
  font-size:14px !important;
  font-weight:750 !important;
}
.st-key-login_submit button p,
.st-key-login_submit button span{
  color:#ffffff !important;
  -webkit-text-fill-color:#ffffff !important;
}
.st-key-login_submit button:hover{transform:translateY(-1px);filter:brightness(1.05);}
.st-key-login_card .stAlert{margin-top:12px !important;}
.st-key-login_card .secure{color:#a5b9c8 !important;font-size:11px;text-align:center;margin:16px 0 0;}

@media (max-width:850px){
  .hero-title{font-size:36px;}
  div[data-testid="stForm"]{margin-top:18px;padding:26px 22px;}
  .topbar{align-items:flex-start;}
}
</style>
"""


def render_login() -> None:
    """Render the manager login without Streamlit's form submit hint."""
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="topbar">
          <div class="brand"><span class="drop"></span>AQUASWARM AI</div>
          <div class="status"><span class="pulse"></span>SYSTEM ONLINE</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.3, 0.7], gap="large")

    with left:
        st.markdown(
            """
            <div class="hero-kicker">AI WATER OPERATIONS</div>
            <h1 class="hero-title">
              Autonomous intelligence<br>for <span>water.</span>
            </h1>
            <div class="hero-sub">
              Eight coordinated agents. One human in command.
            </div>
            <div class="login-label">LIVE AGENT NETWORK</div>
            """,
            unsafe_allow_html=True,
        )
        st.html(build_network_svg())
        st.markdown(
            """
            <div class="stats">
              <div class="stat">
                <div class="sv">08</div>
                <div class="sl">OPERATIONAL AI AGENTS</div>
              </div>
              <div class="stat">
                <div class="sv">24/7</div>
                <div class="sl">MONITORING MODEL</div>
              </div>
              <div class="stat">
                <div class="sv">HUMAN</div>
                <div class="sl">FINAL CONTROL</div>
              </div>
            </div>
            <div class="ticker">
              <i></i>AGENT SWARM ACTIVE · REPLANNING LOOP READY
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        # A normal container is intentional: Streamlit's form UI adds the
        # "Press Enter to submit form" hint to focused inputs.
        with st.container(key="login_card"):
            st.markdown(
                """
                <div class="login-title">Secure Session</div>
                <div class="login-copy">Access the AquaSwarm operations control center.</div>
                <div class="login-field-label">EMAIL</div>
                """,
                unsafe_allow_html=True,
            )
            email = st.text_input(
                "Email",
                placeholder="you@organization.com",
                key="login_email",
                label_visibility="collapsed",
            )
            st.markdown(
                '<div class="login-field-label login-password-label">PASSWORD</div>',
                unsafe_allow_html=True,
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password",
                label_visibility="collapsed",
            )
            submitted = st.button(
                "Sign In  →",
                key="login_submit",
                use_container_width=True,
                type="primary",
            )
            if submitted:
                if not email.strip() or not password:
                    st.error("Please enter your email and password.")
                elif authenticate(email, password):
                    st.session_state.authenticated = True
                    st.session_state.current_user = email.strip().lower()
                    st.session_state.pop("login_password", None)
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
            st.markdown(
                '<p class="secure">🔒 Authorized personnel only</p>',
                unsafe_allow_html=True,
            )


def apply_sidebar_style() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"]{
          background:linear-gradient(180deg,#061421 0%,#040b15 100%);
          border-right:1px solid rgba(120,180,225,.14);
        }
        [data-testid="stSidebar"] section{padding-top:1rem;}
        [data-testid="stSidebar"] button{
          border-radius:10px !important;
          border:1px solid rgba(120,180,225,.18) !important;
          min-height:42px;
        }
        [data-testid="stSidebar"] button[kind="primary"]{
          background:linear-gradient(100deg,#087eff,#5a55ff) !important;
          color:#fff !important;
          border-color:rgba(111,213,255,.4) !important;
          box-shadow:0 8px 22px rgba(38,118,255,.22);
        }
        [data-testid="stSidebar"] button:hover{
          border-color:rgba(67,200,255,.45) !important;
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] label{
          color:#8aa0b4 !important;
          font-size:.78rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_app() -> None:
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("current_user", "")
    st.session_state.setdefault("workflow_state", None)

    if not st.session_state.authenticated:
        render_login()
        return

    apply_sidebar_style()
    st.markdown(
        """<style>
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] div,
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"]{
          color:#9fb4c5 !important;
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] *{
          color:#172534 !important;
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] > div{
          color:#ecf5fb !important;
        }
        [data-testid="stSidebar"] hr{
          border-color:rgba(120,180,225,.14) !important;
        }
        </style>""",
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        """<div style="padding:8px 0 10px 0;">
          <div style="color:#ffffff;font-weight:750;font-size:18px;letter-spacing:-.2px;">AquaSwarm Control</div>
          <div style="color:#6f879b;font-size:11px;margin-top:3px;">Manager operations workspace</div>
        </div>""",
        unsafe_allow_html=True,
    )

    tank_options = get_tank_options()
    if not tank_options:
        st.error(
            "No tanks are available. Start the backend or check data/tanks.csv."
        )
        return

    selected_default = st.session_state.get(
        "selected_tank_id",
        tank_options[0],
    )
    if selected_default not in tank_options:
        selected_default = tank_options[0]

    selected_tank = st.sidebar.selectbox(
        "Select Tank",
        tank_options,
        index=tank_options.index(selected_default),
        key="selected_tank_id",
    )

    st.sidebar.caption(
        "Choose the water tank for the next AI operation."
    )
    workflow_state = st.session_state.get("workflow_state")
    current_status = str(getattr(workflow_state, "operation_status", "Ready"))
    if workflow_state is not None:
        st.sidebar.markdown(
            f"<div style=\"margin:10px 0 14px;padding:10px 12px;border:1px solid rgba(120,180,225,.13);border-radius:10px;background:rgba(7,18,31,.72);\">"
            f"<div style=\"color:#6f879b;font-size:9px;letter-spacing:1.4px;text-transform:uppercase;\">Operation</div>"
            f"<div style=\"color:#dbe9f4;font-size:12px;font-weight:650;margin-top:4px;\">{current_status}</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    st.sidebar.markdown("---")

    run_disabled = current_status in {
        "Awaiting Manager Approval",
        "Delivery Dispatched",
        "Delivery In Progress",
    }

    if st.sidebar.button(
        "▶ Run Water Operation",
        use_container_width=True,
        type="primary",
        disabled=run_disabled,
    ):
        with st.spinner("AquaSwarm agents are analyzing the operation..."):
            try:
                flow = AquaSwarmFlow()
                flow.state.selected_tank_id = selected_tank
                flow.kickoff()

                # CrewAI Flow can return a partially populated state when a
                # method fails. Never render that as a valid 0-value operation.
                if flow.state.water_data is None:
                    detail = getattr(flow.state, "backend_sync_error", "")
                    raise RuntimeError(
                        detail
                        or "The pipeline stopped during initialization. "
                           "Check the backend/CSV data configuration."
                    )

                st.session_state.workflow_state = flow.state
            except Exception as exc:
                st.error(f"Unable to start water operation: {exc}")
        st.rerun()

    if st.sidebar.button(
        "Reset Current Operation",
        use_container_width=True,
    ):
        st.session_state.workflow_state = None
        st.rerun()

    if st.sidebar.button(
        "Logout",
        use_container_width=True,
    ):
        st.session_state.authenticated = False
        st.session_state.current_user = ""
        st.session_state.workflow_state = None
        st.rerun()

    render_dashboard(
        st.session_state.workflow_state,
        approval_handler=handle_manager_decision,
        delivery_completion_handler=handle_delivery_completion,
    )


if __name__ == "__main__":
    render_app()
