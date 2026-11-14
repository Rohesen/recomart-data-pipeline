"""Renders reports/dq/data_quality_report.pdf from dq_results.json (matplotlib only, no extra deps)."""
from __future__ import annotations

import json
import textwrap

from matplotlib.backends.backend_pdf import PdfPages

from .plotting import GREY, INK, OCHRE, OLIVE, RUST, plt, style
from .validation import DQ_DIR

STATUS_COL = {"PASS": OLIVE, "WARN": OCHRE, "FAIL": RUST}


def _page(pdf, title):
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.text(0.07, 0.95, title, fontsize=15, fontweight="bold", color=INK)
    fig.text(0.07, 0.935, "RecoMart · Data Quality Report · DSE ZG529", fontsize=8, color=GREY)
    return fig


def _table(ax, rows, cols, widths, status_col=None, fs=8):
    ax.axis("off")
    t = ax.table(cellText=rows, colLabels=cols, colWidths=widths, loc="upper left", cellLoc="left")
    t.auto_set_font_size(False); t.set_fontsize(fs); t.scale(1, 1.35)
    for (r, c), cell in t.get_celld().items():
        cell.set_edgecolor("#A1A1AA"); cell.set_linewidth(0.4)
        if r == 0:
            cell.set_facecolor("#E4E4E7"); cell.set_text_props(fontweight="bold")
        elif status_col is not None and c == status_col:
            cell.set_text_props(color=STATUS_COL.get(cell.get_text().get_text(), INK), fontweight="bold")
    return t


def build_pdf(results: dict | None = None) -> str:
    style()
    results = results or json.loads((DQ_DIR / "dq_results.json").read_text())
    out = DQ_DIR / "data_quality_report.pdf"
    with PdfPages(out) as pdf:
        # ---- page 1: summary
        fig = _page(pdf, "Data Quality Report")
        fig.text(0.07, 0.89, f"Generated: {results['generated_at']}", fontsize=9)
        fig.text(0.07, 0.86, f"Overall quality score: {results['quality_score']}%  "
                 f"({results['checks_passed']} of {results['checks_total']} checks passed)", fontsize=12, fontweight="bold")
        intro = ("Every raw-lake dataset is checked for schema conformance, completeness (missing values), uniqueness "
                 "(duplicates), validity (ranges, allowed values, ID and timestamp formats) and referential integrity. "
                 "PASS = within threshold, WARN = minor issue handled by the preparation stage (rows are cleaned or "
                 "quarantined), FAIL = blocks the pipeline.")
        fig.text(0.07, 0.80, textwrap.fill(intro, 105), fontsize=9, va="top")
        ax = fig.add_axes([0.07, 0.52, 0.86, 0.22])
        rows = [[d["dataset"], f"{d['rows']:,}", d["files"], f"{d['duplicate_pct']}%",
                 f"{max(d['missing_pct'].values()) if d['missing_pct'] else 0}%", len(d["schema_drift"]),
                 f"{d['checks_passed']}/{d['checks_total']}", d["status"]] for d in results["datasets"]]
        _table(ax, rows, ["Dataset", "Rows", "Files", "Duplicates", "Max missing", "Schema drift", "Checks", "Status"],
               [0.13, 0.12, 0.08, 0.12, 0.13, 0.13, 0.1, 0.1], status_col=7, fs=9)
        ax2 = fig.add_axes([0.1, 0.1, 0.8, 0.33])
        names = [d["dataset"] for d in results["datasets"]]
        ax2.bar(names, [100 * d["checks_passed"] / max(d["checks_total"], 1) for d in results["datasets"]],
                color=[STATUS_COL[d["status"]] for d in results["datasets"]])
        ax2.set_ylim(0, 105); ax2.set_ylabel("% checks passed"); ax2.set_title("Checks passed per dataset")
        pdf.savefig(fig); plt.close(fig)

        # ---- page 2: completeness
        fig = _page(pdf, "Completeness: missing values by column")
        ax = fig.add_axes([0.3, 0.1, 0.62, 0.78])
        items = [(f"{d['dataset']}.{c}", p) for d in results["datasets"] for c, p in d["missing_pct"].items() if p > 0]
        items = sorted(items, key=lambda x: x[1])
        if items:
            ax.barh([i[0] for i in items], [i[1] for i in items], color=GREY)
            for y, (_, v) in enumerate(items):
                ax.text(v, y, f" {v:.2f}%", va="center", fontsize=8)
        ax.set_xlabel("% of rows missing")
        pdf.savefig(fig); plt.close(fig)

        # ---- page 3: all checks
        fig = _page(pdf, "Check results")
        ax = fig.add_axes([0.05, 0.05, 0.9, 0.85])
        rows = [[d["dataset"], c["kind"], c["column"], textwrap.shorten(c["check"], 34), f"{c['failures']:,}",
                 f"{c['pct']}%", c["status"]] for d in results["datasets"] for c in d["checks"]][:52]
        _table(ax, rows, ["Dataset", "Dimension", "Column", "Check", "Failures", "%", "Status"],
               [0.11, 0.14, 0.14, 0.33, 0.1, 0.08, 0.1], status_col=6, fs=7.5)
        pdf.savefig(fig); plt.close(fig)

        # ---- page 4: schema drift + actions
        fig = _page(pdf, "Schema drift and remediation")
        y = 0.88
        drift = [(d["dataset"], s) for d in results["datasets"] for s in d["schema_drift"]]
        if not drift:
            fig.text(0.07, y, "No schema drift detected.", fontsize=10)
        for ds, s in drift:
            fig.text(0.07, y, f"{ds}: {s['file']}  missing {s['missing_columns']}  unexpected {s['unexpected_columns']}",
                     fontsize=9); y -= 0.03
        actions = [
            "Renamed upstream columns (e.g. userId) are mapped to the canonical contract before preparation.",
            "Exact duplicate rows are dropped; duplicate keys keep the latest record.",
            "Rows with invalid timestamps, unknown product IDs, out-of-range ratings or non-positive quantities are "
            "moved to data/lake/quarantine/ with a reason code, never silently deleted.",
            "Missing device/session values are imputed as 'unknown'; missing brands as 'Unknown'; invalid prices are "
            "replaced by the category median.",
            "Thresholds (configs/pipeline.yaml): max missing 2%, max duplicates 1% per dataset.",
        ]
        fig.text(0.07, y - 0.04, "Remediation applied by the preparation stage", fontsize=11, fontweight="bold")
        y -= 0.08
        for a in actions:
            fig.text(0.09, y, textwrap.fill("• " + a, 100), fontsize=9, va="top"); y -= 0.05
        pdf.savefig(fig); plt.close(fig)
    return str(out)


if __name__ == "__main__":
    print(build_pdf())
