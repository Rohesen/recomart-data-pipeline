"""Streamlit theme: a single glassmorphism theme (deep violet, frosted panels, 3D spheres)."""
# flake8: noqa
import streamlit as st



def apply():
    """Compute the active theme and inject its CSS (call once per script run)."""
    global THEMES, THEME_NAME, T, LIGHT, NAVY, TEAL, AMBER, RED, GREEN, GREY, MAGENTA, BG, PANEL, BORDER, MUTED, PLOT, SH, SH_HOVER
    _D = dict(mode="dark", lesson="#FDE9B0", good="#C8F5E2", bad="#FBD0D0", on_acc="#0B0F14", glow=False)
    _L = dict(mode="light", lesson="#7A5300", good="#065F46", bad="#9F1239", on_acc="#FFFFFF", glow=False)
    THEMES = {
        "Glass Violet": {**_D, **dict(bg="#160B33", side="#1A0D3C", panel="#241452", panel2="#1E1046", border="#4B2E8C",
                         acc="#A78BFA", acc2="#7DD3FC", acc_rgb="167,139,250", h1="#241452", h2="#2E1A63",
                         text="#EEE9FF", head="#FFFFFF", sub="#C4B5FD", muted="#B3A6D9", glow=True)},
    }
    THEME_NAME = "Glass Violet"   # single theme: deep violet with glassmorphism panels and 3D spheres
    T = THEMES[THEME_NAME]
    LIGHT = T["mode"] == "light"

    NAVY, TEAL = T["text"], T["acc"]
    AMBER, RED, GREEN, GREY = ("#D97706", "#DC2626", "#059669", "#7C3AED") if LIGHT else ("#FBBF24", "#F87171", "#34D399", "#A78BFA")
    if T["glow"]:
        AMBER, RED, GREEN, GREY = "#FCD34D", "#FB7185", "#5EEAD4", "#A5B4FC"
    if THEME_NAME == "Light · Paper":   # muted, print-friendly data colours
        AMBER, RED, GREEN, GREY = "#B45309", "#B91C1C", "#3F6212", "#A8A29E"
    MAGENTA = "#9A3412" if THEME_NAME == "Light · Paper" else "#C026D3" if LIGHT else ("#818CF8" if T["glow"] else "#C084FC")
    BG, PANEL, BORDER, MUTED = T["bg"], T["panel"], T["border"], T["muted"]
    PLOT = dict(template="plotly_white" if LIGHT else "plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor=T["panel2"], font=dict(family="Inter, Segoe UI, sans-serif", color=NAVY, size=13),
                title_font=dict(family="Source Serif 4, Georgia, serif", size=17),
                margin=dict(l=10, r=10, t=48, b=10))
    if T["glow"]:
        PLOT["colorway"] = ["#A78BFA", "#7DD3FC", "#FB7185", "#86EFAC", "#FDE68A", "#C084FC"]
        PLOT["plot_bgcolor"] = "rgba(255,255,255,.04)"

    SH = ("0 1px 2px rgba(15,23,42,.06), 0 10px 24px -12px rgba(15,23,42,.18)" if LIGHT else
          "0 1px 0 rgba(255,255,255,.04) inset, 0 10px 22px -10px rgba(0,0,0,.7), 0 2px 4px rgba(0,0,0,.3)")
    SH_HOVER = ("0 18px 30px -14px rgba(15,23,42,.28)" if LIGHT else "0 22px 34px -14px rgba(0,0,0,.8)")
    _css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,500;8..60,600;8..60,700&family=JetBrains+Mono:wght@400;500&display=swap');
    :root {--bg:%(bg)s; --side:%(side)s; --panel:%(panel)s; --panel2:%(panel2)s; --border:%(border)s; --acc:%(acc)s;
           --acc2:%(acc2)s; --acc-rgb:%(acc_rgb)s; --h1:%(h1)s; --h2:%(h2)s; --text:%(text)s; --head:%(head)s;
           --sub:%(sub)s; --muted:%(muted)s; --lesson:%(lesson)s; --good:%(good)s; --bad:%(bad)s; --on-acc:%(on_acc)s;}
    html, body, [class*="css"], .stMarkdown, p, label, li, input, textarea, button {font-family:'Inter', 'Segoe UI', sans-serif;}
    .stApp {background: radial-gradient(1100px 520px at 0%% -10%%, rgba(var(--acc-rgb),.08), transparent 60%%),
                        radial-gradient(900px 480px at 100%% 0%%, rgba(var(--acc-rgb),.05), transparent 55%%), var(--bg);
            color:var(--text);}
    .stApp p, .stApp li, .stApp label, .stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stCaptionContainer"],
    .stApp [data-baseweb="select"] div, .stApp [data-baseweb="select"] span, .stApp input, .stApp [data-testid="stSliderTickBarMin"],
    .stApp [data-testid="stSliderTickBarMax"], .stApp [data-testid="stSliderThumbValue"],
    .stApp [data-testid="stExpander"] summary, .stApp [data-testid="stWidgetLabel"] {color:var(--text);}
    .stApp [data-testid="stCaptionContainer"] {color:var(--muted);}
    header[data-testid="stHeader"] {background:transparent;}
    .block-container {padding-top: 1.6rem; max-width: 1360px;}
    h1, h2, h3 {font-family:'Source Serif 4', Georgia, serif !important; font-weight:600 !important; letter-spacing:0;}
    h2 {color:var(--head) !important; font-size:1.75rem !important;}
    h3 {color:var(--sub) !important; font-size:1.3rem !important;}
    section[data-testid="stSidebar"] {background:var(--side); border-right:1px solid var(--border);}
    section[data-testid="stSidebar"] h3 {font-size:1.15rem !important;}
    .stApp div[data-baseweb="select"] div, section[data-testid="stSidebar"] div[data-baseweb="select"] div,
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, .stNumberInput input, .stTextInput input,
    div[data-baseweb="base-input"], div[data-baseweb="popover"] ul, div[data-baseweb="popover"] li,
    div[data-baseweb="calendar"] {background:var(--panel) !important; border-color:var(--border) !important; color:var(--text);}
    .stApp [data-testid="stSelectbox"] div[role], .stApp [data-testid="stMultiSelect"] div[role],
    .stApp [data-testid="stDateInput"] div[data-rac], .stApp [data-testid="stNumberInput"] div[data-rac],
    .stApp [data-testid="stTextInput"] div[data-rac], .stApp [data-testid="stNumberInput"] input,
    .stApp [data-testid="stTextInput"] input, .stApp [data-testid="stDateInput"] input {
           background-color:var(--panel) !important; border-color:var(--border) !important; color:var(--text) !important;}
    .stApp [data-testid="stDateInput"] div, .stApp [data-testid="stNumberInput"] div,
    .stApp [data-testid="stNumberInput"] button, .stApp [data-testid="stTextInput"] div {
           background-color:var(--panel) !important; color:var(--text) !important; border-color:var(--border) !important;}
    .stApp [data-testid="stSelectbox"] svg, .stApp [data-testid="stDateInput"] svg {color:var(--muted); fill:currentColor;}
    [role="listbox"], [role="option"], [role="dialog"], div[data-rac][role="grid"] {background-color:var(--panel) !important;
           color:var(--text) !important;}
    [role="option"]:hover, [role="option"][data-focused], [role="option"][aria-selected="true"] {
           background-color:rgba(var(--acc-rgb),.14) !important;}
    /* ---- 3D depth ---- */
    .hero {padding:28px 34px; border-radius:18px; margin-bottom:24px;
           background: linear-gradient(120deg, var(--h1) 0%%, var(--h2) 100%%);
           border:1px solid var(--border); border-top:3px solid var(--acc);
           box-shadow: %(sh)s; transform: perspective(1400px) rotateX(1.2deg); transform-origin: top center;}
    .hero h1 {font-family:'Source Serif 4', Georgia, serif; font-weight:700; font-size:2.1rem; margin:0 0 8px 0; color:var(--head);}
    .hero p {color:var(--text); opacity:.88; margin:0; font-size:1.03rem; line-height:1.55;}
    .pill {display:inline-block; background:rgba(var(--acc-rgb),.10); border:1px solid rgba(var(--acc-rgb),.45);
           color:var(--sub); padding:3px 12px; border-radius:20px; font-size:.8rem; font-weight:500; margin:14px 6px 0 0;}
    .pill.m, .pill.g, .pill.y {background:rgba(var(--acc-rgb),.04); border-color:var(--border); color:var(--text);}
    .card, .kpi {transform-style: preserve-3d; transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease;
           box-shadow: %(sh)s;}
    .card {background:linear-gradient(180deg, var(--panel) 0%%, var(--panel2) 100%%); border:1px solid var(--border);
           border-radius:14px; padding:16px 18px; height:100%%;}
    .card:hover, .kpi:hover {transform: perspective(900px) translateY(-4px) rotateX(3deg);
           border-color:var(--acc); box-shadow: %(shh)s, 0 0 0 1px rgba(var(--acc-rgb),.25);}
    .card h4 {font-family:'Source Serif 4', Georgia, serif; font-weight:600; margin:0 0 6px 0; color:var(--acc2); font-size:1.05rem;}
    .card p {margin:0; color:var(--text); opacity:.85; font-size:.92rem; line-height:1.5;}
    .kpi {background:linear-gradient(180deg, var(--panel) 0%%, var(--panel2) 100%%); border:1px solid var(--border);
          border-radius:14px; padding:14px 18px; border-left:3px solid var(--acc);}
    .kpi .v {font-family:'Inter', sans-serif; font-size:1.6rem; font-weight:700; color:var(--head); line-height:1.15;
             font-variant-numeric: tabular-nums;}
    .kpi .l {font-size:.74rem; color:var(--muted); text-transform:uppercase; letter-spacing:.07em; margin-top:4px; font-weight:500;}
    .owner {display:inline-block; font-size:.78rem; color:var(--sub); font-weight:600; letter-spacing:.04em;
            background:rgba(var(--acc-rgb),.10); border:1px solid rgba(var(--acc-rgb),.4); padding:3px 12px; border-radius:20px;
            margin-bottom:6px;}
    .lesson {background:rgba(251,191,36,.08); border:1px solid rgba(217,119,6,.30); border-left:4px solid #F59E0B;
             padding:12px 16px; border-radius:10px; color:var(--lesson); font-size:.94rem; line-height:1.55; margin:8px 0;}
    .good {background:rgba(16,185,129,.08); border:1px solid rgba(16,185,129,.30); border-left:4px solid #10B981;
           padding:12px 16px; border-radius:10px; color:var(--good); font-size:.94rem; line-height:1.55; margin:8px 0;}
    .bad {background:rgba(239,68,68,.08); border:1px solid rgba(239,68,68,.30); border-left:4px solid #EF4444;
          padding:12px 16px; border-radius:10px; color:var(--bad); font-size:.94rem; line-height:1.55; margin:8px 0;}
    .mono {font-family:'JetBrains Mono', ui-monospace, Menlo, monospace; font-size:.84rem; color:var(--acc2);}
    .tid {color:var(--acc); font-size:.8rem;} .tpart {color:var(--muted); font-size:.85rem;}
    div[data-testid="stTabs"] button p {font-family:'Inter', sans-serif; font-size:.95rem; font-weight:600;}
    div[data-testid="stTabs"] button[aria-selected="true"] p {color:var(--acc);}
    div[data-baseweb="tab-highlight"] {background:var(--acc) !important; height:3px;}
    .stButton > button, .stDownloadButton > button {border-radius:10px; border:1px solid var(--acc); color:var(--acc);
           background:rgba(var(--acc-rgb),.07); font-weight:600; box-shadow:0 3px 0 rgba(0,0,0,.25);
           transition: transform .15s ease, box-shadow .15s ease, background .2s ease;}
    .stButton > button p, .stDownloadButton > button p {color:inherit;}
    .stButton > button:hover, .stDownloadButton > button:hover {background:rgba(var(--acc-rgb),.16);
           transform: translateY(-1px); box-shadow:0 5px 0 rgba(0,0,0,.25);}
    .stButton > button:active {transform: translateY(2px); box-shadow:0 1px 0 rgba(0,0,0,.25);}
    .stButton > button[kind="primary"] {background:linear-gradient(180deg, rgba(var(--acc-rgb),.98), rgba(var(--acc-rgb),.80));
           color:var(--on-acc); border:1px solid var(--acc);}
    div[data-testid="stDataFrame"] {border:1px solid var(--border); border-radius:10px; box-shadow: %(sh)s;}
    div[data-testid="stExpander"] {border:1px solid var(--border); border-radius:10px; background:var(--panel2);}
    div[data-testid="stPlotlyChart"], div[data-testid="stGraphVizChart"] {background:var(--panel2); border:1px solid var(--border);
           border-radius:14px; padding:6px; box-shadow: %(sh)s;}
    </style>""" % {**T, "sh": SH, "shh": SH_HOVER}

    if LIGHT:   # tables are canvas-drawn in the app's dark base theme -> invert them for light pages
        _tbl_filter = "invert(1) hue-rotate(180deg) contrast(.92)" + (" saturate(0)" if THEME_NAME == "Light · Paper" else "")
        _css += """<style>
    div[data-testid="stDataFrame"] > div {filter: """ + _tbl_filter + """;}
    div[data-testid="stCode"] pre {border:1px solid var(--border);}
    </style>"""
    if THEME_NAME == "Light · Paper":   # strip the base theme's teal from canvas tables, sliders and toggles
        _css += """<style>
    [data-testid="stSlider"], [data-testid="stCheckbox"], .stToggle, [data-testid="stMultiSelect"] span {filter: grayscale(1);}
    </style>"""
    if T["glow"]:   # glassmorphism: deep violet, frosted panels, soft 3D spheres; text stays crisp
        _css += """<style>
    .stApp {background: linear-gradient(140deg, #120826 0%, #22104C 45%, #2B1160 70%, #170A35 100%) !important; background-attachment:fixed !important;}
    .stApp:before {content:""; position:fixed; inset:0; pointer-events:none; z-index:0;
           background:
             radial-gradient(circle closest-side at 36% 32%, rgba(255,255,255,.85), rgba(255,255,255,0) 60%) 104% -8% / 340px 340px no-repeat,
             radial-gradient(circle closest-side, #FDA4AF 0, #F43F5E 55%, #9F1239 96%, rgba(0,0,0,0) 100%) 104% -8% / 340px 340px no-repeat,
             radial-gradient(circle closest-side at 36% 32%, rgba(255,255,255,.85), rgba(255,255,255,0) 60%) 18.5% 64% / 190px 190px no-repeat,
             radial-gradient(circle closest-side, #DDD6FE 0, #8B5CF6 55%, #4C1D95 96%, rgba(0,0,0,0) 100%) 18.5% 64% / 190px 190px no-repeat,
             radial-gradient(circle closest-side at 36% 32%, rgba(255,255,255,.85), rgba(255,255,255,0) 60%) 64% 1.5% / 96px 96px no-repeat,
             radial-gradient(circle closest-side, #FEF3C7 0, #FCD34D 55%, #B45309 96%, rgba(0,0,0,0) 100%) 64% 1.5% / 96px 96px no-repeat,
             radial-gradient(circle closest-side at 36% 32%, rgba(255,255,255,.85), rgba(255,255,255,0) 60%) 24% 112% / 200px 200px no-repeat,
             radial-gradient(circle closest-side, #BBF7D0 0, #22C55E 55%, #14532D 96%, rgba(0,0,0,0) 100%) 24% 112% / 200px 200px no-repeat,
             radial-gradient(circle closest-side at 36% 32%, rgba(255,255,255,.85), rgba(255,255,255,0) 60%) 103% 94% / 260px 260px no-repeat,
             radial-gradient(circle closest-side, #BAE6FD 0, #3B82F6 55%, #1E3A8A 96%, rgba(0,0,0,0) 100%) 103% 94% / 260px 260px no-repeat,
             radial-gradient(800px 500px at 15% 0%, rgba(167,139,250,.22), transparent 60%),
             radial-gradient(700px 500px at 100% 100%, rgba(125,211,252,.12), transparent 60%);
           opacity:.75;}
    .block-container {position:relative; z-index:1;}
    section[data-testid="stSidebar"] {background: rgba(30,14,66,.55) !important; backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
           border-right:1px solid rgba(255,255,255,.14);}
    section[data-testid="stSidebar"] h3 {color:#C4B5FD !important;}
    .tid {color:#7DD3FC !important;}
    .hero, .card, .kpi, div[data-testid="stPlotlyChart"], div[data-testid="stGraphVizChart"], div[data-testid="stDataFrame"],
    div[data-testid="stExpander"], .lesson, .good {
           background: linear-gradient(135deg, rgba(255,255,255,.12), rgba(255,255,255,.04)) !important;
           backdrop-filter: blur(16px) saturate(140%); -webkit-backdrop-filter: blur(16px) saturate(140%);
           border:1px solid rgba(255,255,255,.20) !important; border-top-color: rgba(255,255,255,.35) !important;
           box-shadow: 0 8px 32px rgba(10,4,30,.45) !important; transform:none !important;}
    .hero {border-radius:24px; position:relative; overflow:hidden;}
    .hero:before {content:""; position:absolute; left:0; right:0; top:0; height:3px;
           background:linear-gradient(90deg,#A78BFA,#7DD3FC,#86EFAC,#FDE68A,#FB7185,#A78BFA); background-size:300% 100%;
           animation:flow 9s linear infinite;}
    @keyframes flow {0%{background-position:0% 0} 100%{background-position:300% 0}}
    .hero h1 {color:#7DD3FC !important; text-shadow:none !important;}
    .hero h1 a, h1 a, h2 a, h3 a, [data-testid="stHeaderActionElements"] {display:none !important;}
    .hero p {color:#E4DCFF !important; opacity:1 !important;}
    h2 {color:#FFFFFF !important; text-shadow:none !important;} h3 {color:#C4B5FD !important; text-shadow:none !important;}
    .pill {border:1px solid rgba(255,255,255,.30) !important; background:rgba(255,255,255,.10) !important; color:#FFFFFF !important; box-shadow:none;}
    .pill:nth-of-type(1) {border-color:#A78BFA !important;} .pill.m {border-color:#7DD3FC !important;}
    .pill.g {border-color:#86EFAC !important;} .pill.y {border-color:#FB7185 !important;}
    .kpi {border-radius:18px; border-top:2px solid #A78BFA !important;}
    .kpi:nth-child(6n+2) {border-top-color:#7DD3FC !important;} .kpi:nth-child(6n+3) {border-top-color:#86EFAC !important;}
    .kpi:nth-child(6n+4) {border-top-color:#FDE68A !important;} .kpi:nth-child(6n+5) {border-top-color:#FB7185 !important;}
    .kpi .v {color:#FFFFFF !important; text-shadow:none !important;}
    .kpi .l {color:#C4B5FD !important;}
    .card {border-radius:18px;} .card h4 {color:#7DD3FC !important; text-shadow:none !important;}
    .card:hover, .kpi:hover {border-color:rgba(196,181,253,.7) !important; box-shadow:0 12px 36px rgba(139,92,246,.35) !important;}
    .owner {border:1px solid #A78BFA !important; background:rgba(167,139,250,.15) !important; color:#EDE9FE !important; box-shadow:none;}
    div[data-testid="stTabs"] button[aria-selected="true"] p {color:#FFFFFF !important; text-shadow:none !important;}
    div[data-baseweb="tab-highlight"] {background:linear-gradient(90deg,#A78BFA,#7DD3FC) !important; box-shadow:none;}
    .stButton > button, .stDownloadButton > button {border:1px solid rgba(196,181,253,.6) !important; color:#EDE9FE !important;
           background:rgba(255,255,255,.08) !important; box-shadow:none;}
    .stButton > button[kind="primary"] {background:linear-gradient(90deg,#8B5CF6,#60A5FA) !important; color:#FFFFFF !important; border:none !important;
           box-shadow:0 6px 20px rgba(139,92,246,.45) !important;}
    .lesson {border-left:4px solid #A78BFA !important; color:#EDE9FE !important;}
    .lesson b, .lesson strong {color:#7DD3FC;}
    .good {border-left:4px solid #86EFAC !important; color:#DCFCE7 !important;}
    .bad {border-left-color:#FB7185 !important;}
    div[data-testid="stCode"] pre {background:rgba(15,6,38,.75) !important; border:1px solid rgba(255,255,255,.15);}
    .mono {color:#7DD3FC;}
    hr {border-color:rgba(255,255,255,.15) !important;}
    ::-webkit-scrollbar {width:10px; height:10px;}
    ::-webkit-scrollbar-track {background:#160B33;}
    ::-webkit-scrollbar-thumb {background:linear-gradient(180deg,#A78BFA,#7DD3FC); border-radius:10px;}
    ::selection {background:rgba(167,139,250,.45); color:#fff;}
    </style>"""
    st.markdown(_css, unsafe_allow_html=True)

    from streamlit.delta_generator import DeltaGenerator  # noqa: E402

    if not getattr(DeltaGenerator.plotly_chart, "_themed", False):
        _orig_plotly_chart = DeltaGenerator.plotly_chart

        def _themed_plotly_chart(self, fig, *args, **kwargs):
            """Use our own Plotly template instead of Streamlit's (which follows the app's dark base)."""
            kwargs.setdefault("theme", None)
            return _orig_plotly_chart(self, fig, *args, **kwargs)

        _themed_plotly_chart._themed = True
        DeltaGenerator.plotly_chart = _themed_plotly_chart

    # `st.plotly_chart` is bound to the main container at import time, so patch it too
    st.plotly_chart = lambda fig, *a, **k: DeltaGenerator.plotly_chart(st._main, fig, *a, **k)



def gv(dot: str, **kw):
    """Graphviz with theme colors swapped in."""
    for a, b in {"#111A2E": T["panel"], "#2B3D63": T["border"], "#1C2340": T["h2"], "#38BDF8": T["acc"],
                 "#E8EEF7": T["text"], "#7DD3FC": T["acc2"], "#B6C2D6": T["muted"], "#64748B": T["muted"],
                 "#C084FC": MAGENTA, "#34D399": GREEN, "#FBBF24": (T["acc2"] if T["glow"] else AMBER)}.items():
        dot = dot.replace(a, b)
    # natural size: a 'stretch' graph inside a hidden tab is measured at 0 px and renders blank
    kw.pop("width", None)
    st.graphviz_chart(dot, width="content")


