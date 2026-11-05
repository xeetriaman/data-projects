"""Bundle the results into one JSON file for the interactive dashboard on the portfolio site.

Also fits the final live win-probability model on every season (with the Impact Player
era flag) and exports its coefficients, so the website can run it in the browser.

Usage:
    python src/export_dashboard.py
"""

import csv
import json
import os
import sys

import pandas as pd
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, os.path.dirname(__file__))
from model import LIVE_FEATS, chase_features  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")


def read(name):
    with open(os.path.join(ROOT, "outputs", f"{name}.csv"), encoding="utf-8") as f:
        return [{k: _num(v) for k, v in r.items()} for r in csv.DictReader(f)]


def _num(v):
    try:
        return float(v) if "." in v else int(v)
    except ValueError:
        return v


def final_live_model():
    c = chase_features(pd.read_csv(os.path.join(ROOT, "data", "chase_states.csv")))
    c["impact_era"] = (c.season >= 2023).astype(int)
    feats = LIVE_FEATS + ["impact_era"]
    mean, std = c[feats].mean(), c[feats].std(ddof=0)
    model = LogisticRegression(C=1.0, max_iter=1000).fit((c[feats] - mean) / std, c.chasing_team_won)
    return {
        "features": feats,
        "mean": [round(float(x), 6) for x in mean],
        "std": [round(float(x), 6) for x in std],
        "coef": [round(float(x), 6) for x in model.coef_[0]],
        "intercept": round(float(model.intercept_[0]), 6),
        "trained_on_states": int(len(c)),
    }


def main():
    m = pd.read_csv(os.path.join(ROOT, "data", "matches.csv"))
    played = m[m.result != "no result"]
    results = json.load(open(os.path.join(ROOT, "outputs", "model_results.json")))
    data = {
        "summary": {
            "matches": int(len(m)),
            "seasons": f"{m.season.min()}-{m.season.max()}",
            "toss_winner_win_pct": round(100 * float((played.toss_winner == played.winner).mean()), 1),
            "chasing_win_pct": round(100 * float((played.winner == played.bat_second).mean()), 1),
        },
        "toss": read("01_toss_impact"),
        "seasons": [
            {**a, **b}
            for a, b in zip(read("02_chasing_by_season"), read("03_scoring_by_season"))
        ],
        "phases": read("04_phase_run_rates"),
        "venues": read("05_venue_chasing"),
        "teams": read("06_team_records"),
        "prematch": results["results"],
        "live": {k: results["live_chase_model"][k] for k in ("by_stage", "retrain_check", "calibration")},
        "live_model": final_live_model(),
        "test_seasons": results["test_seasons"],
    }
    path = os.path.join(ROOT, "outputs", "dashboard.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=1)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
