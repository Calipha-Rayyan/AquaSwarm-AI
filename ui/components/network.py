from __future__ import annotations


AGENTS = [
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
    nodes = []

    for i, (name, x, y, color) in enumerate(AGENTS):
        delay = i * 0.35
        tag = ""
        if name == "Approval":
            tag = (
                f'<text x="{x}" y="{y - 38}" class="tag">'
                "HUMAN IN THE LOOP"
                "</text>"
            )

        nodes.append(
            f"""
            <g transform="translate({x},{y})">
              <circle r="26" class="ring"
                      style="stroke:{color};animation-delay:{delay}s"/>
              <circle r="26" class="node" style="stroke:{color}"/>
              <circle r="3" fill="{color}" class="core"
                      style="animation-delay:{delay}s"/>
              <text y="-34" class="num">{i + 1:02d}</text>
              <text y="48" class="name">{name.upper()}</text>
            </g>{tag}
            """
        )

    node_markup = "".join(nodes)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        html,body{{margin:0;background:transparent;
        font-family:Inter,'Segoe UI',system-ui,sans-serif;overflow:hidden}}
        svg{{width:100%;height:100%;display:block}}
        .edge{{stroke:rgba(90,170,230,.16);stroke-width:2;fill:none}}
        .flow{{stroke:#43c8ff;stroke-width:2;fill:none;stroke-dasharray:6 10;
        animation:dash 1.6s linear infinite;opacity:.75}}
        .back{{stroke:#8b7bff;stroke-width:1.6;fill:none;stroke-dasharray:3 9;
        animation:dash 2.2s linear infinite reverse;opacity:.7}}
        @keyframes dash{{to{{stroke-dashoffset:-32}}}}
        .node{{fill:#08182a;stroke-width:1.6;filter:url(#glow)}}
        .ring{{fill:none;stroke-width:1;transform-box:fill-box;
        transform-origin:center;animation:ring 3.2s ease-out infinite}}
        @keyframes ring{{from{{transform:scale(1);opacity:.55}}
        to{{transform:scale(1.9);opacity:0}}}}
        .core{{animation:core 2.8s ease-in-out infinite}}
        @keyframes core{{50%{{opacity:.3}}}}
        .name{{fill:#cfe2f1;font-size:10.5px;font-weight:700;
        letter-spacing:1.6px;text-anchor:middle}}
        .num{{fill:#4f6a82;font-size:9px;font-weight:700;
        letter-spacing:1px;text-anchor:middle}}
        .tag{{fill:#a89cff;font-size:8.5px;font-weight:700;
        letter-spacing:1.6px;text-anchor:middle}}
        .loop{{fill:#6f86a0;font-size:8.5px;font-weight:700;letter-spacing:1.6px}}
        @media (prefers-reduced-motion:reduce){{*{{animation:none!important}}
        .packet{{display:none}}}}
      </style>
    </head>
    <body>
      <svg viewBox="0 0 720 300" preserveAspectRatio="xMidYMid meet"
           xmlns="http://www.w3.org/2000/svg">
        <defs>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="b"/>
            <feMerge>
              <feMergeNode in="b"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>
        <path d="M90,80 H630 V220 H90" class="edge"/>
        <path d="M90,80 H630 V220 H90" class="flow"/>
        <path d="M90,220 V80" class="edge"/>
        <path d="M90,220 V80" class="back"/>
        <text x="102" y="154" class="loop">REPLAN LOOP</text>
        {node_markup}
        <circle r="4" fill="#bff3ff" filter="url(#glow)" class="packet">
          <animateMotion dur="11s" repeatCount="indefinite"
                         path="M90,80 H630 V220 H90 V80"/>
        </circle>
        <circle r="3.5" fill="#c9c2ff" filter="url(#glow)" class="packet">
          <animateMotion dur="11s" begin="-5.5s" repeatCount="indefinite"
                         path="M90,80 H630 V220 H90 V80"/>
        </circle>
      </svg>
    </body>
    </html>
    """
