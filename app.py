"""RecoMart - interactive walkthrough of the end-to-end data management pipeline.

    streamlit run app.py
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
os.environ.setdefault("MLFLOW_DISABLE_TELEMETRY", "true")

import pandas as pd  # noqa: E402
import plotly.express as px  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402
import streamlit.components.v1 as components  # noqa: E402
import yaml  # noqa: E402

st.set_page_config(page_title="RecoMart · Data Pipeline",
                   page_icon=str(Path(__file__).resolve().parent / "assets" / "favicon.png"), layout="wide")

from recomart import ui_theme as ui  # noqa: E402
from recomart.config import (LOG_DIR, PROCESSED, REPORTS, ROOT, SQL_DIR, TEAM,  # noqa: E402
                             WAREHOUSE_DB, cfg)

ui.apply()
PLOT = ui.PLOT


# ---------------------------------------------------------------- bootstrap (first launch)
def _pipeline_ready() -> bool:
    from recomart.train import registry_versions
    try:
        return (REPORTS / "model_metrics.json").exists() and not registry_versions().empty
    except Exception:
        return False


@st.cache_resource(show_spinner=False)
def _boot_lock():
    import threading
    return threading.Lock()


if not _pipeline_ready():
    with _boot_lock():
        if not _pipeline_ready():
            import uuid
            from recomart.pipeline import ORDER, run_stage
            box = st.empty()
            labels = {"sources": "Starting source systems", "ingest": "Ingesting files and APIs into the lake",
                      "validate": "Validating data quality", "prepare": "Cleaning and preparing data",
                      "eda": "Exploratory analysis", "transform": "Building the SQL warehouse and features",
                      "features": "Materialising the feature store", "train": "Training and registering models"}
            rid = uuid.uuid4().hex[:10]
            for i, stg in enumerate(ORDER):
                box.markdown(f'<div class="boot"><div class="eyebrow">First launch · about a minute</div>'
                             f'<h3>Running the RecoMart pipeline</h3><p>Step {i + 1} of {len(ORDER)} · {labels[stg]}…</p>'
                             f'<div style="height:8px;border-radius:8px;background:rgba(255,255,255,.08);overflow:hidden">'
                             f'<div style="height:100%;width:{int(100 * i / len(ORDER))}%;background:linear-gradient(90deg,#93C5FD,#C4B5FD)">'
                             f'</div></div></div>', unsafe_allow_html=True)
                run_stage(stg, rid)
            box.empty()

from recomart import feature_store, lineage  # noqa: E402
from recomart.logging_utils import read_audit  # noqa: E402
from recomart.pipeline import read_runs  # noqa: E402
from recomart.recommend import champion_info, recommend, similar_items  # noqa: E402
from recomart.storage import LakeStorage, tree  # noqa: E402
from recomart.train import registry_versions, runs_dataframe  # noqa: E402


STAGE_COLORS = ["#93C5FD", "#C4B5FD", "#86EFAC", "#FCD34D"]


def initials(name):
    parts = name.split()
    return (parts[0][0] + parts[-1][0]).upper()


def kpi(col, value, label):
    col.markdown(f'<div class="kpi"><div class="v">{value}</div><div class="l">{label}</div></div>', unsafe_allow_html=True)


def owner(i):
    m = TEAM[i]
    st.markdown(f'<div class="owner">{m["member"]} · {m["name"]} · {m["id"]}</div>', unsafe_allow_html=True)


def banner(i, title, goal):
    m = TEAM[i]
    st.markdown(f'<div class="banner" style="--c:{STAGE_COLORS[i]}"><div class="av" style="--c:{STAGE_COLORS[i]}">'
                f'{initials(m["name"])}</div><div><div class="who-l">{m["member"]} · {m["name"]} · {m["id"]}</div>'
                f'<h2>{title}</h2><p>{goal}</p></div></div>', unsafe_allow_html=True)


def kpi_row(items, height=128):
    """KPI tiles whose numbers count up on load (rendered in a small HTML component)."""
    tiles = "".join(
        f'<div class="k" style="--c:{ui.PALETTE[i % len(ui.PALETTE)]}"><div class="v" data-v="{v}">{v}</div>'
        f'<div class="l">{lab}</div></div>' for i, (v, lab) in enumerate(items))
    components.html("""<html><head><link href="https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700&display=swap" rel="stylesheet">
<style>body{margin:0;background:transparent;font-family:Inter,Segoe UI,sans-serif}
.row{display:grid;grid-template-columns:repeat(%d,1fr);gap:14px;padding:2px}
.k{position:relative;overflow:hidden;border-radius:18px;padding:18px 20px;min-height:84px;
 background:linear-gradient(135deg,rgba(255,255,255,.07),rgba(255,255,255,.02));border:1px solid rgba(255,255,255,.16);
 border-top-color:rgba(255,255,255,.3);transition:transform .2s ease}
.k:hover{transform:translateY(-3px)} .k:before{content:"";position:absolute;left:0;right:0;top:0;height:2px;background:var(--c)}
.v{font-size:28px;font-weight:700;color:#fff;letter-spacing:-.01em;white-space:nowrap;font-variant-numeric:tabular-nums}
.l{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#9CA3AF;margin-top:6px;font-weight:600}</style></head>
<body><div class="row">%s</div><script>
document.querySelectorAll('.v').forEach(function(el){
  var raw=el.dataset.v, m=raw.match(/^([^0-9]*)([0-9][0-9,]*\\.?[0-9]*)(.*)$/); if(!m) return;
  var pre=m[1], num=parseFloat(m[2].replace(/,/g,'')), suf=m[3], dec=(m[2].split('.')[1]||'').length, comma=m[2].indexOf(',')>=0;
  var t0=null, dur=1100; function fmt(x){var s=x.toFixed(dec); if(comma){s=Number(s).toLocaleString('en-US',{minimumFractionDigits:dec,maximumFractionDigits:dec});} return pre+s+suf;}
  function step(ts){ if(!t0) t0=ts; var p=Math.min(1,(ts-t0)/dur), e=1-Math.pow(1-p,3); el.textContent=fmt(num*e); if(p<1) requestAnimationFrame(step); else el.textContent=raw;}
  el.textContent=fmt(0); requestAnimationFrame(step);});
</script></body></html>""" % (len(items), tiles), height=height)


def note(kind, html):
    st.markdown(f'<div class="{kind}">{html}</div>', unsafe_allow_html=True)


def tail(path: Path, n=40) -> str:
    return "\n".join(path.read_text(encoding="utf-8").splitlines()[-n:]) if path.exists() else "(no log yet)"


@st.cache_data(show_spinner=False, ttl=30)
def load_json(p: str):
    return json.loads((ROOT / p).read_text())


@st.cache_data(show_spinner=False, ttl=600)
def _eda_data():
    ev = pd.read_parquet(PROCESSED / "events.parquet", columns=["event_ts", "user_id", "product_id", "event_type"])
    pr = pd.read_parquet(PROCESSED / "products.parquet", columns=["product_id", "category"])
    rt = pd.read_parquet(PROCESSED / "ratings.parquet", columns=["rating"])
    return ev, pr, rt


def eda_figures():
    ev, pr, rt = _eda_data()
    P = ui.PALETTE
    order = ["view", "wishlist", "add_to_cart", "purchase"]
    cnt = ev.event_type.value_counts().reindex(order).fillna(0)
    f1 = go.Figure(go.Funnel(y=[o.replace("_", " ") for o in order], x=cnt.values, marker=dict(color=P[:4]),
                             textinfo="value+percent initial", textfont=dict(color="#0B1020", size=13), connector=dict(line=dict(color="rgba(255,255,255,.1)"))))
    ui.style_fig(f1, 330, "Event funnel", legend=False)
    per_user = ev.groupby("user_id").size()
    f2 = px.histogram(per_user, nbins=40, color_discrete_sequence=[P[0]])
    ui.style_fig(f2, 330, "Events per user", legend=False)
    f2.update_layout(xaxis_title="events", yaxis_title="users")
    pop = ev.groupby("product_id").size().sort_values(ascending=False).reset_index(drop=True)
    f3 = go.Figure(go.Scatter(y=pop.values, mode="lines", fill="tozeroy", line=dict(color=P[1], width=2),
                              fillcolor="rgba(196,181,253,.18)"))
    top = int(len(pop) * .1)
    f3.add_vline(x=top, line=dict(color=P[3], dash="dot"))
    f3.add_annotation(x=top, y=pop.max() * .85, text=f"top 10% = {pop[:top].sum() / pop.sum():.0%} of events",
                      showarrow=False, xanchor="left", font=dict(color=P[3]))
    ui.style_fig(f3, 330, "Item popularity (long tail)", legend=False)
    f3.update_layout(xaxis_title="products ranked by popularity", yaxis_title="events")
    rc = rt.rating.value_counts().sort_index()
    f4 = px.bar(x=rc.index.astype(str), y=rc.values, color=rc.index.astype(str), color_discrete_sequence=P)
    ui.style_fig(f4, 330, "Rating distribution", legend=False)
    f4.update_layout(xaxis_title="rating", yaxis_title="ratings")
    hm = ev.merge(pr, on="product_id").pivot_table(index="category", columns="event_type", values="user_id",
                                                     aggfunc="count").reindex(columns=order).fillna(0)
    hm = (hm.div(hm.sum(axis=1), axis=0) * 100).round(1)
    f5 = px.imshow(hm, text_auto=True, aspect="auto", color_continuous_scale=["#0B1020", "#3B4F86", "#93C5FD", "#E0F2FE"])
    ui.style_fig(f5, 360, "Event mix by category (%)", legend=False)
    f5.update_layout(coloraxis_showscale=False, xaxis_title="", yaxis_title="")
    daily = ev.assign(day=ev.event_ts.dt.date).groupby(["day", "event_type"]).size().reset_index(name="events")
    f6 = px.line(daily, x="day", y="events", color="event_type", color_discrete_sequence=P,
                 category_orders={"event_type": order})
    ui.style_fig(f6, 360, "Daily activity")
    f6.update_traces(line=dict(width=2))
    f6.update_layout(xaxis_title="", yaxis_title="events")
    return [[f1, f2], [f3, f4], [f5, f6]]


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("### RecoMart Data Pipeline")
    st.caption("DSE ZG529 · Data Management for ML\nExperiential Learning Assignment (EC1)")
    st.markdown('<div class="sb-label">Team</div>', unsafe_allow_html=True)
    for i, m in enumerate(TEAM):
        st.markdown(f'<div class="tm"><div class="av" style="--c:{STAGE_COLORS[i]}">{initials(m["name"])}</div>'
                    f'<div><div class="tn">{m["name"]}</div><div class="tid">{m["id"]}</div>'
                    f'<div class="tpart">{m["part"]}</div></div></div>', unsafe_allow_html=True)
    st.divider()
    runs = read_runs()
    if runs:
        last = runs[-1]
        st.markdown("**Last pipeline run**")
        st.markdown(f"Run `{last['run_id']}` · {last['finished_at'][:16].replace('T', ' ')} UTC")
        ok = sum(r["status"] == "success" for r in runs if r["run_id"] == last["run_id"])
        st.markdown(f"Stages succeeded: **{ok}**")
    try:
        ch = champion_info()
        st.markdown(f"Champion: **v{ch['version']} · {ch['family']}** · NDCG@10 **{ch['ndcg_at_10']}**")
    except Exception:
        pass

# ---------------------------------------------------------------- header
st.markdown("""<div class="hero"><div class="eyebrow">DSE ZG529 · Data Management for Machine Learning · BITS Pilani WILP</div><h1>RecoMart — End-to-End Data Management Pipeline for Recommendations</h1>
<p>Clickstream, transactions, ratings, user profiles and two REST APIs flow through ingestion, a partitioned
data lake, validation, preparation, a SQL warehouse, a versioned feature store and model training, orchestrated
as one Prefect DAG and served as personalised recommendations.</p>
<span class="pill">Ingestion · data lake · DVC</span><span class="pill m">Validation · preparation · EDA</span>
<span class="pill g">Warehouse · feature store</span><span class="pill y">Models · MLflow · Prefect · API</span></div>""",
            unsafe_allow_html=True)

tabs = st.tabs(["Overview", "① Ingestion & Versioning", "② Validation & EDA", "③ Features & Feature Store",
                "④ Models, Orchestration & Serving"])

dq = load_json("reports/dq/dq_results.json")
mm = load_json("reports/model_metrics.json")
prep = load_json("data/processed/_prep_summary.json")
K = mm["k"]
best = next(r for r in mm["results"] if r["model"] == mm["best"])

# ================================================================ OVERVIEW
with tabs[0]:
    kpi_row([("6", "data sources"), (f"{len(LakeStorage.manifest()):,}", "objects in raw lake"),
             (f"{prep['events']['clean']:,}", "clean events"), (f"{dq['quality_score']}%", "DQ checks passed"),
             (f"{sum(len(v['snapshots']) for v in feature_store.load_registry()['views'].values())}", "feature snapshots"),
             (f"{best[f'ndcg_at_{K}']:.3f}", f"champion NDCG@{K}")])
    st.subheader("Pipeline DAG")
    flow = [("src", "6 sources", "4 CSV feeds · 2 REST APIs", "#94A3B8"),
            ("1", "Ingest", "retry · logging", STAGE_COLORS[0]), ("1", "Raw lake", "source / type / date", STAGE_COLORS[0]),
            ("2", "Validate", "DQ report · gate", STAGE_COLORS[1]), ("2", "Prepare", "clean · encode · EDA", STAGE_COLORS[1]),
            ("3", "Warehouse", "SQL features", STAGE_COLORS[2]), ("3", "Feature store", "versioned v1 / v2", STAGE_COLORS[2]),
            ("4", "Train", "MLflow tracking", STAGE_COLORS[3]), ("4", "Serve", "API · @champion", STAGE_COLORS[3])]
    nodes = '<span class="arr">→</span>'.join(
        f'<div class="fn" style="--c:{c}"><div class="fs">{"①②③④"[int(n) - 1] if n.isdigit() else "◎"}</div>'
        f'<div class="ft">{t}</div><div class="fd">{d}</div></div>' for n, t, d, c in flow)
    st.markdown(f'<div class="flow">{nodes}</div>', unsafe_allow_html=True)
    st.caption("Orchestrated by Prefect (flows/recomart_flow.py) and reproducible with DVC (dvc.yaml).")
    st.subheader("Who does what")
    wc = st.columns(4)
    for i, m in enumerate(TEAM):
        wc[i].markdown(f'<div class="card who" style="--c:{STAGE_COLORS[i]}">'
                       f'<div class="av" style="--c:{STAGE_COLORS[i]}">{initials(m["name"])}</div><div>'
                       f'<h4>{"①②③④"[i]} {m["part"]}</h4>'
                       f'<p>{m["name"]}<br><span class="mono">{m["id"]}</span></p></div></div>',
                       unsafe_allow_html=True)
    st.write("")
    st.subheader("Latest run, stage by stage")
    if runs:
        rid = runs[-1]["run_id"]
        lr = pd.DataFrame([r for r in runs if r["run_id"] == rid])[["stage", "status", "seconds", "finished_at"]]
        cc1, cc2 = st.columns([1, 1.4])
        lr["seconds"] = lr["seconds"].round(2)
        lr["finished_at"] = lr["finished_at"].str[:19].str.replace("T", " ")
        cc1.dataframe(ui.status_style(lr), hide_index=True, width="stretch")
        fig = px.bar(lr, x="seconds", y="stage", orientation="h", color="stage", color_discrete_sequence=ui.PALETTE + ui.PALETTE)
        ui.style_fig(fig, 300, "Stage duration (seconds)", legend=False)
        fig.update_layout(yaxis={"categoryorder": "array", "categoryarray": lr["stage"][::-1], "title": ""})
        cc2.plotly_chart(fig, width="stretch")
    with st.expander("Business problem, outputs and metrics"):
        st.markdown(f"""
**Problem.** RecoMart wants personalised product recommendations to lift conversion and cross-selling.
**Inputs.** Web/app clickstream, purchase history, ratings, CRM user profiles, product catalog API, external popularity/sentiment API.
**Outputs.** Validated clean datasets for EDA · engineered user/item/co-occurrence features in a warehouse and feature store ·
a registered recommendation model with an inference API.
**Metrics.** Precision@{K}, Recall@{K}, NDCG@{K}, HitRate@{K}, MAP@{K} and catalogue coverage on a time-based holdout
(last {cfg()['training']['test_days']} days).""")

# ================================================================ 1. INGESTION / STORAGE / VERSIONING
with tabs[1]:
    banner(0, "① Ingestion, Raw Storage and Data Versioning",
           "Continuously pull every source into one place, never lose or duplicate data, and know exactly which "
           "version of which data every downstream result came from.")
    src = pd.DataFrame([{"source": k, "kind": v["kind"], "location": v.get("landing_dir") or v["base_url"] + v["endpoint"]}
                        for k, v in cfg()["sources"].items()])
    a, b = st.columns([1, 1.2])
    with a:
        st.subheader("Sources")
        st.dataframe(src, hide_index=True, width="stretch")
        ic = cfg()["ingestion"]
        st.markdown(f"Retries: **{ic['max_retries']}** with exponential backoff from **{ic['backoff_seconds']} s** · "
                    f"timeout **{ic['timeout_seconds']} s** · schedule every **{ic['schedule_minutes']} min**")
    with b:
        st.subheader("Raw data lake layout")
        st.code(tree(), language="text")
    man = pd.DataFrame(LakeStorage.manifest())
    st.subheader("Lake manifest (audit trail of stored objects)")
    if not man.empty:
        g = man.groupby("source").agg(objects=("key", "count"), rows=("rows", "sum"), mb=("bytes", "sum")).reset_index()
        g["mb"] = (g["mb"] / 1e6).round(2)
        m1, m2 = st.columns([1, 1.6])
        m1.dataframe(g, hide_index=True, width="stretch")
        m2.dataframe(man[["stored_at", "run_id", "source", "key", "rows", "md5"]].tail(200).iloc[::-1],
                     hide_index=True, width="stretch", height=260)
    st.subheader("Ingestion log (retries and failures)")
    st.code(tail(LOG_DIR / "ingestion.log", 30), language="text")

    st.subheader("Near-real-time ingestion demo")
    st.caption("Drops micro-batch clickstream files into the landing zone (as a Kafka consumer or app gateway would) "
               "and runs one ingestion poll. Already-ingested files are skipped by content hash.")
    if st.button("Simulate 3 micro-batches and ingest", type="primary"):
        last_t = st.session_state.get("_stream_t", 0)
        import time as _t
        if _t.time() - last_t < 20:
            st.warning("Please wait a few seconds between demos.")
        else:
            st.session_state["_stream_t"] = _t.time()
            from recomart.generate import simulate_stream
            from recomart.ingestion import run_ingestion
            files = simulate_stream(3)
            res = run_ingestion()
            st.success(f"Landed {files}; ingestion run {res['run_id']}: " +
                       ", ".join(f"{r['source']}={r.get('new_files', r.get('rows'))}" for r in res["results"]))

    st.subheader("Data versioning and lineage")
    cat = lineage.catalog()
    vt = pd.DataFrame([{"dataset": k, "path": v["path"], "versions": len(v["versions"]),
                        "latest md5": v["versions"][-1]["md5"][:12], "stage": v["versions"][-1]["stage"],
                        "created": v["versions"][-1]["created"][:19], "transformation": v["versions"][-1]["transformation"]}
                       for k, v in cat.items()])
    l1, l2 = st.columns([1.6, 1])
    l1.dataframe(vt, hide_index=True, width="stretch")
    with l2:
        edges = set()
        for h in lineage.history():
            for i in h["inputs"]:
                for o in h["outputs"]:
                    edges.add((i, h["stage"], o))
        dot = ('digraph{rankdir=LR;bgcolor=transparent;node[shape=box style="rounded,filled" fillcolor="#111A2E" '
               'color="#38BDF8" fontcolor="#E8EEF7" fontname=Inter fontsize=9];edge[color="#64748B" fontsize=8 '
               'fontcolor="#B6C2D6"];' + "".join(f'"{i}"->"{o}"[label="{s}"];' for i, s, o in sorted(edges)) + "}")
        ui.gv(dot)
    with st.expander("DVC workflow"):
        st.code("""dvc init                       # once
dvc repro                      # runs only stages whose inputs changed (dvc.yaml)
git add dvc.lock && git commit -m "data: new ingestion"   # dvc.lock = dataset versions
dvc remote add -d storage gdrive://<folder-id>            # or s3://bucket/path
dvc push                       # upload versioned data; Git keeps only hashes
git checkout <old-commit> && dvc checkout                 # restore an older dataset version
dvc dag                        # show the pipeline graph""", language="bash")

# ================================================================ 2. VALIDATION / PREP / EDA
with tabs[2]:
    banner(1, "② Data Profiling, Validation, Preparation and EDA",
           "Catch bad data before it reaches the model, repair or quarantine it, and understand the shape of the "
           "cleaned data.")
    kpi_row([(f"{dq['quality_score']}%", "checks passed"), (f"{dq['checks_passed']}", f"of {dq['checks_total']} checks passed"),
             (str(sum(len(d["schema_drift"]) for d in dq["datasets"])), "schema-drift files"),
             (str(sum(sum(v.values()) for v in prep["quarantine"].values())), "rows quarantined")])
    ds = pd.DataFrame([{"dataset": d["dataset"], "rows": d["rows"], "files": d["files"], "duplicates %": d["duplicate_pct"],
                        "max missing %": max(d["missing_pct"].values()) if d["missing_pct"] else 0,
                        "checks": f"{d['checks_passed']}/{d['checks_total']}", "status": d["status"]} for d in dq["datasets"]])
    st.dataframe(ui.status_style(ds), hide_index=True, width="stretch")
    chk = pd.DataFrame([{"dataset": d["dataset"], **c_} for d in dq["datasets"] for c_ in d["checks"]])
    f1, f2 = st.columns([1, 1])
    with f1:
        flt = st.multiselect("Show checks with status", ["PASS", "WARN", "FAIL"], default=["WARN", "FAIL"])
        st.dataframe(ui.status_style(chk[chk.status.isin(flt)][["dataset", "kind", "column", "check", "failures", "pct",
                                                                 "status"]]), hide_index=True, width="stretch", height=300)
    with f2:
        miss = pd.DataFrame([{"column": f"{d['dataset']}.{k}", "missing %": v} for d in dq["datasets"]
                             for k, v in d["missing_pct"].items() if v > 0]).sort_values("missing %")
        if not miss.empty:
            fig = px.bar(miss, x="missing %", y="column", orientation="h", color_discrete_sequence=[ui.PALETTE[1]])
            ui.style_fig(fig, 320, "Missing values (%)", legend=False)
            fig.update_layout(yaxis_title="")
            st.plotly_chart(fig, width="stretch")
    for d in dq["datasets"]:
        for s in d["schema_drift"]:
            note("bad", f"<b>Schema drift</b> in <span class='mono'>{s['file']}</span>: missing {s['missing_columns']}, "
                        f"unexpected {s['unexpected_columns']} → mapped to the contract during preparation.")
    pdf = REPORTS / "dq" / "data_quality_report.pdf"
    if pdf.exists():
        st.download_button("Download Data Quality Report (PDF)", pdf.read_bytes(), "data_quality_report.pdf",
                           "application/pdf")

    st.subheader("Preparation: raw → clean → quarantine")
    pr = pd.DataFrame([{"dataset": k, "raw": v["raw"], "clean": v["clean"]} for k, v in prep.items()
                       if isinstance(v, dict) and "raw" in v])
    q = pd.DataFrame([{"dataset": k, "reason": r, "rows": n} for k, v in prep["quarantine"].items() for r, n in v.items()])
    p1, p2 = st.columns([1.2, 1])
    fig = px.bar(pr.melt("dataset", var_name="stage", value_name="rows"), x="dataset", y="rows", color="stage",
                 barmode="group", log_y=True, color_discrete_sequence=[ui.PALETTE[1], ui.PALETTE[2]])
    ui.style_fig(fig, 320, "Rows before and after cleaning (log scale)")
    p1.plotly_chart(fig, width="stretch")
    p2.dataframe(q, hide_index=True, width="stretch")
    p2.caption("Quarantined rows are kept in data/lake/quarantine/ with their reason code.")

    st.subheader("Exploratory data analysis")
    eda_s = load_json("reports/eda_summary.json")
    kpi_row([(f"{eda_s['sparsity_pct']}%", "user-item sparsity"), (f"{eda_s['purchase_pairs_sparsity_pct']}%", "purchase sparsity"),
             (str(eda_s["item_popularity_gini"]), "popularity Gini"), (f"{eda_s['top10pct_items_share'] * 100:.0f}%", "share of top 10% items"),
             (f"{eda_s['view_to_purchase_pct']}%", "view → purchase")])
    for row in eda_figures():
        cols = st.columns(len(row))
        for col, f in zip(cols, row):
            col.plotly_chart(f, width="stretch")
    st.caption("Print versions of these charts (for the report) are in reports/figures/.")

# ================================================================ 3. FEATURES / WAREHOUSE / FEATURE STORE
with tabs[3]:
    banner(2, "③ Feature Engineering, Warehouse and Feature Store",
           "Turn cleaned data into reusable, documented, versioned features that are identical for training and "
           "inference.")
    con = sqlite3.connect(WAREHOUSE_DB)
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name", con)
    tables["rows"] = [con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables["name"]]
    w1, w2 = st.columns([1, 1.6])
    with w1:
        st.subheader("Warehouse tables")
        st.dataframe(tables, hide_index=True, width="stretch")
    with w2:
        st.subheader("Feature logic (SQL)")
        sqlf = st.selectbox("Transformation", ["features_user.sql", "features_item.sql", "features_cooccurrence.sql",
                                               "schema.sql"])
        st.code((SQL_DIR / sqlf).read_text(), language="sql")

    reg = feature_store.load_registry()
    st.subheader("Feature registry")
    rv = pd.DataFrame([{"feature view": k, "entity": v["entity"], "versions": ", ".join(v["versions"]),
                        "features": len(v["features"]), "snapshots": len(v["snapshots"]),
                        "latest snapshot": v["snapshots"][-1]["as_of"][:10] if v["snapshots"] else "-",
                        "transformation": v["transformation"]} for k, v in reg["views"].items()])
    st.dataframe(rv, hide_index=True, width="stretch")
    view = st.selectbox("Feature metadata for", list(reg["views"]))
    st.dataframe(pd.DataFrame([{"feature": f, **m} for f, m in reg["views"][view]["features"].items()]),
                 hide_index=True, width="stretch")

    st.subheader("Feature retrieval demo")
    users = sorted(pd.read_parquet(PROCESSED / "interactions.parquet", columns=["user_id"])["user_id"].unique())
    prods = pd.read_parquet(PROCESSED / "products.parquet")[["product_id", "title", "category"]]
    r1, r2 = st.columns(2)
    with r1:
        u = st.selectbox("User (online store, latest)", users[:300], key="fs_user")
        st.dataframe(feature_store.get_online_features("user_activity", [u]).T.rename(columns={0: "value"}).astype(str),
                     width="stretch")
        snaps = [s["as_of"] for s in reg["views"]["user_activity"]["snapshots"] if s["version"] == "v1"]
        when = st.select_slider("Point-in-time: feature values as of", snaps, value=snaps[len(snaps) // 2])
        hist = feature_store.get_training_features("user_activity", when, "v1")
        st.caption(f"Training-time view: snapshot taken at {when[:10]}, events before that date only")
        st.dataframe(hist[hist.user_id == u].T.astype(str), width="stretch")
    with r2:
        pid = st.selectbox("Product (versioned retrieval: item_stats v1 vs v2)", prods["product_id"][:300],
                           format_func=lambda p: f"{p} · {prods.set_index('product_id').loc[p, 'title']}")
        v1 = feature_store.get_online_features("item_stats", [pid], "v1").T.rename(columns={0: "v1"})
        v2 = feature_store.get_online_features("item_stats", [pid], "v2").T.rename(columns={0: "v2"})
        st.dataframe(v1.join(v2, how="outer").astype(str), width="stretch")
        st.caption("v2 adds trend_score; models pinned to v1 keep receiving v1.")
        co = pd.read_sql("SELECT related_product_id, co_users, lift FROM feat_item_cooccurrence WHERE product_id=? "
                         "AND as_of=(SELECT MAX(as_of) FROM feat_item_cooccurrence) ORDER BY rank LIMIT 5", con, params=[pid])
        co = co.merge(prods, left_on="related_product_id", right_on="product_id")[["title", "category", "co_users", "lift"]]
        st.markdown("**Frequently bought together**")
        st.dataframe(co, hide_index=True, width="stretch")
    con.close()

# ================================================================ 4. MODELS / ORCHESTRATION / SERVING
with tabs[4]:
    banner(3, "④ Model Training, Experiment Tracking, Orchestration and Serving",
           "Train and compare recommenders, track every run, run the whole pipeline on a schedule and serve "
           "explained recommendations.")
    note("lesson", f"<b>Protocol:</b> time-based split at {mm['cutoff']} (last {cfg()['training']['test_days']} days held "
                   f"out); a hit is a product the user added to cart or bought afterwards and had never interacted with; "
                   f"{mm['eval_users']} users evaluated.")
    res = pd.DataFrame(mm["results"])
    cols = ["model", f"precision_at_{K}", f"recall_at_{K}", f"ndcg_at_{K}", f"hit_rate_at_{K}", f"map_at_{K}",
            "catalog_coverage", "train_seconds"]
    st.dataframe(res[cols], hide_index=True, width="stretch")
    melt = res.melt("model", [f"precision_at_{K}", f"recall_at_{K}", f"ndcg_at_{K}", f"hit_rate_at_{K}"],
                    var_name="metric", value_name="value")
    melt["metric"] = melt["metric"].str.replace(f"_at_{K}", f"@{K}").str.replace("_", " ")
    fig = px.bar(melt, x="metric", y="value", color="model", barmode="group", color_discrete_sequence=ui.PALETTE)
    ui.style_fig(fig, 360, "Ranking metrics by model")
    fig.update_layout(xaxis_title="", yaxis_title="")
    st.plotly_chart(fig, width="stretch")
    lift = 100 * (best[f"ndcg_at_{K}"] / next(r for r in mm["results"] if r["model"] == "popularity")[f"ndcg_at_{K}"] - 1)
    note("good", f"<b>{mm['best']}</b> is the champion: NDCG@{K} = {best[f'ndcg_at_{K}']:.4f}, "
                 f"<b>{lift:+.0f}%</b> over the popularity baseline. It was refit on all data and registered with "
                 f"the <span class='mono'>@champion</span> alias.")

    st.subheader("MLflow tracking and registry")
    rd = runs_dataframe()
    if not rd.empty:
        show = pd.DataFrame({"run": rd["tags.mlflow.runName"], "stage": rd.get("tags.stage"),
                             "model": rd.get("params.model"), f"NDCG@{K}": rd.get(f"metrics.ndcg_at_{K}"),
                             f"P@{K}": rd.get(f"metrics.precision_at_{K}"), "data md5": rd.get("params.data_md5"),
                             "started": rd["start_time"].dt.strftime("%Y-%m-%d %H:%M"), "run_id": rd["run_id"]})
        st.dataframe(show.head(30), hide_index=True, width="stretch")
    st.dataframe(registry_versions(), hide_index=True, width="stretch")

    st.subheader("Orchestration (Prefect)")
    o1, o2 = st.columns([1, 1.3])
    with o1:
        ui.gv("""digraph{rankdir=TB;bgcolor=transparent;node[shape=box style="rounded,filled" fillcolor="#111A2E"
          color="#FCD34D" fontcolor="#E8EEF7" fontname=Inter fontsize=10];edge[color="#64748B"];
          ingest[label="ingest\\nretries=2"]; validate[label="validate\\nquality gate"]; prepare; eda;
          transform; features; train; ingest->validate->prepare; prepare->eda; prepare->transform->features->train;}""")
        st.code("python flows/recomart_flow.py      # one run\nprefect server start              # UI :4200\n"
                "python flows/serve.py             # scheduled every 60 min", language="bash")
    with o2:
        if runs:
            rr = pd.DataFrame(runs)
            agg = rr.groupby("run_id").agg(started=("finished_at", "min"), stages=("stage", "count"),
                                           failed=("status", lambda s: int((s == "failed").sum())),
                                           seconds=("seconds", "sum")).reset_index().sort_values("started", ascending=False)
            st.markdown("**Run history** (logs/runs.jsonl)")
            st.dataframe(agg.head(15).round(2), hide_index=True, width="stretch")
        st.markdown("**Alerts** (logs/alerts.log)")
        st.code(tail(LOG_DIR / "alerts.log", 8), language="text")

    st.subheader("Recommendation service")
    cat_col = {c: ui.PALETTE[i % len(ui.PALETTE)] for i, c in enumerate(sorted(prods["category"].unique()))}
    s1, s2 = st.columns([1, 2.4])
    with s1:
        mode = st.radio("User", ["Existing customer", "New visitor (cold start)"], horizontal=True)
        uid = st.selectbox("Customer", users[:300]) if mode == "Existing customer" else "U99999"
        k = st.slider("How many recommendations", 3, 20, 9)
        hist = pd.read_parquet(PROCESSED / "interactions.parquet")
        hist = hist[hist.user_id == uid].merge(prods, on="product_id").sort_values("strength", ascending=False)
        if len(hist):
            st.markdown("**Recent interests**")
            st.markdown('<div class="chips">' + "".join(
                f'<span class="chip" style="--c:{cat_col.get(r.category, ui.PALETTE[0])}">{r.title} · <b>{r.category}</b></span>'
                for r in hist.head(8).itertuples()) + "</div>", unsafe_allow_html=True)
        else:
            st.markdown('<div class="chips"><span class="chip">No history: showing trending products</span></div>',
                        unsafe_allow_html=True)
    with s2:
        out = recommend(uid, k)
        cards = "".join(
            f'<div class="reco" style="--c:{cat_col.get(it["category"], ui.PALETTE[0])}"><div class="rk">{it["rank"]}</div>'
            f'<span class="cat">{it["category"]}</span><div class="t">{it["title"]}</div>'
            f'<div class="meta"><span class="price">₹{it["price"]:,.0f}</span>'
            f'<span><span class="star">★</span> {it["avg_rating"]:.1f}</span><span>{it["buyers"]} buyers</span></div>'
            f'<div class="why">{it["reason"]}</div></div>' for it in out["items"])
        st.markdown(f'<div class="reco-grid">{cards}</div>', unsafe_allow_html=True)
        st.caption(f"Model {out['model']['model_name']} v{out['model']['version']} (@{out['model']['alias']}, "
                   f"{out['model']['family']}) · run {out['model']['run_id'][:10]} · data md5 "
                   f"{(out['model']['data_md5'] or '')[:10]} · {out['latency_ms']} ms")
        st.code(f"curl http://127.0.0.1:8000/recommend/{uid}?k={k}     # uvicorn serving.api:app --port 8000",
                language="bash")

    with st.expander("Audit trail (logs/audit.jsonl)"):
        st.dataframe(pd.DataFrame(read_audit(200)).iloc[::-1], hide_index=True, width="stretch")

st.markdown('<div class="foot"><div style="display:flex;gap:16px;align-items:center"><div class="avs">' + "".join(
    f'<div class="av" style="--c:{STAGE_COLORS[i]}">{initials(m["name"])}</div>' for i, m in enumerate(TEAM)) +
    '</div><div class="tx"><b style="color:var(--head)">RecoMart Data Pipeline</b><br>' +
    " · ".join(m["name"] for m in TEAM) + '</div></div><div class="tx" style="text-align:right">'
    'DSE ZG529 · Data Management for Machine Learning · BITS Pilani WILP<br>Built with Prefect · MLflow · DVC · '
    'Pandera · Streamlit · <a href="https://github.com/Rohesen/recomart-data-pipeline" target="_blank">GitHub</a>'
    '</div></div>', unsafe_allow_html=True)
