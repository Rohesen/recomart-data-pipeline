"""Streamlit theme: a single dark theme with sky-blue neon accents."""
# flake8: noqa
import streamlit as st



def apply():
    """Compute the active theme and inject its CSS (call once per script run)."""
    global THEMES, THEME_NAME, T, LIGHT, NAVY, TEAL, AMBER, RED, GREEN, GREY, MAGENTA, BG, PANEL, BORDER, MUTED, PLOT, SH, SH_HOVER
    _D = dict(mode="dark", lesson="#FDE9B0", good="#C8F5E2", bad="#FBD0D0", on_acc="#0B0F14", glow=False)
    _L = dict(mode="light", lesson="#7A5300", good="#065F46", bad="#9F1239", on_acc="#FFFFFF", glow=False)
    THEMES = {
        "Sky Neon": {**_D, **dict(bg="#050A14", side="#07101F", panel="#0B1526", panel2="#09121F", border="#1A3350",
                         acc="#38BDF8", acc2="#7DD3FC", acc_rgb="56,189,248", h1="#0A1A2E", h2="#0E2A44",
                         text="#E6F3FF", head="#FFFFFF", sub="#7DD3FC", muted="#8CA3BF", glow=True)},
    }
    THEME_NAME = "Sky Neon"   # single theme: dark background with sky-blue neon
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
        PLOT["colorway"] = ["#38BDF8", "#5EEAD4", "#A5B4FC", "#7DD3FC", "#FCD34D", "#FB7185"]
        PLOT["plot_bgcolor"] = "rgba(9,18,31,.6)"

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
    if T["glow"]:   # crisp sky-blue neon: glow on borders and lines only, text stays sharp (no haze)
        _css += """<style>
    .stApp {background: radial-gradient(900px 420px at 0% -10%, rgba(56,189,248,.07), transparent 60%), #050A14 !important;}
    .stApp:before {content:""; position:fixed; inset:0; pointer-events:none; z-index:0;
           background-image: linear-gradient(rgba(56,189,248,.035) 1px, transparent 1px),
                             linear-gradient(90deg, rgba(56,189,248,.035) 1px, transparent 1px);
           background-size: 44px 44px;
           mask-image: radial-gradient(1200px 700px at 50% 0%, #000 30%, transparent 85%);
           -webkit-mask-image: radial-gradient(1200px 700px at 50% 0%, #000 30%, transparent 85%);}
    .block-container {position:relative; z-index:1;}
    section[data-testid="stSidebar"] {background:#060D1A !important; border-right:1px solid rgba(56,189,248,.35);}
    section[data-testid="stSidebar"] h3 {color:#38BDF8 !important;}
    .hero {background:#0A1628 !important; border:1px solid #1E5A85 !important; border-radius:20px;
           box-shadow: 0 0 0 1px rgba(56,189,248,.15), 0 0 22px rgba(56,189,248,.18) !important;
           position:relative; overflow:hidden; transform:none !important;}
    .hero:before {content:""; position:absolute; left:0; right:0; top:0; height:3px;
           background:linear-gradient(90deg,#0EA5E9,#7DD3FC,#E0F2FE,#38BDF8,#0EA5E9); background-size:300% 100%;
           animation:flow 7s linear infinite;}
    @keyframes flow {0%{background-position:0% 0} 100%{background-position:300% 0}}
    .hero h1 {color:#FFFFFF !important; text-shadow:none !important;}
    .hero h1 a, h1 a, h2 a, h3 a, [data-testid="stHeaderActionElements"] {display:none !important;}
    .hero p {color:#C9D7E8 !important; opacity:1 !important;}
    h2 {color:#F0F9FF !important; text-shadow:none !important;} h3 {color:#7DD3FC !important; text-shadow:none !important;}
    .pill, .pill.m, .pill.g, .pill.y {border:1px solid #38BDF8 !important; color:#BAE6FD !important;
           background:rgba(56,189,248,.06) !important; box-shadow:0 0 8px rgba(56,189,248,.30);}
    .card, .kpi {background:#0A1628 !important; border:1px solid #17406A !important; transform:none !important;}
    .kpi {border-top:2px solid #38BDF8 !important; border-radius:16px; box-shadow:0 0 12px rgba(56,189,248,.12) !important;}
    .kpi .v {color:#FFFFFF !important; text-shadow:none !important;}
    .kpi .l {color:#7DD3FC !important;}
    .card h4 {color:#7DD3FC !important; text-shadow:none !important;}
    .card:hover, .kpi:hover {border-color:#38BDF8 !important; box-shadow:0 0 18px rgba(56,189,248,.35) !important;}
    .owner {border:1px solid #38BDF8 !important; color:#BAE6FD !important; box-shadow:0 0 8px rgba(56,189,248,.30);}
    div[data-testid="stTabs"] [data-baseweb="tab-list"] {gap:6px; background:#081426; padding:6px;
           border:1px solid #17406A; border-radius:14px;}
    div[data-testid="stTabs"] button[role="tab"] {border-radius:10px; padding:8px 16px;}
    div[data-testid="stTabs"] button[role="tab"]:hover {background:rgba(56,189,248,.08);}
    div[data-testid="stTabs"] button[aria-selected="true"] {background:#0E2A44; box-shadow: inset 0 0 0 1px #38BDF8, 0 0 12px rgba(56,189,248,.35);}
    div[data-testid="stTabs"] button[aria-selected="true"] p {color:#FFFFFF !important; text-shadow:none !important;}
    div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] {display:none;}
    .stButton > button[kind="primary"] {background:#38BDF8; color:#04121F; font-weight:600; border:none;
           box-shadow:0 0 14px rgba(56,189,248,.45);}
    .stButton > button:hover, .stDownloadButton > button:hover {box-shadow:0 0 14px rgba(56,189,248,.5); border-color:#38BDF8;}
    .lesson {background:#0A1A2E !important; border:1px solid #17406A !important; border-left:4px solid #38BDF8 !important;
           color:#D6EEFF !important;}
    .lesson b, .lesson strong {color:#7DD3FC;}
    .good {background:#08201F !important; border-left-color:#5EEAD4 !important; color:#CCFBF1 !important;}
    div[data-testid="stPlotlyChart"], div[data-testid="stGraphVizChart"], div[data-testid="stDataFrame"],
    div[data-testid="stExpander"] {background:#09121F !important; border:1px solid #17406A !important; box-shadow:none !important;}
    div[data-testid="stCode"] pre {background:#06101E !important; border:1px solid #17406A;}
    hr {border-color:#17406A !important;}
    ::-webkit-scrollbar {width:10px; height:10px;}
    ::-webkit-scrollbar-track {background:#050A14;}
    ::-webkit-scrollbar-thumb {background:#1E5A85; border-radius:10px;}
    ::selection {background:rgba(56,189,248,.35); color:#fff;}
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


