"""Streamlit theme: glassmorphism skins (gradient background, soft colour blobs, frosted glass panels)."""
# flake8: noqa
import streamlit as st



def _rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    return "rgba(%d,%d,%d,%s)" % (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def apply():
    """Compute the active theme and inject its CSS (call once per script run)."""
    global THEMES, THEME_NAME, SKIN, SKINS, T, LIGHT, NAVY, TEAL, AMBER, RED, GREEN, GREY, MAGENTA, BG, PANEL, BORDER, MUTED, PLOT, SH, SH_HOVER
    _D = dict(mode="dark", lesson="#FDE9B0", good="#C8F5E2", bad="#FBD0D0", on_acc="#0B0F14", glow=False)
    _L = dict(mode="light", lesson="#7A5300", good="#065F46", bad="#9F1239", on_acc="#FFFFFF", glow=False)
    # ---- glassmorphism skins (one is active; ?skin=<key> previews another) ----
    SKINS = {
        "aurora":   dict(mode="dark", base="#071423", grad="linear-gradient(160deg,#06101F 0%,#0B1E33 55%,#071A2A 100%)",
                         blobs=[("#14B8A6",.55,"8% 10%",900), ("#6366F1",.45,"95% 15%",800), ("#06B6D4",.35,"70% 95%",900)],
                         acc="#5EEAD4", acc2="#A5B4FC", acc_rgb="94,234,212", title="#99F6E4", text="#E2F3F5", head="#FFFFFF",
                         sub="#5EEAD4", muted="#9BB4BF", glass=.08, colorway=["#5EEAD4","#A5B4FC","#38BDF8","#F0ABFC","#FDE68A","#FB7185"]),
        "midnight": dict(mode="dark", base="#05060A", grad="linear-gradient(180deg,#05060A 0%,#0A0D16 100%)",
                         blobs=[("#3B82F6",.30,"15% 0%",900), ("#8B5CF6",.22,"90% 30%",800), ("#0EA5E9",.15,"50% 100%",1000)],
                         acc="#93C5FD", acc2="#C4B5FD", acc_rgb="147,197,253", title="#BFDBFE", text="#E5E7EB", head="#FFFFFF",
                         sub="#93C5FD", muted="#9CA3AF", glass=.05, colorway=["#93C5FD","#C4B5FD","#67E8F9","#F9A8D4","#FDE68A","#86EFAC"]),
        "sunset":   dict(mode="dark", base="#1A0B1E", grad="linear-gradient(150deg,#1B0A24 0%,#3A0F2E 50%,#4A1A1A 100%)",
                         blobs=[("#F97316",.45,"95% 5%",850), ("#EC4899",.45,"5% 40%",850), ("#A855F7",.35,"60% 100%",900)],
                         acc="#FDBA74", acc2="#F9A8D4", acc_rgb="253,186,116", title="#FED7AA", text="#FCE7F3", head="#FFFFFF",
                         sub="#FDBA74", muted="#D6B4C2", glass=.09, colorway=["#FDBA74","#F9A8D4","#C4B5FD","#FDE68A","#5EEAD4","#FB7185"]),
        "ocean":    dict(mode="dark", base="#041A33", grad="linear-gradient(160deg,#03162C 0%,#06305A 55%,#0A4A7A 100%)",
                         blobs=[("#38BDF8",.45,"90% 0%",900), ("#22D3EE",.35,"0% 60%",850), ("#60A5FA",.35,"60% 100%",900)],
                         acc="#7DD3FC", acc2="#A5F3FC", acc_rgb="125,211,252", title="#7DD3FC", text="#E0F2FE", head="#FFFFFF",
                         sub="#7DD3FC", muted="#A5C4DA", glass=.10, colorway=["#7DD3FC","#A5F3FC","#C4B5FD","#FDE68A","#86EFAC","#FDA4AF"]),
        "emerald":  dict(mode="dark", base="#03140F", grad="linear-gradient(160deg,#03120E 0%,#062A20 55%,#0B3B2E 100%)",
                         blobs=[("#10B981",.45,"5% 5%",850), ("#84CC16",.25,"95% 30%",800), ("#14B8A6",.35,"55% 100%",900)],
                         acc="#6EE7B7", acc2="#BEF264", acc_rgb="110,231,183", title="#A7F3D0", text="#E3F7EE", head="#FFFFFF",
                         sub="#6EE7B7", muted="#9FC2B3", glass=.08, colorway=["#6EE7B7","#BEF264","#67E8F9","#FDE68A","#C4B5FD","#FDA4AF"]),
        "frost":    dict(mode="light", base="#EEF2FF", grad="linear-gradient(140deg,#E0E7FF 0%,#F5F3FF 40%,#E0F2FE 75%,#FCE7F3 100%)",
                         blobs=[("#A5B4FC",.70,"5% 5%",850), ("#7DD3FC",.60,"95% 20%",800), ("#F9A8D4",.55,"60% 100%",900)],
                         acc="#4F46E5", acc2="#0284C7", acc_rgb="79,70,229", title="#3730A3", text="#1E1B4B", head="#0F0B33",
                         sub="#4338CA", muted="#5B5F86", glass=.55, colorway=["#4F46E5","#0284C7","#DB2777","#059669","#D97706","#7C3AED"]),
    }
    SKIN_DEFAULT = "midnight"
    try:
        _q = st.query_params.get("skin")
    except Exception:
        _q = None
    SKIN = _q if _q in SKINS else SKIN_DEFAULT
    S = SKINS[SKIN]
    _base = dict(mode=S["mode"], lesson=S["text"], good=S["text"], bad=S["text"],
                 on_acc="#FFFFFF" if S["mode"] == "light" else "#04121F", glow=True)
    THEMES = {"Glass": {**_base, **dict(bg=S["base"], side=S["base"], panel=S["base"], panel2=S["base"], border="rgba(255,255,255,.18)",
                     acc=S["acc"], acc2=S["acc2"], acc_rgb=S["acc_rgb"], h1=S["base"], h2=S["base"], text=S["text"],
                     head=S["head"], sub=S["sub"], muted=S["muted"])}}
    THEME_NAME = "Glass"
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
        PLOT["colorway"] = S["colorway"]
        PLOT["plot_bgcolor"] = "rgba(255,255,255,.04)" if not LIGHT else "rgba(255,255,255,.35)"

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
    if T["glow"]:   # glassmorphism skin: gradient background, soft colour blobs, frosted panels; text stays crisp
        _blobs = ",".join("radial-gradient(closest-side, %s, rgba(0,0,0,0)) %s / %dpx %dpx no-repeat"
                          % (_rgba(c, o), pos, sz, sz) for c, o, pos, sz in S["blobs"])
        _g = S["glass"]
        _gb = "rgba(255,255,255,.65)" if LIGHT else "rgba(255,255,255,.18)"
        _gt = "rgba(255,255,255,.9)" if LIGHT else "rgba(255,255,255,.32)"
        _sh = "0 8px 32px rgba(30,27,75,.12)" if LIGHT else "0 8px 32px rgba(0,0,0,.40)"
        _css += """<style>
    .stApp {background: %(grad)s !important; background-attachment:fixed !important;}
    .stApp:before {content:""; position:fixed; inset:0; pointer-events:none; z-index:0; background: %(blobs)s;}
    .block-container {position:relative; z-index:1;}
    section[data-testid="stSidebar"] {background: rgba(255,255,255,%(gs)s) !important; backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
           border-right:1px solid %(gb)s;}
    section[data-testid="stSidebar"] h3 {color:%(acc)s !important;}
    .tid {color:%(acc)s !important;} .tpart {color:%(muted)s !important;}
    .stApp p, .stApp li, .stApp label, .stApp [data-testid="stMarkdownContainer"] {color:%(text)s;}
    .hero, .card, .kpi, div[data-testid="stPlotlyChart"], div[data-testid="stGraphVizChart"], div[data-testid="stDataFrame"],
    div[data-testid="stExpander"], .lesson, .good, .bad {
           background: linear-gradient(135deg, rgba(255,255,255,%(g1)s), rgba(255,255,255,%(g2)s)) !important;
           backdrop-filter: blur(18px) saturate(150%%); -webkit-backdrop-filter: blur(18px) saturate(150%%);
           border:1px solid %(gb)s !important; border-top-color:%(gt)s !important;
           box-shadow: %(sh)s !important; transform:none !important;}
    .hero {border-radius:24px; position:relative; overflow:hidden;}
    .hero:before {content:""; position:absolute; left:0; right:0; top:0; height:3px;
           background:linear-gradient(90deg,%(acc)s,%(acc2)s,%(acc)s); background-size:200%% 100%%; animation:flow 8s linear infinite;}
    @keyframes flow {0%%{background-position:0%% 0} 100%%{background-position:200%% 0}}
    .hero h1 {color:%(title)s !important; text-shadow:none !important;}
    .hero h1 a, h1 a, h2 a, h3 a, [data-testid="stHeaderActionElements"] {display:none !important;}
    .hero p {color:%(text)s !important; opacity:.92 !important;}
    h2 {color:%(head)s !important; text-shadow:none !important;} h3 {color:%(sub)s !important; text-shadow:none !important;}
    .pill, .pill.m, .pill.g, .pill.y {border:1px solid %(gb)s !important; background:rgba(255,255,255,%(g1)s) !important;
           color:%(head)s !important; box-shadow:none !important;}
    .kpi {border-radius:18px;} .kpi .v {color:%(head)s !important; text-shadow:none !important;} .kpi .l {color:%(sub)s !important;}
    .card {border-radius:18px;} .card h4 {color:%(acc)s !important; text-shadow:none !important;}
    .card:hover, .kpi:hover {border-color:%(acc)s !important;}
    .owner {border:1px solid %(acc)s !important; background:rgba(%(acc_rgb)s,.14) !important; color:%(head)s !important; box-shadow:none !important;}
    div[data-testid="stTabs"] button p {color:%(text)s !important;}
    div[data-testid="stTabs"] button[aria-selected="true"] p {color:%(acc)s !important; text-shadow:none !important;}
    div[data-baseweb="tab-highlight"] {background:%(acc)s !important; box-shadow:none !important;}
    .stButton > button, .stDownloadButton > button {border:1px solid %(gb)s !important; color:%(head)s !important;
           background:rgba(255,255,255,%(g1)s) !important; box-shadow:none !important;}
    .stButton > button[kind="primary"] {background:%(acc)s !important; color:%(on)s !important; border:none !important;}
    .lesson {border-left:4px solid %(acc)s !important; color:%(text)s !important;}
    .good {border-left:4px solid %(acc2)s !important; color:%(text)s !important;}
    .bad {border-left:4px solid #FB7185 !important; color:%(text)s !important;}
    .lesson b, .lesson strong, .good b, .bad b {color:%(acc)s;}
    .mono {color:%(acc)s !important;}
    hr {border-color:%(gb)s !important;}
    ::-webkit-scrollbar {width:10px; height:10px;} ::-webkit-scrollbar-track {background:transparent;}
    ::-webkit-scrollbar-thumb {background:rgba(%(acc_rgb)s,.6); border-radius:10px;}
    </style>""" % dict(grad=S["grad"], blobs=_blobs, gs=(.35 if LIGHT else .04), gb=_gb, gt=_gt, sh=_sh,
                       g1=_g, g2=(_g * .4), acc=S["acc"], acc2=S["acc2"], acc_rgb=S["acc_rgb"], title=S["title"],
                       text=S["text"], head=S["head"], sub=S["sub"], muted=S["muted"], on=T["on_acc"])
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


