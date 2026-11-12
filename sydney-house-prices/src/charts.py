"""Draw the charts in charts/ from the outputs of run_sql.py and model.py.

Usage:
    python src/charts.py
"""

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "outputs")
CHARTS = os.path.join(ROOT, "charts")
BLUE, GREY = "#2f43b8", "#9aa0b5"


def save(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS, name), dpi=150)
    plt.close(fig)


def median_by_quarter() -> None:
    q = pd.read_csv(os.path.join(OUT, "01_median_by_quarter.csv"))
    q = q[q["quarter"] >= "2018-Q1"]  # 2017 contracts in a 2018 settlement file are not representative
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(q["quarter"], q["median_price"] / 1e6, marker="o", color=BLUE)
    for x, y in zip(q["quarter"], q["median_price"] / 1e6):
        ax.annotate(f"${y:.2f}m", (x, y), textcoords="offset points", xytext=(0, 8), ha="center")
    ax.set(title="Median Sydney house price by quarter, 2018", ylabel="Median price ($m)")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "median_by_quarter.png")


def model_accuracy() -> None:
    with open(os.path.join(OUT, "metrics.json")) as f:
        models = json.load(f)["models"]
    names = list(models)
    values = [models[n]["median_abs_pct_error"] for n in names]
    fig, ax = plt.subplots(figsize=(7, 3.5))
    bars = ax.barh(names, values, color=[GREY] + [BLUE] * (len(names) - 1))
    ax.bar_label(bars, labels=[f"{v}%" for v in values], padding=4)
    ax.invert_yaxis()
    ax.set(title="Median error on July-December 2018 sales (lower is better)", xlabel="Median absolute % error")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "model_accuracy.png")


def predicted_vs_actual() -> None:
    t = pd.read_csv(os.path.join(OUT, "test_predictions.csv"))
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.scatter(t["price"] / 1e6, t["predicted"] / 1e6, s=3, alpha=0.25, color=BLUE)
    ax.plot([0.15, 20], [0.15, 20], color="black", lw=1)
    ax.set(xscale="log", yscale="log", xlabel="Actual price ($m)", ylabel="Predicted price ($m)",
           title="Gradient boosting: predicted vs actual")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "predicted_vs_actual.png")


def main() -> None:
    os.makedirs(CHARTS, exist_ok=True)
    median_by_quarter()
    model_accuracy()
    predicted_vs_actual()


if __name__ == "__main__":
    main()
