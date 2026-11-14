"""Neutral, print-friendly matplotlib style shared by the DQ report and EDA figures."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

INK, GREY, RUST, OLIVE, OCHRE, STONE = "#27272A", "#71717A", "#9A3412", "#3F6212", "#B45309", "#A8A29E"
PALETTE = [INK, OCHRE, OLIVE, RUST, STONE, GREY]


def style():
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 160, "savefig.bbox": "tight",
        "font.family": "serif", "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
        "axes.edgecolor": "#52525B", "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
        "axes.grid": True, "grid.color": "#E4E4E7", "grid.linewidth": 0.6, "axes.spines.top": False,
        "axes.spines.right": False, "axes.prop_cycle": matplotlib.cycler(color=PALETTE),
    })
