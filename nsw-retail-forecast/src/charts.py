"""Draw the charts in charts/ from outputs/.

Usage:
    python src/charts.py
"""

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "charts")
BLUE, GREY, INK = "#2f5bea", "#9aa3b2", "#1a1d24"


def style(ax, title: str) -> None:
    ax.set_title(title, loc="left", fontsize=12, color=INK)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25)


def latest_year_total() -> None:
    f = pd.read_csv(os.path.join(ROOT, "outputs", "forecasts.csv"), parse_dates=["month"])
    f = f[f["industry"] == "Total retail"]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(f["month"], f["actual"] / 1000, color=INK, lw=2, label="Actual")
    ax.plot(f["month"], f["holt_winters"] / 1000, color=BLUE, lw=2, ls="--", label="Holt-Winters")
    ax.plot(f["month"], f["seasonal_naive"] / 1000, color=GREY, lw=2, ls=":", label="Same month last year")
    ax.set_ylabel("$ billion")
    ax.legend(frameon=False)
    style(ax, "NSW retail turnover, July 2024 – June 2025: forecast a year ahead")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "total_retail_forecast.png"), dpi=150)


def error_by_year() -> None:
    with open(os.path.join(ROOT, "outputs", "metrics.json")) as fh:
        by_year = pd.DataFrame(json.load(fh)["by_test_year"]).T
    fig, ax = plt.subplots(figsize=(8, 4))
    x = range(len(by_year))
    ax.bar([i - 0.2 for i in x], by_year["holt_winters"], width=0.4, color=BLUE, label="Holt-Winters")
    ax.bar([i + 0.2 for i in x], by_year["seasonal_naive"], width=0.4, color=GREY, label="Same month last year")
    ax.set_xticks(list(x), by_year.index)
    ax.set_ylabel("Average error, % (MAPE)")
    ax.legend(frameon=False)
    style(ax, "Forecast error by test year, average of six store types")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "error_by_year.png"), dpi=150)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    latest_year_total()
    error_by_year()
