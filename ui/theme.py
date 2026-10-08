"""AquaSwarm water theme: river / stream palette and animations.

Palette
  abyss  #031826   deepest water (page background)
  deep   #052b40   panels
  river  #0a6e8a   mid-stream teal
  teal   #12a8b8   current
  aqua   #4de3f0   bright water / primary accent
  foam   #8ff5e0   sea-foam / success
  mist   #d6f7fb   text on dark
  sand   #ffd27a   warning / waiting on a human
  coral  #ff7b72   critical / error
"""
from __future__ import annotations

# Seamless horizontal wave used as an animated "river surface" background.
_WAVE_A = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 120' preserveAspectRatio='none'>"
    "<path d='M0 60 Q150 20 300 60 T600 60 T900 60 T1200 60 V120 H0Z' fill='%234de3f0' fill-opacity='.07'/></svg>"
)
_WAVE_B = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 120' preserveAspectRatio='none'>"
    "<path d='M0 70 Q200 25 400 70 T800 70 T1200 70 V120 H0Z' fill='%2312a8b8' fill-opacity='.09'/></svg>"
)


def base_css() -> str:
    return f"""
<style>
:root{{
  --abyss:#031826; --deep:#052b40; --river:#0a6e8a; --teal:#12a8b8;
  --aqua:#4de3f0; --foam:#8ff5e0; --mist:#d6f7fb; --muted:#8fb7c4;
  --sand:#ffd27a; --coral:#ff7b72; --lilac:#9bb4ff;
  --line:rgba(120,225,240,.16);
}}

/* ---------- canvas: deep water with drifting surface waves ---------- */
.stApp{{
  background:
    radial-gradient(1200px 520px at 12% -10%, rgba(18,168,184,.28), transparent 60%),
    radial-gradient(900px 480px at 100% 20%, rgba(10,110,138,.30), transparent 60%),
    linear-gradient(180deg,#041f31 0%,#031826 55%,#020f19 100%);
  color:var(--mist) !important;
}}
.stApp::before,.stApp::after{{
  content:""; position:fixed; left:0; right:0; bottom:0; height:180px;
  pointer-events:none; z-index:0; background-repeat:repeat-x; background-size:1200px 100%;
}}
.stApp::before{{background-image:url("{_WAVE_A}"); animation:aqDriftA 26s linear infinite;}}
.stApp::after{{height:140px;background-image:url("{_WAVE_B}"); animation:aqDriftB 34s linear infinite;}}
@keyframes aqDriftA{{from{{background-position-x:0}}to{{background-position-x:-1200px}}}}
@keyframes aqDriftB{{from{{background-position-x:-1200px}}to{{background-position-x:0}}}}

[data-testid="stHeader"],[data-testid="stDecoration"]{{background:transparent;}}
footer,#MainMenu,.stDeployButton,[data-testid="stAppDeployButton"],
[data-testid="stToolbarActions"],[data-testid="stStatusWidget"]{{display:none !important;}}
/* never hide the control that re-opens the sidebar */
[data-testid="stExpandSidebarButton"],[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],[data-testid="stSidebarCollapseButton"]{{
  display:flex !important;visibility:visible !important;opacity:1 !important;}}
[data-testid="stExpandSidebarButton"],[data-testid="collapsedControl"],[data-testid="stSidebarCollapsedControl"]{{
  position:relative;z-index:999999;background:rgba(5,43,64,.92) !important;border:1px solid rgba(120,225,240,.35) !important;
  border-radius:12px !important;box-shadow:0 6px 20px rgba(0,0,0,.35);}}
[data-testid="stExpandSidebarButton"] *,[data-testid="collapsedControl"] *,[data-testid="stSidebarCollapsedControl"] *,
[data-testid="stSidebarCollapseButton"] *{{color:#4de3f0 !important;fill:#4de3f0 !important;}}
.block-container{{max-width:1280px; padding-top:1.2rem; padding-bottom:5rem; position:relative; z-index:1;}}
.stApp, .stApp p, .stApp label, .stApp span{{color:var(--mist);}}
.stApp h1,.stApp h2,.stApp h3{{color:#f2fdff !important;}}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"]{{
  background:linear-gradient(185deg,#06324a 0%,#041f31 55%,#031826 100%) !important;
  border-right:1px solid var(--line);
}}
[data-testid="stSidebar"] *{{color:var(--mist);}}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] *{{color:var(--muted) !important;}}
[data-testid="stSidebar"] label p{{color:#bfe6ee !important;font-weight:600 !important;font-size:12px !important;letter-spacing:.3px;}}
[data-testid="stSidebar"] [data-baseweb="select"] > div{{
  background:rgba(4,30,46,.9) !important; border:1px solid rgba(120,225,240,.28) !important; border-radius:12px !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] *{{color:#effcff !important;}}
[data-baseweb="popover"] *{{color:#0b2a3a !important;}}
[data-testid="stSidebar"] button{{
  min-height:42px !important; border-radius:12px !important;
  border:1px solid rgba(120,225,240,.25) !important; background:rgba(4,30,46,.85) !important;
  color:#effcff !important; transition:all .25s ease;
}}
[data-testid="stSidebar"] button p{{color:#effcff !important;}}
[data-testid="stSidebar"] button:hover{{border-color:var(--aqua) !important; box-shadow:0 0 18px rgba(77,227,240,.18);}}
[data-testid="stSidebar"] button[kind="primary"],
.stButton button[kind="primary"]{{
  background:linear-gradient(100deg,#0a9db4,#12c4d6 55%,#4de3f0) !important;
  color:#02222f !important; border:0 !important; font-weight:800 !important;
  box-shadow:0 10px 26px rgba(18,196,214,.28);
}}
[data-testid="stSidebar"] button[kind="primary"] p,
.stButton button[kind="primary"] p{{color:#02222f !important;}}
.stButton button[kind="primary"]:hover{{filter:brightness(1.08); transform:translateY(-1px);}}
.stButton button:disabled{{opacity:.45 !important;}}
.stButton button:not([kind="primary"]){{
  border-radius:12px; background:rgba(5,43,64,.8); border:1px solid rgba(120,225,240,.3); color:#effcff;
}}
.stButton button:not([kind="primary"]) p{{color:#effcff !important;}}

/* ---------- inputs ---------- */
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stTextArea"] textarea{{
  background:rgba(3,24,38,.92) !important; color:#f2fdff !important;
  -webkit-text-fill-color:#f2fdff !important; caret-color:var(--aqua) !important;
  border:1px solid rgba(120,225,240,.28) !important; border-radius:12px !important;
}}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stNumberInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus{{
  border-color:var(--aqua) !important; box-shadow:0 0 0 1px rgba(77,227,240,.4),0 0 22px rgba(77,227,240,.12) !important;
}}
div[data-testid="stTextInput"] label p,div[data-testid="stNumberInput"] label p,div[data-testid="stTextArea"] label p{{
  color:#bfe6ee !important; font-weight:600 !important;
}}
.stAlert{{border-radius:14px;}}

/* ---------- top bar & login ---------- */
.topbar{{display:flex;justify-content:space-between;align-items:center;padding-bottom:14px;border-bottom:1px solid var(--line);gap:14px;}}
.brand{{display:flex;align-items:center;gap:10px;color:#f2fdff !important;font-size:13px;font-weight:800;letter-spacing:2.4px;}}
.drop{{width:15px;height:15px;background:linear-gradient(135deg,#bff8ff,#12a8b8);border-radius:0 50% 50% 50%;transform:rotate(45deg);
  box-shadow:0 0 16px rgba(77,227,240,.8);animation:aqBob 3.2s ease-in-out infinite;}}
@keyframes aqBob{{0%,100%{{transform:rotate(45deg) translate(0,0)}}50%{{transform:rotate(45deg) translate(-2px,-2px)}}}}
.status{{display:flex;align-items:center;gap:8px;color:var(--foam) !important;font-size:11px;font-weight:700;letter-spacing:1.4px;
  padding:6px 12px;border-radius:99px;border:1px solid rgba(143,245,224,.28);background:rgba(143,245,224,.07);}}
.pulse{{width:7px;height:7px;border-radius:50%;background:var(--foam);box-shadow:0 0 10px var(--foam);animation:aqPulse 1.8s ease-in-out infinite;}}
@keyframes aqPulse{{50%{{opacity:.35;transform:scale(.8)}}}}
.hero-kicker{{color:var(--aqua) !important;font-size:11px;font-weight:800;letter-spacing:2.6px;margin:34px 0 12px;}}
.hero-title{{color:#f6feff !important;font-size:50px;line-height:1.04;font-weight:800;letter-spacing:-2px;margin:0;}}
.hero-title span{{background:linear-gradient(100deg,#4de3f0,#8ff5e0 60%,#d6f7fb);-webkit-background-clip:text;background-clip:text;color:transparent !important;}}
.hero-sub{{color:var(--muted) !important;font-size:14px;margin:14px 0 4px;line-height:1.6;}}
.login-label{{color:#79a8b6 !important;font-size:10px;font-weight:700;letter-spacing:2px;margin:18px 0 0;}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);margin-top:6px;border-top:1px solid var(--line);border-bottom:1px solid var(--line);}}
.stat{{padding:16px 4px 14px;border-right:1px solid var(--line);}} .stat:last-child{{border-right:none;}} .stat+.stat{{padding-left:22px;}}
.sv{{color:#f6feff !important;font-size:27px;font-weight:800;line-height:1;}}
.sl{{color:#86b4c1 !important;font-size:9px;font-weight:700;letter-spacing:1.2px;margin-top:8px;}}
.ticker{{display:flex;align-items:center;gap:10px;margin-top:16px;color:var(--aqua) !important;font-size:11px;letter-spacing:1.2px;font-weight:600;}}
.ticker i{{width:6px;height:6px;border-radius:50%;background:var(--aqua);box-shadow:0 0 10px var(--aqua);animation:aqPulse 1.6s infinite;}}
.st-key-login_card{{margin-top:34px;padding:32px 36px 28px;border-radius:22px;
  background:linear-gradient(150deg,rgba(10,72,98,.62),rgba(3,28,44,.92));
  border:1px solid rgba(120,225,240,.28);box-shadow:0 30px 80px rgba(0,0,0,.45),inset 0 1px 0 rgba(255,255,255,.06);
  backdrop-filter:blur(10px);}}
.login-title{{color:#fff !important;font-size:28px;font-weight:800;letter-spacing:-.7px;margin-bottom:9px;}}
.login-copy{{color:#a9d2dc !important;font-size:13px;line-height:1.6;margin-bottom:24px;}}
.login-field-label{{color:#bfe6ee !important;font-size:11px;font-weight:800;letter-spacing:1.5px;margin:0 0 7px;}}
.login-password-label{{margin-top:16px;}}
.st-key-login_card div[data-testid="stTextInput"] input{{min-height:46px !important;height:46px !important;font-size:14px !important;}}
.st-key-login_submit button{{margin-top:22px !important;height:48px !important;font-size:14px !important;}}
.secure{{color:#8fb7c4 !important;font-size:11px;text-align:center;margin:16px 0 0;}}
@media (max-width:850px){{.hero-title{{font-size:36px;}}.st-key-login_card{{padding:24px 20px;}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none !important;transition:none !important;}}}}
</style>
"""


def dashboard_css() -> str:
    return """
<style>
.aq{--abyss:#031826;--deep:#052b40;--river:#0a6e8a;--teal:#12a8b8;--aqua:#4de3f0;--foam:#8ff5e0;--mist:#d6f7fb;
    --muted:#8fb7c4;--dim:#5f8f9e;--sand:#ffd27a;--coral:#ff7b72;--lilac:#9bb4ff;--orange:#ffa05a;
    --line:rgba(120,225,240,.16);
    --glass:linear-gradient(150deg,rgba(10,84,112,.46),rgba(3,32,48,.82));
    color:var(--mist);font-family:Inter,'Segoe UI',system-ui,sans-serif;}
.aq *{box-sizing:border-box;}

/* ---------- header ---------- */
.aq-header{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;padding:6px 2px 14px;}
.aq-brand{display:flex;align-items:center;gap:12px;font-size:25px;font-weight:800;letter-spacing:-.6px;color:#f6feff;}
.aq-drop{width:18px;height:18px;border-radius:0 50% 50% 50%;transform:rotate(45deg);
  background:linear-gradient(135deg,#d6f7fb,#12a8b8);box-shadow:0 0 20px rgba(77,227,240,.8);animation:aqBobD 3.4s ease-in-out infinite;}
@keyframes aqBobD{0%,100%{transform:rotate(45deg) translate(0,0)}50%{transform:rotate(45deg) translate(-2px,-3px)}}
.aq-sub{color:var(--muted);font-size:12.5px;margin-top:4px;letter-spacing:.3px;}
.aq-right{display:flex;gap:10px;align-items:center;flex-wrap:wrap;}
.aq-chip{padding:7px 14px;border-radius:99px;font-size:11.5px;font-weight:800;letter-spacing:.9px;text-transform:uppercase;
  color:var(--aqua);background:rgba(77,227,240,.09);border:1px solid rgba(77,227,240,.35);}
.aq-chip.sim{color:var(--sand);background:rgba(255,210,122,.09);border-color:rgba(255,210,122,.4);}
.aq-chip.ok{color:var(--foam);background:rgba(143,245,224,.08);border-color:rgba(143,245,224,.35);}
.aq-chip.bad{color:var(--coral);background:rgba(255,123,114,.09);border-color:rgba(255,123,114,.4);}
.aq-river-line{height:26px;margin:0 0 14px;overflow:hidden;position:relative;border-radius:14px;
  background:linear-gradient(90deg,rgba(18,168,184,.0),rgba(18,168,184,.16),rgba(18,168,184,.0));}
.aq-river-line svg{position:absolute;left:0;top:0;width:200%;height:100%;animation:aqWaveX 9s linear infinite;}
@keyframes aqWaveX{to{transform:translateX(-50%)}}

/* ---------- cards ---------- */
.card{position:relative;background:var(--glass);border:1px solid var(--line);border-radius:20px;padding:20px 22px;
  box-shadow:0 18px 50px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.05);overflow:hidden;backdrop-filter:blur(8px);
  animation:aqRise .6s ease both;}
.card::after{content:"";position:absolute;left:-40%;top:0;width:40%;height:100%;
  background:linear-gradient(100deg,transparent,rgba(77,227,240,.07),transparent);animation:aqSheen 7s ease-in-out infinite;pointer-events:none;}
@keyframes aqSheen{0%{left:-45%}60%,100%{left:120%}}
@keyframes aqRise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin:6px 0 20px;}
.kpi-label{font-size:11px;font-weight:800;letter-spacing:1.5px;color:var(--muted);text-transform:uppercase;display:flex;justify-content:space-between;}
.kpi-value{font-size:31px;font-weight:800;letter-spacing:-1px;margin-top:10px;color:#f6feff;line-height:1.05;}
.kpi-unit{font-size:12px;font-weight:600;color:var(--muted);margin-left:6px;letter-spacing:0;}
.kpi-meta{font-size:12px;color:var(--muted);margin-top:8px;}
.pbadge{display:inline-flex;align-items:center;gap:9px;margin-top:8px;padding:6px 14px;border-radius:99px;font-weight:800;font-size:20px;letter-spacing:.5px;}
.pbadge i{width:9px;height:9px;border-radius:50%;background:currentColor;box-shadow:0 0 12px currentColor;animation:aqPulse 1.7s infinite;}
.p-low{color:#5ef2b6;background:rgba(94,242,182,.1);border:1px solid rgba(94,242,182,.35);}
.p-medium{color:var(--sand);background:rgba(255,210,122,.1);border:1px solid rgba(255,210,122,.38);}
.p-high{color:var(--orange);background:rgba(255,160,90,.1);border:1px solid rgba(255,160,90,.4);}
.p-critical{color:var(--coral);background:rgba(255,123,114,.12);border:1px solid rgba(255,123,114,.5);animation:aqAlarm 1.6s ease-in-out infinite;}
@keyframes aqAlarm{50%{box-shadow:0 0 22px rgba(255,123,114,.45)}}
.aq-h{font-size:18px;font-weight:800;letter-spacing:-.3px;margin:26px 0 2px;color:#f6feff;}
.aq-c{font-size:12.5px;color:var(--muted);margin-bottom:12px;}
.grid2{display:grid;grid-template-columns:1.05fr .95fr;gap:14px;}
@media (max-width:900px){.grid2{grid-template-columns:1fr;}}
.row{display:flex;justify-content:space-between;align-items:baseline;gap:14px;padding:11px 0;border-bottom:1px solid rgba(120,225,240,.09);}
.row:last-child{border-bottom:none;}
.row .l{color:var(--muted);font-size:13px;} .row .v{font-weight:750;font-size:15px;text-align:right;color:#f2fdff;}
.row .v small{color:var(--muted);font-weight:600;margin-left:5px;font-size:11px;}
.row .v.warn{color:var(--sand);} .row .v.good{color:var(--foam);}
.ctitle{font-weight:800;font-size:15px;color:#f6feff;} .csub{font-size:12px;color:var(--muted);margin-top:2px;}
.chead{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;margin-bottom:10px;}
.tag{font-size:11px;font-weight:800;letter-spacing:1px;padding:5px 11px;border-radius:99px;color:var(--aqua);border:1px solid rgba(77,227,240,.35);background:rgba(77,227,240,.07);}
.note{margin-top:12px;padding:12px 14px;border-radius:14px;font-size:13px;line-height:1.55;color:#cfeef4;
  background:rgba(3,24,38,.55);border:1px solid rgba(120,225,240,.12);}
.note b{color:#f6feff;}

/* ---------- animated tank ---------- */
.tankwrap{display:flex;gap:22px;align-items:center;}
.tank{position:relative;width:128px;height:210px;flex:none;border-radius:18px 18px 26px 26px;overflow:hidden;
  background:linear-gradient(180deg,rgba(214,247,251,.06),rgba(214,247,251,.02));border:2px solid rgba(140,235,245,.45);
  box-shadow:inset 0 0 30px rgba(77,227,240,.12),0 12px 36px rgba(0,0,0,.35);}
.tank .water{position:absolute;left:0;right:0;bottom:0;transition:height 1.4s cubic-bezier(.2,.8,.2,1);
  background:linear-gradient(180deg,rgba(77,227,240,.95),rgba(10,110,138,.96) 70%,rgba(5,60,84,1));}
.tank .water.low{background:linear-gradient(180deg,rgba(255,168,100,.95),rgba(190,80,60,.95));}
.tank .wave{position:absolute;left:0;top:-13px;width:200%;height:15px;animation:aqWaveX 4.5s linear infinite;}
.tank .wave.b{top:-9px;opacity:.55;animation-duration:7s;animation-direction:reverse;}
.tank .wave path{fill:rgba(77,227,240,.95);} .tank .water.low .wave path{fill:rgba(255,168,100,.95);}
.tank .bubbles i{position:absolute;bottom:-8px;width:6px;height:6px;border-radius:50%;background:rgba(255,255,255,.55);animation:aqBubble 5s ease-in infinite;}
.tank .bubbles i:nth-child(1){left:22%;animation-delay:0s}.tank .bubbles i:nth-child(2){left:52%;animation-delay:1.7s;width:4px;height:4px}
.tank .bubbles i:nth-child(3){left:76%;animation-delay:3.1s}
@keyframes aqBubble{0%{transform:translateY(0);opacity:0}15%{opacity:.8}100%{transform:translateY(-160px);opacity:0}}
.tank .mark{position:absolute;left:0;right:0;border-top:1px dashed rgba(255,255,255,.6);}
.tank .mark span{position:absolute;right:4px;top:3px;font-size:9px;font-weight:800;letter-spacing:.8px;color:#fff;text-shadow:0 1px 3px rgba(0,0,0,.6);}
.tank .mark.crit{border-color:rgba(255,123,114,.85)}
.tank-pct{position:absolute;left:0;right:0;top:46%;text-align:center;font-size:26px;font-weight:800;color:#fff;text-shadow:0 2px 10px rgba(0,0,0,.55);}
.tank-info{flex:1;min-width:0;}
.big{font-size:34px;font-weight:800;letter-spacing:-1px;color:#f6feff;} .big small{font-size:13px;color:var(--muted);font-weight:600;margin-left:6px;letter-spacing:0;}
.meter{height:9px;border-radius:9px;background:rgba(120,225,240,.12);overflow:hidden;margin:12px 0 6px;}
.meter i{display:block;height:100%;border-radius:9px;background:linear-gradient(90deg,#12a8b8,#4de3f0,#8ff5e0,#4de3f0);background-size:200% 100%;animation:aqFlow 2.4s linear infinite;}
@keyframes aqFlow{to{background-position:-200% 0}}
.stat-line{display:flex;align-items:center;gap:9px;margin-top:12px;font-size:13px;color:#cfeef4;}
.dot{width:9px;height:9px;border-radius:50%;background:var(--sand);box-shadow:0 0 10px var(--sand);animation:aqPulse 1.6s infinite;flex:none;}
.dot.ok{background:var(--foam);box-shadow:0 0 10px var(--foam);}

/* ---------- the river pipeline ---------- */
.river-card{padding:24px 22px 18px;}
.rhead{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:22px;}
.rtitle{font-weight:800;font-size:16px;color:#f6feff;} .rop{font-size:12.5px;color:var(--muted);}
.river{display:flex;align-items:flex-start;position:relative;}
.stage{flex:1;min-width:0;display:flex;flex-direction:column;align-items:center;text-align:center;position:relative;padding:0 4px;}
.link{position:absolute;top:26px;left:calc(-50% + 30px);width:calc(100% - 60px);height:6px;border-radius:6px;background:rgba(120,225,240,.1);overflow:hidden;}
.stage:first-child .link{display:none;}
.link .w{position:absolute;inset:0;transform-origin:left center;transform:scaleX(0);border-radius:6px;
  background:linear-gradient(90deg,#12a8b8,#4de3f0,#8ff5e0,#4de3f0,#12a8b8);background-size:200% 100%;}
.link.full .w{transform:scaleX(1);animation:aqFlow 3s linear infinite;}
.link.flow .w{transform:scaleX(1);animation:aqFlow 1.1s linear infinite;filter:brightness(1.15);}
.link.fresh .w{animation:aqFill .9s ease-out both,aqFlow 3s linear infinite;}
.link.dead{background:repeating-linear-gradient(90deg,rgba(120,225,240,.18) 0 6px,transparent 6px 12px);}
.link .drop{position:absolute;top:-1px;width:8px;height:8px;border-radius:50%;background:#fff;opacity:0;box-shadow:0 0 10px #fff;}
.link.flow .drop{animation:aqDropMove 1.5s linear infinite;} .link.flow .drop.d2{animation-delay:.75s;}
@keyframes aqFill{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes aqDropMove{0%{left:-6%;opacity:0}15%{opacity:1}85%{opacity:1}100%{left:102%;opacity:0}}
.node{width:54px;height:54px;border-radius:50%;display:grid;place-items:center;position:relative;z-index:2;font-weight:800;font-size:17px;
  background:rgba(3,28,44,.95);border:2px solid rgba(120,225,240,.26);color:#6fa0ae;transition:all .4s;}
.node .ring{position:absolute;inset:-2px;border-radius:50%;border:2px solid var(--aqua);opacity:0;}
.node .swirl{position:absolute;inset:-6px;border-radius:50%;border:2px solid transparent;border-top-color:var(--aqua);border-right-color:var(--foam);opacity:0;}
.stage.running .node{border-color:var(--aqua);color:var(--aqua);box-shadow:0 0 24px rgba(77,227,240,.45);}
.stage.running .node .swirl{opacity:1;animation:aqSpin 1s linear infinite;}
.stage.running .node .ring,.stage.active .node .ring{animation:aqRipple 2s ease-out infinite;}
.stage.active .node{border-color:var(--sand);color:var(--sand);box-shadow:0 0 24px rgba(255,210,122,.4);}
.stage.active .node .ring{border-color:var(--sand);}
.stage.active.human .node{border-color:var(--lilac);color:var(--lilac);box-shadow:0 0 24px rgba(155,180,255,.45);} .stage.active.human .node .ring{border-color:var(--lilac);}
.stage.done .node{background:radial-gradient(circle at 35% 28%,#d6f7fb,#4de3f0 45%,#12a8b8);color:#02222f;border-color:var(--foam);box-shadow:0 0 22px rgba(77,227,240,.5);}
.stage.fresh .node{animation:aqPop .7s cubic-bezier(.2,1.4,.4,1);}
.stage.skipped .node{border-style:dashed;opacity:.5;} .stage.skipped{opacity:.7;}
.stage.blocked .node,.stage.error .node{border-color:var(--coral);color:var(--coral);box-shadow:0 0 20px rgba(255,123,114,.3);}
.stage.rejected .node{border-color:var(--orange);color:var(--orange);}
@keyframes aqSpin{to{transform:rotate(360deg)}}
@keyframes aqRipple{0%{transform:scale(1);opacity:.7}100%{transform:scale(1.9);opacity:0}}
@keyframes aqPop{0%{transform:scale(.6)}60%{transform:scale(1.18)}100%{transform:scale(1)}}
.sname{margin-top:12px;font-size:11px;font-weight:800;letter-spacing:1.6px;color:#eafcff;text-transform:uppercase;}
.sstate{margin-top:4px;font-size:11.5px;font-weight:700;color:var(--dim);}
.stage.running .sstate{color:var(--aqua);} .stage.done .sstate{color:var(--foam);} .stage.active .sstate{color:var(--sand);}
.stage.active.human .sstate{color:var(--lilac);} .stage.blocked .sstate,.stage.error .sstate{color:var(--coral);} .stage.rejected .sstate{color:var(--orange);}
.sdetail{margin-top:5px;font-size:11px;line-height:1.35;color:var(--muted);max-width:150px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;}
.stage.running .sstate::after{content:"";display:inline-block;width:14px;text-align:left;animation:aqDots 1.2s steps(4) infinite;}
@keyframes aqDots{0%{content:""}25%{content:"."}50%{content:".."}75%{content:"..."}}
.replan{margin-top:18px;padding-top:14px;border-top:1px dashed rgba(155,180,255,.35);display:flex;align-items:center;gap:12px;font-size:12.5px;color:#cfd9ff;}
.replan .node{width:34px;height:34px;font-size:14px;}
@media (max-width:820px){
  .river{flex-direction:column;gap:6px;}
  .stage{flex-direction:row;text-align:left;gap:14px;align-items:center;padding:6px 0;}
  .link{display:none;}
  .sname,.sstate,.sdetail{margin:0;max-width:none;}
  .stage .txt{display:flex;flex-direction:column;gap:3px;}
}

/* ---------- approval / tables / log ---------- */
.approval{border-color:rgba(155,180,255,.4);background:linear-gradient(150deg,rgba(40,60,130,.35),rgba(3,32,48,.85));}
.ai-rec{display:flex;gap:12px;align-items:flex-start;margin-top:14px;padding:13px 15px;border-radius:14px;background:rgba(77,227,240,.07);border:1px solid rgba(77,227,240,.25);font-size:13px;line-height:1.55;}
.ai-rec .badge{flex:none;font-size:10.5px;font-weight:800;letter-spacing:1px;padding:4px 10px;border-radius:99px;}
.badge.ok{color:#02222f;background:var(--foam);} .badge.no{color:#2a0a08;background:var(--coral);}
table.sup{width:100%;border-collapse:collapse;font-size:13px;}
table.sup th{font-size:10.5px;letter-spacing:1.2px;color:var(--muted);text-align:left;padding:8px 10px;text-transform:uppercase;border-bottom:1px solid var(--line);}
table.sup td{padding:11px 10px;border-bottom:1px solid rgba(120,225,240,.08);color:#e6fafd;}
table.sup tr.rec td{background:rgba(77,227,240,.09);} table.sup tr.rec td:first-child{box-shadow:inset 3px 0 0 var(--aqua);}
.pill{font-size:10.5px;font-weight:800;letter-spacing:.8px;padding:3px 9px;border-radius:99px;white-space:nowrap;}
.pill.rec{background:var(--aqua);color:#02222f;} .pill.el{background:rgba(143,245,224,.14);color:var(--foam);}
.pill.no{background:rgba(255,123,114,.12);color:var(--coral);} .pill.off{background:rgba(143,183,196,.14);color:var(--muted);}
.tablescroll{overflow-x:auto;}
.log{display:flex;flex-direction:column;gap:2px;max-height:330px;overflow-y:auto;}
.li{display:flex;gap:12px;align-items:baseline;padding:8px 4px;border-bottom:1px solid rgba(120,225,240,.07);font-size:12.5px;animation:aqRise .4s ease both;}
.li .t{color:var(--dim);font-variant-numeric:tabular-nums;flex:none;} .li .a{flex:none;min-width:104px;font-weight:800;color:var(--aqua);font-size:11px;letter-spacing:.6px;text-transform:uppercase;}
.li .m{color:#d6f2f7;} .li.warn .a{color:var(--sand);} .li.error .a{color:var(--coral);}
.banner{display:flex;gap:14px;align-items:flex-start;padding:15px 18px;border-radius:16px;margin:12px 0;font-size:13.5px;line-height:1.55;}
.banner.err{background:rgba(255,123,114,.1);border:1px solid rgba(255,123,114,.45);}
.banner.warn{background:rgba(255,210,122,.08);border:1px solid rgba(255,210,122,.35);}
.banner.ok{background:rgba(143,245,224,.08);border:1px solid rgba(143,245,224,.35);}
.banner .ic{flex:none;width:28px;height:28px;border-radius:50%;display:grid;place-items:center;font-weight:900;}
.banner.err .ic{background:var(--coral);color:#2a0a08;} .banner.warn .ic{background:var(--sand);color:#2b1d00;} .banner.ok .ic{background:var(--foam);color:#02222f;}
.banner b{color:#fff;}
.ready{display:flex;align-items:center;gap:20px;padding:26px;}
.ready .big-drop{width:54px;height:54px;border-radius:0 50% 50% 50%;transform:rotate(45deg);flex:none;background:linear-gradient(135deg,#d6f7fb,#12a8b8);box-shadow:0 0 34px rgba(77,227,240,.6);animation:aqBobD 3.4s ease-in-out infinite;}
.features{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin-top:14px;}
.fk{font-size:10.5px;letter-spacing:1.6px;font-weight:800;color:var(--aqua);} .ft{font-weight:800;font-size:15px;margin-top:8px;color:#f6feff;} .fx{font-size:12.5px;color:var(--muted);margin-top:6px;line-height:1.5;}
@media (prefers-reduced-motion:reduce){.aq *{animation:none !important;transition:none !important;}}
</style>
"""