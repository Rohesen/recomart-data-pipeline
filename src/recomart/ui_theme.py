"""Shared Streamlit theme system (9 themes: dark, neon and light; default Light · Paper)."""
# flake8: noqa
import streamlit as st



def apply():
    """Compute the active theme and inject its CSS (call once per script run)."""
    global THEMES, THEME_NAME, T, LIGHT, NAVY, TEAL, AMBER, RED, GREEN, GREY, MAGENTA, BG, PANEL, BORDER, MUTED, PLOT, SH, SH_HOVER
    _D = dict(mode="dark", lesson="#FDE9B0", good="#C8F5E2", bad="#FBD0D0", on_acc="#0B0F14", glow=False)
    _L = dict(mode="light", lesson="#7A5300", good="#065F46", bad="#9F1239", on_acc="#FFFFFF", glow=False)
    THEMES = {
        "Deep Ocean":      {**_D, **dict(bg="#06181D", side="#081F25", panel="#0C2830", panel2="#0A222A", border="#1B4550",
                               acc="#2DD4BF", acc2="#7DD3FC", acc_rgb="45,212,191", h1="#0C2A33", h2="#124350",
                               text="#E6F2F2", head="#F4FBFB", sub="#99F6E4", muted="#8FB3B8")},
        "Neon Glow":       {**_D, **dict(bg="#070B14", side="#0A0F1C", panel="#0E1424", panel2="#0B1120", border="#1E2A44",
                               acc="#00F0FF", acc2="#FF2BD6", acc_rgb="0,240,255", h1="#1A0F2E", h2="#0B2A3A",
                               text="#E6F1FF", head="#FFFFFF", sub="#7DF9FF", muted="#8892B0", glow=True)},
        "Midnight Navy":   {**_D, **dict(bg="#0B1220", side="#0E172A", panel="#111A2E", panel2="#0F1829", border="#22304D",
                               acc="#38BDF8", acc2="#A5B4FC", acc_rgb="56,189,248", h1="#13203A", h2="#1C2F52",
                               text="#E8EEF7", head="#F1F5FB", sub="#BFDBFE", muted="#94A3B8")},
        "Royal Plum":      {**_D, **dict(bg="#130B1D", side="#170E25", panel="#1D1430", panel2="#1A1129", border="#3A2858",
                               acc="#C084FC", acc2="#F0ABFC", acc_rgb="192,132,252", h1="#22153A", h2="#352058",
                               text="#F1EAFB", head="#FAF5FF", sub="#E9D5FF", muted="#A99BC0")},
        "Graphite & Gold": {**_D, **dict(bg="#111214", side="#15161A", panel="#1B1D22", panel2="#18191D", border="#30333B",
                               acc="#E2B55A", acc2="#F5D58A", acc_rgb="226,181,90", h1="#1D1F25", h2="#2C2F37",
                               text="#ECEAE4", head="#FAF8F2", sub="#F5DFA8", muted="#A3A09A")},
        "Emerald":         {**_D, **dict(bg="#06150E", side="#081B12", panel="#0D2419", panel2="#0B2016", border="#1D4430",
                               acc="#34D399", acc2="#A7F3D0", acc_rgb="52,211,153", h1="#0D2A1C", h2="#14432D",
                               text="#E6F4EC", head="#F3FBF6", sub="#BBF7D0", muted="#8DB09C")},
        "Light · Paper":   {**_L, **dict(bg="#FAFAF7", side="#F2F1EC", panel="#FFFFFF", panel2="#FBFBF8", border="#D6D3CC",
                               acc="#3F3F46", acc2="#18181B", acc_rgb="63,63,70", h1="#FFFFFF", h2="#F1EFEA",
                               text="#1C1917", head="#0C0A09", sub="#27272A", muted="#71717A")},
        "Light · Classic": {**_L, **dict(bg="#F5F7FB", side="#EEF2F8", panel="#FFFFFF", panel2="#F8FAFD", border="#D9E1EC",
                               acc="#1D4ED8", acc2="#1E40AF", acc_rgb="29,78,216", h1="#FFFFFF", h2="#E8EFFC",
                               text="#1E293B", head="#0F172A", sub="#1E3A8A", muted="#64748B")},
        "Light · Ivory":   {**_L, **dict(bg="#FAF7F0", side="#F3EEE2", panel="#FFFDF8", panel2="#FBF8F1", border="#E4DCC8",
                               acc="#9A6B12", acc2="#1E3A5F", acc_rgb="154,107,18", h1="#FFFDF8", h2="#F4EBD6",
                               text="#2B2A26", head="#1C1B18", sub="#1E3A5F", muted="#7A7466")},
        "Light · Sky":     {**_L, **dict(bg="#F1F8FC", side="#E6F2F9", panel="#FFFFFF", panel2="#F6FBFE", border="#CFE3EE",
                               acc="#0369A1", acc2="#0E7490", acc_rgb="3,105,161", h1="#FFFFFF", h2="#DCEFF9",
                               text="#0F2A3A", head="#0B1F2C", sub="#075985", muted="#5B7486")},
    }
    st.session_state.setdefault("theme", "Light · Paper")
    THEME_NAME = st.session_state["theme"]
    T = THEMES.get(THEME_NAME, THEMES["Deep Ocean"])
    LIGHT = T["mode"] == "light"

    NAVY, TEAL = T["text"], T["acc"]
    AMBER, RED, GREEN, GREY = ("#D97706", "#DC2626", "#059669", "#7C3AED") if LIGHT else ("#FBBF24", "#F87171", "#34D399", "#A78BFA")
    if THEME_NAME == "Neon Glow":
        AMBER, RED, GREEN, GREY = "#FFC300", "#FF3B6B", "#39FF88", "#B26BFF"
    if THEME_NAME == "Light · Paper":   # muted, print-friendly data colours
        AMBER, RED, GREEN, GREY = "#B45309", "#B91C1C", "#3F6212", "#A8A29E"
    MAGENTA = "#9A3412" if THEME_NAME == "Light · Paper" else "#C026D3" if LIGHT else ("#FF2BD6" if T["glow"] else "#C084FC")
    BG, PANEL, BORDER, MUTED = T["bg"], T["panel"], T["border"], T["muted"]
    PLOT = dict(template="plotly_white" if LIGHT else "plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor=T["panel2"], font=dict(family="Inter, Segoe UI, sans-serif", color=NAVY, size=13),
                title_font=dict(family="Source Serif 4, Georgia, serif", size=17),
                margin=dict(l=10, r=10, t=48, b=10))

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
    if T["glow"]:   # neon: glows, animated rainbow edge, glowing numbers and cards
        _css += """<style>
    .hero {background: linear-gradient(115deg, rgba(255,43,214,.20), rgba(157,78,221,.16) 45%, rgba(0,240,255,.20));
           border:1px solid rgba(0,240,255,.45); box-shadow: 0 0 28px rgba(0,240,255,.25), inset 0 0 40px rgba(255,43,214,.10);
           position:relative; overflow:hidden; border-top:1px solid rgba(0,240,255,.45);}
    .hero:before {content:""; position:absolute; left:0; right:0; top:0; height:3px;
           background:linear-gradient(90deg,#FF2BD6,#00F0FF,#39FF88,#FF2BD6); background-size:300% 100%;
           animation:flow 8s linear infinite;}
    @keyframes flow {0%{background-position:0% 0} 100%{background-position:300% 0}}
    .hero h1 {text-shadow:0 0 10px #00F0FF, 0 0 26px rgba(255,43,214,.55);}
    h2 {text-shadow:0 0 18px rgba(0,240,255,.35);} h3 {text-shadow:0 0 12px rgba(0,240,255,.4);}
    .pill {box-shadow:0 0 10px rgba(0,240,255,.35); color:#7DF9FF;}
    .pill.m {border-color:#FF2BD6; color:#FF7BE5; box-shadow:0 0 10px rgba(255,43,214,.35);}
    .pill.g {border-color:#39FF88; color:#8CFFC0; box-shadow:0 0 10px rgba(57,255,136,.35);}
    .pill.y {border-color:#FFC300; color:#FFE07A; box-shadow:0 0 10px rgba(255,195,0,.35);}
    .kpi {border-top:2px solid #00F0FF; border-left:1px solid var(--border); box-shadow:0 0 16px rgba(0,240,255,.15);}
    .kpi:nth-child(odd) {border-top-color:#FF2BD6;}
    .kpi .v {text-shadow:0 0 12px rgba(0,240,255,.6);}
    .card h4 {text-shadow:0 0 8px rgba(255,43,214,.5);}
    .card:hover, .kpi:hover {border-color:#FF2BD6; box-shadow:0 0 24px rgba(255,43,214,.4);}
    .owner {box-shadow:0 0 12px rgba(0,240,255,.4);}
    div[data-baseweb="tab-highlight"] {background:linear-gradient(90deg,#FF2BD6,#00F0FF) !important; box-shadow:0 0 12px #00F0FF;}
    div[data-testid="stTabs"] button[aria-selected="true"] p {text-shadow:0 0 10px rgba(0,240,255,.7);}
    .stButton > button[kind="primary"] {background:linear-gradient(90deg,#FF2BD6,#9D4EDD 50%,#00F0FF); color:#fff;
           border:none; box-shadow:0 0 18px rgba(255,43,214,.45);}
    .stButton > button:hover {box-shadow:0 0 18px rgba(0,240,255,.55);}
    div[data-testid="stPlotlyChart"], div[data-testid="stGraphVizChart"] {box-shadow:0 0 18px rgba(0,240,255,.12);}
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
                 "#C084FC": MAGENTA, "#34D399": GREEN, "#FBBF24": AMBER}.items():
        dot = dot.replace(a, b)
    # natural size: a 'stretch' graph inside a hidden tab is measured at 0 px and renders blank
    kw.pop("width", None)
    st.graphviz_chart(dot, width="content")


