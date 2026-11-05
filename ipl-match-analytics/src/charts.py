"""Draw the charts used in the README from the SQL outputs and model results.

Usage:
    python src/charts.py
"""

import csv
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "charts")
INK, MUTED, GRID = "#172033", "#5A6478", "#E3E7EF"
BLUE, AMBER, GREY = "#2A55E5", "#E8A317", "#B8C0CE"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.edgecolor": GRID,
    "axes.labelcolor": MUTED,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.titlecolor": INK,
    "axes.titlelocation": "left",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
})


def read(name):
    with open(os.path.join(ROOT, "outputs", f"{name}.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, name), facecolor="white")
    plt.close(fig)


def scoring():
    rows = read("03_scoring_by_season")
    seasons = [int(r["season"]) for r in rows]
    avg = [float(r["avg_first_innings"]) for r in rows]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.axvspan(2022.5, max(seasons) + 0.5, color=AMBER, alpha=0.12, lw=0)
    ax.plot(seasons, avg, color=BLUE, lw=2.5, marker="o", ms=4)
    ax.text(2022.7, max(avg) - 2, "Impact Player\nrule (2023)", color=INK, fontsize=10, va="top")
    ax.set_title("Average first-innings score by season")
    ax.set_ylabel("Runs")
    ax.set_xticks(seasons[::2])
    ax.grid(axis="x", visible=False)
    save(fig, "scores_by_season.png")


def toss_vs_chase():
    rows = read("02_chasing_by_season")
    seasons = [int(r["season"]) for r in rows]
    field = [float(r["chose_to_field_pct"]) for r in rows]
    chase = [float(r["chasing_win_pct"]) for r in rows]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.axhline(50, color=MUTED, lw=1, ls="--")
    ax.plot(seasons, field, color=GREY, lw=2.5, marker="o", ms=4, label="Toss winners who chose to field")
    ax.plot(seasons, chase, color=BLUE, lw=2.5, marker="o", ms=4, label="Matches won by the chasing side")
    ax.set_title("Captains choose to chase far more often than chasing pays off")
    ax.set_ylabel("% of matches")
    ax.set_ylim(25, 95)
    ax.set_xticks(seasons[::2])
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False, loc="upper left")
    save(fig, "toss_vs_chase.png")


def phases():
    rows = read("04_phase_run_rates")
    order = ["powerplay", "middle", "death"]
    labels = ["Powerplay (1-6)", "Middle (7-15)", "Death (16-20)"]
    old = {r["phase"]: float(r["run_rate"]) for r in rows if r["era"] == "2008-2022"}
    new = {r["phase"]: float(r["run_rate"]) for r in rows if r["era"] != "2008-2022"}
    fig, ax = plt.subplots(figsize=(9, 4.2))
    x = range(len(order))
    ax.bar([i - 0.2 for i in x], [old[p] for p in order], 0.38, color=GREY, label="2008-2022")
    ax.bar([i + 0.2 for i in x], [new[p] for p in order], 0.38, color=BLUE, label="2023 onwards")
    for i, p in enumerate(order):
        ax.text(i - 0.2, old[p] + 0.15, f"{old[p]:.1f}", ha="center", color=MUTED, fontsize=10)
        ax.text(i + 0.2, new[p] + 0.15, f"{new[p]:.1f}", ha="center", color=INK, fontsize=10, weight="bold")
    ax.set_xticks(list(x), labels)
    ax.set_title("Runs per over by phase of the innings")
    ax.set_ylabel("Runs per over")
    ax.set_ylim(0, 12.5)
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False, loc="upper left")
    save(fig, "run_rate_by_phase.png")


def venues():
    rows = sorted(read("05_venue_chasing"), key=lambda r: float(r["chasing_win_pct"]))
    names = [f'{r["venue"]} ({r["matches"]})' for r in rows]
    vals = [float(r["chasing_win_pct"]) for r in rows]
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.barh(names, vals, color=[BLUE if v > 55 else GREY for v in vals], height=0.65)
    ax.axvline(50, color=MUTED, lw=1, ls="--")
    for i, v in enumerate(vals):
        ax.text(v + 0.6, i, f"{v:.0f}%", va="center", color=INK, fontsize=10)
    ax.set_xlim(0, 75)
    ax.set_title("Chasing win rate by ground (completed matches in brackets)")
    ax.set_xlabel("% of matches won by the chasing side")
    ax.grid(axis="y", visible=False)
    save(fig, "chasing_by_venue.png")


def models():
    res = json.load(open(os.path.join(ROOT, "outputs", "model_results.json")))
    pre = res["results"]
    live = res["live_chase_model"]["by_stage"]
    names = list(pre) + [f"Live model: {k.lower()}" for k in live]
    vals = [v["accuracy"] * 100 for v in pre.values()] + [v["accuracy"] * 100 for v in live.values()]
    colors = [GREY] * 4 + [BLUE] * 2 + [AMBER] * len(live)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(names[::-1], vals[::-1], color=colors[::-1], height=0.65)
    ax.axvline(50, color=MUTED, lw=1, ls="--")
    for i, v in enumerate(vals[::-1]):
        ax.text(v + 0.8, i, f"{v:.0f}%", va="center", color=INK, fontsize=10)
    ax.set_xlim(0, 100)
    ax.set_title(f"Accuracy on unseen seasons ({res['test_seasons']})")
    ax.set_xlabel("% of matches called correctly")
    ax.grid(axis="y", visible=False)
    save(fig, "model_accuracy.png")


def calibration():
    live = json.load(open(os.path.join(ROOT, "outputs", "model_results.json")))["live_chase_model"]
    cal = live["calibration"]
    fig, ax = plt.subplots(figsize=(5.2, 5))
    ax.plot([0, 100], [0, 100], color=MUTED, lw=1, ls="--", label="Perfect calibration")
    ax.plot([c["predicted"] * 100 for c in cal], [c["actual"] * 100 for c in cal], color=BLUE, lw=2.5, marker="o", label="Live chase model")
    ax.set_title("Predicted vs actual win rate")
    ax.set_xlabel("Predicted chance of chasing team winning (%)")
    ax.set_ylabel("Actual win rate (%)")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.legend(frameon=False, loc="upper left")
    save(fig, "calibration.png")


if __name__ == "__main__":
    scoring()
    toss_vs_chase()
    phases()
    venues()
    models()
    calibration()
    print("Charts written to charts/")
