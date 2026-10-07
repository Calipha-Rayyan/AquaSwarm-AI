from __future__ import annotations

# name, x, y, colour
AGENTS = [
    ("Demand", 90, 80, "#4de3f0"),
    ("Anomaly", 270, 80, "#4de3f0"),
    ("Supply", 450, 80, "#4de3f0"),
    ("Allocation", 630, 80, "#4de3f0"),
    ("Approval", 630, 220, "#9bb4ff"),
    ("Delivery", 450, 220, "#4de3f0"),
    ("Verification", 270, 220, "#8ff5e0"),
    ("Replanning", 90, 220, "#4de3f0"),
]

_RIVER = "M90,80 H600 Q630,80 630,110 V190 Q630,220 600,220 H90"
_LOOP = "M90,80 H600 Q630,80 630,110 V190 Q630,220 600,220 H90 V80"


def build_network_svg() -> str:
    """The eight agents as pools along one flowing river."""
    nodes = []
    for i, (name, x, y, color) in enumerate(AGENTS):
        delay = i * 0.4
        tag = ""
        if name == "Approval":
            tag = (
                f'<text x="{x}" y="{y - 40}" class="tag">HUMAN IN THE LOOP</text>'
            )
        nodes.append(
            f"""
            <g transform="translate({x},{y})">
              <circle r="26" class="ring" style="stroke:{color};animation-delay:{delay}s"/>
              <circle r="26" class="ring" style="stroke:{color};animation-delay:{delay + 1.6}s"/>
              <circle r="26" class="node" style="stroke:{color}"/>
              <circle r="4" fill="{color}" class="core" style="animation-delay:{delay}s"/>
              <text y="-35" class="num">{i + 1:02d}</text>
              <text y="49" class="name">{name.upper()}</text>
            </g>{tag}
            """
        )
    node_markup = "".join(nodes)

    return f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><style>
      html,body{{margin:0;background:transparent;font-family:Inter,'Segoe UI',system-ui,sans-serif;overflow:hidden}}
      svg{{width:100%;height:100%;display:block}}
      .bed{{stroke:rgba(18,168,184,.16);stroke-width:16;fill:none;stroke-linecap:round;stroke-linejoin:round}}
      .edge{{stroke:rgba(77,227,240,.28);stroke-width:2;fill:none}}
      .flow{{stroke:url(#stream);stroke-width:3;fill:none;stroke-dasharray:10 12;stroke-linecap:round;
             animation:dash 1.8s linear infinite;opacity:.9}}
      .back{{stroke:#9bb4ff;stroke-width:1.8;fill:none;stroke-dasharray:3 9;animation:dash 2.4s linear infinite reverse;opacity:.7}}
      @keyframes dash{{to{{stroke-dashoffset:-44}}}}
      .node{{fill:#042235;stroke-width:1.8;filter:url(#glow)}}
      .ring{{fill:none;stroke-width:1;transform-box:fill-box;transform-origin:center;animation:ring 3.4s ease-out infinite}}
      @keyframes ring{{from{{transform:scale(1);opacity:.6}}to{{transform:scale(2);opacity:0}}}}
      .core{{animation:core 2.8s ease-in-out infinite}}
      @keyframes core{{50%{{opacity:.3}}}}
      .name{{fill:#d6f7fb;font-size:10.5px;font-weight:700;letter-spacing:1.6px;text-anchor:middle}}
      .num{{fill:#5f8f9e;font-size:9px;font-weight:700;letter-spacing:1px;text-anchor:middle}}
      .tag{{fill:#b8c8ff;font-size:8.5px;font-weight:700;letter-spacing:1.6px;text-anchor:middle}}
      .loop{{fill:#7fb0be;font-size:8.5px;font-weight:700;letter-spacing:1.6px}}
      @media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.packet{{display:none}}}}
    </style></head><body>
      <svg viewBox="0 0 720 300" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="stream" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0" stop-color="#12a8b8"/><stop offset=".5" stop-color="#4de3f0"/><stop offset="1" stop-color="#8ff5e0"/>
          </linearGradient>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="b"/>
            <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>
        <path d="{_RIVER}" class="bed"/>
        <path d="{_RIVER}" class="edge"/>
        <path d="{_RIVER}" class="flow"/>
        <path d="M90,220 V80" class="edge"/>
        <path d="M90,220 V80" class="back"/>
        <text x="102" y="154" class="loop">REPLAN LOOP</text>
        {node_markup}
        <circle r="4.5" fill="#d6f7fb" filter="url(#glow)" class="packet">
          <animateMotion dur="12s" repeatCount="indefinite" path="{_LOOP}"/>
        </circle>
        <circle r="3.5" fill="#8ff5e0" filter="url(#glow)" class="packet">
          <animateMotion dur="12s" begin="-6s" repeatCount="indefinite" path="{_LOOP}"/>
        </circle>
      </svg>
    </body></html>
    """