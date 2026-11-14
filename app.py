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
import streamlit as st  # noqa: E402
import yaml  # noqa: E402

st.set_page_config(page_title="RecoMart Data Pipeline", page_icon="🛒", layout="wide")

from recomart import ui_theme as ui  # noqa: E402
from recomart.config import (FIGURES, LOG_DIR, PROCESSED, REPORTS, ROOT, SQL_DIR, TEAM,  # noqa: E402
                             WAREHOUSE_DB, cfg)

ui.apply()
PLOT = ui.PLOT


# ---------------------------------------------------------------- bootstrap (first launch)
@st.cache_resource(show_spinner=False)
def bootstrap() -> bool:
    from recomart.pipeline import run_all
    from recomart.train import registry_versions
    try:
        ready = (REPORTS / "model_metrics.json").exists() and not registry_versions().empty
    except Exception:
        ready = False
    if not ready:
        run_all()
    return True


with st.spinner("First launch: generating source data and running the whole pipeline (about a minute)…"):
    bootstrap()

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


def note(kind, html):
    st.markdown(f'<div class="{kind}">{html}</div>', unsafe_allow_html=True)


def tail(path: Path, n=40) -> str:
    return "\n".join(path.read_text(encoding="utf-8").splitlines()[-n:]) if path.exists() else "(no log yet)"


@st.cache_data(show_spinner=False, ttl=30)
def load_json(p: str):
    return json.loads((ROOT / p).read_text())


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
    c = st.columns(6)
    kpi(c[0], "6", "data sources")
    kpi(c[1], f"{len(LakeStorage.manifest()):,}", "objects in raw lake")
    kpi(c[2], f"{prep['events']['clean']:,}", "clean events")
    kpi(c[3], f"{dq['quality_score']}%", "DQ checks passed")
    kpi(c[4], f"{sum(len(v['snapshots']) for v in feature_store.load_registry()['views'].values())}", "feature snapshots")
    kpi(c[5], f"{best[f'ndcg_at_{K}']:.3f}", f"champion NDCG@{K}")
    st.write("")
    st.subheader("Pipeline DAG")
    ui.gv("""digraph G { rankdir=LR; bgcolor="transparent"; nodesep=0.22; ranksep=0.32; pad=0.1;
      node [shape=box style="rounded,filled" fontname="Inter" fontsize=12 margin="0.14,0.06" penwidth=1.4
            color="#2B3D63" fillcolor="#111A2E" fontcolor="#E8EEF7"];
      edge [color="#64748B" arrowsize=0.6 penwidth=1.1];
      src [label="6 sources\\n4 CSV feeds · 2 REST APIs" color="#94A3B8"];
      ing [label="① Ingest\\nretry · logging" color="#93C5FD"]; lake [label="Raw lake\\nsource/type/date" color="#93C5FD"];
      val [label="② Validate\\nDQ report" color="#C4B5FD"]; prep [label="② Prepare\\nclean · encode" color="#C4B5FD"];
      eda [label="② EDA" color="#C4B5FD"]; wh [label="③ SQL warehouse\\n+ features" color="#86EFAC"];
      fs [label="③ Feature store\\nversioned" color="#86EFAC"]; tr [label="④ Train + MLflow" color="#FCD34D"];
      api [label="④ Recommend API" color="#FCD34D"];
      src -> ing -> lake -> val -> prep; prep -> eda; prep -> wh -> fs -> tr -> api; }""")
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
        cc1.dataframe(lr, hide_index=True, width="stretch")
        fig = px.bar(lr, x="seconds", y="stage", orientation="h", color="status",
                     color_discrete_map={"success": ui.GREEN, "failed": ui.RED}, title="Stage duration (s)")
        fig.update_layout(**PLOT, height=300, yaxis={"categoryorder": "array", "categoryarray": lr["stage"][::-1]})
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
    owner(0)
    st.header("① Ingestion, Raw Storage and Data Versioning")
    note("lesson", "<b>Goal:</b> continuously pull every source into one place, never lose or duplicate data, and know "
                   "exactly which version of which data every downstream result came from.")
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
    owner(1)
    st.header("② Data Profiling, Validation, Preparation and EDA")
    note("lesson", "<b>Goal:</b> catch bad data before it reaches the model, repair or quarantine it, and understand "
                   "the shape of the cleaned data.")
    c = st.columns(4)
    kpi(c[0], f"{dq['quality_score']}%", "checks passed")
    kpi(c[1], f"{dq['checks_passed']}/{dq['checks_total']}", "checks")
    kpi(c[2], sum(len(d["schema_drift"]) for d in dq["datasets"]), "schema-drift files")
    kpi(c[3], sum(sum(v.values()) for v in prep["quarantine"].values()), "rows quarantined")
    st.write("")
    ds = pd.DataFrame([{"dataset": d["dataset"], "rows": d["rows"], "files": d["files"], "duplicates %": d["duplicate_pct"],
                        "max missing %": max(d["missing_pct"].values()) if d["missing_pct"] else 0,
                        "checks": f"{d['checks_passed']}/{d['checks_total']}", "status": d["status"]} for d in dq["datasets"]])
    st.dataframe(ds, hide_index=True, width="stretch")
    chk = pd.DataFrame([{"dataset": d["dataset"], **c_} for d in dq["datasets"] for c_ in d["checks"]])
    f1, f2 = st.columns([1, 1])
    with f1:
        flt = st.multiselect("Show checks with status", ["PASS", "WARN", "FAIL"], default=["WARN", "FAIL"])
        st.dataframe(chk[chk.status.isin(flt)][["dataset", "kind", "column", "check", "failures", "pct", "status"]],
                     hide_index=True, width="stretch", height=300)
    with f2:
        miss = pd.DataFrame([{"column": f"{d['dataset']}.{k}", "missing %": v} for d in dq["datasets"]
                             for k, v in d["missing_pct"].items() if v > 0]).sort_values("missing %")
        if not miss.empty:
            fig = px.bar(miss, x="missing %", y="column", orientation="h", title="Missing values",
                         color_discrete_sequence=[ui.GREY])
            fig.update_layout(**PLOT, height=320)
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
                 barmode="group", title="Rows before and after cleaning", log_y=True,
                 color_discrete_sequence=[ui.GREY, ui.GREEN])
    fig.update_layout(**PLOT, height=320)
    p1.plotly_chart(fig, width="stretch")
    p2.dataframe(q, hide_index=True, width="stretch")
    p2.caption("Quarantined rows are kept in data/lake/quarantine/ with their reason code.")

    st.subheader("Exploratory data analysis")
    eda_s = load_json("reports/eda_summary.json")
    c = st.columns(5)
    kpi(c[0], f"{eda_s['sparsity_pct']}%", "user-item sparsity")
    kpi(c[1], f"{eda_s['purchase_pairs_sparsity_pct']}%", "purchase sparsity")
    kpi(c[2], eda_s["item_popularity_gini"], "popularity Gini")
    kpi(c[3], f"{eda_s['top10pct_items_share']:.0%}", "share of top 10% items")
    kpi(c[4], f"{eda_s['view_to_purchase_pct']}%", "view → purchase")
    st.write("")
    figs = sorted(FIGURES.glob("*.png"))
    for i in range(0, len(figs), 2):
        cols = st.columns(2)
        for col, f in zip(cols, figs[i:i + 2]):
            col.image(str(f), width="stretch")

# ================================================================ 3. FEATURES / WAREHOUSE / FEATURE STORE
with tabs[3]:
    owner(2)
    st.header("③ Feature Engineering, Warehouse and Feature Store")
    note("lesson", "<b>Goal:</b> turn cleaned data into reusable, documented, versioned features that are identical "
                   "for training and inference.")
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
    owner(3)
    st.header("④ Model Training, Experiment Tracking, Orchestration and Serving")
    note("lesson", f"<b>Protocol:</b> time-based split at {mm['cutoff']} (last {cfg()['training']['test_days']} days held "
                   f"out); a hit is a product the user added to cart or bought afterwards and had never interacted with; "
                   f"{mm['eval_users']} users evaluated.")
    res = pd.DataFrame(mm["results"])
    cols = ["model", f"precision_at_{K}", f"recall_at_{K}", f"ndcg_at_{K}", f"hit_rate_at_{K}", f"map_at_{K}",
            "catalog_coverage", "train_seconds"]
    st.dataframe(res[cols], hide_index=True, width="stretch")
    melt = res.melt("model", [f"precision_at_{K}", f"recall_at_{K}", f"ndcg_at_{K}", f"hit_rate_at_{K}"],
                    var_name="metric", value_name="value")
    fig = px.bar(melt, x="metric", y="value", color="model", barmode="group", title="Ranking metrics by model",
                 color_discrete_sequence=[ui.GREY, ui.TEAL, ui.AMBER, ui.GREEN])
    fig.update_layout(**PLOT, height=340)
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
            st.dataframe(agg.head(15), hide_index=True, width="stretch")
        st.markdown("**Alerts** (logs/alerts.log)")
        st.code(tail(LOG_DIR / "alerts.log", 8), language="text")

    st.subheader("Recommendation service")
    s1, s2 = st.columns([1, 2])
    with s1:
        mode = st.radio("User", ["Existing customer", "New visitor (cold start)"], horizontal=True)
        uid = st.selectbox("Customer", users[:300]) if mode == "Existing customer" else "U99999"
        k = st.slider("How many recommendations", 3, 20, 10)
        hist = pd.read_parquet(PROCESSED / "interactions.parquet")
        hist = hist[hist.user_id == uid].merge(prods, on="product_id").sort_values("strength", ascending=False)
        if len(hist):
            st.markdown("**Recent interests**")
            st.dataframe(hist[["title", "category", "strength"]].head(8), hide_index=True, width="stretch")
    with s2:
        out = recommend(uid, k)
        st.dataframe(pd.DataFrame(out["items"])[["rank", "title", "category", "price", "avg_rating", "buyers", "reason"]],
                     hide_index=True, width="stretch")
        st.caption(f"Model {out['model']['model_name']} v{out['model']['version']} (@{out['model']['alias']}, "
                   f"{out['model']['family']}) · run {out['model']['run_id'][:10]} · data md5 "
                   f"{(out['model']['data_md5'] or '')[:10]} · {out['latency_ms']} ms")
        st.code(f"curl http://127.0.0.1:8000/recommend/{uid}?k={k}     # uvicorn serving.api:app --port 8000",
                language="bash")

    with st.expander("Audit trail (logs/audit.jsonl)"):
        st.dataframe(pd.DataFrame(read_audit(200)).iloc[::-1], hide_index=True, width="stretch")

st.markdown("<br><center style='color:var(--muted);font-size:.8rem'>DSE ZG529 · Data Management for Machine Learning · "
            "BITS Pilani WILP · Experiential Learning Assignment (EC1)</center>", unsafe_allow_html=True)
